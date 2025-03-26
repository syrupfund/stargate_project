"""
Custom logger with console and Telegram output
"""

import sys
from enum import Enum

import telebot
from loguru import logger as loguru_logger

from config import TG_TOKEN, TG_IDS, USE_TG_BOT


class Icons(Enum):
    """Icons for different log levels"""
    SUCCESS = "🟢"
    ERROR = "🔴"
    WARNING = "🟡"
    INFO = "🔵"
    DEBUG = "🟣"


class CustomLogger:
    """
    Custom logger with console and Telegram output
    """

    def __init__(self, telegram_logger=None):
        """
        Initialize the logger
        
        Args:
            telegram_logger: Function to send logs to Telegram
        """
        self.telegram_logger = telegram_logger or self.tg_logger
        self.loguru_logger = loguru_logger
        
        # Remove default logger and add custom format
        self.loguru_logger.remove()
        self.loguru_logger.add(
            sys.stderr, 
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>"
        )

    def success(self, message: str, send_to_tg=True) -> None:
        """
        Log a success message
        
        Args:
            message: Message to log
            send_to_tg: Whether to send to Telegram
        """
        self.loguru_logger.success(message)
        if send_to_tg:
            self.telegram_logger(f"{Icons.SUCCESS.value} {message}")

    def error(self, message: str, send_to_tg=True) -> None:
        """
        Log an error message
        
        Args:
            message: Message to log
            send_to_tg: Whether to send to Telegram
        """
        self.loguru_logger.error(message)
        if send_to_tg:
            self.telegram_logger(f"{Icons.ERROR.value} {message}")

    def warning(self, message: str, send_to_tg=True) -> None:
        """
        Log a warning message
        
        Args:
            message: Message to log
            send_to_tg: Whether to send to Telegram
        """
        self.loguru_logger.warning(message)
        if send_to_tg:
            self.telegram_logger(f"{Icons.WARNING.value} {message}")

    def info(self, message: str, send_to_tg=True) -> None:
        """
        Log an info message
        
        Args:
            message: Message to log
            send_to_tg: Whether to send to Telegram
        """
        self.loguru_logger.info(message)
        if send_to_tg:
            self.telegram_logger(f"{Icons.INFO.value} {message}")

    def debug(self, message: str, send_to_tg=True) -> None:
        """
        Log a debug message
        
        Args:
            message: Message to log
            send_to_tg: Whether to send to Telegram
        """
        self.loguru_logger.debug(message)
        if send_to_tg:
            self.telegram_logger(f"{Icons.DEBUG.value} {message}")

    def exception(self, message: str) -> None:
        """
        Log an exception
        
        Args:
            message: Exception message
        """
        self.loguru_logger.exception(message)

    @staticmethod
    def send_message_telegram(bot, text: str):
        """
        Send a message to Telegram
        
        Args:
            bot: Telebot instance
            text: Message to send
        """
        try:
            if USE_TG_BOT:
                for tg_id in TG_IDS:
                    bot.send_message(tg_id, text)
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

    @staticmethod
    def tg_logger(text: str):
        """
        Log to Telegram
        
        Args:
            text: Message to log
        """
        if not USE_TG_BOT or not TG_TOKEN:
            return
            
        try:
            bot = telebot.TeleBot(TG_TOKEN, disable_web_page_preview=True)
            CustomLogger.send_message_telegram(bot, text)
        except Exception as e:
            print(f"Error initializing Telegram bot: {e}")


# Create a singleton logger instance
logger = CustomLogger()
