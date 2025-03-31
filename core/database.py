"""
Database module for tracking transaction history
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.constants import DATABASE_PATH
from core.logger import logger


class Database:
    """Database class for managing transaction history"""

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize database

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.data = self._load_db()

    def _load_db(self) -> Dict:
        """
        Load database from file

        Returns:
            Database data as dictionary
        """
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in database file {self.db_path}. Creating new database.")
                return self._create_default_db()
        else:
            return self._create_default_db()

    def _create_default_db(self) -> Dict:
        """
        Create default database structure

        Returns:
            Default database structure
        """
        return {
            "transactions": {},
            "stats": {
                "total_transactions": 0,
                "total_value_bridged": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        }

    def _save_db(self) -> bool:
        """
        Save database to file

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            # Update stats
            self.data["stats"]["last_updated"] = datetime.now().isoformat()

            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            return False

    def add_transaction(self, wallet_address: str, tx_data: Dict[str, Any]) -> bool:
        """
        Add a transaction to the database

        Args:
            wallet_address: Wallet address
            tx_data: Transaction data

        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Ensure wallet exists in transactions
            if wallet_address not in self.data["transactions"]:
                self.data["transactions"][wallet_address] = []

            # Add timestamp if not present
            if "timestamp" not in tx_data:
                tx_data["timestamp"] = datetime.now().isoformat()

            # Add transaction
            self.data["transactions"][wallet_address].append(tx_data)

            # Update stats
            self.data["stats"]["total_transactions"] += 1
            if "amount" in tx_data and tx_data.get("success", False):
                self.data["stats"]["total_value_bridged"] += float(tx_data["amount"])

            # Save database
            return self._save_db()
        except Exception as e:
            logger.error(f"Failed to add transaction: {e}")
            return False

    def get_wallet_transactions(self, wallet_address: str) -> List[Dict]:
        """
        Get all transactions for a wallet

        Args:
            wallet_address: Wallet address

        Returns:
            List of transactions
        """
        return self.data["transactions"].get(wallet_address, [])

    def get_stats(self) -> Dict:
        """
        Get database statistics

        Returns:
            Statistics dictionary
        """
        return self.data["stats"]

    def get_all_transactions(self) -> Dict[str, List[Dict]]:
        """
        Get all transactions

        Returns:
            Dictionary mapping wallet addresses to lists of transactions
        """
        return self.data["transactions"]


# Create a singleton database instance
db = Database()