"""
ETH bridging module for LayerZero V2
"""

import asyncio
import random
from typing import List, Optional

from config import (
    USE_FULL_BRIDGE,
    USE_MOBILE_PROXY,
    BALANCE_PERCENTAGE_TO_BRIDGE,
    WALLET_DELAY_RANGE,
    AFTER_FAIL_DELAY_RANGE,
    INCLUDE_FEES_IN_AMOUNT,
)
from core.logger import logger
from core.client import Client
from core.models.chain import get_chain_by_name
from core.stargate import Stargate
from core.utils import change_ip, sleep_pause, read_from_txt
from core.models.wallet import Wallet

async def bridge_eth(
    src_chain: str,
    dst_chain: str,
    bridge_mode: str = "BUS",
    full_balance: bool = False,
    amount_percentage: Optional[float] = None,
    delay_after: bool = True
) -> bool:
    """
    Bridge ETH from one chain to another
    
    Args:
        src_chain: Source chain name
        dst_chain: Destination chain name
        bridge_mode: Bridge mode (BUS or TAXI)
        full_balance: Whether to use full balance
        amount_percentage: Percentage of balance to bridge (0-100)
        delay_after: Whether to pause after bridging
        
    Returns:
        True if successful, False otherwise
    """
    # Load keys and proxies
    try:
        private_keys = read_from_txt("data/private_keys.txt")
        proxies = read_from_txt("data/proxies.txt") if USE_MOBILE_PROXY else []
    except FileNotFoundError:
        logger.error("Private keys or proxy file not found. Please check data directory.")
        return False
    
    if not private_keys:
        logger.error("No private keys found. Please add keys to data/private_keys.txt")
        return False
    
    # If mobile proxies enabled but none provided, use None for all
    if USE_MOBILE_PROXY and not proxies:
        logger.warning("Mobile proxies enabled but none provided. Using direct connection.")
        proxies = [None] * len(private_keys)
    # If not using mobile proxies, use None for all
    elif not USE_MOBILE_PROXY:
        proxies = [None] * len(private_keys)
    # If there are fewer proxies than keys, cycle through them
    elif len(proxies) < len(private_keys):
        proxies = proxies * (len(private_keys) // len(proxies) + 1)
        proxies = proxies[:len(private_keys)]
    
    # Get source and destination chain objects
    source_chain = get_chain_by_name(src_chain)
    destination_chain = get_chain_by_name(dst_chain)
    
    # Process each wallet
    success_count = 0
    for idx, (private_key, proxy) in enumerate(zip(private_keys, proxies)):
        logger.info(f"Processing wallet {idx+1}/{len(private_keys)}")
        
        # Change IP if using mobile proxies
        if USE_MOBILE_PROXY and proxy:
            await change_ip()
        
        # Initialize client for source chain
        client = Client(private_key=private_key, proxy=proxy, chain=source_chain)
        addr = client.address
        
        logger.info(f"Wallet: {addr}")
        
        # Get balance and determine amount to bridge
        balance = await client.get_native_balance(wei=False)
        if balance is None:
            logger.error(f"Failed to get balance for {addr}")
            continue
            
        logger.info(f"Balance on {source_chain.name}: {balance:.6f} {source_chain.coin_symbol}")
        
        if balance <= 0.001:  # Minimum viable balance
            logger.warning(f"Balance too low for bridging: {balance:.6f} {source_chain.coin_symbol}")
            continue
        
        # Calculate bridge amount
        if full_balance or USE_FULL_BRIDGE:
            amount_to_bridge = None
            include_fees = False
        elif amount_percentage is not None:
            amount_to_bridge = balance * (amount_percentage / 100)
            include_fees = INCLUDE_FEES_IN_AMOUNT
        else:
            # Use random percentage from config
            percentage = random.randint(*BALANCE_PERCENTAGE_TO_BRIDGE) / 100
            amount_to_bridge = balance * percentage
            include_fees = INCLUDE_FEES_IN_AMOUNT
        
        # Bridge ETH
        stargate = Stargate(client=client)
        bridge_result = await stargate.bridge(
            dst_chain=destination_chain,
            amount=amount_to_bridge,
            mode=bridge_mode,
            include_fees=include_fees,
        )
        
        if bridge_result:
            success_count += 1
            sleep_range = WALLET_DELAY_RANGE
        else:
            sleep_range = AFTER_FAIL_DELAY_RANGE
        
        # Sleep between wallets if there are more to process
        if delay_after and idx < len(private_keys) - 1:
            await sleep_pause(delay_range=sleep_range)
    
    logger.success(f"Bridging complete. {success_count}/{len(private_keys)} successful.")
    return success_count > 0


async def bridge_batch(wallets: List[Wallet]) -> int:
    """
    Process a batch of wallets for bridging
    
    Args:
        wallets: List of Wallet objects
        
    Returns:
        Number of successful bridges
    """
    active_wallets = [wallet for wallet in wallets if not wallet.bridge_sent]
    
    if not active_wallets:
        logger.info("No active wallets to process.")
        return 0
        
    success_count = 0
    for wallet in active_wallets:
        if USE_MOBILE_PROXY:
            await change_ip()
        
        logger.info(f"Processing wallet: {wallet.address}")
        
        # TODO: Implement batch processing logic
        # This would require defining source/destination chains for each wallet
        
    return success_count
