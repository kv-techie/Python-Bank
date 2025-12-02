#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))
from Bank import Bank
from BankClock import BankClock

TARGET_ACCOUNT = "562132892448"

if __name__ == "__main__":
    bank = Bank()
    print(f"BankClock: {BankClock.get_formatted_datetime()}")
    print(f"Total accounts loaded: {len(bank.accounts)}")
    print("Sample accounts:")
    for a in bank.accounts[:5]:
        print(f" - {a.account_number} ({a.username})")
    processed = bank.process_daily_tasks()
    print(f"Total recurring bills processed across bank: {processed}")

    acc = bank.get_account(TARGET_ACCOUNT)
    if not acc:
        print(f"Account {TARGET_ACCOUNT} not found")
        sys.exit(1)

    print(f"\nRecurring bills for account {acc.account_number} ({acc.username}):")
    if not acc.recurring_bills:
        print(" No recurring bills.")
    else:
        today = BankClock.today()
        for b in acc.recurring_bills:
            last = (
                b.last_processed.isoformat()
                if getattr(b, "last_processed", None)
                else None
            )
            print(
                f" - {b.name}: amount={b.base_amount}, freq={b.frequency}, day={b.day_of_month}, autoDebit={b.auto_debit}, paymentMethod={b.payment_method}, lastProcessed={last}"
            )

    bank.save()
