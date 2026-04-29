#!/usr/bin/env python3
"""
Scala Bank - Python Edition
Main entry point for the banking application
"""

import sys
import os

# Add parent directory to sys.path to support both direct execution and package imports
if __name__ == "__main__" and __package__ is None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from backend.BankClock import switch_to_real_mode, switch_to_virtual_mode
    from backend.BankingApp import BankingApp
else:
    from .BankClock import switch_to_real_mode, switch_to_virtual_mode
    from .BankingApp import BankingApp


def choose_clock_mode():
    """Let user choose clock mode at startup"""
    print("\n" + "=" * 60)
    print("           SCALA BANK - CLOCK MODE SELECTION")
    print("=" * 60)
    print("\nSelect Clock Mode:")
    print("1. [LIVE] Real-Time Mode (Syncs with your device clock)")
    print("   - Shows actual current date and time")
    print("   - Time simulation DISABLED")
    print()
    print("2. [VIRTUAL]  Virtual Mode (Manual time control)")
    print("   - Allows time simulation for testing")
    print("   - Fast forward days/weeks/months")
    print()

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == "1":
            switch_to_real_mode()
            print("\n[SUCCESS] Real-Time Mode activated")
            break
        elif choice == "2":
            switch_to_virtual_mode()
            print("\n[SUCCESS] Virtual Mode activated (Time simulation enabled)")
            break
        else:
            print("[FAIL] Invalid choice. Please enter 1 or 2.")

    input("\nPress Enter to continue...")


def main():
    """Main entry point for the application"""

    try:
        # Choose clock mode at startup
        choose_clock_mode()

        # Start the banking app
        app = BankingApp()

        app.run()

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        print("Thank you for using Scala Bank!")
    except Exception as e:
        print(f"\n[FAIL] An unexpected error occurred: {e}")
        print("Please contact support if the problem persists.")


if __name__ == "__main__":
    main()