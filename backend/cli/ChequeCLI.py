from datetime import datetime
from typing import List, Optional

from ..Account import Account
from ..Logger import BankLogger
from ..BankClock import BankClock
from ..Cheque import ChequeStatus
from ..Transaction import Transaction



class ChequeCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.logger = BankLogger.get_logger("ChequeCLI")

    def cheque_management_menu(self, account: Account):
        """Cheque management submenu"""
        while True:
            print("\n" + "=" * 50)
            print("CHEQUE MANAGEMENT")
            print("=" * 50)
            print("1. Issue Cheque")
            print("2. View Cheque Book Status")
            print("3. View Cheque History")
            print("4. Present Cheque for Clearing")
            print("5. Deposit Cheque from Another Account")
            print("6. Cancel Cheque")
            print("7. Back to Main Menu")
            print("=" * 50)

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.issue_cheque(account)

            elif choice == "2":
                account.get_cheque_book_status()

            elif choice == "3":
                self.view_cheque_history(account)

            elif choice == "4":
                self.present_cheque_for_clearing(account)

            elif choice == "5":
                self.deposit_cheque_from_other_account(account)

            elif choice == "6":
                self.cancel_cheque(account)

            elif choice == "7":
                break

            else:
                print("Invalid choice")

    def issue_cheque(self, account: Account):
        """Issue a new cheque from the account"""
        print("\n" + "=" * 60)
        print("ISSUE CHEQUE")
        print("=" * 60)

        # Get unused cheque number
        active_book = account.cheque_book_manager.get_active_cheque_book()
        if not active_book:
            print("\n[INFO] Creating new cheque book...")
            # Allocate numbers from bank's global counter
            starting_number = self.bank.allocate_cheque_numbers(50)
            account.cheque_book_manager.create_and_issue_cheque_book(starting_number)
            active_book = account.cheque_book_manager.get_active_cheque_book()

        unused_cheques = active_book.get_unused_cheques()
        if not unused_cheques:
            print("\n[INFO] Current cheque book fully used. Creating new book...")
            # Allocate numbers from bank's global counter
            starting_number = self.bank.allocate_cheque_numbers(50)
            account.cheque_book_manager.create_and_issue_cheque_book(starting_number)
            active_book = account.cheque_book_manager.get_active_cheque_book()
            unused_cheques = active_book.get_unused_cheques()

        if not unused_cheques:
            print("\n[ERROR] Cannot create new cheque book.")
            return

        cheque_number = unused_cheques[0].cheque_number

        print(f"\nCheque Number: {cheque_number}")
        print(f"Available Balance: Rs. {account.balance:,.2f} INR")

        # Get cheque details
        try:
            amount = float(input("Enter cheque amount (Rs.): ").strip())
            if amount <= 0:
                print("[ERROR] Amount must be greater than 0")
                return
            if amount > 10000000:  # Reasonable limit
                print("[ERROR] Amount exceeds maximum limit")
                return

            payee_name = input("Enter payee name: ").strip()
            if not payee_name:
                print("[ERROR] Payee name cannot be empty")
                return

            print("\nSelect presentable date:")
            print("1. Today")
            print("2. Custom date (YYYY-MM-DD format)")
            date_choice = input("Enter choice (1 or 2): ").strip()

            if date_choice == "1":

                date_presentable = BankClock.today().isoformat()
            elif date_choice == "2":
                date_presentable = input("Enter date (YYYY-MM-DD): ").strip()
                # Validate date format
                try:
                    from datetime import datetime

                    datetime.strptime(date_presentable, "%Y-%m-%d")
                except ValueError:
                    print("[ERROR] Invalid date format")
                    return
            else:
                print("[ERROR] Invalid choice")
                return

            # Issue the cheque
            cheque_id = account.issue_cheque(
                cheque_number, amount, payee_name, date_presentable
            )

            print("\n" + "=" * 60)
            print("[SUCCESS] CHEQUE ISSUED")
            print("=" * 60)
            print(f"Cheque ID: {cheque_id}")
            print(f"Cheque Number: {cheque_number}")
            print(f"Amount: Rs. {amount:,.2f} INR")
            print(f"Payee: {payee_name}")
            print(f"Presentable From: {date_presentable}")
            print("=" * 60)

            self.bank.save()
            # Force reload account with fresh transactions from storage
            self.bank.reload_account_with_transactions(account.account_number)

        except ValueError:
            print("[ERROR] Invalid amount entered")

    def view_cheque_history(self, account: Account):
        """View cheque history for the account"""
        print("\n" + "=" * 60)
        print("CHEQUE HISTORY")
        print("=" * 60)

        cheque_books = account.cheque_book_manager.get_all_cheque_books()
        if not cheque_books:
            print("\nNo cheque books found for this account.")
            return

        total_issued = 0
        total_cleared = 0
        total_bounced = 0

        for book in cheque_books:
            for cheque in book.cheques.values():
                if cheque.status == ChequeStatus.ISSUED:
                    total_issued += 1
                elif cheque.status == ChequeStatus.CLEARED:
                    total_cleared += 1
                elif cheque.status == ChequeStatus.BOUNCED:
                    total_bounced += 1

        print(f"\nTotal Cheques Issued: {total_issued}")
        print(f"Total Cleared: {total_cleared}")
        print(f"Total Bounced: {total_bounced}")

        # Show recent cheques
        all_cheques = []
        for book in cheque_books:
            for cheque in book.cheques.values():
                if cheque.amount > 0:  # Only show cheques that have been issued
                    all_cheques.append(cheque)

        if all_cheques:
            print("\n" + "-" * 60)
            print("Recent Cheques:")
            print("-" * 60)
            # Show last 10 cheques
            for cheque in all_cheques[-10:]:
                print(f"\nCheque: {cheque.cheque_number} (ID: {cheque.cheque_id})")
                print(f"  Status: {cheque.status.value}")
                print(f"  Payee: {cheque.payee_name}")
                print(f"  Amount: Rs. {cheque.amount:,.2f}")
                print(f"  Presentable: {cheque.date_presentable}")
                if cheque.status == ChequeStatus.BOUNCED:
                    print(f"  Bounce Reason: {cheque.bounce_reason}")

    def present_cheque_for_clearing(self, account: Account):
        """Present cheque for clearing/payment"""
        print("\n" + "=" * 60)
        print("PRESENT CHEQUE FOR CLEARING")
        print("=" * 60)

        # Get all issued cheques
        cheque_books = account.cheque_book_manager.get_all_cheque_books()
        if not cheque_books:
            print("\nNo cheque books found for this account.")
            return

        issued_cheques = []
        for book in cheque_books:
            for cheque in book.cheques.values():
                if cheque.status == ChequeStatus.ISSUED and cheque.amount > 0:
                    issued_cheques.append((cheque, book))

        if not issued_cheques:
            print("\nNo issued cheques available for clearing.")
            return

        # Display issued cheques
        print("\nAvailable cheques for clearing:\n")
        for idx, (cheque, book) in enumerate(issued_cheques, 1):
            print(
                f"{idx}. {cheque.cheque_number} | Payee: {cheque.payee_name} | "
                f"Amount: Rs. {cheque.amount:,.2f} | Date: {cheque.date_presentable}"
            )

        try:
            choice = input(
                "\nSelect cheque by number or list index (or press ESC to cancel): "
            ).strip()
            if not choice or choice.lower() == "esc":
                return

            # Find the selected cheque (by index or cheque number)
            selected_cheque = None
            selected_book = None

            # Try as index first
            try:
                idx = int(choice) - 1  # Convert 1-based to 0-based
                if 0 <= idx < len(issued_cheques):
                    selected_cheque, selected_book = issued_cheques[idx]
            except ValueError:
                pass

            # If not found by index, try by cheque number
            if not selected_cheque:
                for cheque, book in issued_cheques:
                    if cheque.cheque_number == choice:
                        selected_cheque = cheque
                        selected_book = book
                        break

            if not selected_cheque:
                print(
                    "[ERROR] Cheque not found. Please enter a valid index or cheque number."
                )
                return

            # Check if cheque is presentable
            if not selected_cheque.is_presentable():
                print(
                    "\n[ERROR] Cheque is not yet presentable or is stale (> 6 months old)"
                )
                return

            # Present the cheque
            print(f"\nProcessing cheque {selected_cheque.cheque_number}...")
            is_cleared = self.bank.present_cheque_for_clearing(
                account, selected_cheque.cheque_id
            )

            if is_cleared:
                # Update cheque status to CLEARED
                selected_cheque.status = ChequeStatus.CLEARED
                print("\n" + "=" * 60)
                print("[SUCCESS] CHEQUE CLEARED")
                print("=" * 60)
                print(f"Cheque Number: {selected_cheque.cheque_number}")
                print(f"Amount: Rs. {selected_cheque.amount:,.2f}")
                print(f"Payee: {selected_cheque.payee_name}")
                print("Status: CLEARED")
                print("=" * 60)

            else:
                # Update cheque status to BOUNCED
                selected_cheque.status = ChequeStatus.BOUNCED
                selected_cheque.bounce_reason = (
                    "Insufficient balance or presentation issue"
                )
                print("\n" + "=" * 60)
                print("[BOUNCED] CHEQUE PRESENTATION FAILED")
                print("=" * 60)
                print(f"Cheque Number: {selected_cheque.cheque_number}")
                print(f"Amount: Rs. {selected_cheque.amount:,.2f}")
                print(f"Payee: {selected_cheque.payee_name}")
                print("Status: BOUNCED")
                print("Fee Deducted: Rs. 500")
                print("\n*** CIBIL IMPACT WARNING ***")
                print("Bounce recorded and CIBIL score reduced.")
                print("Check CIBIL report for complete impact.")
                print("=" * 60)

            self.bank.save()
            # Force reload account with fresh transactions from storage
            self.bank.reload_account_with_transactions(account.account_number)

        except Exception as e:
            print(f"[ERROR] {str(e)}")

    def deposit_cheque_from_other_account(self, account: Account):
        """Deposit a cheque issued by another account into this account"""
        print("\n" + "=" * 60)
        print("DEPOSIT CHEQUE FROM ANOTHER ACCOUNT")
        print("=" * 60)

        try:
            # Load transactions if needed
            account._load_transactions_if_needed()

            cheque_number = input("\nEnter cheque number to deposit: ").strip()
            if not cheque_number:
                print("[ERROR] Cheque number cannot be empty")
                return

            # Search all accounts for this cheque
            found_cheque = None
            issuing_account = None

            for acc in self.bank.accounts:
                # Load transactions for all accounts
                acc._load_transactions_if_needed()

                cheque_books = acc.cheque_book_manager.get_all_cheque_books()
                for book in cheque_books:
                    for cheque in book.cheques.values():
                        if cheque.cheque_number == cheque_number:
                            found_cheque = cheque
                            issuing_account = acc
                            break
                    if found_cheque:
                        break
                if found_cheque:
                    break

            if not found_cheque:
                print(f"[ERROR] Cheque {cheque_number} not found in any account")
                return

            # DEBUG: Verify account reference
            print(
                f"\n[DEBUG] Found cheque in account: {issuing_account.account_number}"
            )
            is_same = False
            for acc in self.bank.accounts:
                if acc.account_number == issuing_account.account_number:
                    is_same = acc is issuing_account
                    print(
                        f"[DEBUG] Account is {'SAME' if is_same else 'DIFFERENT'} object in bank.accounts"
                    )
                    break

            # Verify cheque status
            if found_cheque.status != ChequeStatus.ISSUED:
                print(f"[ERROR] Cheque is {found_cheque.status.value}, cannot deposit")
                return

            # Verify cheque is presentable
            if not found_cheque.is_presentable():
                print(
                    "[ERROR] Cheque is not yet presentable or is stale (> 6 months old)"
                )
                return

            # Display cheque details
            print("\n" + "-" * 60)
            print(f"Cheque Number: {found_cheque.cheque_number}")
            print(
                f"Issued By: {issuing_account.first_name} {issuing_account.last_name} ({issuing_account.account_number})"
            )
            print(f"Payee: {found_cheque.payee_name}")
            print(f"Amount: Rs. {found_cheque.amount:,.2f}")
            print(f"Presentable Date: {found_cheque.date_presentable}")
            print("-" * 60)

            # Validate payee matches account holder
            depositor_name = f"{account.first_name} {account.last_name}"
            if found_cheque.payee_name.lower() != depositor_name.lower():
                print(
                    f"\n[ERROR] Cheque is payable to '{found_cheque.payee_name}', not '{depositor_name}'"
                )
                print("Cheque can only be deposited by the payee.")
                return

            # Confirm deposit
            confirm = (
                input(
                    f"\nDeposit cheque for Rs. {found_cheque.amount:,.2f}? (yes/no): "
                )
                .strip()
                .lower()
            )
            if confirm != "yes":
                print("Deposit cancelled")
                return

            # Process deposit
            # 1. Deduct from issuing account
            if issuing_account.balance < found_cheque.amount:
                # Bounce the cheque
                found_cheque.status = ChequeStatus.BOUNCED
                found_cheque.bounce_reason = "Insufficient balance in issuing account"
                self.bank.save()
                print("\n[BOUNCED] Insufficient balance in issuing account")
                return

            # 2. Deduct from issuing account
            issuing_account.balance -= found_cheque.amount
            issuing_account.transactions.append(
                Transaction(
                    type="CHEQUE_CLEARED",
                    amount=found_cheque.amount,
                    resulting_balance=issuing_account.balance,
                    cheque_id=found_cheque.cheque_id,
                    metadata=f"Cheque deposited to {account.account_number}",
                )
            )

            # 3. Credit to depositing account
            account.balance += found_cheque.amount
            account.transactions.append(
                Transaction(
                    type="CHEQUE_DEPOSITED",
                    amount=found_cheque.amount,
                    resulting_balance=account.balance,
                    cheque_id=found_cheque.cheque_id,
                    metadata=f"Cheque from {issuing_account.account_number}",
                )
            )

            # 4. Mark cheque as cleared
            found_cheque.status = ChequeStatus.CLEARED

            # DEBUG: Show transaction counts before save
            print("\n[DEBUG] Before save:")
            print(
                f"  Depositing account ({account.account_number}): {len(account.transactions)} transactions"
            )
            if account.transactions:
                print(f"    Last: {account.transactions[-1].type}")
            print(
                f"  Issuing account ({issuing_account.account_number}): {len(issuing_account.transactions)} transactions"
            )
            if issuing_account.transactions:
                print(f"    Last: {issuing_account.transactions[-1].type}")

            # Save all changes
            self.bank.save()

            # DEBUG: Show transaction counts after save
            print("\n[DEBUG] After save, before reload:")
            print(f"  Depositing account: {len(account.transactions)} transactions")
            print(
                f"  Issuing account: {len(issuing_account.transactions)} transactions"
            )

            # Force reload both accounts with fresh transactions from storage
            self.bank.reload_account_with_transactions(account.account_number)
            self.bank.reload_account_with_transactions(issuing_account.account_number)

            # DEBUG: Show transaction counts after reload
            print("\n[DEBUG] After reload:")
            print(f"  Depositing account: {len(account.transactions)} transactions")
            if account.transactions:
                print(f"    Last: {account.transactions[-1].type}")
            print(
                f"  Issuing account: {len(issuing_account.transactions)} transactions"
            )
            if issuing_account.transactions:
                print(f"    Last: {issuing_account.transactions[-1].type}")

            # Show success
            print("\n" + "=" * 60)
            print("[SUCCESS] CHEQUE DEPOSITED")
            print("=" * 60)
            print(f"Cheque Number: {found_cheque.cheque_number}")
            print(f"Amount: Rs. {found_cheque.amount:,.2f}")
            print(f"Deposited to: {account.account_number}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] {str(e)}")

    def cancel_cheque(self, account: Account):
        """Cancel an issued cheque before it's cleared"""
        print("\n" + "=" * 60)
        print("CANCEL CHEQUE")
        print("=" * 60)

        # Get all issued cheques from this account
        cheque_books = account.cheque_book_manager.get_all_cheque_books()
        if not cheque_books:
            print("\nNo cheque books found for this account.")
            return

        issued_cheques = []
        for book in cheque_books:
            for cheque in book.cheques.values():
                # Can only cancel ISSUED cheques (not cleared, bounced, or already cancelled)
                if cheque.status == ChequeStatus.ISSUED and cheque.amount > 0:
                    issued_cheques.append((cheque, book))

        if not issued_cheques:
            print("\nNo issued cheques available to cancel.")
            return

        # Display issued cheques
        print("\nCheques available for cancellation:\n")
        for idx, (cheque, book) in enumerate(issued_cheques, 1):
            print(
                f"{idx}. {cheque.cheque_number} | Payee: {cheque.payee_name} | "
                f"Amount: Rs. {cheque.amount:,.2f} | Date: {cheque.date_presentable}"
            )

        try:
            choice = input(
                "\nSelect cheque by number or list index (or press ESC to cancel): "
            ).strip()
            if not choice or choice.lower() == "esc":
                return

            # Find the selected cheque (by index or cheque number)
            selected_cheque = None

            # Try as index first
            try:
                idx = int(choice) - 1  # Convert 1-based to 0-based
                if 0 <= idx < len(issued_cheques):
                    selected_cheque, _ = issued_cheques[idx]
            except ValueError:
                pass

            # If not found by index, try by cheque number
            if not selected_cheque:
                for cheque, book in issued_cheques:
                    if cheque.cheque_number == choice:
                        selected_cheque = cheque
                        break

            if not selected_cheque:
                print(
                    "[ERROR] Cheque not found. Please enter a valid index or cheque number."
                )
                return

            # Confirm cancellation
            print("\n" + "-" * 60)
            print(f"Cheque Number: {selected_cheque.cheque_number}")
            print(f"Payee: {selected_cheque.payee_name}")
            print(f"Amount: Rs. {selected_cheque.amount:,.2f}")
            print("-" * 60)

            confirm = (
                input(f"\nCancel cheque {selected_cheque.cheque_number}? (yes/no): ")
                .strip()
                .lower()
            )
            if confirm != "yes":
                print("Cancellation cancelled")
                return

            # Cancel the cheque
            selected_cheque.status = ChequeStatus.CANCELLED
            selected_cheque.cancellation_reason = "Cancelled by account holder"

            # Save changes
            self.bank.save()
            # Force reload account with fresh transactions from storage
            self.bank.reload_account_with_transactions(account.account_number)

            # Show success
            print("\n" + "=" * 60)
            print("[SUCCESS] CHEQUE CANCELLED")
            print("=" * 60)
            print(f"Cheque Number: {selected_cheque.cheque_number}")
            print(f"Amount: Rs. {selected_cheque.amount:,.2f}")
            print("Status: CANCELLED")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] {str(e)}")

    def track_cheque(self):
        """Track a cheque by ID"""
        cheque_id = input("Enter Cheque ID to track: ").strip()
        if cheque_id:
            self.bank.show_cheque_details(cheque_id)
        else:
            print("Cheque ID cannot be empty.")
        input("\nPress Enter to continue...")
