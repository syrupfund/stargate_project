"""
Balance checker module for LayerZero V2 Bridge
"""

import asyncio
from typing import Dict, List

from colorama import Fore, Style
from prettytable import PrettyTable
from web3 import AsyncWeb3

from core.logger import logger
from core.client import Client
from core.models.chain import MAINNET, ARBITRUM, OPTIMISM, BASE, LINEA, SCROLL
from core.utils import read_from_txt


async def check_balance() -> bool:
    """
    Check ETH balances across all supported chains
    
    Returns:
        True if successful, False otherwise
    """
    try:
        private_keys = read_from_txt("data/private_keys.txt")
    except FileNotFoundError:
        logger.error("Private keys file not found. Please check data directory.")
        return False
    
    if not private_keys:
        logger.error("No private keys found. Please add keys to data/private_keys.txt")
        return False
        
    # Define chains to check
    chains = [MAINNET, ARBITRUM, OPTIMISM, BASE, LINEA, SCROLL]

    # Initialize result table
    table = PrettyTable()
    table.field_names = ["Wallet", *[chain.name for chain in chains]]
    
    logger.info(f"Checking balances for {len(private_keys)} wallets across {len(chains)} chains...")
    
    # Process each wallet
    for idx, private_key in enumerate(private_keys):
        # Create a temporary client to get address
        temp_client = Client(private_key=private_key)
        addr = temp_client.address
        
        # Shortened address for display
        short_addr = f"{addr[:6]}...{addr[-4:]}"
        
        row = [short_addr]
        
        # Check balance on each chain
        for chain in chains:
            try:
                client = Client(private_key=private_key, chain=chain)
                balance = await client.get_native_balance(wei=False)
                
                if balance is None:
                    row.append("Error")
                else:
                    row.append(f"{balance:.6f}")
            except Exception as e:
                logger.error(f"Error checking balance on {chain.name}: {e}")
                row.append("Error")
        
        table.add_row(row)
        
        # Progress indicator
        logger.info(f"Processed wallet {idx+1}/{len(private_keys)}")
    
    # Apply color to the table
    colored_table = Fore.GREEN + Style.NORMAL + str(table) + Style.RESET_ALL
    
    logger.info("WALLET BALANCES")
    print(colored_table)
    
    return True


async def get_total_value() -> float:
    """
    Calculate total ETH value across all chains
    
    Returns:
        Total ETH value
    """
    try:
        private_keys = read_from_txt("data/private_keys.txt")
    except FileNotFoundError:
        logger.error("Private keys file not found. Please check data directory.")
        return 0.0
    
    if not private_keys:
        logger.error("No private keys found. Please add keys to data/private_keys.txt")
        return 0.0
    
    # Define chains to check
    chains = [MAINNET, ARBITRUM, OPTIMISM, BASE, LINEA, SCROLL]

    total_eth = 0.0
    
    # Process each wallet
    for private_key in private_keys:
        wallet_total = 0.0
        
        # Check balance on each chain
        for chain in chains:
            try:
                client = Client(private_key=private_key, chain=chain)
                balance = await client.get_native_balance(wei=False)
                
                if balance is not None:
                    wallet_total += balance
            except Exception:
                pass
        
        total_eth += wallet_total
    
    return total_eth
