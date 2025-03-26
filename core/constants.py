"""
Constants used throughout the application
"""

import os
import sys
from pathlib import Path

from core.utils import read_json


# Determine root directory based on whether we're running from a frozen executable or script
if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

# ABI directory
ABI_DIR = os.path.join(ROOT_DIR, "core", "abis")

# Data files
PRIVATE_KEYS_PATH = os.path.join(ROOT_DIR, "data", "private_keys.txt")
PROXIES_PATH = os.path.join(ROOT_DIR, "data", "proxies.txt")
DATABASE_PATH = os.path.join(ROOT_DIR, "data", "database.json")

# Transaction parameters
GAS_MULTIPLIER = 1.2
RETRIES = 10
MAX_SLIPPAGE = 1
GAS_FEES_ESTIMATION_MULTIPLIER = 0.99

# Load ABIs
STARGATE_NATIVE_POOL_ABI = read_json(os.path.join(ABI_DIR, "stargate_native_pool.json"))

# LayerZero V2 Stargate addresses for ETH (Native) Pools
STARGATE_ETH_NATIVE_POOL_ADDRESSES = {
    # Chain IDs mapped to contract addresses
    42161: "0xA45B5130f36CDcA45667738e2a258AB09f4A5f7F",  # Arbitrum
    10: "0xe8CDF27AcD73a434D661C84887215F7598e7d0d3",     # Optimism
    59144: "0x81F6138153d473E8c5EcebD3DC8Cd4903506B075",  # Linea
    8453: "0xdc181Bd607330aeeBEF6ea62e03e5e1Fb4B6F7C7",   # Base
    534352: "0xC2b638Cb5042c1B3c5d5C969361fB50569840583", # Scroll
}

# Value for simulating full bridging to estimate fees
STARGATE_FULL_BRIDGE_SIMULATION_TX_VALUE = 10000000000000

# Common constants
EMPTY_DATA = "0x"
