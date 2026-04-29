#!/usr/bin/env python3
"""
Scala Bank - Python Edition
Main entry point for the banking application v11.2
"""

import sys
import os
import argparse
import logging

# Add parent directory to sys.path to support both direct execution and package imports
if __name__ == "__main__" and __package__ is None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from .Logger import BankLogger
    from .BankClock import switch_to_real_mode, switch_to_virtual_mode
    from .BankingApp import BankingApp
else:
    from .Logger import BankLogger
    from .BankClock import switch_to_real_mode, switch_to_virtual_mode
    from .BankingApp import BankingApp

logger = BankLogger.get_logger("Main")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Scala Bank CLI v11.2")
    parser.add_argument("--silent", action="store_true", help="Enable Silent Mode (Errors only on console)")
    return parser.parse_args()

def choose_clock_mode():
    """Let user choose clock mode at startup"""
    print("\n" + "=" * 60)
    print("           SCALA BANK - CLOCK MODE SELECTION")
    print("=" * 60)
    print("\nSelect Clock Mode:")
    print("1. [LIVE] Real-Time Mode (Syncs with your device clock)")
    print("2. [VIRTUAL] Virtual Mode (Manual time control)")
    print()

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == "1":
            switch_to_real_mode()
            logger.info("Real-Time Mode activated")
            break
        elif choice == "2":
            switch_to_virtual_mode()
            logger.info("Virtual Mode activated (Time simulation enabled)")
            break
        else:
            print("[FAIL] Invalid choice. Please enter 1 or 2.")

    input("\nPress Enter to continue...")


def main():
    """Main entry point for the application"""
    args = parse_arguments()
    
    if args.silent:
        BankLogger.set_silent_mode(True)

    logger.info("Initializing Scala Bank System...")

    try:
        # Choose clock mode at startup
        choose_clock_mode()

        # Start the banking app
        app = BankingApp()

        app.run()

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        logger.info("System shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        logger.critical(f"Critical System Failure: {e}", exc_info=True)
        print(f"\n[FAIL] A critical error occurred: {e}")


if __name__ == "__main__":
    main()
