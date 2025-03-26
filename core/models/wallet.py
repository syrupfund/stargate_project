"""
Wallet model for tracking bridge operations
"""

from dataclasses import dataclass

from core.client import Client
from core.models.chain import Chain


@dataclass
class Wallet:
    """Wallet class for tracking bridge operations"""

    private_key: str
    address: str
    proxy: str
    bridge_sent: bool = False

    def to_client(self, chain: Chain) -> Client:
        """
        Create a Client object for this wallet on the specified chain

        Args:
            chain: Chain to connect to

        Returns:
            Client object connected to the specified chain
        """
        return Client(private_key=self.private_key, proxy=self.proxy, chain=chain)
