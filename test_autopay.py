#!/usr/bin/env python3
"""
Test script to verify autopay functionality
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from BankClock import BankClock
from BankingApp import BankingApp


def test_autopay():
    """Test autopay functionality end-to-end"""
    print("=" * 70)
    print("AUTOPAY FUNCTIONALITY TEST")
    print("=" * 70)

    # Initialize app (loads data automatically)
    app = BankingApp()

    # Find an account with recurring bills set up
    target_account = None
    for account in app.bank.accounts:
        if account.recurring_bills and account.recurring_bills[0].auto_debit:
            target_account = account
            break

    if not target_account:
        print("\n❌ No account with auto-debit bills found!")
        print("   Please run setup_test_data.py first.")
        return False

    account = target_account
    print(f"\n✅ Found test account: {account.account_number}")
    print(f"   Current balance: Rs. {account.balance:,.2f}")
    print(f"   Current date: {BankClock.get_formatted_date()}")

    # Check if there are any recurring bills
    print(f"\n📋 Recurring Bills: {len(account.recurring_bills)}")
    for bill in account.recurring_bills:
        print(f"   - {bill.name} (Rs. {bill.base_amount:,.2f})")
        print(f"     Auto-debit: {'✅' if bill.auto_debit else '❌'}")
        print(f"     Payment Method: {bill.payment_method.name}")
        if bill.payment_card_id:
            print(f"     Card ID: {bill.payment_card_id}")
        print(f"     Last Processed: {bill.last_processed}")

    if not account.recurring_bills:
        print("\n❌ No recurring bills set up!")
        print("   Please set up a recurring bill first using the main app.")
        return False

    # Get a bill with auto_debit enabled
    auto_bills = [b for b in account.recurring_bills if b.auto_debit]
    if not auto_bills:
        print("\n❌ No auto-debit bills found!")
        print("   Please enable auto-debit on a bill first.")
        return False

    target_bill = auto_bills[0]
    print(f"\n🎯 Testing bill: {target_bill.name}")
    print(f"   Amount: Rs. {target_bill.base_amount:,.2f}")
    print(f"   Day of Month: {target_bill.day_of_month}")
    print(f"   Last Processed: {target_bill.last_processed}")

    # Simulate time to the day of month if needed
    today = BankClock.today()
    if today.day < target_bill.day_of_month:
        days_to_advance = target_bill.day_of_month - today.day
        print(f"\n⏰ Advancing time by {days_to_advance} days to reach due date...")

        for i in range(days_to_advance):
            BankClock.advance_day()
            account.process_recurring_bills(BankClock.today(), app.bank)

        print(f"   Current date: {BankClock.get_formatted_date()}")

    # Check the bill status after advancing
    print("\n📊 Bill Status After Time Advance:")
    print(f"   Last Processed: {target_bill.last_processed}")
    print(
        f"   Should process today: {target_bill.should_process_today(BankClock.today())}"
    )

    # Check if bill was processed
    if target_bill.last_processed == BankClock.today():
        print("\n✅ SUCCESS: Bill was auto-processed!")

        # Check transactions
        print(f"\n📜 Recent Transactions ({len(account.transactions)} total):")
        for txn in account.transactions[-5:]:
            ts_str = (
                txn.timestamp
                if isinstance(txn.timestamp, str)
                else txn.timestamp.strftime("%Y-%m-%d %H:%M")
            )
            print(f"   - {txn.type}: Rs. {-txn.amount:,.2f} ({ts_str})")

        return True
    else:
        print("\n❌ FAILED: Bill was not auto-processed!")
        print(f"   Bill's last_processed: {target_bill.last_processed}")
        print(f"   Expected date: {BankClock.today()}")

        # Debug: Check should_process_today logic
        print("\n🔍 Debugging should_process_today():")
        print(f"   Today: {BankClock.today()}")
        print(f"   Next Due Date: {target_bill.next_due_date}")
        print(f"   Last Processed: {target_bill.last_processed}")
        print(f"   Day of Month: {target_bill.day_of_month}")
        print(f"   Frequency: {target_bill.frequency}")

        return False


if __name__ == "__main__":
    success = test_autopay()
    sys.exit(0 if success else 1)
