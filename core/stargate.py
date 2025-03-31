"""
Stargate protocol integration module for LayerZero V2
"""

from typing import Optional, Tuple, Literal
import time
import aiohttp

from web3 import AsyncWeb3
from web3.contract import AsyncContract

from core.client import Client
from core.database import db  # Import the database
from core.logger import logger
from core.constants import (
    STARGATE_ETH_NATIVE_POOL_ADDRESSES,
    STARGATE_NATIVE_POOL_ABI,
    EMPTY_DATA,
    MAX_SLIPPAGE,
    STARGATE_FULL_BRIDGE_SIMULATION_TX_VALUE,
    GAS_FEES_ESTIMATION_MULTIPLIER,
)
from core.models.chain import Chain
from core.utils import address_to_bytes32


class Stargate:
    """Stargate V2 protocol integration for bridging ETH across chains"""

    def __init__(self, client: Client):
        """
        Initialize Stargate integration

        Args:
            client: Client object connected to the source chain
        """
        self.client = client

        # Validate that the chain is supported
        if self.client.chain.chain_id not in STARGATE_ETH_NATIVE_POOL_ADDRESSES:
            raise ValueError(f"Chain {self.client.chain.name} is not supported for Stargate ETH bridging")

        self.contract: AsyncContract = self.client.w3.eth.contract(
            address=STARGATE_ETH_NATIVE_POOL_ADDRESSES[self.client.chain.chain_id],
            abi=STARGATE_NATIVE_POOL_ABI
        )

    async def _get_tx_data(
        self, dst_chain_lz_eid: int, amount: int, mode: Literal["TAXI", "BUS"]
    ) -> Tuple[int, Tuple, Tuple]:
        """
        Get transaction data for a bridge operation

        Args:
            dst_chain_lz_eid: Destination chain LayerZero endpoint ID
            amount: Amount to bridge in wei
            mode: Bridge mode (TAXI or BUS)

        Returns:
            Tuple of (total value to send, send parameters, message fee)
        """
        try:
            oft_cmd = "0x01" if mode == "BUS" else "0x"

            send_param = (
                dst_chain_lz_eid,
                address_to_bytes32(self.client.address),
                amount,
                int(amount * (100 - MAX_SLIPPAGE) / 100),
                EMPTY_DATA,
                EMPTY_DATA,
                oft_cmd,
            )
            message_fee = await self.contract.functions.quoteSend(send_param, False).call()
            value = amount + message_fee[0]
            return value, send_param, message_fee
        except Exception as e:
            raise Exception(f"Failed to build tx data: {e}")

    async def _estimate_amount_for_full_amount_bridge(
        self, amount: Optional[float], dst_chain_lz_eid: int, mode: Literal["TAXI", "BUS"]
    ) -> float:
        """
        Estimate the maximum amount that can be bridged accounting for gas fees

        Args:
            amount: Amount to bridge in ether, or None to use full balance
            dst_chain_lz_eid: Destination chain LayerZero endpoint ID
            mode: Bridge mode (TAXI or BUS)

        Returns:
            Maximum amount that can be bridged in ether
        """
        try:
            if amount is None:
                amount_wei = STARGATE_FULL_BRIDGE_SIMULATION_TX_VALUE
            else:
                amount_wei = AsyncWeb3.to_wei(amount, "ether")

            value, send_param, message_fee = await self._get_tx_data(
                dst_chain_lz_eid=dst_chain_lz_eid, amount=amount_wei, mode=mode
            )

            data = self.contract.encodeABI("send", args=(send_param, message_fee, self.client.address))
            tx_params = await self.client.get_tx_params(to=self.contract.address, data=data, value=value)
            gas_used = await self.client.get_gas_estimate(tx_params=tx_params)
            gas_fee = gas_used * (await self.client.w3.eth.gas_price)

            initial_amount = await self.client.get_native_balance() if amount is None else amount_wei
            return float(
                AsyncWeb3.from_wei(
                    (initial_amount - message_fee[0] - gas_fee) * GAS_FEES_ESTIMATION_MULTIPLIER, "ether"
                )
            )
        except Exception as e:
            raise Exception(f"Failed to estimate transaction fees: {e}")

    async def _get_eth_price(self) -> float:
        """
        Get current ETH price in USD

        Returns:
            ETH price in USD
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd") as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data["ethereum"]["usd"])
                    else:
                        # Fallback price if API fails
                        logger.warning("Failed to get ETH price from API. Using fallback price.")
                        return 3000.0  # Default fallback price
        except Exception as e:
            logger.warning(f"Error getting ETH price: {e}. Using fallback price.")
            return 3000.0  # Default fallback price

    async def bridge(
        self, dst_chain: Chain, amount: Optional[float], mode: Literal["TAXI", "BUS"], include_fees: bool = False
    ) -> bool:
        """
        Bridge ETH from current chain to destination chain

        Args:
            dst_chain: Destination Chain object
            amount: Amount to bridge in ether, or None to use full balance
            mode: Bridge mode (TAXI or BUS)
            include_fees: Whether to include fees in amount calculation

        Returns:
            True if bridging was successful, False otherwise
        """
        try:
            start_time = time.time()
            gas_price = await self.client.w3.eth.gas_price
            gas_price_gwei = self.client.w3.from_wei(gas_price, 'gwei')

            # Get ETH price in USD
            eth_price_usd = await self._get_eth_price()

            # Store initial balance for tracking
            initial_balance = await self.client.get_native_balance(wei=False)

            if amount is None or include_fees:
                amount = await self._estimate_amount_for_full_amount_bridge(
                    amount=amount, dst_chain_lz_eid=dst_chain.lz_eid, mode=mode
                )

            logger.info(f"[Stargate {mode}] Bridging {amount} ETH from {self.client.chain.name} to {dst_chain.name}")

            value, send_param, message_fee = await self._get_tx_data(
                dst_chain_lz_eid=dst_chain.lz_eid, amount=AsyncWeb3.to_wei(amount, "ether"), mode=mode
            )

            data = self.contract.encodeABI("send", args=(send_param, message_fee, self.client.address))

            # Get gas estimate to calculate total fees
            tx_params = await self.client.get_tx_params(to=self.contract.address, data=data, value=value)
            gas_estimate = await self.client.get_gas_estimate(tx_params=tx_params)

            # Calculate transaction fees
            gas_fee_wei = gas_estimate * gas_price
            gas_fee_eth = self.client.w3.from_wei(gas_fee_wei, 'ether')

            # Calculate bridge fees
            bridge_fee_eth = self.client.w3.from_wei(message_fee[0], 'ether')

            # Calculate total fees in ETH and USD
            total_fee_eth = float(gas_fee_eth) + float(bridge_fee_eth)
            total_fee_usd = total_fee_eth * eth_price_usd

            # Execute transaction
            tx_hash = await self.client.send_transaction(to=self.contract.address, data=data, value=value)
            success = await self.client.verify_tx(tx_hash=tx_hash)

            # Recalculate actual gas fee if transaction was successful
            actual_gas_fee_eth = 0
            actual_gas_fee_usd = 0

            if success and tx_hash:
                try:
                    receipt = await self.client.w3.eth.get_transaction_receipt(tx_hash)
                    actual_gas_used = receipt.get('gasUsed', gas_estimate)
                    actual_gas_fee_wei = actual_gas_used * gas_price
                    actual_gas_fee_eth = float(self.client.w3.from_wei(actual_gas_fee_wei, 'ether'))
                    actual_gas_fee_usd = actual_gas_fee_eth * eth_price_usd

                    # Update total fees
                    total_fee_eth = actual_gas_fee_eth + float(bridge_fee_eth)
                    total_fee_usd = total_fee_eth * eth_price_usd
                except Exception as e:
                    logger.warning(f"Error calculating actual gas fees: {e}")

            # Record transaction in database with fee information
            tx_data = {
                "tx_hash": self.client.w3.to_hex(tx_hash) if tx_hash else None,
                "from_chain": self.client.chain.name,
                "to_chain": dst_chain.name,
                "amount": amount,
                "mode": mode,
                "gas_price_gwei": float(gas_price_gwei),
                "gas_fee_eth": actual_gas_fee_eth if success and tx_hash else float(gas_fee_eth),
                "bridge_fee_eth": float(bridge_fee_eth),
                "total_fee_eth": total_fee_eth,
                "eth_price_usd": eth_price_usd,
                "total_fee_usd": total_fee_usd,
                "message_fee_wei": int(message_fee[0]),
                "success": success,
                "timestamp": time.time(),
                "duration": time.time() - start_time
            }

            db.add_transaction(self.client.address, tx_data)

            return success
        except Exception as e:
            # Record error in database
            error_data = {
                "from_chain": self.client.chain.name,
                "to_chain": dst_chain.name,
                "amount": amount,
                "mode": mode,
                "error": str(e),
                "success": False,
                "timestamp": time.time()
            }
            db.add_transaction(self.client.address, error_data)

            logger.error(
                f"[Stargate] Error while bridging {amount} ETH from {self.client.chain.name} to {dst_chain.name}: {e}"
            )
            return False