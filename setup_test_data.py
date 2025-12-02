#!/usr/bin/env python3
"""
Setup test data for autopay testing
"""

import sys
from datetime import timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from BankClock import BankClock
from BankingApp import BankingApp


def setup_test_data():
    """Create test customer with recurring bills"""
    print("=" * 70)
    print("SETTING UP TEST DATA FOR AUTOPAY")
    print("=" * 70)

    # Initialize app (loads existing data)
    app = BankingApp()

    # Create test customer
    print("\n📝 Creating test customer...")
    test_customer, account = app.bank.register_customer(
        username="test_user",
        password="password123",
        first_name="Test",
        last_name="User",
        dob="1990-01-01",
        gender="M",
        phone_number="9876543210",
        email="test@example.com",
        account_type="Pride",
    )

    print("✅ Customer created!")
    print(f"   Customer ID: {test_customer.customer_id}")
    print(f"   Account Number: {account.account_number}")
    print(f"   Balance: Rs. {account.balance:,.2f}")

    # Add credit to account
    print("\n💰 Adding credit to account...")
    account.balance = 50000
    app.bank.save()
    print(f"✅ Balance updated: Rs. {account.balance:,.2f}")

    # Create a credit card
    print("\n💳 Creating credit card...")
    from Card import CreditCard

    credit_card = CreditCard(
        account_number=account.account_number,
        customer_id=test_customer.customer_id,
        network="VISA",
        credit_limit=100000,  # 1 lakh limit
    )
    account.cards.append(credit_card)
    app.bank.save()

    print("✅ Credit card created!")
    print(f"   Card ID: {credit_card.card_id}")
    print(f"   Card Number: {credit_card.card_number}")
    print(f"   Limit: Rs. {credit_card.credit_limit:,.2f}")

    # Create a recurring bill with auto-debit on credit card
    print("\n📋 Creating recurring bill with auto-debit...")

    today = BankClock.today()
    tomorrow = today + timedelta(days=1)

    from RecurringBill import PaymentMethod, RecurringBillFactory

    bill = RecurringBillFactory.create_custom_bill(
        name="Internet Bill",
        category="UTILITIES",
        amount=1000,
        frequency="MONTHLY",
        day_of_month=tomorrow.day,
        auto_debit=True,
        payment_method=PaymentMethod.CREDIT_CARD,
        payment_card_id=credit_card.card_id,
    )

    account.recurring_bills.append(bill)
    app.bank.save()

    print("✅ Recurring bill created!")
    print(f"   Bill ID: {bill.id}")
    print(f"   Name: {bill.name}")
    print(f"   Amount: Rs. {bill.base_amount:,.2f}")
    print(f"   Payment Method: {bill.payment_method.name}")
    print(f"   Card ID: {bill.payment_card_id}")
    print(f"   Day of Month: {bill.day_of_month}")
    print(f"   Auto-Debit: {bill.auto_debit}")
    print(f"   Last Processed: {bill.last_processed}")

    print("\n" + "=" * 70)
    print("TEST DATA SETUP COMPLETE!")
    print("=" * 70)
    print("\nYou can now run: python test_autopay.py")

    return True


if __name__ == "__main__":
    try:
        success = setup_test_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
