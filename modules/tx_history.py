"""
Transaction history module for displaying bridge history
"""

from datetime import datetime
from typing import Optional

from colorama import Fore, Style
from prettytable import PrettyTable
from web3 import Web3

from core.database import db
from core.logger import logger
from core.utils import read_from_txt


def format_timestamp(timestamp) -> str:
    """
    Format a timestamp into a readable date and time

    Args:
        timestamp: Unix timestamp or ISO format string

    Returns:
        Formatted date and time string
    """
    try:
        # Handle both numeric timestamp and ISO format
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = datetime.fromisoformat(timestamp)

        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(timestamp)


def format_address(address: str) -> str:
    """
    Format an address for display

    Args:
        address: Ethereum address

    Returns:
        Shortened address
    """
    if not address:
        return "N/A"
    return f"{address[:8]}...{address[-6:]}"


def format_amount(amount) -> str:
    """
    Format an amount for display

    Args:
        amount: ETH amount

    Returns:
        Formatted amount string
    """
    if not amount:
        return "N/A"
    return f"{float(amount):.6f} ETH"


def format_usd_amount(amount) -> str:
    """
    Format a USD amount for display

    Args:
        amount: USD amount

    Returns:
        Formatted USD amount string
    """
    if not amount:
        return "N/A"
    return f"${float(amount):.2f}"


def format_tx_hash(tx_hash: str, chain_name: str) -> str:
    """
    Format a transaction hash with explorer link

    Args:
        tx_hash: Transaction hash
        chain_name: Chain name for explorer URL

    Returns:
        Formatted transaction hash
    """
    if not tx_hash:
        return "N/A"

    # Get display version
    return f"{tx_hash[:8]}...{tx_hash[-6:]}"


async def show_tx_history(wallet_address: Optional[str] = None, limit: int = 20) -> bool:
    """
    Show transaction history for a wallet or all wallets

    Args:
        wallet_address: Specific wallet address (or None for all wallets)
        limit: Maximum number of transactions to show per wallet

    Returns:
        True if successful, False otherwise
    """
    try:
        if wallet_address:
            # Show transactions for specific wallet
            address = Web3.to_checksum_address(wallet_address)
            transactions = db.get_wallet_transactions(address)
            wallets = {address: transactions}
        else:
            # Load all wallet addresses
            try:
                private_keys = read_from_txt("data/private_keys.txt")
            except FileNotFoundError:
                logger.error("Private keys file not found.")
                return False

            # Create temporary Web3 instance to get addresses
            web3 = Web3()
            wallets = {}

            for private_key in private_keys:
                try:
                    address = web3.eth.account.from_key(private_key).address
                    transactions = db.get_wallet_transactions(address)
                    if transactions:
                        wallets[address] = transactions
                except Exception as e:
                    logger.error(f"Error processing private key: {e}")

        if not wallets:
            logger.info("No transaction history found.")
            return True

        total_spending_usd = 0
        total_bridged_eth = 0
        total_successful_tx = 0

        # Display transactions for each wallet
        for address, transactions in wallets.items():
            if not transactions:
                continue

            # Sort by timestamp (newest first)
            transactions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

            # Limit number of transactions
            shown_transactions = transactions[:limit]

            # Calculate statistics
            successful_txs = sum(1 for tx in transactions if tx.get('success', False))
            total_bridged = sum(float(tx.get('amount', 0)) for tx in transactions if tx.get('success', False))
            total_fees_usd = sum(float(tx.get('total_fee_usd', 0)) for tx in transactions if tx.get('success', False))

            # Update global stats
            total_spending_usd += total_fees_usd
            total_bridged_eth += total_bridged
            total_successful_tx += successful_txs

            # Create table
            table = PrettyTable()
            table.field_names = ["Date", "From", "To", "Amount", "Mode", "Fee (USD)", "Status", "Tx Hash"]

            for tx in shown_transactions:
                status = Fore.GREEN + "Success" + Style.RESET_ALL if tx.get('success', False) else Fore.RED + "Failed" + Style.RESET_ALL

                # Format fee in USD
                fee_usd = format_usd_amount(tx.get('total_fee_usd')) if tx.get('success', False) else "N/A"

                table.add_row([
                    format_timestamp(tx.get('timestamp', '')),
                    tx.get('from_chain', 'N/A'),
                    tx.get('to_chain', 'N/A'),
                    format_amount(tx.get('amount', '')),
                    tx.get('mode', 'N/A'),
                    fee_usd,
                    status,
                    format_tx_hash(tx.get('tx_hash', ''), tx.get('from_chain', ''))
                ])

            # Print wallet info
            print(f"\n{Fore.CYAN}Wallet: {address}{Style.RESET_ALL}")
            print(f"Total Transactions: {len(transactions)} ({successful_txs} successful)")
            print(f"Total Amount Bridged: {format_amount(total_bridged)}")
            print(f"Total Fees Paid: {format_usd_amount(total_fees_usd)}")

            # Print transaction table
            print(table)

            if len(transactions) > limit:
                print(f"Showing {limit} of {len(transactions)} transactions (newest first)")

            print("-" * 80)

        # Print global statistics for all wallets
        if len(wallets) > 1:
            print(f"\n{Fore.YELLOW}GLOBAL STATISTICS{Style.RESET_ALL}")
            print(f"Total Wallets: {len(wallets)}")
            print(f"Total Successful Transactions: {total_successful_tx}")
            print(f"Total ETH Bridged: {format_amount(total_bridged_eth)}")
            print(f"Total Fees Paid: {format_usd_amount(total_spending_usd)}")
            print("-" * 80)

        return True

    except Exception as e:
        logger.error(f"Error displaying transaction history: {e}")
        return False