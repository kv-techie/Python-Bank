#!/usr/bin/env python3
"""
Scala Bank - Python Edition
Main entry point for the banking application
"""

from BankClock import switch_to_real_mode, switch_to_virtual_mode
from BankingApp import BankingApp


def choose_clock_mode():
    """Let user choose clock mode at startup"""
    print("\n" + "=" * 60)
    print("           SCALA BANK - CLOCK MODE SELECTION")
    print("=" * 60)
    print("\nSelect Clock Mode:")
    print("1. 🕐 Real-Time Mode (Syncs with your device clock)")
    print("   - Shows actual current date and time")
    print("   - Time simulation DISABLED")
    print()
    print("2. ⏸️  Virtual Mode (Manual time control)")
    print("   - Allows time simulation for testing")
    print("   - Fast forward days/weeks/months")
    print()

    while True:
        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == "1":
            switch_to_real_mode()
            print("\n✅ Real-Time Mode activated")
            break
        elif choice == "2":
            switch_to_virtual_mode()
            print("\n✅ Virtual Mode activated (Time simulation enabled)")
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")

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
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please contact support if the problem persists.")


if __name__ == "__main__":
    main()
