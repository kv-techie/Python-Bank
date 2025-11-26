#!/usr/bin/env python3
"""
Scala Bank - Python Edition
Main entry point for the banking application
"""

from BankingApp import BankingApp


def main():
    """Main entry point for the application"""
    try:
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
