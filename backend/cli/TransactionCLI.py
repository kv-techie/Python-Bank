from datetime import datetime
from typing import List, Optional, Dict, Any

from ..Account import Account
from ..Transaction import Transaction
from ..Logger import BankLogger
from ..DataStore import DataStore
from ..BankClock import BankClock

class TransactionCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.logger = BankLogger.get_logger("TransactionCLI")

    def _parse_metadata(self, metadata) -> dict:
        """Parse transaction metadata which can be a dict or a string"""
        if not metadata:
            return {}
        if isinstance(metadata, dict):
            return metadata
        if isinstance(metadata, str):
            try:
                import json
                return json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def _get_transaction_limit(self) -> int:
        """Get user input for transaction limit"""
        try:
            val = input("\nEnter limit (number of transactions, or leave blank for last 20): ").strip()
            if not val:
                return 20
            return int(val)
        except ValueError:
            print("[FAIL] Invalid number. Using default limit of 20.")
            return 20

    def search_transaction(self):
        """Search for a transaction by ID"""
        txn_id = input("Enter Transaction ID (e.g. TXN1234567890): ").strip()
        result = self.bank.search_transaction_by_id(txn_id)

        if result:
            acc, txn = result
            cheque_line = (
                f"\nCheque ID: {txn.cheque_id}"
                if getattr(txn, "cheque_id", None)
                else ""
            )
            print(f"""
Transaction Found:
Account Holder: {acc.first_name} {acc.last_name}
Account Type: {acc.account_type}
Account Number: {acc.account_number}
Txn ID: {txn.id}
Type: {txn.type}
Amount: Rs. {txn.amount:.2f} INR
Resulting Balance: Rs. {txn.resulting_balance:.2f} INR
Timestamp: {txn.timestamp}{cheque_line}
            """)
        else:
            print(f"Transaction ID '{txn_id}' not found.")

    def view_transaction_history_menu(self, account: Account):
        """Interactive menu for viewing transaction history"""

        while True:
            print("\n" + "=" * 60)
            print("TRANSACTION HISTORY")
            print("=" * 60)

            # Quick View Options
            print("\n[STATS] QUICK VIEW:")
            print("1. Mini Statement (Last 10 transactions)")
            print("2. Last 20 transactions")
            print("3. Last 30 transactions")
            print("4. Last 50 transactions")
            print("5. All transactions")

            # Filter by Category
            print("\n[SEARCH] FILTER BY CATEGORY:")
            print("6. Deposits")
            print("7. Withdrawals")
            print("8. NEFT Transactions")
            print("9. RTGS Transactions")
            print("10. Inter-Account Transfers")
            print("11. SWIFT Transactions")
            print("12. Cheque Transactions")
            print("13. Expenses")
            print("14. Salary & Tax")
            print("15. Debit Card Transactions")
            print("16. Credit Card Transactions")
            print("17. Bill Payments")
            print("18. Loan EMI Payments")
            print("19. Fees & Charges")

            print("\n20. Back to Account Menu")
            print("=" * 60)

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                account.show_transactions(limit=10)
            elif choice == "2":
                account.show_transactions(limit=20)
            elif choice == "3":
                account.show_transactions(limit=30)
            elif choice == "4":
                account.show_transactions(limit=50)
            elif choice == "5":
                account.show_transactions(limit=None)
            elif choice == "6":
                limit = self._get_transaction_limit()
                print("\n[MONEY] Deposits:")
                account.show_transactions(
                    limit=limit, transaction_type_filter="DEPOSIT"
                )
            elif choice == "7":
                limit = self._get_transaction_limit()
                print("\n💸 Withdrawals:")
                account.show_transactions(
                    limit=limit, transaction_type_filter="WITHDRAW"
                )
            elif choice == "8":
                self.view_neft_transactions(account)
            elif choice == "9":
                self.view_rtgs_transactions(account)
            elif choice == "10":
                self.view_inter_account_transactions(account)
            elif choice == "11":
                limit = self._get_transaction_limit()
                print("\n🌍 SWIFT Transactions:")
                account.show_transactions(limit=limit, transaction_type_filter="SWIFT")
            elif choice == "12":
                limit = self._get_transaction_limit()
                print("\n📄 Cheque Transactions:")
                account.show_transactions(limit=limit, transaction_type_filter="CHEQUE")
            elif choice == "13":
                self.view_expense_transactions(account)
            elif choice == "14":
                self.view_salary_tax_transactions(account)
            elif choice == "15":
                self.view_debit_card_transactions(account)
            elif choice == "16":
                self.view_credit_card_transactions(account)
            elif choice == "17":
                limit = self._get_transaction_limit()
                print("\n[INFO] Bill Payments:")
                account.show_transactions(
                    limit=limit, transaction_type_filter="BILL_PAYMENT"
                )
            elif choice == "18":
                self.view_loan_emi_transactions(account)
            elif choice == "19":
                limit = self._get_transaction_limit()
                print("\n💳 Fees & Charges:")
                account.show_transactions(limit=limit, transaction_type_filter="FEES")
            elif choice == "20":
                break
            else:
                print("Invalid choice")

    def view_legacy_transactions(self, account: Account):
        """View legacy banking transactions (no card)"""
        limit = self._get_transaction_limit()
        print("\n🏛️ Legacy Banking Transactions (No Card):")
        account.show_transactions(limit=limit, transaction_type_filter="LEGACY_BANKING")

    def view_loan_emi_transactions(self, account: Account):
        """View only loan EMI transactions"""
        limit = self._get_transaction_limit()
        print("\n[BANK] Loan EMI Payments:")
        account.show_transactions(limit=limit, transaction_type_filter="LOAN_EMI")

    def view_neft_transactions(self, account: Account):
        """View NEFT transactions"""
        limit = self._get_transaction_limit()
        print("\n💸 NEFT Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="NEFT")

    def view_rtgs_transactions(self, account: Account):
        """View RTGS transactions"""
        limit = self._get_transaction_limit()
        print("\n[MONEY] RTGS Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="RTGS")

    def view_inter_account_transfer_transactions(self, account: Account):
        """View inter-account transfers"""
        limit = self._get_transaction_limit()
        print("\n🔄 Inter-Account Transfers:")
        account.show_transactions(limit=limit, transaction_type_filter="INTER_ACCOUNT")

    def view_inter_account_transactions(self, account: Account):
        """View inter-account transfers"""
        limit = self._get_transaction_limit()
        print("\n🔄 Inter-Account Transfers:")
        account.show_transactions(limit=limit, transaction_type_filter="INTER_ACCOUNT")

    def view_salary_tax_transactions(self, account: Account):
        """View salary and tax transactions"""
        limit = self._get_transaction_limit()
        print("\n💵 Salary & Tax Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="SALARY_TAX")

    def view_expense_transactions(self, account: Account):
        """View expense transactions"""
        limit = self._get_transaction_limit()
        print("\n🛒 Expense Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="EXPENSE")

    def view_debit_card_transactions(self, account: Account):
        """View debit card transactions"""
        limit = self._get_transaction_limit()
        print("\n💳 Debit Card Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="DEBIT_CARD")

    def view_credit_card_transactions(self, account: Account):
        """View credit card transactions"""
        limit = self._get_transaction_limit()
        print("\n💳 Credit Card Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="CREDIT_CARD")

    def view_registry_statistics(self):
        """View international registry statistics"""
        stats = self.bank.international_registry.get_statistics()

        print("\n" + "=" * 70)
        print("INTERNATIONAL REGISTRY STATISTICS")
        print("=" * 70)
        print(f"\nTotal Accounts: {stats['total_accounts']}")
        print(
            f"Total Balance (USD Equivalent): ${stats['total_balance_usd_equivalent']:,.2f}"
        )

        print("\n[STATS] Accounts by Country:")
        for country, count in sorted(stats["by_country"].items()):
            print(f"   {country}: {count} accounts")

        print("\n💱 Accounts by Currency:")
        for currency, count in sorted(stats["by_currency"].items()):
            print(f"   {currency}: {count} accounts")

    def view_swift_transactions(self, account: Account):
        """View all SWIFT/international transfers"""
        account._load_transactions_if_needed()
        swift_transfers = [
            t
            for t in account.transactions
            if t.type in ["SWIFT_SENT", "SWIFT_RECEIVED"]
        ]

        if not swift_transfers:
            print("\n📭 No SWIFT transactions found")
            return

        print("\n" + "=" * 100)
        print(f"INTERNATIONAL TRANSFERS (SWIFT) - Account: {account.account_number}")
        print("=" * 100)
        print(
            f"{'#':<4} {'Date/Time':<20} {'SWIFT Reference':<30} {'Recipient':<25} {'Amount':<15}"
        )
        print("-" * 100)

        for idx, txn in enumerate(swift_transfers, 1):
            metadata = self._parse_metadata(txn.metadata)
            if metadata:
                swift_ref = metadata.get("swift_reference", metadata.get("swiftRef", "N/A"))
                recipient = metadata.get("recipient_name", "N/A")[:25]
                currency = metadata.get("currency", "INR")
                try:
                    amount = float(metadata.get("amount_foreign", metadata.get("foreignAmt", abs(txn.amount))))
                except (ValueError, TypeError):
                    amount = abs(txn.amount)
                amount_str = f"{amount:,.2f} {currency}"
            else:
                swift_ref = "N/A"
                recipient = "N/A"
                amount_str = f"{abs(txn.amount):,.2f} INR"

            print(
                f"{idx:<4} {txn.timestamp:<20} {swift_ref:<30} {recipient:<25} {amount_str:<15}"
            )

        print("-" * 100)
        print(f"Total: {len(swift_transfers)} international transfer(s)")
        view = input("\nView details? (enter # or press Enter to go back): ").strip()
        if view.isdigit():
            num = int(view)
            if 1 <= num <= len(swift_transfers):
                self._display_transaction_details(swift_transfers[num - 1], account)

    def _display_transaction_details(self, txn: Transaction, account: Account):
        """Display detailed information about a transaction"""
        print("\n" + "=" * 80)
        print("TRANSACTION DETAILS")
        print("=" * 80)
        print(f"Transaction ID:     {txn.id}")
        print(f"Type:               {txn.type}")
        print(f"Date/Time:          {txn.timestamp}")
        print(f"Amount:             Rs. {abs(txn.amount):,.2f}")
        print(f"Resulting Balance:  Rs. {txn.resulting_balance:,.2f}")

        metadata = self._parse_metadata(txn.metadata)
        if txn.type == "SWIFT_SENT" and metadata:
            print("\n" + "-" * 80)
            print("INTERNATIONAL TRANSFER DETAILS")
            print("-" * 80)
            print(f"SWIFT Reference:    {metadata.get('swift_reference', 'N/A')}")
            print(f"Recipient Name:     {metadata.get('recipient_name', 'N/A')}")
            print(f"Recipient Account:  {metadata.get('recipient_account', 'N/A')}")
            print(f"Bank:               {metadata.get('recipient_bank', 'N/A')}")
            print(f"SWIFT Code:         {metadata.get('swift_code', 'N/A')}")
            print(f"Country:            {metadata.get('country', 'N/A')}")
            currency = metadata.get("currency", "")
            try:
                amount_foreign = float(metadata.get("amount_foreign", 0))
                exchange_rate = float(metadata.get("exchange_rate", 0))
            except (ValueError, TypeError):
                amount_foreign = 0
                exchange_rate = 0
            print(f"\nAmount Sent:        {amount_foreign:,.2f} {currency}")
            print(f"Exchange Rate:      1 {currency} = Rs. {exchange_rate:,.2f}")
            print(f"Amount in INR:      Rs. {amount_foreign * exchange_rate:,.2f}")
            print(f"SWIFT Charges:      Rs. {float(metadata.get('swift_charges', 0)):,.2f}")
            print(f"Purpose:            {metadata.get('purpose', 'N/A')}")
            print(f"Expected Arrival:   {metadata.get('expected_arrival', 'N/A')}")
        elif metadata:
            print("\n" + "-" * 80)
            print("ADDITIONAL DETAILS")
            print("-" * 80)
            for key, value in metadata.items():
                print(f"{key.replace('_', ' ').title():<20}: {value}")

        print("=" * 80)
        input("\nPress Enter to continue...")
    def view_balance(self, account: Account):
        """Display current account balance"""
        print(f"\nAccount Number: {account.account_number}")
        print(f"Current Balance: Rs. {account.balance:,.2f} INR")
        input("\nPress Enter to continue...")

    def deposit_money(self, account: Account):
        """Handle cash deposit to account"""
        print("\n=== Deposit Money ===")
        amount = self.app.read_positive_double("Enter amount to deposit (Rs.): ")
        
        account.balance += amount
        
        # Log transaction
        txn = Transaction(
            type="CASH_DEPOSIT",
            amount=amount,
            resulting_balance=account.balance,
            metadata="Self cash deposit"
        )
        account.transactions.append(txn)
        
        # Log to activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="DEPOSIT",
            amount=amount,
            resulting_balance=account.balance,
            txn_id=txn.id
        )
        
        self.bank.save()
        print(f"\n[SUCCESS] Rs. {amount:,.2f} deposited. New balance: Rs. {account.balance:,.2f}")
        input("\nPress Enter to continue...")

    def withdraw_money(self, account: Account):
        """Handle cash withdrawal from account"""
        print("\n=== Withdraw Money ===")
        amount = self.app.read_positive_double("Enter amount to withdraw (Rs.): ")
        
        if account.balance < amount:
            print("\n[FAIL] Insufficient balance.")
            return
            
        account.balance -= amount
        
        # Log transaction
        txn = Transaction(
            type="CASH_WITHDRAWAL",
            amount=amount,
            resulting_balance=account.balance,
            metadata="Self cash withdrawal"
        )
        account.transactions.append(txn)
        
        # Log to activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="WITHDRAWAL",
            amount=amount,
            resulting_balance=account.balance,
            txn_id=txn.id
        )
        
        self.bank.save()
        print(f"\n[SUCCESS] Rs. {amount:,.2f} withdrawn. New balance: Rs. {account.balance:,.2f}")
        input("\nPress Enter to continue...")

    def view_expense_analysis(self, account: Account):
        """View analysis of expenses categorized by type"""
        from ..ExpenseSimulator import ExpenseSimulator
        ExpenseSimulator.analyze_spending(account)
        input("\nPress Enter to continue...")

    def view_swift_transactions(self, account: Account):
        """View international SWIFT transactions"""
        print("\n=== SWIFT Transactions ===")
        swift_txns = [t for t in account.transactions if t.type == "SWIFT_TRANSFER"]
        if not swift_txns:
            print("[INFO] No SWIFT transactions found.")
        else:
            for t in swift_txns:
                print(f"{t.timestamp} | {t.id} | Rs. {t.amount:,.2f} | {t.metadata}")
        input("\nPress Enter to continue...")
