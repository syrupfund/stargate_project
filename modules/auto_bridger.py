"""
Auto bridging module for performing multiple randomized bridges
"""

import asyncio
import random
from typing import List, Optional, Tuple

from config import (
    AUTO_BRIDGE_PAIRS,
    AUTO_BRIDGE_COUNT,
    AUTO_BRIDGE_DELAY_MIN,
    AUTO_BRIDGE_DELAY_MAX,
    BALANCE_PERCENTAGE_TO_BRIDGE,
)
from core import logger
from core.utils import sleep_pause
from modules.bridger import bridge_eth


async def auto_bridge(
    count: Optional[int] = None,
    delay_min: Optional[int] = None,
    delay_max: Optional[int] = None,
    bridge_pairs: Optional[List[Tuple[str, str]]] = None
) -> bool:
    """
    Perform multiple randomized bridges automatically
    
    Args:
        count: Number of bridges to perform (default from config)
        delay_min: Minimum delay between bridges in seconds (default from config)
        delay_max: Maximum delay between bridges in seconds (default from config)
        bridge_pairs: List of (source, destination) chain pairs (default from config)
        
    Returns:
        True if at least one bridge was successful, False otherwise
    """
    # Use defaults from config if not specified
    count = count or AUTO_BRIDGE_COUNT
    delay_min = delay_min or AUTO_BRIDGE_DELAY_MIN
    delay_max = delay_max or AUTO_BRIDGE_DELAY_MAX
    bridge_pairs = bridge_pairs or AUTO_BRIDGE_PAIRS
    
    if not bridge_pairs:
        logger.error("No bridge pairs defined")
        return False
    
    logger.info(f"Starting auto bridge with {count} iterations")
    logger.info(f"Bridge pairs: {bridge_pairs}")
    
    success_count = 0
    
    for i in range(count):
        # Select random bridge pair
        src_chain, dst_chain = random.choice(bridge_pairs)
        
        # Select random percentage of balance
        percentage = random.randint(*BALANCE_PERCENTAGE_TO_BRIDGE)
        
        # Select random bridge mode
        bridge_mode = random.choice(["BUS", "TAXI"])
        
        logger.info(f"Auto bridge iteration {i+1}/{count}")
        logger.info(f"Bridging from {src_chain} to {dst_chain} using {bridge_mode} mode")
        logger.info(f"Using {percentage}% of balance")
        
        # Execute bridge
        success = await bridge_eth(
            src_chain=src_chain,
            dst_chain=dst_chain,
            bridge_mode=bridge_mode,
            full_balance=False,
            amount_percentage=percentage,
            delay_after=False
        )
        
        if success:
            success_count += 1
        
        # Sleep between iterations if not the last one
        if i < count - 1:
            delay = random.randint(delay_min, delay_max)
            logger.info(f"Waiting {delay} seconds before next bridge...")
            await sleep_pause(delay_range=[delay, delay])
    
    logger.success(f"Auto bridge complete. {success_count}/{count} successful.")
    return success_count > 0
