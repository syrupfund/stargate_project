"""
Wallet generator module for creating new Ethereum wallets
"""

import os
import secrets
from pathlib import Path

from eth_account import Account
from termcolor import colored

from core import logger


def create_wallet() -> dict:
    """
    Generate a new Ethereum wallet (private key and address)
    
    Returns:
        Dictionary with private_key and address
    """
    # Generate random private key
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    
    # Create account from private key
    acct = Account.from_key(private_key)
    address = acct.address
    
    # Print wallet info with colors
    print("\n" + "="*50)
    print("New wallet generated:")
    print("PRIVATE KEY:", colored(private_key, "light_magenta"))
    print("ADDRESS:", colored(address, "light_cyan"))
    print("="*50 + "\n")
    
    # Ask if user wants to save the wallet
    choice = input("Would you like to add this wallet to your private_keys.txt? (y/n): ")
    
    if choice.lower() in ['y', 'yes']:
        save_wallet(private_key)
    
    return {
        'private_key': private_key,
        'address': address
    }


def save_wallet(private_key: str) -> bool:
    """
    Save private key to private_keys.txt
    
    Args:
        private_key: The private key to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        data_path = Path("data")
        if not data_path.exists():
            os.makedirs(data_path)
        
        # Write to private_keys.txt
        keys_file = data_path / "private_keys.txt"
        
        # Check if file exists and if we need to add a newline
        needs_newline = False
        if keys_file.exists() and keys_file.stat().st_size > 0:
            with open(keys_file, 'r') as f:
                content = f.read()
                if not content.endswith('\n'):
                    needs_newline = True
        
        # Append to file
        with open(keys_file, 'a') as f:
            if needs_newline:
                f.write('\n')
            f.write(f"{private_key}\n")
        
        logger.success("Private key saved to data/private_keys.txt")
        return True
        
    except Exception as e:
        logger.error(f"Error saving private key: {e}")
        return False
