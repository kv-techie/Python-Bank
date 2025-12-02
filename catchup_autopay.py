#!/usr/bin/env python3
"""
Catch-up script to run daily tasks for the past N days so missed autopays are processed.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from Bank import Bank
from BankClock import BankClock

DAYS_TO_CATCHUP = 90

if __name__ == "__main__":
    bank = Bank()

    orig_dt = BankClock.now()
    target_date = BankClock.today()
    start_date = target_date - timedelta(days=DAYS_TO_CATCHUP)

    print(f"BankClock currently: {BankClock.get_formatted_datetime()}")
    print(
        f"Running catch-up from {start_date} to {target_date} ({DAYS_TO_CATCHUP} days)"
    )

    # Set clock to start_date (midnight)
    current_dt = datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        orig_dt.hour,
        orig_dt.minute,
        orig_dt.second,
    )
    BankClock.set_datetime(current_dt)

    total_processed = 0
    day_count = 0
    while BankClock.today() <= target_date:
        processed = bank.process_daily_tasks()
        total_processed += processed
        day_count += 1
        # Advance a day
        BankClock.advance_day()

    # Restore clock to original target_date/time
    BankClock.set_datetime(orig_dt)
    bank.save()

    print(
        f"Catch-up complete. Days processed: {day_count}, Bills processed in total: {total_processed}"
    )
    print(f"BankClock restored to: {BankClock.get_formatted_datetime()}")
