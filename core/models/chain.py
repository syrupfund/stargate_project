"""
Chain models for supported blockchains
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config import (
    MAINNET_RPC_URL,
    LINEA_RPC_URL,
    SCROLL_RPC_URL,
    ARBITRUM_RPC_URL,
    BASE_RPC_URL,
    OPTIMISM_RPC_URL,
)


@dataclass
class Chain:
    """Chain class representing an EVM-compatible blockchain"""
    
    name: str
    chain_id: int | None = None
    coin_symbol: str | None = None
    explorer: str | None = None
    eip_1559: bool | None = None
    rpc: str | None = None
    lz_eid: int | None = None
    requires_poa_middleware: bool = False

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_name(cls, name: str) -> Optional["Chain"]:
        """
        Get a Chain object by name
        
        Args:
            name: Chain name
            
        Returns:
            Chain object if found, None otherwise
        """
        try:
            return ChainEnum[name.capitalize()].value
        except KeyError:
            return None


# Ethereum Mainnet
MAINNET = Chain(
    name="Mainnet",
    rpc=MAINNET_RPC_URL,
    chain_id=1,
    lz_eid=30101,
    coin_symbol="ETH",
    explorer="https://etherscan.io/",
    eip_1559=True
)

# Arbitrum
ARBITRUM = Chain(
    name="Arbitrum",
    rpc=ARBITRUM_RPC_URL,
    chain_id=42161,
    coin_symbol="ETH",
    explorer="https://arbiscan.io/",
    eip_1559=True,
    lz_eid=30110
)

# Linea
LINEA = Chain(
    name="Linea",
    rpc=LINEA_RPC_URL,
    chain_id=59144,
    coin_symbol="ETH",
    explorer="https://lineascan.build/",
    eip_1559=True,
    lz_eid=30183,
    requires_poa_middleware=True
)

# Base
BASE = Chain(
    name="Base",
    rpc=BASE_RPC_URL,
    chain_id=8453,
    coin_symbol="ETH",
    explorer="https://basescan.org/",
    eip_1559=True,
    lz_eid=30184
)

# Scroll
SCROLL = Chain(
    name="Scroll",
    rpc=SCROLL_RPC_URL,
    chain_id=534352,
    coin_symbol="ETH",
    explorer="https://scrollscan.com/",
    eip_1559=False,
    lz_eid=30214
)

# Optimism
OPTIMISM = Chain(
    name="Optimism",
    rpc=OPTIMISM_RPC_URL,
    chain_id=10,
    coin_symbol="ETH",
    explorer="https://optimistic.etherscan.io/",
    eip_1559=True,
    lz_eid=30111
)


class ChainEnum(Enum):
    """Enum of supported chains for easy access"""
    
    Mainnet = MAINNET
    Arbitrum = ARBITRUM
    Optimism = OPTIMISM
    Base = BASE
    Scroll = SCROLL
    Linea = LINEA


def get_chain_by_name(name: str) -> Chain:
    """
    Get a Chain object by name (case-insensitive)
    
    Args:
        name: Chain name
        
    Returns:
        Chain object
        
    Raises:
        ValueError: If the chain is not supported
    """
    name_lower = name.lower()
    
    if name_lower == "arbitrum":
        return ARBITRUM
    elif name_lower == "optimism":
        return OPTIMISM
    elif name_lower == "base":
        return BASE
    elif name_lower == "scroll":
        return SCROLL
    elif name_lower == "linea":
        return LINEA
    elif name_lower == "mainnet":
        return MAINNET
    else:
        raise ValueError(f"Unsupported chain: {name}")
