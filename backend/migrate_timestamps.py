"""
Timestamp format fixer - Adds missing colons to time component
Converts: 2026-01-18 041130 → 2026-01-18 04:11:30
"""

from datetime import datetime

from MongoDataStore import MongoDataStore


def migrate_timestamps():
    MongoDataStore.connect()

    all_txns = list(MongoDataStore._db.transactions.find({}))

    print(f"Converting {len(all_txns)} transaction timestamps...")

    converted = 0
    failed = 0
    skipped = 0

    for txn in all_txns:
        old_timestamp = txn.get("timestamp")
        if isinstance(old_timestamp, str) and old_timestamp:
            # Check if already has colons
            if ":" in old_timestamp:
                skipped += 1
                continue

            try:
                # Parse format: YYYY-MM-DD HHMMSS (no colons in time)
                parts = old_timestamp.split()
                if len(parts) == 2:
                    date_part = parts[0]
                    time_part = parts[1]

                    # Add colons to time: HHMMSS → HH:MM:SS
                    if len(time_part) == 6:
                        formatted_time = (
                            f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        )
                        new_timestamp = f"{date_part} {formatted_time}"

                        # Validate it parses correctly
                        datetime.strptime(new_timestamp, "%Y-%m-%d %H:%M:%S")

                        # Update in database
                        MongoDataStore._db.transactions.update_one(
                            {"_id": txn["_id"]}, {"$set": {"timestamp": new_timestamp}}
                        )
                        converted += 1

                        if converted % 100 == 0:
                            print(f"  Converted {converted}...")
                    else:
                        failed += 1
                        print(f"Invalid time length: {time_part}")
                else:
                    failed += 1
                    print(f"Unexpected format: {old_timestamp}")

            except Exception as e:
                print(f"Failed to convert: {old_timestamp} - {e}")
                failed += 1

    print("\n[OK] Migration complete!")
    print(f"  Converted: {converted}")
    print(f"  Skipped (already formatted): {skipped}")
    print(f"  Failed: {failed}")

    # Show sample of converted data
    print("\nSample of timestamps after conversion:")
    samples = MongoDataStore._db.transactions.find({}).sort("timestamp", -1).limit(5)
    for s in samples:
        print(f"  {s.get('timestamp')}")


if __name__ == "__main__":
    print("=" * 60)
    print("TIMESTAMP FORMAT FIXER")
    print("=" * 60)
    print("\nThis will add missing colons to timestamps")
    print("Example: 2026-01-18 041130 → 2026-01-18 04:11:30\n")

    confirm = input("Continue? (yes/no): ").strip().lower()

    if confirm in ["yes", "y"]:
        migrate_timestamps()
    else:
        print("Migration cancelled")
