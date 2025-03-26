"""
Stargate protocol integration module for LayerZero V2
"""

from typing import Optional, Tuple, Literal

from web3 import AsyncWeb3
from web3.contract import AsyncContract

from core.client import Client
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
            if amount is None or include_fees:
                amount = await self._estimate_amount_for_full_amount_bridge(
                    amount=amount, dst_chain_lz_eid=dst_chain.lz_eid, mode=mode
                )

            logger.info(f"[Stargate {mode}] Bridging {amount} ETH from {self.client.chain.name} to {dst_chain.name}")

            value, send_param, message_fee = await self._get_tx_data(
                dst_chain_lz_eid=dst_chain.lz_eid, amount=AsyncWeb3.to_wei(amount, "ether"), mode=mode
            )

            data = self.contract.encodeABI("send", args=(send_param, message_fee, self.client.address))

            tx_hash = await self.client.send_transaction(to=self.contract.address, data=data, value=value)
            return await self.client.verify_tx(tx_hash=tx_hash)
        except Exception as e:
            logger.error(
                f"[Stargate] Error while bridging {amount} ETH from {self.client.chain.name} to {dst_chain.name}: {e}"
            )
            return False
