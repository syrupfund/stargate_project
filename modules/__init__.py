"""
Modules initialization
"""

from modules.balance_checker import check_balance, get_total_value
from modules.bridger import bridge_eth, bridge_batch
from modules.auto_bridger import auto_bridge
from modules.wallet_generator import create_wallet
from modules.tx_history import show_tx_history