"""
Core client module for interacting with EVM-compatible blockchains
"""

import asyncio
from typing import Dict, Optional, Union

from aiohttp_proxy import ProxyConnector
from web3 import AsyncWeb3
from web3.middleware import async_geth_poa_middleware

from core import logger
from core.constants import GAS_MULTIPLIER, RETRIES
from core.models.chain import Chain
from core.utils import retry_on_fail


class Client:
    """Client for interacting with EVM-compatible blockchains"""
    
    def __init__(self, private_key: str, proxy: str = None, chain: Chain = None) -> None:
        """
        Initialize a blockchain client
        
        Args:
            private_key: Wallet private key
            proxy: Optional proxy server in format user:pass@ip:port
            chain: Chain object representing the blockchain to connect to
        """
        self.private_key = private_key
        self.chain = chain
        self.proxy = proxy
        self.w3 = self.init_web3(chain=chain) if chain else None
        
        if self.w3:
            self.address = AsyncWeb3.to_checksum_address(
                value=self.w3.eth.account.from_key(private_key=private_key).address
            )
        else:
            # Initialize address even without a chain for convenience
            temp_w3 = AsyncWeb3()
            self.address = AsyncWeb3.to_checksum_address(
                value=temp_w3.eth.account.from_key(private_key=private_key).address
            )

    def __str__(self) -> str:
        return self.address

    def __repr__(self) -> str:
        return self.address

    def init_web3(self, chain: Chain = None):
        """
        Initialize Web3 connection to the specified chain
        
        Args:
            chain: Chain object with connection details
            
        Returns:
            AsyncWeb3 instance connected to the specified chain
        """
        if not chain:
            raise ValueError("Chain must be specified")
            
        if not chain.rpc:
            raise ValueError(f"No RPC endpoint specified for chain {chain.name}")

        request_kwargs = {"proxy": f"http://{self.proxy}"} if self.proxy else {}
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(endpoint_uri=chain.rpc, request_kwargs=request_kwargs))
        
        # Add POA middleware for chains that need it
        if chain.requires_poa_middleware:
            w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
            
        return w3

    def change_chain(self, chain: Chain) -> None:
        """
        Change the chain the client is connected to
        
        Args:
            chain: New Chain object to connect to
        """
        self.chain = chain
        self.w3 = self.init_web3(chain=chain)

    async def send_transaction(
        self,
        to: str,
        data: str = None,
        from_: str = None,
        value: int = None,
    ):
        """
        Build and send a transaction
        
        Args:
            to: Recipient address
            data: Transaction data (for contract interactions)
            from_: Sender address (defaults to client address)
            value: Amount of native token to send (in wei)
            
        Returns:
            Transaction hash if successful
        """
        tx_params = await self.get_tx_params(to=to, data=data, from_=from_, value=value)
        tx_params["gas"] = await self.get_gas_estimate(tx_params=tx_params)

        sign = self.w3.eth.account.sign_transaction(tx_params, self.private_key)

        try:
            tx_hash = await self.w3.eth.send_raw_transaction(sign.rawTransaction)
            return tx_hash
        except Exception as e:
            logger.error(f"Error while sending transaction: {e}")
            return None

    async def get_gas_estimate(self, tx_params: dict) -> int:
        """
        Estimate gas for a transaction
        
        Args:
            tx_params: Transaction parameters
            
        Returns:
            Estimated gas amount
        """
        for _ in range(3):  # Retry a few times in case of blockchain reorg
            try:
                return await self.w3.eth.estimate_gas(tx_params)
            except Exception as e:
                if 'Block with id:' in str(e):
                    await asyncio.sleep(1)
                    continue
                raise e
        
        # If we're still here after retries, try one last time and let any error propagate
        return await self.w3.eth.estimate_gas(tx_params)

    async def get_tx_params(self, to: str, data: str = None, from_: str = None, value: int = None) -> Dict:
        """
        Build transaction parameters
        
        Args:
            to: Recipient address
            data: Transaction data (for contract interactions)
            from_: Sender address (defaults to client address)
            value: Amount of native token to send (in wei)
            
        Returns:
            Dictionary of transaction parameters
        """
        if not from_:
            from_ = self.address

        tx_params = {
            "chainId": await self.w3.eth.chain_id,
            "nonce": await self.w3.eth.get_transaction_count(self.address),
            "from": self.w3.to_checksum_address(from_),
            "to": self.w3.to_checksum_address(to),
        }

        if data:
            tx_params["data"] = data

        if value:
            tx_params["value"] = value

        if self.chain.eip_1559:
            eip1559_params = await self._get_eip1559_params()
            tx_params["maxPriorityFeePerGas"] = eip1559_params["max_priority_fee_per_gas"]
            tx_params["maxFeePerGas"] = eip1559_params["max_fee_per_gas"]
        else:
            tx_params["gasPrice"] = await self.w3.eth.gas_price

        return tx_params

    async def verify_tx(self, tx_hash: str) -> bool:
        """
        Verify if a transaction was successful
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            True if transaction was successful, False otherwise
        """
        try:
            if tx_hash is None:
                return False

            response = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)

            if "status" in response and response["status"] == 1:
                logger.success(f"Transaction was successful: {self.chain.explorer}tx/{self.w3.to_hex(tx_hash)}")
                return True
            else:
                logger.error(f"Transaction failed: {self.chain.explorer}tx/{self.w3.to_hex(tx_hash)}")
                return False

        except Exception as e:
            logger.error(f"Unexpected error in verify_tx function: {e}")
            return False

    async def _get_eip1559_params(self) -> Dict[str, int]:
        """
        Get EIP-1559 gas parameters
        
        Returns:
            Dictionary with max_priority_fee_per_gas and max_fee_per_gas
        """
        w3 = self.init_web3(chain=self.chain)
        
        # Ensure POA middleware for chains that need it
        if self.chain.requires_poa_middleware:
            w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

        last_block = await w3.eth.get_block("latest")

        max_priority_fee_per_gas = await self.get_max_priority_fee_per_gas(w3=w3, block=last_block)
        base_fee = int(last_block["baseFeePerGas"] * GAS_MULTIPLIER)
        max_fee_per_gas = base_fee + max_priority_fee_per_gas

        return {"max_priority_fee_per_gas": max_priority_fee_per_gas, "max_fee_per_gas": max_fee_per_gas}

    @staticmethod
    async def get_max_priority_fee_per_gas(w3: AsyncWeb3, block: dict) -> int:
        """
        Determine the appropriate max priority fee per gas based on recent transactions
        
        Args:
            w3: AsyncWeb3 instance
            block: Block data
            
        Returns:
            Appropriate max priority fee per gas value
        """
        block_number = block["number"]

        latest_block_transaction_count = await w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_list = []
        
        for i in range(latest_block_transaction_count):
            try:
                transaction = await w3.eth.get_transaction_by_block(block_number, i)
                if "maxPriorityFeePerGas" in transaction:
                    max_priority_fee_per_gas_list.append(transaction["maxPriorityFeePerGas"])
            except Exception:
                continue

        if not max_priority_fee_per_gas_list:
            try:
                max_priority_fee_per_gas = await w3.eth.max_priority_fee
            except Exception:
                # Fallback value if the RPC doesn't support eth_maxPriorityFeePerGas
                max_priority_fee_per_gas = 1_500_000_000  # 1.5 gwei
        else:
            max_priority_fee_per_gas_list.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_list[len(max_priority_fee_per_gas_list) // 2]
            
        return max_priority_fee_per_gas

    @retry_on_fail(tries=RETRIES)
    async def get_native_balance(self, chain: Optional[Chain] = None, wei: bool = True) -> Optional[Union[int, float]]:
        """
        Get native token balance
        
        Args:
            chain: Optional Chain object (uses the client's chain if not specified)
            wei: If True, returns the balance in wei, otherwise in ether
            
        Returns:
            Balance in wei or ether
        """
        w3 = self.w3 if chain is None else self.init_web3(chain=chain)

        try:
            balance = await w3.eth.get_balance(self.address)
            return balance if wei else float(AsyncWeb3.from_wei(balance, 'ether'))
        except Exception as e:
            logger.exception(f"Could not get balance of: {self.address}: {e}")
            return None

    def get_proxy_connector(self):
        """
        Get aiohttp connector with proxy settings
        
        Returns:
            ProxyConnector if proxy is set, None otherwise
        """
        if self.proxy is not None:
            proxy_url = f"http://{self.proxy}"
            return ProxyConnector.from_url(url=proxy_url)
        else:
            return None
