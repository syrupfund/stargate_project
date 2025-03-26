# LayerZero V2 ETH Bridge

A powerful Python utility for bridging ETH tokens across various networks using LayerZero V2 technology. This tool supports:

1. **Specific network-to-network bridging** with a simple command
2. **LayerZero V2 endpoints** for efficient bridging with both "BUS" (economical) and "TAXI" (fast) modes
3. **Multiple randomized bridges** automatically over time

## Supported Networks

- Arbitrum
- Optimism 
- Base
- Linea
- Scroll

## Requirements

- Python 3.10+
- Web3.py and other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/layerzero-v2-bridge.git
   cd layerzero-v2-bridge
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your private keys and proxies (optional):
   - Add your private keys to `data/private_keys.txt` (one key per line)
   - Add your proxies to `data/proxies.txt` (format: `user:pass@ip:port`, one per line)

4. Review and adjust settings in `config.py` if needed

## Usage

### Check Balances

Check your ETH balances across all supported networks:

```bash
python main.py --mode balance
```

### Bridge ETH

Bridge ETH from one network to another:

```bash
python main.py --mode bridge --source arbitrum --destination optimism
```

Additional options:
- `--type bus` or `--type taxi` - Bridge mode (default: BUS)
- `--amount 0.1` - Amount to bridge (in ETH)
- `--full` - Use full balance (ignores --amount)

### Auto Bridge

Perform multiple randomized bridges over time:

```bash
python main.py --mode auto-bridge --count 5
```

Additional options:
- `--delay-min 300` - Minimum delay between bridges (seconds)
- `--delay-max 600` - Maximum delay between bridges (seconds)

### Generate New Wallet

Create a new Ethereum wallet:

```bash
python main.py --mode new-wallet
```

## Configuration

You can customize the behavior by editing `config.py`. Key settings include:

- Bridge mode (BUS or TAXI)
- Delay ranges
- Balance percentage ranges
- RPC endpoints
- Gas thresholds
- Telegram notification settings

## Security Notes

- **NEVER share your private keys**
- Store your private keys securely
- Consider using a new wallet for testing
- Review the code before running it with your keys

## How It Works

1. **BUS vs TAXI Modes**: 
   - BUS: More economical but may take longer
   - TAXI: Faster but more expensive

2. **LayerZero V2**: Uses the latest version of LayerZero protocol for efficient cross-chain bridging

3. **Auto Bridge**: Randomly selects source/destination pairs, amounts, and modes for natural-looking bridging patterns

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses or security issues.
