"""Quick tool to verify international transfers"""

from DataStore import DataStore


def verify_transfer():
    """Verify a transfer by account number or SWIFT reference"""

    print("\n" + "=" * 80)
    print(" " * 20 + "INTERNATIONAL TRANSFER VERIFICATION")
    print("=" * 80)

    registry = DataStore.load_international_accounts()

    print("\nVerify by:")
    print("1. Account Number (View full account details)")
    print("2. SWIFT Reference (Track specific transfer)")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        verify_by_account(registry)
    elif choice == "2":
        verify_by_swift(registry)
    elif choice == "3":
        print("Goodbye!")
        return
    else:
        print("❌ Invalid choice")


def verify_by_account(registry):
    """Verify by account number - shows full details"""
    account_number = input("\nEnter account number: ").strip()
    account = registry.find_account_by_number(account_number)

    if not account:
        print("❌ Account not found")
        return

    print("\n" + "=" * 80)
    print("ACCOUNT DETAILS")
    print("=" * 80)
    print(f"Account Holder:    {account.account_holder}")
    print(f"Bank:              {account.bank_name}")
    print(f"Country:           {account.country}")
    print(f"Account Number:    {account.account_number}")
    print(f"SWIFT Code:        {account.swift_code}")
    print(f"Currency:          {account.currency}")
    print(f"Current Balance:   {account.balance:,.2f} {account.currency}")
    print("=" * 80)

    if account.transactions:
        print(f"\nTRANSACTION HISTORY ({len(account.transactions)} total)")
        print("-" * 80)
        print(f"{'Date/Time':<20} {'Amount':<20} {'From':<30} {'SWIFT Ref':<25}")
        print("-" * 80)

        # Show last 10 transactions
        for txn in account.transactions[-10:]:
            amount_str = f"+{txn['amount']:,.2f} {account.currency}"
            from_info = txn.get("from", "N/A")[:30]
            swift_ref = txn.get("swift_ref", "N/A")[:25]

            print(
                f"{txn['timestamp']:<20} {amount_str:<20} {from_info:<30} {swift_ref:<25}"
            )

        print("-" * 80)

        # Calculate total received
        total_received = sum(txn["amount"] for txn in account.transactions)
        print(f"\nTotal Received: {total_received:,.2f} {account.currency}")
        print(f"Number of Transactions: {len(account.transactions)}")
    else:
        print("\n📭 No transactions found")

    print("=" * 80)


def verify_by_swift(registry):
    """Verify by SWIFT reference - tracks specific transfer"""
    swift_ref = input("\nEnter SWIFT reference: ").strip()
    found = False

    for account in registry.accounts.values():
        for txn in account.transactions:
            if txn.get("swift_ref") == swift_ref:
                print("\n" + "=" * 80)
                print("✓ TRANSFER FOUND!")
                print("=" * 80)
                print(f"\nSWIFT Reference:   {swift_ref}")
                print("Status:            ✅ COMPLETED")
                print("\nRecipient Details:")
                print(f"  Name:            {account.account_holder}")
                print(f"  Bank:            {account.bank_name}")
                print(f"  Country:         {account.country}")
                print(f"  Account:         {account.account_number}")
                print("\nTransfer Details:")
                print(f"  Amount Received: {txn['amount']:,.2f} {account.currency}")
                print(f"  From:            {txn['from']}")
                print(f"  Date/Time:       {txn['timestamp']}")
                print("\nAccount Status:")
                print(f"  Current Balance: {account.balance:,.2f} {account.currency}")
                print("=" * 80)
                found = True
                break
        if found:
            break

    if not found:
        print("\n" + "=" * 80)
        print("❌ SWIFT REFERENCE NOT FOUND")
        print("=" * 80)
        print("\nPossible reasons:")
        print("  • Transfer is still processing")
        print("  • SWIFT reference was entered incorrectly")
        print("  • Transfer was not completed")
        print("=" * 80)


def main():
    """Main loop"""
    while True:
        verify_transfer()

        print("\n")
        again = input("Check another transfer? (yes/no): ").strip().lower()
        if again not in ["yes", "y"]:
            print("\n✓ Thank you for using International Transfer Verification!")
            break


if __name__ == "__main__":
    main()
