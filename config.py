"""
Configuration file for the LayerZero V2 Bridge utility
"""

##########################################################################
############################# Telegram logs ##############################
##########################################################################

# Telegram bot token
TG_TOKEN = ""

# Telegram user IDs to receive logs
TG_IDS = []

# Enable/disable Telegram logs
USE_TG_BOT = False

##########################################################################
################################## Proxy #################################
##########################################################################

# Enable/disable mobile proxies
USE_MOBILE_PROXY = False

# URL for changing mobile proxy IP
PROXY_CHANGE_IP_URL = ""

##########################################################################
########################### Basic settings ##############################
##########################################################################

# Delay range after successful bridge (seconds)
WALLET_DELAY_RANGE = [30, 100]

# Delay range after failed bridge (seconds)
AFTER_FAIL_DELAY_RANGE = [10, 15]

# Minimum sleep time between actions (seconds)
MIN_SLEEP_TIME = 5

# Maximum sleep time between actions (seconds)
MAX_SLEEP_TIME = 20

# Default bridge mode ('BUS' or 'TAXI')
DEFAULT_BRIDGE_MODE = "BUS"

# Percentage of balance to bridge (range)
BALANCE_PERCENTAGE_TO_BRIDGE = [50, 80]

# Include fees in the amount when calculating bridge amount
INCLUDE_FEES_IN_AMOUNT = True

# Use full balance for bridging by default
USE_FULL_BRIDGE = False

# Maximum allowed slippage percentage
MAX_SLIPPAGE = 1

# Gas price thresholds for chains (in GWEI)
# If gas price exceeds threshold, the operation will be delayed
GAS_THRESHOLDS = {
    "Arbitrum": {"enabled": True, "value": 0.1},
    "Optimism": {"enabled": True, "value": 0.01},
    "Base": {"enabled": True, "value": 0.1},
    "Linea": {"enabled": True, "value": 0.1},
    "Scroll": {"enabled": True, "value": 0.1},
}

##########################################################################
########################### RPC Endpoints ###############################
##########################################################################

# RPC URLs for all supported networks
MAINNET_RPC_URL = "https://eth.llamarpc.com"
ARBITRUM_RPC_URL = "https://arbitrum.drpc.org"
OPTIMISM_RPC_URL = "https://optimism.drpc.org"
LINEA_RPC_URL = "https://linea.drpc.org"
SCROLL_RPC_URL = "https://scroll.drpc.org"
BASE_RPC_URL = "https://base.drpc.org"

##########################################################################
######################### Auto-Bridge Settings ##########################
##########################################################################

# Chain pairs for auto bridging (source -> destination)
AUTO_BRIDGE_PAIRS = [
    ("arbitrum", "optimism"),
    ("optimism", "base"),
    ("base", "linea"),
    ("linea", "scroll"),
    ("scroll", "arbitrum")
]

# Number of times to bridge in auto mode
AUTO_BRIDGE_COUNT = 5

# Minimum delay between auto bridges (seconds)
AUTO_BRIDGE_DELAY_MIN = 1800  # 30 minutes

# Maximum delay between auto bridges (seconds)
AUTO_BRIDGE_DELAY_MAX = 3600  # 1 hour
