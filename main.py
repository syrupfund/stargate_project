"""
LayerZero V2 Bridge - Main Entry Point

This script provides functionality to bridge ETH tokens across various networks
using LayerZero V2 technology. It supports:
1) Specific network-to-network bridging with a simple command
2) LayerZero V2 endpoints for efficient bridging
3) Multiple randomized bridges over time

Usage:
    python main.py --mode [mode] [options]

Modes:
    bridge          - Bridge ETH from one network to another
    auto-bridge     - Perform multiple random bridges over time
    balance         - Check balances across all networks
    new-wallet      - Generate a new wallet
    history         - View transaction history
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Local imports
from core import logger
from modules.balance_checker import check_balance
from modules.bridger import bridge_eth
from modules.auto_bridger import auto_bridge
from modules.wallet_generator import create_wallet
from modules.tx_history import show_tx_history


async def main():
    """Main entry point for the LayerZero V2 bridge utility"""
    parser = argparse.ArgumentParser(description="LayerZero V2 Bridger")

    mode_group = parser.add_argument_group("Mode Selection")
    mode_group.add_argument(
        "--mode",
        type=str,
        choices=["bridge", "auto-bridge", "balance", "new-wallet", "history"],
        default="balance",
        help="Operation mode"
    )

    bridge_group = parser.add_argument_group("Bridge Options")
    bridge_group.add_argument(
        "--source", "-s",
        type=str,
        choices=["arbitrum", "optimism", "base", "linea", "scroll", "mainnet"],
        help="Source network for bridging"
    )
    bridge_group.add_argument(
        "--destination", "-d",
        type=str,
        choices=["arbitrum", "optimism", "base", "linea", "scroll", "mainnet"],
        help="Destination network for bridging"
    )
    bridge_group.add_argument(
        "--type", "-t",
        choices=["bus", "taxi"],
        default="bus",
        help="Bridge mode (BUS=economical, TAXI=fast)"
    )
    bridge_group.add_argument(
        "--amount", "-a",
        type=float,
        help="Amount to bridge (specific value or percentage)"
    )
    bridge_group.add_argument(
        "--full", "-f",
        action="store_true",
        help="Use full balance (ignores --amount)"
    )

    auto_bridge_group = parser.add_argument_group("Auto Bridge Options")
    auto_bridge_group.add_argument(
        "--count", "-c",
        type=int,
        default=1,
        help="Number of bridges to perform in auto-bridge mode"
    )
    auto_bridge_group.add_argument(
        "--delay-min",
        type=int,
        default=30,
        help="Minimum delay between operations (seconds)"
    )
    auto_bridge_group.add_argument(
        "--delay-max",
        type=int,
        default=100,
        help="Maximum delay between operations (seconds)"
    )

    history_group = parser.add_argument_group("History Options")
    history_group.add_argument(
        "--wallet", "-w",
        type=str,
        help="Specific wallet address to show history for"
    )
    history_group.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Maximum number of transactions to show per wallet"
    )

    args = parser.parse_args()

    # Create data directories if they don't exist
    data_path = Path("data")
    if not data_path.exists():
        os.makedirs(data_path)
        with open(data_path / "private_keys.txt", "w") as f:
            f.write("# Add your private keys here, one per line\n")
        with open(data_path / "proxies.txt", "w") as f:
            f.write("# Add your proxies here in format user:pass@ip:port, one per line\n")

    # Execute selected mode
    try:
        if args.mode == "balance":
            await check_balance()

        elif args.mode == "bridge":
            if not args.source or not args.destination:
                logger.error("Both --source and --destination must be specified for bridge mode")
                sys.exit(1)

            if args.source == args.destination:
                logger.error("Source and destination networks must be different")
                sys.exit(1)

            await bridge_eth(
                src_chain=args.source,
                dst_chain=args.destination,
                bridge_mode=args.type.upper(),
                full_balance=args.full,
                amount_percentage=args.amount if not args.full else None
            )

        elif args.mode == "auto-bridge":
            await auto_bridge(
                count=args.count,
                delay_min=args.delay_min,
                delay_max=args.delay_max
            )

        elif args.mode == "new-wallet":
            create_wallet()

        elif args.mode == "history":
            await show_tx_history(
                wallet_address=args.wallet,
                limit=args.limit
            )

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")

    logger.success("Operation completed")


if __name__ == "__main__":
    asyncio.run(main())