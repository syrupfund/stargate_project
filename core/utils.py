"""
Utility functions for the LayerZero V2 Bridge
"""

import asyncio
import functools
import json
import os
import random
import re
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Coroutine

import aiohttp
from tqdm import tqdm
from web3 import AsyncWeb3

from config import PROXY_CHANGE_IP_URL

# Import logger directly to avoid circular imports
from loguru import logger

T = TypeVar('T')


def read_from_txt(file_path: str) -> List[str]:
    """
    Read lines from a text file
    
    Args:
        file_path: Path to the text file
        
    Returns:
        List of non-empty lines
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip() and not line.strip().startswith("#")]
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        raise


def read_json(file_path: str) -> Dict[str, Any]:
    """
    Read a JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON data
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path) as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in '{file_path}': {e}")
        raise


async def sleep_pause(delay_range: List[int], enable_message: bool = True, enable_progress: bool = True) -> None:
    """
    Sleep for a random time within the specified range
    
    Args:
        delay_range: [min, max] range in seconds
        enable_message: Whether to log a message
        enable_progress: Whether to show a progress bar
    """
    delay = random.randint(*delay_range)

    if enable_message:
        logger.info(f"Sleeping for {delay} seconds...")

    if enable_progress:
        with tqdm(total=delay, desc="Waiting", unit="s", dynamic_ncols=True, colour="blue") as pbar:
            for _ in range(delay):
                await asyncio.sleep(delay=1)
                pbar.update(1)
    else:
        await asyncio.sleep(delay=delay)


def retry_on_fail(tries: int, retry_delay: Optional[List[int]] = None) -> Callable:
    """
    Decorator to retry a function if it fails
    
    Args:
        tries: Number of attempts
        retry_delay: [min, max] delay range between attempts (default [5, 10])
        
    Returns:
        Decorated function
    """
    if retry_delay is None:
        retry_delay = [5, 10]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(tries):
                result = await func(*args, **kwargs)
                if result is None or result is False:
                    if attempt < tries - 1:  # Don't sleep after the last attempt
                        logger.warning(f"Attempt {attempt + 1}/{tries} failed, retrying...")
                        await sleep_pause(delay_range=retry_delay, enable_message=False, enable_progress=False)
                else:
                    return result
            return False  # All attempts failed

        return wrapper

    return decorator


async def get_chain_gas_fee(chain) -> int:
    """
    Get current gas price for a chain
    
    Args:
        chain: Chain object
        
    Returns:
        Gas price in wei
    """
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(chain.rpc))
    return await w3.eth.gas_price


def address_to_bytes32(address: str) -> str:
    """
    Convert an Ethereum address to bytes32 format
    
    Args:
        address: Ethereum address
        
    Returns:
        Address in bytes32 format
    """
    return '0x' + address[2:].zfill(64)


async def change_ip() -> bool:
    """
    Change IP address for mobile proxy
    
    Returns:
        True if successful, False otherwise
    """
    if not PROXY_CHANGE_IP_URL:
        logger.warning("PROXY_CHANGE_IP_URL is not set, cannot change IP")
        return False
        
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url=PROXY_CHANGE_IP_URL) as response:
                if response.status == 200:
                    logger.success("Successfully changed IP address")
                    return True
                else:
                    logger.warning(f"Failed to change IP address: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error changing IP address: {e}")
            return False


def extract_private_keys(file_content: str) -> List[str]:
    """
    Extract private keys from file content
    
    Args:
        file_content: Content of private keys file
        
    Returns:
        List of private keys
    """
    # Match both standard format (0x...) and environment variable format (KEY=0x...)
    pattern = r'(?:^|=)(0x[a-fA-F0-9]{64})(?:$|\s)'
    matches = re.findall(pattern, file_content, re.MULTILINE)
    return matches


def run_async(coroutine: Coroutine) -> Any:
    """
    Run an async function in a synchronous context
    
    Args:
        coroutine: Async function to run
        
    Returns:
        Result of the coroutine
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


def wei_to_eth(wei_amount: int) -> float:
    """
    Convert wei to ETH
    
    Args:
        wei_amount: Amount in wei
        
    Returns:
        Amount in ETH
    """
    return float(AsyncWeb3.from_wei(wei_amount, 'ether'))


def eth_to_wei(eth_amount: float) -> int:
    """
    Convert ETH to wei
    
    Args:
        eth_amount: Amount in ETH
        
    Returns:
        Amount in wei
    """
    return AsyncWeb3.to_wei(eth_amount, 'ether')
