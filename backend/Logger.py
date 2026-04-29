import logging
import os
from datetime import datetime
from typing import Optional

class BankLogger:
    """Central Logging System for Scala Bank v11.2
    Implements 'Silent Mode' (Console shows UI-relevant info, File stores full audit trail)
    """
    
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _LOG_DIR = os.path.join(_BASE_DIR, "data", "logs")
    _LOG_FILE = os.path.join(_LOG_DIR, f"bank_audit_{datetime.now().strftime('%Y%m')}.log")
    
    _initialized = False
    _silent_mode = False
    _console_handler: Optional[logging.StreamHandler] = None
    
    @staticmethod
    def setup():
        if BankLogger._initialized:
            return
            
        # Ensure log directory exists
        os.makedirs(BankLogger._LOG_DIR, exist_ok=True)
        
        # 1. Create a root logger
        logger = logging.getLogger("ScalaBank")
        logger.setLevel(logging.DEBUG) # Catch everything internally
        
        # Clear existing handlers
        logger.handlers = []
        
        # 2. File Handler (The "Audit Trail")
        file_handler = logging.FileHandler(BankLogger._LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 3. Console Handler (The "User UI")
        BankLogger._console_handler = logging.StreamHandler()
        BankLogger._update_console_level()
        console_formatter = logging.Formatter('%(message)s') # Clean UI format
        BankLogger._console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(BankLogger._console_handler)
        
        BankLogger._initialized = True
        logger.debug("Logging system initialized. File: %s", BankLogger._LOG_FILE)

    @staticmethod
    def _update_console_level():
        if BankLogger._console_handler:
            if BankLogger._silent_mode:
                # In silent mode, only show errors to the user
                BankLogger._console_handler.setLevel(logging.ERROR)
            else:
                BankLogger._console_handler.setLevel(logging.INFO)

    @staticmethod
    def set_silent_mode(enabled: bool):
        """Toggle Silent Mode globally: only show Errors to the user, but save everything to the file."""
        BankLogger._silent_mode = enabled
        if BankLogger._initialized:
            BankLogger._update_console_level()
            status = "ENABLED" if enabled else "DISABLED"
            logging.getLogger("ScalaBank").debug(f"Silent Mode {status}")

    @staticmethod
    def get_logger(name: str = "ScalaBank"):
        BankLogger.setup()
        if not name.startswith("ScalaBank"):
            name = f"ScalaBank.{name}"
        return logging.getLogger(name)

# Helper for easy access
logger = BankLogger.get_logger()
