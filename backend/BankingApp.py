from datetime import date
from typing import Dict, List
import sys
import os

# Add parent directory to sys.path to support both direct execution and package imports
if __name__ == "__main__" and __package__ is None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from backend.Account import Account
    from backend.AdminControlPanel import AdminControlPanel
    from backend.Bank import Bank
    from backend.BankClock import BankClock, switch_to_real_mode, switch_to_virtual_mode
    from backend.Card import Card, CreditCard, DebitCard
    from backend.Cheque import ChequeStatus
    from backend.CIBIL import add_credit_inquiry, calculate_cibil_score
    from backend.ClosureFormalities import ClosureFormalities
    from backend.CreditEvaluator import CreditEvaluator
    from backend.Customer import Customer
    from backend.ExpenseSimulator import ExpenseSimulator
    from backend.FixedDeposit import FixedDeposit
    from backend.ITRFiling import ITRFiling, ITRStatus
    from backend.PasswordRecovery import PasswordRecoveryUI
    from backend.RDStatement import RDStatement
    from backend.RecurringBill import PaymentMethod, RecurringBill, RecurringBillFactory
    from backend.RecurringDeposit import RecurringDeposit
    from backend.TaxCalculator import TaxCalculator
    from backend.TaxDeductionAnalyzer import TaxDeductionAnalyzer
    from backend.TaxExemption import DeductionStatus, DeductionType, TaxExemption
    from backend.Transaction import Transaction
else:
    from .Account import Account
    from .AdminControlPanel import AdminControlPanel
    from .Bank import Bank
    from .BankClock import BankClock, switch_to_real_mode, switch_to_virtual_mode
    from .Card import Card, CreditCard, DebitCard
    from .Cheque import ChequeStatus
    from .CIBIL import add_credit_inquiry, calculate_cibil_score
    from .ClosureFormalities import ClosureFormalities
    from .CreditEvaluator import CreditEvaluator
    from .Customer import Customer
    from .ExpenseSimulator import ExpenseSimulator
    from .FixedDeposit import FixedDeposit
    from .ITRFiling import ITRFiling, ITRStatus
    from .PasswordRecovery import PasswordRecoveryUI
    from .RDStatement import RDStatement
    from .RecurringBill import PaymentMethod, RecurringBill, RecurringBillFactory
    from .RecurringDeposit import RecurringDeposit
    from .TaxCalculator import TaxCalculator
    from .TaxDeductionAnalyzer import TaxDeductionAnalyzer
    from .TaxExemption import DeductionStatus, DeductionType, TaxExemption
    from .Transaction import Transaction


class BankingApp:
    """Main banking application with CLI interface"""

    def __init__(self):
        self.bank = Bank()
        self.running = True

    @staticmethod
    def read_date(prompt: str) -> str:
        """Read and validate a date in YYYY-MM-DD format"""
        while True:
            user_input = input(prompt).strip()
            try:
                date.fromisoformat(user_input)
                return user_input
            except ValueError:
                print("Invalid date. Please use YYYY-MM-DD.")

    @staticmethod
    def read_positive_double(prompt: str, allow_zero: bool = False) -> float:
        """Read and validate a positive number"""
        while True:
            try:
                value = float(input(prompt))
                if allow_zero:
                    if value >= 0:
                        return value
                    else:
                        print("Please enter a non-negative number.")
                else:
                    if value > 0:
                        return value
                    else:
                        print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")

    @staticmethod
    def read_valid_gender(prompt: str) -> str:
        """Read and validate gender input"""
        while True:
            user_input = input(prompt).strip().lower()
            if user_input in ["male", "m"]:
                return "Male"
            elif user_input in ["female", "f"]:
                return "Female"
            else:
                print("Invalid input. Please enter 'Male' or 'Female' (or 'M'/'F').")

    @staticmethod
    def read_valid_choice(
        prompt: str,
        valid_choices: list,
        error_message: str = "Invalid choice. Please try again.",
    ) -> str:
        """Read and validate user choice from a list of valid options"""
        while True:
            choice = input(prompt).strip()
            if choice in valid_choices:
                return choice
            else:
                print(error_message)

    @staticmethod
    def read_valid_account_type(prompt: str) -> str:
        """Read and validate account type selection"""
        account_types = {
            "1": "Pride",
            "2": "Bespoke",
            "3": "Club",
            "4": "Delite",
            "5": "Future",
        }
        while True:
            choice = input(prompt).strip()
            if choice in account_types:
                return account_types[choice]
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

    @staticmethod
    def read_valid_transfer_mode(prompt: str) -> str:
        """Read and validate transfer mode (NEFT/RTGS)"""
        while True:
            choice = input(prompt).strip()
            if choice == "1":
                return "NEFT"
            elif choice == "2":
                return "RTGS"
            else:
                print("Invalid choice. Please enter 1 for NEFT or 2 for RTGS.")

    def open_new_account(self):
        """Handle new account registration"""
        print("Please fill in your details to open a new account.")

        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()

        dob = self.read_date("Date of Birth (YYYY-MM-DD): ")
        dob_date = date.fromisoformat(dob)
        today = date.today()
        age = (
            today.year
            - dob_date.year
            - ((today.month, today.day) < (dob_date.month, dob_date.day))
        )

        gender = self.read_valid_gender("Gender (Male/Female): ")
        phone_number = input("Phone Number: ").strip()
        email = input("Email: ").strip()

        if age < 18:
            print("Age is below 18. Automatically assigning 'Future' account.")
            account_type = "Future"
        else:
            print("""
Choose Account Type:
1  Pride (Min Balance: Rs. 2,000.00)
2  Bespoke (Min Balance: Rs. 2,00,000.00)
3  Club (Min Balance: Rs. 10,000.00)
4  Delite (Min Balance: Rs. 5,000.00)
5  Future (For Minors)
            """)
            account_type = self.read_valid_account_type("Enter choice (1-5): ")

        # Username validation
        while True:
            username = input("Choose a Username: ").strip()
            if not username:
                print("Username cannot be empty. Please try again.")
            elif self.bank.username_exists(username):
                print("Username already exists. Try another.")
            else:
                break

        # Password validation
        while True:
            password = input("Set a Password: ").strip()
            if not password:
                print("Password cannot be empty. Please try again.")
            else:
                break

        customer, account = self.bank.register_customer(
            username,
            password,
            first_name,
            last_name,
            dob,
            gender,
            phone_number,
            email,
            account_type,
        )

        print(f"""
Account successfully created!
Customer ID: {customer.customer_id}
Account Holder: {first_name} {last_name}
Account Type: {account.account_type}
Account Number: {account.account_number}

{Account.get_branch_details()}

You can now login!
        """)

    def handle_login(self):
        """Handle user login and account management"""
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        customer = self.bank.authenticate(username, password)
        if not customer:
            print("Invalid credentials or account locked.")
            return

        # NEW: Check if customer needs to set up security question
        if not customer.has_security_question():
            print("\n" + "=" * 70)
            print("[SECURE] SECURITY SETUP REQUIRED")
            print("=" * 70)
            print("For account security, please set up a security question.")
            print("This helps you recover your password if you forget it.")
            print("=" * 70)

            PasswordRecoveryUI.prompt_legacy_customer_setup(customer, self.bank)

        accounts = self.bank.get_customer_accounts(customer)
        if not accounts:
            print("No accounts found for this customer.")
            return

        # ... rest of existing code ...

        # Account selection
        if len(accounts) > 1:
            print(f"""
Login Successful! 

{BankClock.get_login_banner()}

Customer: {customer.first_name} {customer.last_name}
Customer ID: {customer.customer_id}

You have {len(accounts)} accounts. Please select one:
            """)
            for idx, acc in enumerate(accounts, 1):
                print(
                    f"{idx}. {acc.account_type} - {acc.account_number} (Balance: Rs. {acc.balance:.2f} INR)"
                )

            choice = self.read_valid_choice(
                f"Enter account number (1-{len(accounts)}): ",
                [str(i) for i in range(1, len(accounts) + 1)],
            )
            selected_account = accounts[int(choice) - 1]
        else:
            print(f"""
Login Successful!

{BankClock.get_login_banner()}

Customer: {customer.first_name} {customer.last_name}
Customer ID: {customer.customer_id}
            """)
            selected_account = accounts[0]

        # Account menu loop
        self.account_menu(customer, accounts, selected_account)

    def account_menu(
        self, customer: Customer, accounts: List[Account], selected_account: Account
    ):
        """Display and handle account menu options"""
        active = True

        while active:
            print(f"""
    Current Date/Time: {BankClock.get_formatted_datetime()}
    
    Choose an option:
    1   View Balance
    2   Deposit Money
    3   Withdraw Money
    4   Transfer Funds (NEFT/RTGS/Inter-Account)
    5   View Transaction History
    6   Search Transaction by ID
    7   View SWIFT Transactions
    8   Switch Account
    9   Create Additional Account
    10  Manage Recurring Bills
    11  Manage Salary
    12  Simulate Time (Fast Forward)
    13  View Expense Analysis
    14  Loan Menu
    15  Card Management
    16  Cheque Management
    17  Close Card
    18  Close Account
    19  Fixed Deposit and Recurring Deposit
    20  Change Clock Mode
    21  Tax Planning & Exemptions [STATS]
    22  Manage Beneficiaries
    23  Logout
            """)
            menu_choice = self.read_valid_choice(
                "Enter your choice: ",
                [str(i) for i in range(1, 24)],
                "Invalid choice. Please enter a number from 1 to 23.",
            )

            if menu_choice == "1":
                self.view_balance(selected_account)
            elif menu_choice == "2":
                self.deposit_money(selected_account)
            elif menu_choice == "3":
                self.withdraw_money(selected_account)
            elif menu_choice == "4":
                self.transfer_funds(customer, selected_account, accounts)
            elif menu_choice == "5":
                self.view_transaction_history_menu(selected_account)
            elif menu_choice == "6":
                self.search_transaction()
            elif menu_choice == "7":
                self.view_swift_transactions(selected_account)
            elif menu_choice == "8":
                selected_account = self.switch_account(accounts)
            elif menu_choice == "9":
                accounts = self.create_additional_account(customer, accounts)
            elif menu_choice == "10":
                self.manage_recurring_bills(selected_account)
            elif menu_choice == "11":
                self.manage_salary(selected_account)
            elif menu_choice == "12":
                self.simulate_time(selected_account)
            elif menu_choice == "13":
                self.view_expense_analysis(selected_account)
            elif menu_choice == "14":
                self.loan_menu(customer, selected_account)
            elif menu_choice == "15":
                self.card_management_menu(selected_account)
            elif menu_choice == "16":
                self.cheque_management_menu(selected_account)
            elif menu_choice == "17":
                ClosureFormalities.close_card_menu(selected_account, self.bank)
            elif menu_choice == "18":
                closure_success = ClosureFormalities.close_account_menu(
                    selected_account, customer, accounts, self.bank
                )
                if closure_success:
                    # Account was closed, exit to main menu
                    active = False
            elif menu_choice == "19":
                self.fd_rd_menu(customer, selected_account)  # [SUCCESS] FIX: Added ()
            elif menu_choice == "20":
                self.change_clock_mode()
            elif menu_choice == "21":
                self.tax_planning_menu(customer, selected_account)
            elif menu_choice == "22":
                self.manage_beneficiaries_menu(customer)
            elif menu_choice == "23":
                print("Logged out successfully.")
                active = False


    # ========== BENEFICIARY MANAGEMENT ==========
    
    def manage_beneficiaries_menu(self, customer: Customer):
        """Beneficiary management submenu"""
        from .Beneficiary import IFSCValidator
        
        while True:
            print("\n" + "=" * 50)
            print("MANAGE BENEFICIARIES")
            print("=" * 50)
            print("1. View All Beneficiaries")
            print("2. Add New Beneficiary")
            print("3. Remove Beneficiary")
            print("4. Back to Main Menu")
            print("=" * 50)

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                beneficiaries = customer.beneficiary_manager.list_all()
                if not beneficiaries:
                    print("\nNo beneficiaries found.")
                else:
                    print("\n" + "-" * 70)
                    print(f"{'Name':<20} {'Account Number':<20} {'Bank':<20} {'Status'}")
                    print("-" * 70)
                    for b in beneficiaries:
                        print(f"{b.beneficiary_name:<20} {b.account_number:<20} {b.bank_name[:18]:<20} {b.status}")
                    print("-" * 70)

            elif choice == "2":
                print("\n--- Add New Beneficiary ---")
                name = input("Beneficiary Name: ").strip()
                account_num = input("Account Number: ").strip()
                ifsc = input("IFSC Code: ").strip().upper()
                
                print("\n[INFO] Validating IFSC Code...")
                bank_details = IFSCValidator.get_bank_details(ifsc)
                
                if bank_details:
                    bank_name = bank_details['bank_name']
                    branch = bank_details['branch']
                    print(f"[SUCCESS] Bank Found: {bank_name} ({branch})")
                else:
                    print("[WARN] Could not verify IFSC. Please enter details manually.")
                    bank_name = input("Bank Name: ").strip()
                    
                account_type = input("Account Type (Savings/Current) [Savings]: ").strip() or "Savings"
                
                b = customer.beneficiary_manager.add_beneficiary(name, account_num, ifsc, bank_name, account_type)
                self.bank.save()
                print(f"\n[SUCCESS] Beneficiary '{b.beneficiary_name}' added successfully!")

            elif choice == "3":
                beneficiaries = customer.beneficiary_manager.list_all()
                if not beneficiaries:
                    print("\nNo beneficiaries found.")
                    continue
                    
                print("\nSelect beneficiary to remove:")
                for idx, b in enumerate(beneficiaries, 1):
                    print(f"{idx}. {b.beneficiary_name} - {b.account_number}")
                    
                idx_choice = input("Enter number to remove (or 0 to cancel): ").strip()
                if idx_choice.isdigit() and 1 <= int(idx_choice) <= len(beneficiaries):
                    b = beneficiaries[int(idx_choice) - 1]
                    confirm = input(f"Are you sure you want to remove {b.beneficiary_name}? (yes/no): ").strip().lower()
                    if confirm in ['yes', 'y']:
                        customer.beneficiary_manager.remove_beneficiary(b.beneficiary_id)
                        self.bank.save()
                        print(f"\n[SUCCESS] Beneficiary '{b.beneficiary_name}' removed.")
                
            elif choice == "4":
                break
            else:
                print("Invalid choice")

    # ========== CARD MANAGEMENT ==========

    def card_management_menu(self, account: Account):
        """Card management submenu"""
        while True:
            print("\n" + "=" * 50)
            print("CARD MANAGEMENT")
            print("=" * 50)
            print("1. View All Cards")
            print("2. Apply for Debit Card")
            print("3. Apply for Credit Card")
            print("4. View Card Details")  # NEW OPTION
            print("5. Make Card Purchase")
            print("6. Pay Credit Card Bill")
            print("7. View Credit Card Statement")
            print("8. Block Card")
            print("9. Unblock Card")
            print("10.Credit Limit Enhancement Request")
            print("11. Manage Auto-Pay Settings")
            print("12. Set/Change Card PIN")
            print("13. Back to Main Menu")
            print("=" * 50)

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                account.list_cards()

            elif choice == "2":
                self.apply_debit_card(account)

            elif choice == "3":
                self.apply_credit_card(account)

            elif choice == "4":
                self.view_card_details(account)  # NEW METHOD

            elif choice == "5":
                self.make_card_purchase(account)

            elif choice == "6":
                self.pay_credit_card(account)

            elif choice == "7":
                self.view_credit_statement(account)

            elif choice == "8":
                self.block_card(account)

            elif choice == "9":
                self.unblock_card(account)

            elif choice == "10":
                self.request_credit_limit_enhancement(account)

            elif choice == "11":
                self.manage_card_auto_pay(account)

            elif choice == "12":
                self.set_card_pin(account)

            elif choice == "13":
                break

            else:
                print("Invalid choice")

    # ========== CHEQUE MANAGEMENT ==========

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

    def request_credit_limit_enhancement(self, account: Account):
        """Request credit limit enhancement for a credit card"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards found")
            return

        print("\n" + "=" * 70)
        print("CREDIT LIMIT ENHANCEMENT REQUEST [UP]")
        print("=" * 70)

        # Show all credit cards
        for idx, card in enumerate(credit_cards, 1):
            print(f"\n{idx}. {card.network} **** **** **** {card.card_number[-4:]}")
            print(f"   Current Limit: Rs. {card.credit_limit:,.2f}")
            print(f"   Used: Rs. {card.credit_used:,.2f}")
            print(f"   Available: Rs. {card.available_credit():,.2f}")
            print(f"   Utilization: {card.credit_utilization():.1f}%")

        if len(credit_cards) == 1:
            selected_card = credit_cards[0]
        else:
            choice = input(f"\nSelect card (1-{len(credit_cards)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(credit_cards):
                    selected_card = credit_cards[idx]
                else:
                    print("[FAIL] Invalid choice")
                    return
            except ValueError:
                print("[FAIL] Invalid input")
                return

        # Get customer object
        customer = self.bank.get_customer_by_id(account.customer_id)
        if not customer:
            print("[FAIL] Error: Customer not found")
            return

        print(f"\n{'=' * 70}")
        print(f"Checking eligibility for {selected_card.network} card...")
        print(f"{'=' * 70}")

        # Check eligibility
        eligible, reason, details = CreditLimitEnhancement.check_eligibility(
            selected_card, customer, self.bank, account
        )

        # Display eligibility details
        print("\n[STATS] ELIGIBILITY CRITERIA:")
        print(f"{'=' * 70}")

        if "card_age_months" in details:
            status = "[SUCCESS]" if details["card_age_months"] >= 6 else "[FAIL]"
            print(
                f"{status} Card Age: {details['card_age_months']} months (Required: 6+)"
            )

        if "cibil_score" in details:
            status = "[SUCCESS]" if details["cibil_score"] >= 700 else "[FAIL]"
            print(
                f"{status} CIBIL Score: {details['cibil_score']:.0f} (Required: 700+)"
            )

        if "utilization" in details:
            util = details["utilization"]
            status = "[SUCCESS]" if 30 <= util <= 90 else "[FAIL]"
            print(f"{status} Credit Utilization: {util:.1f}% (Required: 30-90%)")

        if "total_payments" in details:
            status = "[SUCCESS]" if details["total_payments"] >= 3 else "[FAIL]"
            print(
                f"{status} Payment History: {details['total_payments']} payments (Required: 3+)"
            )

        if "on_time_ratio" in details:
            ratio = details["on_time_ratio"] * 100
            status = "[SUCCESS]" if details["on_time_ratio"] >= 0.95 else "[FAIL]"
            print(f"{status} On-Time Payments: {ratio:.0f}% (Required: 95%+)")

        if "defaulted_loans" in details:
            status = "[SUCCESS]" if details["defaulted_loans"] == 0 else "[FAIL]"
            print(
                f"{status} Defaulted Loans: {details['defaulted_loans']} (Required: 0)"
            )

        print(f"{'=' * 70}")

        if not eligible:
            print(f"\n[FAIL] INELIGIBLE: {reason}")
            print("\n💡 Tips to become eligible:")
            print("   • Maintain good payment history (pay bills on time)")
            print("   • Use your credit card regularly (30-75% utilization)")
            print("   • Keep your CIBIL score above 700")
            print("   • Wait for 6 months between enhancement requests")
            return

        print(f"\n[SUCCESS] ELIGIBLE: {reason}")

        # Calculate and show potential new limit
        annual_income = 0
        if account.salary_profile:
            annual_income = account.salary_profile.gross_salary * 12
        else:
            annual_income = 300000

        potential_new_limit = CreditLimitEnhancement.calculate_new_limit(
            current_limit=selected_card.credit_limit,
            cibil_score=details["cibil_score"],
            utilization=details["utilization"],
            income=annual_income,
        )

        increase = potential_new_limit - selected_card.credit_limit
        increase_pct = (increase / selected_card.credit_limit) * 100

        print("\n[MONEY] POTENTIAL ENHANCEMENT:")
        print(f"{'=' * 70}")
        print(f"Current Limit:     Rs. {selected_card.credit_limit:>15,.2f}")
        print(f"Proposed New Limit: Rs. {potential_new_limit:>15,.2f}")
        print(f"Increase Amount:    Rs. {increase:>15,.2f} ({increase_pct:.1f}%)")
        print(f"{'=' * 70}")

        # Confirm request
        confirm = (
            input("\nProceed with enhancement request? (yes/no): ").strip().lower()
        )

        if confirm not in ["yes", "y"]:
            print("[FAIL] Request cancelled")
            return

        # Process enhancement
        approved, message, new_limit = CreditLimitEnhancement.request_enhancement(
            selected_card, customer, self.bank, account
        )

        print(f"\n{'=' * 70}")
        if approved:
            print("🎉 CREDIT LIMIT ENHANCED!")
            print(f"{'=' * 70}")
            print(message)
            print(
                f"\n💳 Your new available credit: Rs. {selected_card.available_credit():,.2f}"
            )
            self.bank.save()
        else:
            print("[FAIL] ENHANCEMENT DENIED")
            print(f"{'=' * 70}")
            print(message)

        print(f"{'=' * 70}")

    def apply_debit_card(self, account: Account):
        """Apply for a new debit card"""
        print("\n--- Apply for Debit Card ---")

        # Show existing debit cards (if any)
        existing_debit = [c for c in account.cards if isinstance(c, DebitCard)]
        if existing_debit:
            print(
                f"\nYou currently have {len(existing_debit)} debit card(s) linked to this account:"
            )
            for idx, card in enumerate(existing_debit, 1):
                status = (
                    "Blocked"
                    if card.blocked
                    else ("Expired" if card.is_expired() else "Active")
                )
                print(
                    f"  {idx}. {card.network} **** {card.card_number[-4:]} ({status})"
                )
            print()

        confirm = input("Apply for a new debit card? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Application cancelled")
            return

        # Ask user to select card network
        print("\nSelect Card Network:")
        print("1. VISA")
        print("2. Mastercard")
        print("3. RuPay (Indian domestic)")

        network_choice = self.read_valid_choice("Enter choice (1-3): ", ["1", "2", "3"])
        network_map = {"1": "VISA", "2": "MASTERCARD", "3": "RUPAY"}
        network = network_map[network_choice]

        debit_card = DebitCard(account.customer_id, account.account_number, network)
        account.add_card(debit_card)
        self.bank.save()
        print(f"\n[OK] {network} Debit card issued successfully!")
        print(
            f"Total debit cards: {len([c for c in account.cards if isinstance(c, DebitCard)])}"
        )

    def apply_credit_card(self, account: Account):
        """Apply for a new credit card"""
        from datetime import datetime

        print("\n--- Apply for Credit Card ---")

        # Show existing credit cards (if any)
        existing_credit = [c for c in account.cards if isinstance(c, CreditCard)]
        if existing_credit:
            print(
                f"\nYou currently have {len(existing_credit)} credit card(s) linked to this account:"
            )
            for idx, card in enumerate(existing_credit, 1):
                status = (
                    "Blocked"
                    if card.blocked
                    else ("Expired" if card.is_expired() else "Active")
                )
                print(
                    f"  {idx}. {card.network} **** {card.card_number[-4:]} - Limit: Rs. {card.credit_limit:,.0f} ({status})"
                )
            print()

        # Check eligibility
        if not account.salary_profile:
            print(
                "✗ Credit card requires a salary profile. Please set up salary first."
            )
            return

        # Get customer object
        customer = self.bank.get_customer_by_id(account.customer_id)
        if not customer:
            print("✗ Error: Customer information not found")
            return

        # Calculate age
        dob = datetime.strptime(account.dob, "%Y-%m-%d")
        age = (datetime.now() - dob).days // 365

        # Get CIBIL score
        cibil_score = calculate_cibil_score(customer, self.bank)
        annual_income = account.salary_profile.gross_salary * 12

        eligible, reason = CreditEvaluator.is_eligible_for_credit_card(
            cibil_score, annual_income, age
        )

        if not eligible:
            print(f"✗ Not eligible for credit card: {reason}")
            return

        print(f"[OK] {reason}")
        print(f"CIBIL Score: {cibil_score:.0f}")
        print(f"Annual Income: Rs. {annual_income:,.2f} INR")

        # Calculate credit limit
        credit_limit = CreditEvaluator.calculate_credit_limit(
            cibil_score=cibil_score,
            annual_income=annual_income,
            age=age,
            existing_debt=0.0,
            employer_category=getattr(customer, "employer_category", "pvt"),
            has_salary_account=True,
        )
        print(f"\nApproved Credit Limit: Rs. {credit_limit:,.2f} INR")

        confirm = (
            input("\nProceed with credit card application? (yes/no): ").strip().lower()
        )
        if confirm not in ["yes", "y"]:
            print("Application cancelled")
            return

        # Ask user to select card network
        print("\nSelect Card Network:")
        print("1. VISA")
        print("2. Mastercard")
        print("3. RuPay (Indian domestic)")

        network_choice = self.read_valid_choice("Enter choice (1-3): ", ["1", "2", "3"])
        network_map = {"1": "VISA", "2": "MASTERCARD", "3": "RUPAY"}
        network = network_map[network_choice]

        # Get billing day preference
        while True:
            billing_day = input("\nPreferred billing day (1-28): ").strip()
            try:
                billing_day = int(billing_day)
                if 1 <= billing_day <= 28:
                    break
                else:
                    print("Billing day must be between 1 and 28")
            except ValueError:
                print("Invalid input")

        credit_card = CreditCard(
            account.customer_id,
            account.account_number,
            credit_limit,
            billing_day,
            network,
        )
        account.add_card(credit_card)
        self.bank.save()
        print(f"\n[OK] {network} Credit card issued successfully!")
        print(f"Billing Day: {billing_day} of each month")
        print(
            f"Total credit cards: {len([c for c in account.cards if isinstance(c, CreditCard)])}"
        )

        # Ask about auto-pay policy
        print("\n" + "=" * 60)
        print("AUTO-PAY POLICY CONFIGURATION")
        print("=" * 60)
        print("Set how your credit card bill should be paid automatically:")
        print("1. NONE - Manual payment only (default)")
        print("2. MINIMUM - Auto-pay minimum due amount")
        print("3. FULL - Auto-pay full outstanding balance")
        print("=" * 60)

        policy_choice = self.read_valid_choice(
            "Select auto-pay policy (1-3): ", ["1", "2", "3"]
        )
        policy_map = {"1": "NONE", "2": "MINIMUM", "3": "FULL"}
        auto_pay_policy = policy_map[policy_choice]
        credit_card.auto_pay_policy = auto_pay_policy
        self.bank.save()

        if auto_pay_policy == "NONE":
            print("\n[OK] Auto-pay disabled. You'll pay manually each month.")
        elif auto_pay_policy == "MINIMUM":
            print(
                "\n[OK] Auto-pay enabled: Minimum due will be paid automatically from your account."
            )
        else:
            print(
                "\n[OK] Auto-pay enabled: Full outstanding balance will be paid automatically from your account."
            )

    def make_card_purchase(self, account: Account):
        """Make a purchase using a card"""
        if not account.cards:
            print("No cards available")
            return

        print("\n--- Make Card Purchase ---")
        account.list_cards()

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card:
            print("Card not found")
            return

        try:
            amount = float(input("Enter amount: ").strip())
            merchant = input("Merchant name: ").strip()
            category = (
                input(
                    "Category (Shopping/Dining/Travel/Entertainment/Bills/Other): "
                ).strip()
                or "Shopping"
            )

            account.make_card_purchase(card.card_id, amount, merchant, category)
            self.bank.save()

        except ValueError:
            print("Invalid amount")

    def pay_credit_card(self, account: Account):
        """Pay credit card bill with option to use reward points"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("No credit cards available")
            return

        print("\n--- Pay Credit Card Bill ---")

        for card in credit_cards:
            print(f"\nCard: **** **** **** {card.card_number[-4:]}")
            print(f"Outstanding: Rs. {card.credit_used:,.2f} INR")
            print(
                f"💎 Reward Points: {card.reward_points:.0f} (Value: Rs. {RewardPointsManager.calculate_points_value(card.reward_points):.2f})"
            )
            if card.outstanding_balance > 0:
                print(f"Bill Amount: Rs. {card.outstanding_balance:,.2f} INR")
                print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card or not isinstance(card, CreditCard):
            print("Credit card not found")
            return

        outstanding = card.credit_used if card.credit_used > 0 else 0

        if outstanding == 0:
            print("\n[SUCCESS] No outstanding balance!")
            return

        print(f"\n{'=' * 70}")
        print("PAYMENT OPTIONS")
        print(f"{'=' * 70}")
        print(f"Account Balance: Rs. {account.balance:,.2f} INR")
        print(f"Outstanding: Rs. {outstanding:,.2f} INR")
        print(
            f"💎 Reward Points: {card.reward_points:.0f} (Rs. {RewardPointsManager.calculate_points_value(card.reward_points):.2f})"
        )
        print(f"{'=' * 70}")

        # Check if rewards can be used
        can_use_rewards = (
            card.reward_points >= RewardPointsManager.MIN_REDEMPTION_POINTS
        )

        # Ask about reward points
        reward_points_to_use = 0
        if can_use_rewards:
            use_rewards = (
                input("\nUse reward points for payment? (yes/no): ").strip().lower()
            )

            if use_rewards in ["yes", "y"]:
                redemption_options = RewardPointsManager.get_redemption_options(
                    card, outstanding
                )

                print("\n💎 REWARD POINTS REDEMPTION")
                print(f"{'=' * 70}")
                print(f"Available: {redemption_options['available_points']:.0f} points")
                print(
                    f"Max Redeemable: {redemption_options['max_redeemable_points']:.0f} points (Rs. {redemption_options['max_redeemable_value']:.2f})"
                )
                print(f"Rate: 1 point = Rs. {RewardPointsManager.REDEMPTION_RATE}")

                # Show preset options if available
                if "presets" in redemption_options and redemption_options["presets"]:
                    print("\n🎯 QUICK OPTIONS:")
                    for idx, preset in enumerate(redemption_options["presets"], 1):
                        print(
                            f"  {idx}. {preset['label']}: {preset['points']:.0f} points → Rs. {preset['value']:.2f}"
                        )
                    print(f"  {len(redemption_options['presets']) + 1}. Custom amount")
                    print("  0. Skip (pay cash only)")

                    choice = input("\nSelect: ").strip()

                    try:
                        choice_num = int(choice)
                        if choice_num == 0:
                            reward_points_to_use = 0
                        elif 1 <= choice_num <= len(redemption_options["presets"]):
                            reward_points_to_use = redemption_options["presets"][
                                choice_num - 1
                            ]["points"]
                        elif choice_num == len(redemption_options["presets"]) + 1:
                            reward_points_to_use = float(
                                input(
                                    f"Enter points ({RewardPointsManager.MIN_REDEMPTION_POINTS}-{redemption_options['max_redeemable_points']:.0f}): "
                                )
                            )
                        else:
                            print("[FAIL] Invalid option")
                            return
                    except ValueError:
                        print("[FAIL] Invalid input")
                        return
                else:
                    try:
                        reward_points_to_use = float(
                            input(
                                f"Enter points to redeem (100-{redemption_options['max_redeemable_points']:.0f}): "
                            )
                        )
                    except ValueError:
                        print("[FAIL] Invalid input")
                        return

        # Calculate amounts
        reward_value = 0
        remaining_balance = outstanding

        if reward_points_to_use > 0:
            # Validate redemption
            can_redeem, reason = RewardPointsManager.can_redeem(
                card, reward_points_to_use
            )
            if not can_redeem:
                print(f"\n[FAIL] {reason}")
                return

            reward_value = RewardPointsManager.calculate_points_value(
                reward_points_to_use
            )
            remaining_balance = outstanding - reward_value

            print(
                f"\n💎 Redeeming: {reward_points_to_use:.0f} points → Rs. {reward_value:.2f}"
            )
            print(f"[MONEY] Remaining to pay: Rs. {remaining_balance:.2f}")

        # Get cash amount
        cash_amount = 0
        if remaining_balance > 0:
            print(f"\nAccount Balance: Rs. {account.balance:,.2f} INR")

            try:
                cash_input = input(
                    f"Enter cash amount to pay (0-{remaining_balance:.2f}): Rs. "
                ).strip()
                cash_amount = float(cash_input) if cash_input else 0

                if cash_amount < 0 or cash_amount > remaining_balance:
                    print("[FAIL] Invalid amount")
                    return
            except ValueError:
                print("[FAIL] Invalid amount")
                return

        # Validate total payment
        total_payment = cash_amount + reward_value
        if total_payment == 0:
            print("[FAIL] No payment amount entered")
            return

        # Process payment
        print(f"\n{'=' * 70}")
        print("PROCESSING PAYMENT...")
        print(f"{'=' * 70}")

        try:
            # Use the combined payment method
            success, message, txn_id = card.pay_bill_with_rewards(
                cash_amount, reward_points_to_use, account
            )

            if success:
                print("\n[SUCCESS] PAYMENT SUCCESSFUL!")
                print(f"{'=' * 70}")

                # Show breakdown
                if cash_amount > 0:
                    print(f"💵 Cash:           Rs. {cash_amount:>12,.2f}")
                if reward_value > 0:
                    print(
                        f"💎 Rewards:        Rs. {reward_value:>12,.2f} ({reward_points_to_use:.0f} pts)"
                    )
                print(f"{'─' * 70}")
                print(f"[STATS] Total:          Rs. {total_payment:>12,.2f}")
                print(f"{'=' * 70}")
                print(f"💳 New Balance:    Rs. {card.credit_used:>12,.2f}")
                print(f"💎 Remaining Pts:  {card.reward_points:>15,.0f}")
                print(f"{'=' * 70}")

                self.bank.save()
            else:
                print(f"\n[FAIL] Payment failed: {message}")

        except Exception as e:
            print(f"\n[FAIL] Error: {e}")

    def view_credit_statement(self, account: Account):
        """View credit card statement"""
        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("No credit cards available")
            return

        if len(credit_cards) == 1:
            account.show_credit_card_statement(credit_cards[0].card_id)
        else:
            print("\n--- Select Credit Card ---")
            for i, card in enumerate(credit_cards, 1):
                print(f"{i}. **** **** **** {card.card_number[-4:]}")

            try:
                choice = int(input("Enter choice: ").strip())
                if 1 <= choice <= len(credit_cards):
                    account.show_credit_card_statement(credit_cards[choice - 1].card_id)
                else:
                    print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def block_card(self, account: Account):
        """Block a card"""
        if not account.cards:
            print("No cards available")
            return

        account.list_cards()
        card_id = input("\nEnter Card ID to block: ").strip()
        account.block_card(card_id)
        self.bank.save()

    def unblock_card(self, account: Account):
        """Unblock a card"""
        if not account.cards:
            print("No cards available")
            return

        account.list_cards()
        card_id = input("\nEnter Card ID to unblock: ").strip()
        account.unblock_card(card_id)
        self.bank.save()

    def set_card_pin(self, account: Account):
        """Set or change the PIN for a card"""
        if not account.cards:
            print("\n[FAIL] No cards found for this account.")
            return

        print("\n" + "=" * 50)
        print("SET/CHANGE CARD PIN")
        print("=" * 50)
        
        # List all cards
        account.list_cards()
        
        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)
        
        if not card:
            print("[FAIL] Card not found.")
            return
            
        print(f"\nSetting PIN for: {card.network} **** **** **** {card.card_number[-4:]}")
        
        new_pin = input("Enter new 4-digit PIN: ").strip()
        if not new_pin.isdigit() or len(new_pin) != 4:
            print("[FAIL] Invalid PIN. Must be exactly 4 digits.")
            return
            
        confirm_pin = input("Confirm new 4-digit PIN: ").strip()
        if new_pin != confirm_pin:
            print("[FAIL] PINs do not match.")
            return
            
        if card.set_pin(new_pin):
            print(f"\n[SUCCESS] PIN set successfully for card ending in {card.card_number[-4:]}!")
            self.bank.save()
        else:
            print("[FAIL] Failed to set PIN.")

    # ========== LOAN MENU AND OPERATIONS ==========

    def loan_menu(self, customer: Customer, account: Account):
        # Check for loans that might need type update (large loans likely to be home loans)
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        # Consider loans over 10 lakhs as potentially home loans
        loans_needing_type = [
            loan
            for loan in loans
            if getattr(loan, "loan_type", "PERSONAL") == "PERSONAL"
            and loan.status == "Active"
            and loan.principal >= 1000000  # 10 lakhs or more
        ]

        if loans_needing_type:
            print("\n" + "[WARN]" * 30)
            print("[WARN]  IMPORTANT: LOAN TYPE UPDATE RECOMMENDED")
            print("[WARN]" * 30)
            print(
                f"\n[INFO] You have {len(loans_needing_type)} large loan(s) (₹10L+) marked as PERSONAL."
            )
            print("   If any of these are HOME loans, you can claim tax benefits:")
            print("   • HOME loans: Up to ₹2,00,000 interest deduction (Section 24)")

            for loan in loans_needing_type:
                emi = loan.calculate_emi()
                print(
                    f"\n   • Loan {loan.loan_id}: ₹{loan.principal:,.2f} | EMI: ₹{emi:,.2f}/month"
                )

            print(
                "\n💡 Tip: Use option 7 (Update Loan Type) to classify your loans correctly."
            )
            input("\nPress Enter to continue...")

        while True:
            print("""
9  Update Loan Type (for tax deductions)
10 Download Loan Statement of Account (PDF)
11 Back to Account Menu
            """)
            choice = self.read_valid_choice(
                "Enter choice: ", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
            )
            if choice == "1":
                self.apply_for_loan(customer, account)
            elif choice == "2":
                self.bank.show_loans_for_customer(customer.customer_id)
            elif choice == "3":
                self.pay_loan_emi_flow(customer, account)
            elif choice == "4":
                self.view_cibil_report(customer)
            elif choice == "5":
                self.prepay_loan_early(customer, account)
            elif choice == "6":
                self.generate_loan_closure_certificate(customer, account)
            elif choice == "7":
                self.loan_nach_mandate_menu(customer, account)
            elif choice == "8":
                self.update_loan_type(customer, account)
            elif choice == "9":
                break
            elif choice == "10":
                self.download_loan_statement(customer, account)
            elif choice == "11":
                break

    def update_loan_type(self, customer: Customer, account: Account):
        """Update the loan type for existing loans to enable proper tax deductions"""
        print("\n" + "=" * 60)
        print("UPDATE LOAN TYPE FOR TAX DEDUCTIONS")
        print("=" * 60)
        print("""
ℹ️  Loan types are important for tax deductions:
   • HOME loans: Interest deduction up to ₹2,00,000 (Section 24)
   • PERSONAL loans: No tax benefit
   • CAR loans: No direct tax benefit (business use may qualify)
   • EDUCATION loans: Interest deduction (Section 80E)
        """)

        # Get all loans for customer
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("[FAIL] You have no loans on record.")
            input("\nPress Enter to continue...")
            return

        # Show all loans with their current types
        print("\n[INFO] YOUR LOANS:")
        print("=" * 60)
        for idx, loan in enumerate(loans, 1):
            loan_type = getattr(loan, "loan_type", "PERSONAL")
            emi = loan.calculate_emi()
            remaining = (
                loan.get_remaining_balance()
                if hasattr(loan, "get_remaining_balance")
                else loan.principal
            )

            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Type: {loan_type}")
            print(f"   Principal: ₹{loan.principal:,.2f}")
            print(f"   Remaining Balance: ₹{remaining:,.2f}")
            print(f"   EMI: ₹{emi:,.2f}/month")
            print(f"   Status: {loan.status}")
            print(f"   EMIs Paid: {loan.emis_paid}/{loan.tenure_months}")

        print("\n" + "=" * 60)

        # Select loan to update
        loan_choices = [str(i) for i in range(1, len(loans) + 1)]
        loan_choices.append("0")  # Option to cancel

        choice = self.read_valid_choice(
            f"\nSelect loan to update (1-{len(loans)}, 0 to cancel): ", loan_choices
        )

        if choice == "0":
            print("Cancelled.")
            return

        selected_loan = loans[int(choice) - 1]
        current_type = getattr(selected_loan, "loan_type", "PERSONAL")

        print(
            f"\n📌 Selected: Loan {selected_loan.loan_id} (Current Type: {current_type})"
        )
        print("\nSelect New Loan Type:")
        print("1. PERSONAL - Personal loans (no tax benefit)")
        print("2. HOME - Housing/Home loans (₹2L interest deduction)")
        print("3. CAR - Vehicle loans (no direct tax benefit)")
        print("4. EDUCATION - Education loans (interest deduction, no limit)")

        type_choice = self.read_valid_choice(
            "\nEnter choice (1-4): ", ["1", "2", "3", "4"]
        )

        loan_type_map = {"1": "PERSONAL", "2": "HOME", "3": "CAR", "4": "EDUCATION"}

        new_type = loan_type_map[type_choice]

        # Update the loan type
        selected_loan.loan_type = new_type

        # Save changes
        self.bank.save()

        print("\n" + "=" * 60)
        print("[SUCCESS] LOAN TYPE UPDATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Previous Type: {current_type}")
        print(f"New Type: {new_type}")

        if new_type == "HOME":
            remaining = (
                selected_loan.get_remaining_balance()
                if hasattr(selected_loan, "get_remaining_balance")
                else selected_loan.principal
            )
            monthly_rate = selected_loan.interest_rate / 100 / 12
            monthly_interest = remaining * monthly_rate
            annual_interest = monthly_interest * 12
            deduction = min(annual_interest, 200000)

            print("\n[MONEY] TAX BENEFIT ESTIMATE (Section 24):")
            print(f"   Annual Interest: ₹{annual_interest:,.2f}")
            print(f"   Deduction Eligible: ₹{deduction:,.2f}")
            print(f"   Tax Savings (30% bracket): ₹{deduction * 0.30:,.2f}/year")

        print("\nℹ️  Tax deductions will now be automatically detected in the")
        print("   Tax Planning & Exemptions menu.")

        input("\nPress Enter to continue...")

    def apply_for_loan(self, customer: Customer, account: Account):
        print("\n=== Loan Application ===")

        # Get salary from account's salary profile if available
        if account.salary_profile:
            customer.salary = account.salary_profile.gross_salary
            print(f"[OK] Salary Profile Found: Rs {customer.salary:,.2f}/month")
        else:
            customer.salary = self.read_positive_double(
                "Enter your Net Monthly Salary: "
            )

        if not getattr(customer, "employer_name", None):
            customer.employer_name = input("Enter your Employer Name: ").strip()
        if not getattr(customer, "employer_type", None):
            customer.employer_type = input("Type of Employer [MNC/Govt/Pvt]: ").strip()
        if not getattr(customer, "job_start_date", None):
            customer.job_start_date = self.read_date("Job Start Date (YYYY-MM-DD): ")
        if not getattr(customer, "employer_category", None):
            customer.employer_category = (
                input("Employer Category (A/B/C): ").strip().upper()
            )
        if not getattr(customer, "city", None):
            customer.city = input("Working City: ").strip()
        if not getattr(customer, "kyc_completed", None):
            completed = input("Is your KYC complete? (y/n): ").strip().lower()
            customer.kyc_completed = completed == "y"

        # Register hard inquiry for this loan application
        add_credit_inquiry(customer)

        # Automatically calculate CIBIL score based on customer's credit history
        print("\n[SEARCH] Calculating your CIBIL score based on credit history...")
        customer.cibil_score = calculate_cibil_score(customer, self.bank)

        # Determine rating for display
        if customer.cibil_score >= 750:
            rating = "Excellent ⭐⭐⭐⭐⭐"
        elif customer.cibil_score >= 650:
            rating = "Good ⭐⭐⭐⭐"
        elif customer.cibil_score >= 550:
            rating = "Average ⭐⭐⭐"
        else:
            rating = "Poor ⭐⭐"

        print(f"[OK] Your current CIBIL Score: {customer.cibil_score} ({rating})")

        # Ask for loan type
        print("\nSelect Loan Type:")
        print("1. Personal Loan")
        print("2. Home Loan")
        print("3. Car Loan")
        print("4. Education Loan")
        loan_type_choice = self.read_valid_choice(
            "Enter choice (1-4): ", ["1", "2", "3", "4"]
        )
        loan_type_map = {"1": "PERSONAL", "2": "HOME", "3": "CAR", "4": "EDUCATION"}
        loan_type = loan_type_map[loan_type_choice]
        print(f"[OK] Loan Type: {loan_type}")

        principal = self.read_positive_double("\nEnter principal amount (Rs): ")
        interest_rate = self.read_positive_double("Enter annual interest rate (%): ")
        tenure_months = int(self.read_positive_double("Enter tenure (months): "))

        approved, loan, msg = self.bank.evaluate_and_add_loan(
            customer, principal, interest_rate, tenure_months, account, loan_type
        )
        if approved:
            print(
                f"\n✔ Loan approved! Amount Rs.{principal:,.2f} credited to your account."
            )
            print(f"Loan ID: {loan.loan_id} | EMI: Rs.{loan.calculate_emi():.2f}/month")
            print(f"Interest Rate: {loan.interest_rate:.2f}% p.a.")
        else:
            print(f"\n[FAIL] Loan denied: {msg}")

    def pay_loan_emi_flow(self, customer: Customer, account: Account):
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("You have no loans to pay.")
            return
        print("\nYour Loans:")
        for idx, loan in enumerate(loans, 1):
            outstanding = max(0, loan.tenure_months - getattr(loan, "emis_paid", 0))
            print(
                f"{idx}. {loan.loan_id} | Status: {loan.status} | Outstanding EMIs: {outstanding}"
            )
        choice = self.read_valid_choice(
            "Select loan number to pay EMI for: ",
            [str(i) for i in range(1, len(loans) + 1)],
        )
        selected_loan = loans[int(choice) - 1]
        outstanding_emis = max(
            0, selected_loan.tenure_months - getattr(selected_loan, "emis_paid", 0)
        )
        if outstanding_emis <= 0:
            print("All EMIs for this loan have already been paid.")
            return
        if outstanding_emis == 1:
            count = 1
        else:
            while True:
                try:
                    count = int(
                        input(
                            f"How many EMIs would you like to pay now? (1-{outstanding_emis}): "
                        )
                    )
                    if 1 <= count <= outstanding_emis:
                        break
                    else:
                        print(
                            f"Please enter a number between 1 and {outstanding_emis}."
                        )
                except ValueError:
                    print("Please enter a valid number.")
        self.bank.pay_multiple_emis_for_loan(
            selected_loan.loan_id, account.account_number, count
        )
        print(f"\nSuccessfully paid {count} EMI(s) for loan {selected_loan.loan_id}.")

    def prepay_loan_early(self, customer: Customer, account: Account):
        """Prepay loan early and close it (with prepayment penalty)"""
        
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        active_loans = [loan for loan in loans if loan.status == "Active"]
        
        if not active_loans:
            print("[FAIL] You have no active loans to prepay.")
            return
        
        print("\n" + "=" * 70)
        print("LOAN PREPAYMENT (EARLY CLOSURE)")
        print("=" * 70)
        print("\n[INFO] YOUR ACTIVE LOANS:")
        
        for idx, loan in enumerate(active_loans, 1):
            remaining = loan.get_remaining_balance()
            emi = loan.calculate_emi()
            outstanding_emis = loan.tenure_months - loan.emis_paid
            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Type: {loan.loan_type} | Status: {loan.status}")
            print(f"   Principal: ₹{loan.principal:,.2f} | Rate: {loan.interest_rate}% p.a.")
            print(f"   EMI: ₹{emi:,.2f}/month | Paid: {loan.emis_paid}/{loan.tenure_months}")
            print(f"   Remaining Balance: ₹{remaining:,.2f}")
        
        choice = self.read_valid_choice(
            f"\nSelect loan to prepay (1-{len(active_loans)}): ",
            [str(i) for i in range(1, len(active_loans) + 1)],
        )
        selected_loan = active_loans[int(choice) - 1]
        
        # Get closure details
        closure_details = selected_loan.get_closure_details()
        
        print("\n" + "=" * 70)
        print("PREPAYMENT CALCULATION")
        print("=" * 70)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Loan Type: {selected_loan.loan_type}")
        print(f"EMIs Paid: {selected_loan.emis_paid}/{selected_loan.tenure_months}")
        print(f"\nOutstanding Principal: ₹{closure_details['remaining_balance']:,.2f}")
        print(f"Prepayment Penalty Rate: {closure_details['penalty_rate']}%")
        print(f"Prepayment Penalty: ₹{closure_details['penalty_amount']:,.2f}")
        print("-" * 70)
        print(f"TOTAL AMOUNT DUE: ₹{closure_details['total_payment']:,.2f}")
        print("=" * 70)
        
        if closure_details['penalty_amount'] == 0:
            print(f"\n[SUCCESS] Good news! No prepayment penalty for {selected_loan.loan_type} loans.")
        else:
            print(f"\n[WARN]  Note: Prepayment penalty of ₹{closure_details['penalty_amount']:,.2f} will be charged.")
        
        # Confirmation
        confirm = input("\nProceed with loan closure? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] Loan prepayment cancelled.")
            return
        
        # Check account balance
        min_balance = account._min_operational_balance
        required_amount = closure_details['total_payment']
        
        if account.balance - required_amount < min_balance:
            print(f"\n[FAIL] Insufficient balance!")
            print(f"   Required: ₹{required_amount:,.2f}")
            print(f"   Available: ₹{account.balance - min_balance:,.2f}")
            print(f"   (Must maintain minimum balance of ₹{min_balance:,.2f})")
            return
        
        # Process prepayment
        account.balance -= required_amount
        selected_loan.status = "Closed"
        selected_loan.closure_date = BankClock.today()
        selected_loan.prepayment_penalty_charged = closure_details['penalty_amount']
        
        # Log main payment transaction
        main_txn = Transaction(
            type="LOAN_PREPAYMENT",
            amount=closure_details['remaining_balance'],
            resulting_balance=account.balance,
            metadata={"loanId": selected_loan.loan_id, "loanType": selected_loan.loan_type},
        )
        account.transactions.append(main_txn)
        
        # Log penalty transaction separately
        if closure_details['penalty_amount'] > 0:
            penalty_txn = Transaction(
                type="LOAN_PREPAYMENT_PENALTY",
                amount=closure_details['penalty_amount'],
                resulting_balance=account.balance,
                metadata={
                    "loanId": selected_loan.loan_id,
                    "loanType": selected_loan.loan_type,
                    "penaltyRate": closure_details['penalty_rate'],
                },
            )
            account.transactions.append(penalty_txn)
        
        # Log to activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="LOAN_PREPAYMENT",
            amount=required_amount,
            resulting_balance=account.balance,
            txn_id=main_txn.id,
            metadata=f"loanId={selected_loan.loan_id};principal={closure_details['remaining_balance']:.2f};penalty={closure_details['penalty_amount']:.2f}",
        )
        
        self.bank.save()
        
        # Display confirmation
        print("\n" + "=" * 70)
        print("[SUCCESS] LOAN PREPAYMENT SUCCESSFUL")
        print("=" * 70)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Status: CLOSED")
        print(f"\nPayment Breakdown:")
        print(f"  Principal Outstanding: ₹{closure_details['remaining_balance']:,.2f}")
        print(f"  Prepayment Penalty: ₹{closure_details['penalty_amount']:,.2f}")
        print(f"  Total Deducted: ₹{required_amount:,.2f}")
        print(f"\nNew Account Balance: ₹{account.balance:,.2f}")
        print("=" * 70)
        print("\n📄 You can view your Loan Closure Certificate from Loan Menu option 6.")

    # ========== ORIGINAL BANKING METHODS CONTINUE BELOW ===========

    def view_balance(self, account: Account):
        """Display account balance and details"""
        print(f"""
Account Details:
----------------
{BankClock.get_login_banner()}

Name: {account.first_name} {account.last_name}
Account Type: {account.account_type}
Account Number: {account.account_number}
{Account.get_branch_details()}

Current Balance: Rs. {account.balance:.2f} INR
        """)

    # In BankingApp.py, replace deposit_money() and withdraw_money():

    def deposit_money(self, account: Account):
        """Handle deposit transaction - requires debit card"""
        # Check if account has debit cards
        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n[FAIL] No debit card found. You need a debit card to deposit money.")
            print("Please apply for a debit card first from Card Management menu.")
            return

        # Show available debit cards
        print("\n--- Select Debit Card for Deposit ---")
        for idx, card in enumerate(debit_cards, 1):
            status = (
                "Blocked"
                if card.blocked
                else ("Expired" if card.is_expired() else "Active")
            )
            print(
                f"{idx}. {card.network} **** **** **** {card.card_number[-4:]} ({status})"
            )

        # Card selection
        if len(debit_cards) == 1:
            selected_card = debit_cards[0]
            print(
                f"Using: {selected_card.network} **** **** **** {selected_card.card_number[-4:]}"
            )
        else:
            choice = self.read_valid_choice(
                f"Select card (1-{len(debit_cards)}): ",
                [str(i) for i in range(1, len(debit_cards) + 1)],
            )
            selected_card = debit_cards[int(choice) - 1]

        amount = self.read_positive_double("\nEnter amount to deposit: Rs. ")
        
        # PIN Prompt
        pin = input("Enter 4-digit Card PIN: ").strip()
        
        account.deposit(amount, card=selected_card, pin=pin)
        self.bank.save()

    def withdraw_money(self, account: Account):
        """Handle withdrawal transaction - requires debit card"""
        # Check if account has debit cards
        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n[FAIL] No debit card found. You need a debit card to withdraw money.")
            print("Please apply for a debit card first from Card Management menu.")
            return

        # Show available debit cards
        print("\n--- Select Debit Card for Withdrawal ---")
        for idx, card in enumerate(debit_cards, 1):
            status = (
                "Blocked"
                if card.blocked
                else ("Expired" if card.is_expired() else "Active")
            )
            print(
                f"{idx}. {card.network} **** **** **** {card.card_number[-4:]} ({status})"
            )

        # Card selection
        if len(debit_cards) == 1:
            selected_card = debit_cards[0]
            print(
                f"Using: {selected_card.network} **** **** **** {selected_card.card_number[-4:]}"
            )
        else:
            choice = self.read_valid_choice(
                f"Select card (1-{len(debit_cards)}): ",
                [str(i) for i in range(1, len(debit_cards) + 1)],
            )
            selected_card = debit_cards[int(choice) - 1]

        amount = self.read_positive_double("\nEnter amount to withdraw: Rs. ")
        
        # PIN Prompt
        pin = input("Enter 4-digit Card PIN: ").strip()
        
        account.withdraw(amount, card=selected_card, pin=pin)
        self.bank.save()

    def transfer_funds(self, customer: Customer, account: Account, accounts: List[Account]):
        """Handle fund transfer (Inter-Account, NEFT, RTGS, International)"""
        if len(accounts) > 1:
            print("""
    Choose transfer type:
    1  Inter-Account (Between your own accounts)
    2  NEFT (Up to Rs. 1,99,999.99)
    3  RTGS (From Rs. 2,00,000.00)
    4  International Transfer (SWIFT/Wire)
                """)
            transfer_choice = self.read_valid_choice(
                "Enter choice (1-4): ", ["1", "2", "3", "4"]
            )

            if transfer_choice == "1":
                self.inter_account_transfer(account, accounts)
            elif transfer_choice == "2":
                self.external_transfer(customer, account, "NEFT")
            elif transfer_choice == "3":
                self.external_transfer(customer, account, "RTGS")
            elif transfer_choice == "4":
                self.international_transfer(account)  # NEW
        else:
            print("""
Choose transfer mode:
1  NEFT (Up to Rs. 1,99,999.99)
2  RTGS (From Rs. 2,00,000.00)
3  International Transfer (SWIFT/Wire)
            """)
            transfer_choice = self.read_valid_choice(
                "Enter choice (1-3): ", ["1", "2", "3"]
            )

            if transfer_choice == "1":
                self.external_transfer(customer, account, "NEFT")
            elif transfer_choice == "2":
                self.external_transfer(customer, account, "RTGS")
            elif transfer_choice == "3":
                self.international_transfer(account)  # NEW

    def inter_account_transfer(self, account: Account, accounts: List[Account]):
        """Handle inter-account transfer"""
        print("\nYour other accounts:")
        other_accounts = [acc for acc in accounts if acc != account]

        for idx, acc in enumerate(other_accounts, 1):
            print(
                f"{idx}. {acc.account_type} - {acc.account_number} (Balance: Rs. {acc.balance:.2f} INR)"
            )

        choice = self.read_valid_choice(
            f"Select recipient account (1-{len(other_accounts)}): ",
            [str(i) for i in range(1, len(other_accounts) + 1)],
        )
        recipient = other_accounts[int(choice) - 1]
        amount = self.read_positive_double("Enter amount to transfer: Rs. ")
        account.transfer(recipient, amount, "INTER_ACCOUNT")
        self.bank.save()

    def external_transfer(self, customer: Customer, account: Account, mode: str):
        """Handle external transfer (NEFT/RTGS)"""
        beneficiaries = customer.beneficiary_manager.list_all()
        
        print("\n" + "=" * 50)
        print(f"EXTERNAL TRANSFER ({mode})")
        print("=" * 50)
        
        if beneficiaries:
            print("\n1. Transfer to Saved Beneficiary")
            print("2. Transfer to New Account")
            choice = input("Enter choice (1-2) [default: 1]: ").strip() or "1"
        else:
            print("\n[INFO] No saved beneficiaries found. Proceeding with manual entry.")
            choice = "2"
            
        if choice == "1":
            print("\n--- Saved Beneficiaries ---")
            recent = customer.beneficiary_manager.get_recent(3)
            frequent = customer.beneficiary_manager.get_frequent(3)
            
            # Print recent/frequent suggestions if available
            if recent:
                print("\nRecently Used:")
                for b in recent:
                    print(f"  - {b.beneficiary_name} ({b.account_number})")
                    
            print("\nAll Beneficiaries:")
            for idx, b in enumerate(beneficiaries, 1):
                print(f"{idx}. {b.beneficiary_name} - {b.account_number} ({b.bank_name})")
                
            idx_choice = input("\nSelect beneficiary number (or 0 to cancel): ").strip()
            if idx_choice.isdigit() and 1 <= int(idx_choice) <= len(beneficiaries):
                b = beneficiaries[int(idx_choice) - 1]
                amount = self.read_positive_double(f"Enter amount to transfer to {b.beneficiary_name}: Rs. ")
                success = account.pay_to_beneficiary(b.beneficiary_id, amount, mode, customer.beneficiary_manager)
                if success:
                    self.bank.save()
            return
            
        # Proceed with manual entry (Choice 2)
        while True:
            recipient_acc_num = input("\nEnter recipient's account number: ").strip()
            if not recipient_acc_num:
                print("Account number cannot be empty. Please try again.")
                continue

            recipient = self.bank.find_account_by_number(recipient_acc_num)
            if recipient:
                if recipient.account_number == account.account_number:
                    print("Cannot transfer to your own account. Please enter a different account number.")
                    continue
                print(f"Recipient Name: {recipient.first_name} {recipient.last_name} (Internal Account)")
                amount = self.read_positive_double("Enter amount to transfer: Rs. ")
                account.transfer(recipient, amount, mode)
                self.bank.save()
                break
            else:
                if not recipient_acc_num.isdigit() or not (9 <= len(recipient_acc_num) <= 18):
                    print("[ERROR] External account numbers must be numeric and between 9 and 18 digits. Please try again.")
                    continue
                    
                print("\n[EXTERNAL ACCOUNT DETECTED]")
                recipient_name = input("Enter recipient's name: ").strip()
                
                from .Beneficiary import IFSCValidator
                bank_name = ""
                ifsc = ""
                while True:
                    ifsc = input("Enter recipient's IFSC Code (MANDATORY): ").strip().upper()
                    if not ifsc:
                        print("[ERROR] IFSC code is mandatory for external transfers.")
                        continue
                    
                    if not IFSCValidator.validate_format(ifsc):
                        print("Invalid IFSC format. Expected 4 letters, '0', 6 alphanumeric characters.")
                        continue
                        
                    print(f"Validating IFSC Code '{ifsc}' via Razorpay API...")
                    bank_details = IFSCValidator.get_bank_details(ifsc)
                    
                    if bank_details:
                        bank_name = bank_details['bank_name']
                        branch = bank_details.get('branch', '')
                        swift = bank_details.get('swift', '')
                        if swift:
                            print(f"[OK] Bank Found: {bank_name}, {branch} (SWIFT: {swift})")
                        else:
                            print(f"[OK] Bank Found: {bank_name}, {branch}")
                        break

                    else:
                        print("[WARN] Could not validate IFSC via API.")
                        bank_name = input("Enter recipient's bank name manually: ").strip()
                        if not bank_name:
                            print("[ERROR] Bank name is required if IFSC validation fails.")
                            continue
                        break
                
                amount = self.read_positive_double("Enter amount to transfer: Rs. ")
                
                # Check minor account limits
                if account.is_minor_account:
                    today_transactions = account.get_today_transactions()
                    if today_transactions + amount > account._minor_daily_transaction_limit:
                        remaining = account._minor_daily_transaction_limit - today_transactions
                        print("Transfer amount exceeds daily transaction limit for minor accounts.")
                        print(f"Remaining limit: Rs. {remaining:.2f} INR")
                        continue
                
                # Check operational balance
                if account.balance - amount < account._min_operational_balance:
                    print(f"Insufficient funds. Must keep at least Rs. {account._min_operational_balance:.2f} INR.")
                    continue
                
                import random
                from .Transaction import Transaction
                from .DataStore import DataStore
                
                account.balance -= amount
                cheque_id = f"CHQ{random.randint(1000000000, 9999999999)}"
                
                txn = Transaction(
                    type=f"{mode}_SENT",
                    amount=amount,
                    resulting_balance=account.balance,
                    cheque_id=cheque_id,
                )
                account.transactions.append(txn)
                
                metadata = f"requestedMode={mode};recipientName={recipient_name};recipientAccount={recipient_acc_num};recipientBank={bank_name}"
                if account.is_minor_account:
                    metadata += ";minorAccount=true"
                    
                DataStore.append_activity(
                    timestamp=txn.timestamp,
                    username=account.username,
                    account_number=account.account_number,
                    action=f"{mode}_SENT_EXTERNAL",
                    amount=amount,
                    resulting_balance=account.balance,
                    txn_id=txn.id,
                    cheque_id=cheque_id,
                    metadata=metadata,
                )
                
                print(f"{mode} payment to {recipient_name} at {bank_name} successful.")
                print(f"Sent: Rs. {amount:.2f} INR | Transaction ID: {txn.id}")
                print(f"Cheque ID: {cheque_id}")
                
                account._check_and_apply_amb_fee()
                self.bank.save()
                
                # Generate receipt for external transfer
                self._generate_transfer_receipt(
                    account, recipient_name, recipient_acc_num, bank_name, ifsc, amount, mode, txn.id
                )
                break


    def _generate_transfer_receipt(
        self, sender_acc, recipient_name, recipient_acc, bank_name, ifsc, amount, mode, txn_id
    ):
        """Generates both text and PDF receipts for the external transfer"""
        import os
        from datetime import datetime
        
        # Ensure data directory exists for receipts
        receipt_dir = os.path.join(os.getcwd(), "receipts")
        if not os.path.exists(receipt_dir):
            os.makedirs(receipt_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"Receipt_{txn_id}_{timestamp}"
        
        # --- Generate PDF Receipt ---
        pdf_filepath = os.path.join(receipt_dir, f"{base_filename}.pdf")

        try:
            from fpdf import FPDF
            
            class ReceiptPDF(FPDF):
                def header(self):
                    self.set_font("helvetica", "B", 20)
                    self.set_text_color(0, 51, 102) # Dark blue
                    self.cell(0, 10, "SCALA BANK", ln=True, align="C")
                    self.set_font("helvetica", "B", 12)
                    self.cell(0, 10, "OFFICIAL TRANSACTION RECEIPT", ln=True, align="C")
                    self.ln(5)
                    self.set_draw_color(0, 51, 102)
                    self.line(10, self.get_y(), 200, self.get_y())
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("helvetica", "I", 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f"Page {self.page_no()} | Generated by Scala Bank v5.0", align="C")

            pdf = ReceiptPDF()
            pdf.add_page()
            
            # Transaction Header
            pdf.set_font("helvetica", "B", 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, f" Transaction Details: {txn_id}", ln=True, fill=True)
            pdf.ln(2)
            
            pdf.set_font("helvetica", "", 10)
            pdf.cell(50, 8, "Date/Time:", border=0)
            pdf.cell(0, 8, datetime.now().strftime("%d-%m-%Y %H:%M:%S"), ln=True)
            pdf.cell(50, 8, "Transaction Status:", border=0)
            pdf.set_text_color(0, 128, 0) # Green
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 8, "SUCCESSFUL", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(50, 8, "Transfer Mode:", border=0)
            pdf.cell(0, 8, f"{mode}", ln=True)
            pdf.ln(5)
            
            # Details Table
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 10, "SENDER & RECIPIENT INFORMATION", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 10)
            
            # Simple 2-column layout
            y_start = pdf.get_y()
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(95, 8, "SENDER DETAILS", border="B", ln=False)
            pdf.cell(5, 8, "", ln=False)
            pdf.cell(90, 8, "RECIPIENT DETAILS", border="B", ln=True)
            
            pdf.set_font("helvetica", "", 10)
            pdf.cell(95, 8, f"Name: {sender_acc.first_name} {sender_acc.last_name}", ln=False)
            pdf.cell(5, 8, "", ln=False)
            pdf.cell(90, 8, f"Name: {recipient_name}", ln=True)
            
            pdf.cell(95, 8, f"Account: {sender_acc.account_number}", ln=False)
            pdf.cell(5, 8, "", ln=False)
            pdf.cell(90, 8, f"Account: {recipient_acc}", ln=True)
            
            pdf.cell(95, 8, "Bank: SCALA BANK (INTERNAL)", ln=False)
            pdf.cell(5, 8, "", ln=False)
            pdf.cell(90, 8, f"Bank: {bank_name}", ln=True)
            
            pdf.cell(95, 8, f"IFSC: {sender_acc.BRANCH_IFSC}", ln=False)
            pdf.cell(5, 8, "", ln=False)
            pdf.cell(90, 8, f"IFSC: {ifsc}", ln=True)
            pdf.ln(10)
            
            # Amount Section
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 15, f" TOTAL AMOUNT SENT: Rs. {amount:,.2f} INR ", align="R", fill=True, ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "I", 9)
            pdf.ln(20)
            pdf.multi_cell(0, 5, "Note: This is a computer-generated receipt for a simulated banking transaction and does not require a physical signature.", align="C")
            
            pdf.output(pdf_filepath)
            
            print(f"\n[SUCCESS] Transaction PDF receipt generated: {pdf_filepath}")
            print("The receipt has been 'downloaded' to the 'receipts' folder in your workspace.")

            
        except Exception as e:
            print(f"[WARN] Could not generate PDF receipt: {e}")


    def international_transfer(self, account: Account):
        """Handle international wire transfer"""

        print("\n" + "=" * 70)
        print("INTERNATIONAL WIRE TRANSFER (SWIFT)")
        print("=" * 70)

        # Show current limits
        used_today = InternationalTransfer.get_today_international_limit_used(account)
        remaining = InternationalTransfer.DAILY_LIMIT_INR - used_today

        print(
            f"\nDaily International Transfer Limit: Rs. {InternationalTransfer.DAILY_LIMIT_INR:,.2f}"
        )
        print(f"Used Today: Rs. {used_today:,.2f}")
        print(f"Remaining: Rs. {remaining:,.2f}")

        # Option to view sample accounts
        view_samples = (
            input("\nView sample international accounts? (yes/no): ").strip().lower()
        )

        if view_samples in ["yes", "y"]:
            print("\n[INFO] SAMPLE INTERNATIONAL ACCOUNTS")
            print("=" * 120)
            print(f"{'Holder':<30} {'Country':<12} {'Bank':<35} {'Account':<35}")
            print("-" * 120)

            for acc_info in self.bank.international_registry.list_sample_accounts()[
                :10
            ]:
                print(
                    f"{acc_info['holder']:<30} {acc_info['country']:<12} "
                    f"{acc_info['bank']:<35} {acc_info['account']:<35}"
                )

            print("=" * 120)
            print(
                "\n💡 You can transfer to any of these accounts, or enter custom details.\n"
            )

        print("\n" + "-" * 70)
        print("BENEFICIARY DETAILS")
        print("-" * 70)

        recipient_name = input("Recipient Name: ").strip()
        recipient_account = input("Recipient Account/IBAN: ").strip()

        # Check if account exists in registry
        foreign_account = self.bank.international_registry.find_account_by_number(
            recipient_account
        )

        if foreign_account:
            print("\n[OK] Found recipient account:")
            print(f"  Holder: {foreign_account.account_holder}")
            print(f"  Bank: {foreign_account.bank_name}")
            print(f"  Country: {foreign_account.country}")
            print(f"  Currency: {foreign_account.currency}")

            recipient_bank = foreign_account.bank_name
            swift_code = foreign_account.swift_code
            recipient_country = foreign_account.country
            currency = foreign_account.currency
        else:
            print("\n[WARN]  Account not found in registry. Please enter details manually.")
            recipient_bank = input("Recipient Bank Name: ").strip()
            swift_code = input("SWIFT/BIC Code: ").strip().upper()

            print("\nSupported Countries:")
            countries = [
                "USA",
                "UK",
                "UAE",
                "Singapore",
                "Australia",
                "Canada",
                "Germany",
                "France",
                "Japan",
            ]
            for idx, country in enumerate(countries, 1):
                print(f"{idx}. {country}")

            country_choice = input("\nSelect country (1-9) or type name: ").strip()
            if country_choice.isdigit() and 1 <= int(country_choice) <= len(countries):
                recipient_country = countries[int(country_choice) - 1]
            else:
                recipient_country = country_choice

            print("\nSupported Currencies:")
            currencies = list(InternationalTransfer.EXCHANGE_RATES.keys())
            for idx, (curr, rate) in enumerate(
                InternationalTransfer.EXCHANGE_RATES.items(), 1
            ):
                print(f"{idx}. {curr} (1 {curr} = Rs. {rate:,.2f})")

            curr_choice = (
                input(f"\nSelect currency (1-{len(currencies)}) or type code: ")
                .strip()
                .upper()
            )
            if curr_choice.isdigit() and 1 <= int(curr_choice) <= len(currencies):
                currency = currencies[int(curr_choice) - 1]
            elif curr_choice in currencies:
                currency = curr_choice
            else:
                print("Invalid currency")
                return

        recipient_address = input("Recipient Address (optional): ").strip() or None

        print("\n" + "-" * 70)
        print("TRANSFER AMOUNT")
        print("-" * 70)

        try:
            amount_foreign = float(input(f"\nEnter amount in {currency}: "))
            if amount_foreign <= 0:
                print("Amount must be positive")
                return
        except ValueError:
            print("Invalid amount")
            return

        # Show conversion preview
        amount_inr, rate = InternationalTransfer.convert_currency(
            amount_foreign, currency, "INR"
        )
        charges = InternationalTransfer.calculate_swift_charges(amount_inr)
        total = amount_inr + charges

        print("\n" + "-" * 70)
        print("TRANSFER SUMMARY")
        print("-" * 70)
        print(f"Amount to Send: {amount_foreign:,.2f} {currency}")
        print(f"Exchange Rate: 1 {currency} = Rs. {rate:,.2f}")
        print(f"Equivalent INR: Rs. {amount_inr:,.2f}")
        print(f"SWIFT Charges: Rs. {charges:,.2f}")
        print(f"Total Debit: Rs. {total:,.2f}")
        print(
            f"\nExpected Arrival: {InternationalTransfer.PROCESSING_DAYS} business days"
        )
        print("-" * 70)

        # Purpose of remittance
        print("\nPurpose of Remittance:")
        purposes = [
            "Family Maintenance",
            "Education",
            "Medical Treatment",
            "Business Payment",
            "Investment",
            "Gift",
            "Other",
        ]
        for idx, purpose in enumerate(purposes, 1):
            print(f"{idx}. {purpose}")

        purpose_choice = input("\nSelect purpose (1-7): ").strip()
        if purpose_choice.isdigit() and 1 <= int(purpose_choice) <= len(purposes):
            purpose = purposes[int(purpose_choice) - 1]
        else:
            purpose = input("Enter purpose: ").strip()

        # Confirm
        print("\n" + "=" * 70)
        confirm = input("Confirm international transfer? (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("Transfer cancelled")
            return

        # Initiate transfer
        success, message, swift_ref = (
            InternationalTransfer.initiate_international_transfer(
                account=account,
                recipient_name=recipient_name,
                recipient_account=recipient_account,
                recipient_bank_name=recipient_bank,
                swift_code=swift_code,
                recipient_country=recipient_country,
                amount_to_send=amount_foreign,
                currency=currency,
                purpose=purpose,
                recipient_address=recipient_address,
                registry=self.bank.international_registry,
            )
        )

        if success:
            print("\n" + "=" * 70)
            print("[SUCCESS] TRANSFER SUCCESSFUL")
            print("=" * 70)
            print(message)

            if foreign_account:
                # Load transactions if needed
                foreign_account._load_transactions_if_needed()

                print("\n[MONEY] Foreign account credited successfully")
                print(
                    f"   New balance: {foreign_account.balance:,.2f} {foreign_account.currency}"
                )

                # Show last transaction
                if foreign_account.transactions:
                    last_txn = foreign_account.transactions[-1]
                    print("\n📝 Transaction recorded:")
                    print(
                        f"   Amount: +{last_txn['amount']:,.2f} {foreign_account.currency}"
                    )
                    print(f"   From: {last_txn['from']}")
                    print(f"   SWIFT Ref: {last_txn['swift_ref']}")

            self.bank.save()

    def track_swift_transfer_menu(self):
        """Track international SWIFT transfer"""

        swift_ref = input("\nEnter SWIFT Reference Number: ").strip()

        result = InternationalTransfer.track_swift_transfer(swift_ref, self.bank)

        if result:
            print("\n" + "=" * 80)
            print("SWIFT TRANSFER TRACKING")
            print("=" * 80)
            print(f"\nSWIFT Reference: {result['swift_reference']}")
            print(f"Status: {result['status']}")
            print(f"\nSender: {result['sender_name']} ({result['sender_account']})")
            print(f"Recipient: {result['recipient_name']}")
            print(f"Recipient Account: {result['recipient_account']}")
            print(f"Recipient Bank: {result['recipient_bank']}")
            print(f"SWIFT Code: {result['swift_code']}")
            print(f"Country: {result['country']}")
            print(f"\nAmount: {result['amount']:,.2f} {result['currency']}")
            print(
                f"Exchange Rate: 1 {result['currency']} = Rs. {result['exchange_rate']:,.2f}"
            )
            print(f"Total Debited: Rs. {result['total_debited_inr']:,.2f}")
            print(f"SWIFT Charges: Rs. {result['charges']:,.2f}")
            print(f"\nPurpose: {result['purpose']}")
            print(f"Initiated: {result['initiated_on']}")
            print(f"Expected Arrival: {result['expected_arrival']}")
            print(f"Transaction ID: {result['transaction_id']}")
            print("=" * 80)
        else:
            print(f"\n[FAIL] SWIFT transfer with reference '{swift_ref}' not found")

    def view_international_accounts_menu(self):
        """View international accounts registry"""
        while True:
            print("\n" + "=" * 70)
            print("INTERNATIONAL ACCOUNTS REGISTRY")
            print("=" * 70)
            print("1. View Sample Accounts")
            print("2. View Accounts by Country")
            print("3. Search Account by Number")
            print("4. View Registry Statistics")
            print("5. Back to Main Menu")
            print("=" * 70)

            choice = input("\nEnter choice: ").strip()

            if choice == "1":
                self.view_sample_international_accounts()
            elif choice == "2":
                self.view_accounts_by_country()
            elif choice == "3":
                self.search_international_account()
            elif choice == "4":
                self.view_registry_statistics()
            elif choice == "5":
                break

    def view_sample_international_accounts(self):
        """View sample international accounts"""
        accounts = self.bank.international_registry.list_sample_accounts()

        print("\n" + "=" * 130)
        print(
            f"{'Holder':<30} {'Country':<12} {'Bank':<35} {'Account':<35} {'Balance':<18}"
        )
        print("-" * 130)

        for acc in accounts[:20]:
            balance_str = f"{acc['balance']:,.2f} {acc['currency']}"
            print(
                f"{acc['holder']:<30} {acc['country']:<12} "
                f"{acc['bank']:<35} {acc['account']:<35} {balance_str:<18}"
            )

        print("=" * 130)
        print(f"\nShowing 20 of {len(accounts)} total accounts")

    def view_accounts_by_country(self):
        """View accounts filtered by country"""

        countries = list(InternationalBankRegistry.BANKS.keys())

        print("\nSelect country:")
        for idx, country in enumerate(countries, 1):
            print(f"{idx}. {country}")

        choice = input(f"\nEnter choice (1-{len(countries)}): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(countries):
            country = countries[int(choice) - 1]

            matching = self.bank.international_registry.get_accounts_by_country(country)

            print(f"\n📍 {len(matching)} Accounts in {country}:")
            print("=" * 130)
            print(f"{'Holder':<30} {'Bank':<40} {'Account':<35} {'Balance':<18}")
            print("-" * 130)

            for acc in matching[:10]:
                balance_str = f"{acc.balance:,.2f} {acc.currency}"
                print(
                    f"{acc.account_holder:<30} {acc.bank_name:<40} "
                    f"{acc.account_number:<35} {balance_str:<18}"
                )

            print("=" * 130)

    def search_international_account(self):
        """Search for international account"""
        account_num = input("\nEnter account number/IBAN: ").strip()

        account = self.bank.international_registry.find_account_by_number(account_num)

        if account:
            # Load transactions if needed
            account._load_transactions_if_needed()

            print("\n[OK] ACCOUNT FOUND")
            print("=" * 70)
            print(f"Holder: {account.account_holder}")
            print(f"Account: {account.account_number}")
            print(f"Bank: {account.bank_name}")
            print(f"SWIFT: {account.swift_code}")
            print(f"Country: {account.country}")
            print(f"Currency: {account.currency}")
            print(f"Balance: {account.balance:,.2f} {account.currency}")

            if account.transactions:
                print(f"\nTransactions: {len(account.transactions)}")
                print("\nRecent Transactions:")
                for txn in account.transactions[-5:]:
                    print(
                        f"  - {txn['date']}: +{txn['amount']:,.2f} {account.currency} from {txn['from']}"
                    )

            print("=" * 70)
        else:
            print("\n[FAIL] Account not found")

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

    def switch_account(self, accounts: List[Account]) -> Account:
        """Switch to a different account"""
        if len(accounts) > 1:
            print("\nSelect account to use:")
            for idx, acc in enumerate(accounts, 1):
                print(
                    f"{idx}. {acc.account_type} - {acc.account_number} (Balance: Rs. {acc.balance:.2f} INR)"
                )

            choice = self.read_valid_choice(
                f"Enter account number (1-{len(accounts)}): ",
                [str(i) for i in range(1, len(accounts) + 1)],
            )
            selected = accounts[int(choice) - 1]
            print(
                f"Switched to account: {selected.account_type} - {selected.account_number}"
            )
            return selected
        else:
            print("You only have one account.")
            return accounts[0]

    def create_additional_account(
        self, customer: Customer, accounts: List[Account]
    ) -> List[Account]:
        """Create an additional account for the customer"""
        print("\n=== Create Additional Account ===")
        print("Available Account Types:")
        print("1  Pride (Min Balance: Rs. 2,000.00)")
        print("2  Bespoke (Min Balance: Rs. 2,00,000.00)")
        print("3  Club (Min Balance: Rs. 10,000.00)")
        print("4  Delite (Min Balance: Rs. 5,000.00)")
        print("5  Future (Min Balance: Rs. 0.00 - For Minors)")

        account_type = self.read_valid_account_type("Enter account type (1-5): ")
        new_account = self.bank.add_account_to_customer(customer, account_type)

        updated_accounts = self.bank.get_customer_accounts(customer)

        print(f"""
New Account Created Successfully!

Account Holder: {customer.first_name} {customer.last_name}
Customer ID: {customer.customer_id}
Account Type: {account_type}
Account Number: {new_account.account_number}

{Account.get_branch_details()}

You now have {customer.account_count} account(s) linked to your Customer ID.
        """)

        return updated_accounts

    def manage_recurring_bills(self, account: Account):
        """Manage recurring bills"""
        managing = True
        while managing:
            print("\n=== Recurring Bills Management ===")
            print("1. View Recurring Bills")
            print("2. Add Recurring Bill")
            print("3. Remove Recurring Bill")
            print("4. View Rewards Dashboard 💎")  # NEW
            print("5. Back to Main Menu")

            choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3", "4", "5"])

            if choice == "1":
                self.view_recurring_bills(account)  # CHANGED
            elif choice == "2":
                self.add_recurring_bill(account)
            elif choice == "3":
                self.remove_recurring_bill(account)
            elif choice == "4":
                self.show_rewards_dashboard(account)  # NEW
            elif choice == "5":
                managing = False

    def view_recurring_bills(self, account: Account):
        """View recurring bills with payment methods and rewards"""
        if not account.recurring_bills:
            print("\n[INFO] No recurring bills found.")
            input("\nPress Enter to continue...")
            return

        # Update dynamic bills
        updated = account.update_dynamic_bills()
        if updated:
            print("\n💳 Dynamic Bills Updated:")
            for u in updated:
                print(
                    f"   {u['bill_name']}: Rs. {u['old_amount']:,.2f} → Rs. {u['new_amount']:,.2f}"
                )

        # Calculate rewards
        total_monthly_rewards = 0
        total_annual_rewards = 0
        bills_on_card = []

        for bill in account.recurring_bills:
            if (
                bill.payment_method == PaymentMethod.CREDIT_CARD
                and bill.payment_card_id
            ):
                card = account.get_card_by_id(bill.payment_card_id)
                if card and isinstance(card, CreditCard):
                    rewards = bill.base_amount * card.reward_rate

                    if bill.frequency == "MONTHLY":
                        total_monthly_rewards += rewards
                        total_annual_rewards += rewards * 12
                        bills_on_card.append((bill.name, rewards, card.network))
                    elif bill.frequency == "QUARTERLY":
                        total_annual_rewards += rewards * 4
                    elif bill.frequency == "YEARLY":
                        total_annual_rewards += rewards

        print("\n" + "=" * 130)
        print(f"{'RECURRING BILLS':^130}")
        print("=" * 130)

        print(
            f"\n{'Name':<35} {'Amount':<15} {'Freq':<10} {'Due Day':<10} {'Payment Method':<40} {'Rewards'}"
        )
        print("-" * 130)

        for bill in account.recurring_bills:
            payment_desc = bill.get_payment_description(account)

            # Calculate rewards
            rewards_str = ""
            if (
                bill.payment_method == PaymentMethod.CREDIT_CARD
                and bill.payment_card_id
            ):
                card = account.get_card_by_id(bill.payment_card_id)
                if card:
                    rewards = int(bill.base_amount * card.reward_rate)
                    rewards_str = f"💎 {rewards} pts"

            auto_marker = " 🤖" if bill.auto_debit else ""
            dynamic_marker = " [STATS]" if bill.is_dynamic else ""

            print(
                f"{bill.name:<35} Rs. {bill.base_amount:<12,.2f} {bill.frequency:<10} "
                f"{bill.day_of_month:<10} {payment_desc:<40} {rewards_str}{auto_marker}{dynamic_marker}"
            )

        print("=" * 130)

        # Summary
        print("\n[STATS] SUMMARY")
        print(f"   Total bills: {len(account.recurring_bills)}")
        print(f"   Bills paid via credit card: {len(bills_on_card)}")

        if bills_on_card:
            print("\n💎 REWARD EARNINGS")
            print(f"   Monthly rewards: {int(total_monthly_rewards)} points")
            print(f"   Annual rewards: {int(total_annual_rewards)} points")
            print(f"   Estimated value: Rs. {int(total_annual_rewards):,.2f}")

            print("\n   Top reward earners:")
            for name, rewards, network in sorted(
                bills_on_card, key=lambda x: x[1], reverse=True
            )[:3]:
                print(f"   • {name}: {int(rewards)} pts/payment ({network})")

        # Check for optimization opportunities
        missed_rewards = 0
        opportunities = []

        for bill in account.recurring_bills:
            if bill.payment_method == PaymentMethod.BANK_ACCOUNT:
                # Find best card
                credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

                for card in credit_cards:
                    available = card.credit_limit - card.current_balance
                    if available >= bill.base_amount:
                        potential_rewards = bill.base_amount * card.reward_rate
                        missed_rewards += potential_rewards
                        opportunities.append(
                            (bill.name, potential_rewards, card.network)
                        )
                        break

        if opportunities:
            print("\n💡 OPTIMIZATION OPPORTUNITY")
            print(
                f"   You're missing out on {int(missed_rewards)} reward points monthly!"
            )
            print("   Consider paying these bills with credit card:")
            for name, rewards, network in opportunities[:3]:
                print(f"   • {name} via {network} → +{int(rewards)} pts/month")

        print("\n" + "=" * 130)
        print(
            "Legend: 🤖 Auto-pay | [STATS] Dynamic amount | 💳 Card payment | [MONEY] Bank payment"
        )
        print("=" * 130)

        input("\nPress Enter to continue...")

    def show_rewards_dashboard(self, account: Account):
        """Show rewards earned from credit card purchases"""
        # Load transactions if needed
        account._load_transactions_if_needed()

        print("\n" + "=" * 80)
        print(f"{'💎 REWARDS DASHBOARD':^80}")
        print("=" * 80)

        total_lifetime_rewards = 0
        monthly_rewards = 0
        rewards_by_card = {}
        transaction_count = 0

    def _parse_metadata(self, metadata) -> dict:
        """Parse metadata into a dictionary regardless of format (dict or semi-colon string)"""
        if not metadata:
            return {}
        if isinstance(metadata, dict):
            return metadata
        if isinstance(metadata, str):
            try:
                # If it's empty string
                if not metadata.strip():
                    return {}
                # Handle semicolon-separated key=value pairs
                pairs = metadata.split(";")
                result = {}
                for pair in pairs:
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        result[k.strip()] = v.strip()
                return result
            except:
                return {}
        return {}

    # Helper function to extract reward points from metadata
    def get_reward_points(self, metadata):
        """Extract reward points from metadata (string or dict)"""
        parsed = self._parse_metadata(metadata)
        try:
            return int(parsed.get("reward_points_earned", 0) or parsed.get("rewardPoints", 0) or 0)
        except:
            return 0

        # Analyze transactions - look for CREDIT_CARD_PURCHASE and CREDIT_CARD_BILL_PAYMENT transactions
        for txn in account.transactions:
            points = 0

            # Check for purchase rewards OR bill payment rewards
            if txn.type in ["CREDIT_CARD_PURCHASE", "CREDIT_CARD_BILL_PAYMENT"]:
                points = self.get_reward_points(txn.metadata)
                if points > 0:
                    transaction_count += 1
                    total_lifetime_rewards += points

                    # Try to extract card_id from metadata
                    card_id = "Unknown"
                    parsed_meta = self._parse_metadata(txn.metadata)
                    card_id = parsed_meta.get("cardId", "Unknown")

                    if card_id not in rewards_by_card:
                        rewards_by_card[card_id] = {"points": 0, "count": 0}
                    rewards_by_card[card_id]["points"] += points
                    rewards_by_card[card_id]["count"] += 1

        # Calculate this month's rewards
        from datetime import datetime

        current_month = datetime.now().strftime("%m-%Y")

        for txn in account.transactions:
            if txn.type in ["CREDIT_CARD_PURCHASE", "CREDIT_CARD_BILL_PAYMENT"]:
                try:
                    # Parse transaction timestamp to get month
                    # Timestamp format: "DD-MM-YYYY HH:MM:SS"
                    txn_date_part = txn.timestamp.split()[0]  # Get "DD-MM-YYYY"
                    txn_month = txn_date_part[3:10]  # Get "MM-YYYY"
                    if txn_month == current_month:
                        points = self.get_reward_points(txn.metadata)
                        if points > 0:
                            monthly_rewards += points
                except:
                    pass

        print("\n[STATS] LIFETIME REWARDS FROM PURCHASES")
        print(f"   Total points earned: {int(total_lifetime_rewards)}")
        print(f"   Estimated value: Rs. {int(total_lifetime_rewards):,.2f}")
        if transaction_count > 0:
            print(
                f"   Average per transaction: {int(total_lifetime_rewards / transaction_count)} points"
            )

        print("\n📅 THIS MONTH")
        print(f"   Rewards earned: {int(monthly_rewards)} points")
        print(f"   Estimated value: Rs. {int(monthly_rewards):,.2f}")
        if monthly_rewards > 0:
            print(
                f"   Projected annual: {int(monthly_rewards * 12)} points (Rs. {int(monthly_rewards * 12):,.2f})"
            )

        if rewards_by_card:
            print("\n💳 REWARDS BY CARD")
            for card_id, data in sorted(
                rewards_by_card.items(), key=lambda x: x[1]["points"], reverse=True
            ):
                card = account.get_card_by_id(card_id)
                if card:
                    print(
                        f"   {card.network} ****{card.card_number[-4:]}: {int(data['points'])} points ({int(data['count'])} purchases)"
                    )

        # Value breakdown
        if total_lifetime_rewards > 0:
            print("\n[MONEY] REWARDS VALUE")
            print(f"   Value @ Rs. 1.00/point: Rs. {int(total_lifetime_rewards):,.2f}")
            print(f"   💎 Total benefit: Rs. {int(total_lifetime_rewards):,.2f}")
        else:
            print(
                "\n ℹ️  No rewards earned yet. Make credit card purchases to earn points!"
            )

        print("\n" + "=" * 80)
        input("\nPress Enter to continue...")

    def add_recurring_bill(self, account: Account):
        """Add a recurring bill"""
        print("\n=== Add Recurring Bill ===")
        print("\nCommon bills:")
        common_bills = RecurringBillFactory.get_common_bills()

        for idx, (name, cat, min_amt, max_amt, freq) in enumerate(common_bills, 1):
            print(
                f"{idx}. {name} ({cat}) - Rs. {min_amt:.2f}-Rs. {max_amt:.2f} [{freq}]"
            )

        print(f"{len(common_bills) + 1}. Custom Bill")

        template_choice = self.read_valid_choice(
            "Select bill template: ", [str(i) for i in range(1, len(common_bills) + 2)]
        )

        # Handle Credit Card Bill (option 17)
        if int(template_choice) == 17:
            self.add_credit_card_bill(account)
            return

        # Get bill details
        if int(template_choice) <= len(common_bills):
            name, category, min_amt, max_amt, frequency = common_bills[
                int(template_choice) - 1
            ]
            amount = float(
                input(f"Enter amount (Rs. {min_amt:.2f}-Rs. {max_amt:.2f}): ")
            )
        else:
            name = input("Bill name: ").strip()
            category = input("Category: ").strip()
            amount = self.read_positive_double("Amount (Rs.): ")
            print("\nFrequency: 1=Monthly, 2=Quarterly, 3=Yearly")
            freq_choice = self.read_valid_choice("Select: ", ["1", "2", "3"])
            frequency = {"1": "MONTHLY", "2": "QUARTERLY", "3": "YEARLY"}[freq_choice]

        day_of_month = int(input("Due day of month (1-28): "))

        # ===== PAYMENT METHOD SELECTION =====
        print("\n" + "=" * 60)
        print("💳 PAYMENT METHOD")
        print("=" * 60)
        print("How would you like to pay this bill?")
        print("1. Bank Account (Direct Debit)")
        print("2. Credit Card (Earn Reward Points 💎)")

        payment_choice = input("\nEnter choice (1-2): ").strip()

        payment_method = PaymentMethod.BANK_ACCOUNT
        payment_card_id = None

        if payment_choice == "2":
            # Check for credit cards
            credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

            if not credit_cards:
                print("\n[FAIL] No credit cards available.")
                print("   Defaulting to bank account payment.")
            else:
                print("\n--- Select Credit Card ---")

                for idx, card in enumerate(credit_cards, 1):
                    available = card.credit_limit - card.current_balance
                    reward_rate = card.reward_rate * 100

                    print(
                        f"{idx}. {card.network} ****{card.card_number[-4:]} "
                        f"(Available: Rs. {available:,.2f}, Rewards: {reward_rate:.1f}%)"
                    )

                card_choice = input(f"\nSelect card (1-{len(credit_cards)}): ").strip()

                if card_choice.isdigit() and 1 <= int(card_choice) <= len(credit_cards):
                    selected_card = credit_cards[int(card_choice) - 1]
                    payment_method = PaymentMethod.CREDIT_CARD
                    payment_card_id = selected_card.card_id

                    # Calculate rewards
                    estimated_rewards = amount * selected_card.reward_rate

                    print(
                        f"\n[SUCCESS] Selected: {selected_card.network} ****{selected_card.card_number[-4:]}"
                    )
                    print(
                        f"💎 Estimated rewards per payment: {int(estimated_rewards)} points"
                    )

                    if frequency == "MONTHLY":
                        annual_rewards = estimated_rewards * 12
                        print(
                            f"💎 Annual rewards potential: {int(annual_rewards)} points!"
                        )
                else:
                    print("[FAIL] Invalid choice. Using bank account.")

        # Create the bill with payment method
        if int(template_choice) <= len(common_bills):
            bill = RecurringBillFactory.create_from_template(
                template_index=int(template_choice) - 1,
                amount=amount,
                day_of_month=day_of_month,
                auto_debit=True,
                payment_method=payment_method,
                payment_card_id=payment_card_id,
            )
        else:
            bill = RecurringBillFactory.create_custom_bill(
                name=name,
                category=category,
                amount=amount,
                frequency=frequency,
                day_of_month=day_of_month,
                auto_debit=True,
                payment_method=payment_method,
                payment_card_id=payment_card_id,
            )

        account.add_recurring_bill(bill)
        self.bank.save()

        print("\n" + "=" * 60)
        print("[SUCCESS] RECURRING BILL ADDED")
        print("=" * 60)
        print(f"Bill Name: {bill.name}")
        print(f"Amount: Rs. {bill.base_amount:,.2f}")
        print(f"Frequency: {bill.frequency}")
        print(f"Due Day: {bill.day_of_month}")
        print(f"Payment Method: {bill.get_payment_description(account)}")
        print(f"Auto-pay: {'[SUCCESS] Enabled' if bill.auto_debit else '[FAIL] Disabled'}")
        print("=" * 60)

        input("\nPress Enter to continue...")

    def add_credit_card_bill(self, account: Account):
        """Special handling for credit card bills"""
        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards linked to this account.")
            print("Add a credit card first from Card Management menu.")
            input("\nPress Enter to continue...")
            return

        print("\n" + "=" * 60)
        print("CREDIT CARD BILL SETUP")
        print("=" * 60)
        print("0. Manual Entry (Custom Amount)")

        for idx, card in enumerate(credit_cards, 1):
            current_bill = card.current_balance

            print(
                f"{idx}. {card.network} ****{card.card_number[-4:]} "
                f"(Current Balance: Rs. {current_bill:,.2f})"
            )

        card_choice = input(f"\nSelect option (0-{len(credit_cards)}): ").strip()

        if card_choice == "0":
            # Manual entry
            bill_name = input("Bill name: ") or "Credit Card Bill (Manual)"
            amount = float(input("Enter bill amount: Rs. "))
            linked_card_id = None
            is_dynamic = False

        elif card_choice.isdigit() and 1 <= int(card_choice) <= len(credit_cards):
            selected_card = credit_cards[int(card_choice) - 1]

            bill_name = f"{selected_card.network} Credit Card"
            amount = selected_card.current_balance
            linked_card_id = selected_card.card_id
            is_dynamic = True

            print(
                f"\n[SUCCESS] Linked to {selected_card.network} ****{selected_card.card_number[-4:]}"
            )
            print("💡 Bill amount will auto-update from card statement")

        else:
            print("[FAIL] Invalid choice")
            input("\nPress Enter...")
            return

        category = "Finance"
        frequency = "MONTHLY"
        day_of_month = int(input("Due day of month (1-28): "))

        # Credit card bills are ALWAYS paid from bank account
        payment_method = PaymentMethod.BANK_ACCOUNT
        payment_card_id = None

        print("\n💡 Credit card bills are automatically paid from your bank account.")

        auto_debit_choice = input("\nEnable auto-pay? (y/n): ").strip().lower()
        auto_debit = auto_debit_choice == "y"

        # Create bill
        bill = RecurringBill(
            name=bill_name,
            category=category,
            base_amount=amount,
            frequency=frequency,
            day_of_month=day_of_month,
            auto_debit=auto_debit,
            linked_card_id=linked_card_id,
            is_dynamic=is_dynamic,
            payment_method=payment_method,
            payment_card_id=payment_card_id,
        )

        account.add_recurring_bill(bill)
        self.bank.save()

        print("\n" + "=" * 60)
        print("[SUCCESS] CREDIT CARD BILL ADDED")
        print("=" * 60)
        print(f"Bill: {bill.name}")
        print(f"Amount: Rs. {bill.base_amount:,.2f}")
        print(f"Due Day: {bill.day_of_month}")
        print(f"Auto-pay: {'[SUCCESS] Enabled' if bill.auto_debit else '[FAIL] Disabled'}")
        if is_dynamic:
            print("[STATS] Amount will auto-update from card")
        print("=" * 60)

        input("\nPress Enter to continue...")

    def remove_recurring_bill(self, account: Account):
        """Remove a recurring bill"""
        account.show_recurring_bills()
        if getattr(account, "recurring_bills", None):
            bill_id = input("Enter Bill ID to remove: ").strip()
            account.remove_recurring_bill(bill_id)
            self.bank.save()

    def manage_salary(self, account: Account):
        """Manage salary profile"""
        managing = True
        while managing:
            print("""
Salary Management
1  View Salary Details
2  Set/Update Salary
3  Remove Salary
4  Back to Main Menu
            """)

            choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3", "4"])

            if choice == "1":
                account.show_salary_details()
            elif choice == "2":
                print("\n=== Configure Salary ===")
                gross_salary = self.read_positive_double(
                    "Enter gross monthly salary: Rs. "
                )
                salary_day = int(input("Enter salary credit day (1-28): "))

                # Company Deductions
                print("\n--- Company Deductions ---")
                epf_contribution = self.read_positive_double(
                    "Monthly EPF contribution (leave blank for 0): Rs. ",
                    allow_zero=True,
                )
                professional_tax = self.read_positive_double(
                    "Monthly professional tax (leave blank for 0): Rs. ",
                    allow_zero=True,
                )
                other_deductions = self.read_positive_double(
                    "Other monthly deductions (leave blank for 0): Rs. ",
                    allow_zero=True,
                )

                account.set_salary(
                    gross_salary,
                    salary_day,
                    employee_epf_contribution=epf_contribution,
                    professional_tax=professional_tax,
                    other_deductions=other_deductions,
                )
                self.bank.save()
            elif choice == "3":
                account.remove_salary()
                self.bank.save()
            elif choice == "4":
                managing = False

    def simulate_time(self, account: Account):
        """Simulate time passage with recurring bills and expenses"""
        # Check if clock is in REAL mode
        if BankClock._mode == "REAL":
            print("\n[WARN]  Time Simulation Not Possible")
            print("Time simulation is only available in VIRTUAL mode.")
            print("\nTo enable time simulation:")
            print("1. Go to main menu (option 20 from account menu)")
            print("2. Select 'Change Clock Mode' (option 20 from main menu)")
            print("3. Switch to VIRTUAL mode")
            return

        print("\nTime Simulation")
        print(f"Current Date/Time: {BankClock.get_formatted_datetime()}")
        print("1  Simulate 1 Day")
        print("2  Simulate 1 Week (7 days)")
        print("3  Simulate 1 Month (30 days)")
        print("4  Simulate 3 Months (90 days)")
        print("5  Custom Duration")

        sim_choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3", "4", "5"])

        days_map = {"1": 1, "2": 7, "3": 30, "4": 90}
        days = days_map.get(sim_choice, int(input("Enter number of days: ")))

        print(f"\nSimulating {days} day(s)...")
        print(f"Starting Date/Time: {BankClock.get_formatted_datetime()}")
        print("=" * 60)

        total_transactions = 0
        start_balance = account.balance

        for day in range(1, days + 1):
            BankClock.advance_day()
            current_date = BankClock.today()

            # Process daily tasks across the whole bank (recurring bills, salary credits, card bills)
            bills_processed = self.bank.process_daily_tasks()

            # Still simulate daily expenses for the focused account for reporting
            daily_txns = ExpenseSimulator.simulate_day(account, self.bank, current_date)

            total_transactions += bills_processed + daily_txns

            if day % 7 == 0 or day == days:
                print(
                    f"Day {day:3d} [{BankClock.get_formatted_date()}]: Balance = Rs. {account.balance:,.2f} INR | Txns = {bills_processed + daily_txns}"
                )

        self.bank.save()
        balance_change = account.balance - start_balance
        change_symbol = "+" if balance_change >= 0 else ""

        print("=" * 60)
        print("Simulation complete!")
        print(f"Ending Date/Time: {BankClock.get_formatted_datetime()}")
        print(f"Total Transactions: {total_transactions}")
        print(f"Starting Balance: Rs. {start_balance:,.2f} INR")
        print(f"Ending Balance: Rs. {account.balance:,.2f} INR")
        print(f"Net Change: {change_symbol}Rs. {balance_change:,.2f} INR")
        print("=" * 60)

    def view_expense_analysis(self, account: Account):
        """View expense analysis for a period"""
        # Load transactions if needed
        account._load_transactions_if_needed()

        print("\nExpense Analysis Period:")
        print("1  Last 7 days")
        print("2  Last 30 days")
        print("3  Last 90 days")

        period_choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3"])
        days = {"1": 7, "2": 30, "3": 90}[period_choice]

        account.show_expense_analysis(days)

    def track_cheque(self):
        """Track a cheque by ID"""
        cheque_id = input("Enter Cheque ID to track: ").strip()
        if cheque_id:
            self.bank.show_cheque_details(cheque_id)
        else:
            print("Cheque ID cannot be empty.")

    def run(self):
        """Main application loop"""
        print("Welcome to Scala Bank v5.0 (Python Edition)")

        while self.running:
            print(f"""
Current Date/Time: {BankClock.get_formatted_datetime()}

Choose an option:
1  Open a New Account
2  Login to Existing Account
3  Forgot Password
4  Track Cheque ID
5  Admin Dashboard
6  Exit
            """)

            choice = self.read_valid_choice(
                "Enter your choice: ",
                ["1", "2", "3", "4", "5", "6"],
                "Invalid option. Please enter 1, 2, 3, 4, 5, or 6.",
            )

            if choice == "1":
                self.open_new_account()
            elif choice == "2":
                self.handle_login()
            elif choice == "3":
                PasswordRecoveryUI.forgot_password_flow(self.bank)
            elif choice == "4":
                self.track_cheque()
            elif choice == "5":
                self.access_admin_dashboard()
            elif choice == "6":
                print("Thank you for using Scala Bank!")
                self.running = False

    def access_admin_dashboard(self):
        """Access admin dashboard with PIN authentication"""
        print("\n" + "="*80)
        print("🔐 ADMIN DASHBOARD ACCESS".center(80))
        print("="*80)
        
        admin_panel = AdminControlPanel(self.bank)
        
        # Prompt for PIN
        pin = input("\nEnter Admin PIN: ").strip()
        
        if admin_panel.authenticate(pin):
            print("[OK] Authentication successful!")
            input("Press Enter to access dashboard...")
            admin_panel.display_dashboard()
        else:
            print("\n[FAIL] Invalid PIN. Access denied.")
            print("[OK] Returning to main menu...")

    def view_cibil_report(self, customer: Customer):
        """View detailed CIBIL score report with history"""
        print("\n" + "=" * 70)
        print("                    CIBIL SCORE REPORT")
        print("=" * 70)

        # Calculate current score
        current_score = calculate_cibil_score(customer, self.bank)
        customer.cibil_score = current_score

        # Determine rating
        if current_score >= 750:
            rating = "Excellent ⭐⭐⭐⭐⭐"
            color = "🟢"
        elif current_score >= 650:
            rating = "Good ⭐⭐⭐⭐"
            color = "🟡"
        elif current_score >= 550:
            rating = "Average ⭐⭐⭐"
            color = "🟠"
        else:
            rating = "Poor ⭐⭐"
            color = "🔴"

        print(f"\n{color} CIBIL Score: {current_score}/900")
        print(f"Rating: {rating}")
        print(f"Customer: {customer.first_name} {customer.last_name}")
        print(f"Customer ID: {customer.customer_id}")
        print(f"Report Generated: {BankClock.get_formatted_datetime()}")

        print("\n" + "-" * 70)
        print("SCORE BREAKDOWN")
        print("-" * 70)

        # Get loans for analysis
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        today = BankClock.today()

        # 1. Repayment History Analysis
        print("\n[STATS] REPAYMENT HISTORY")
        total_emis = 0
        late_payments = 0
        on_time_payments = 0

        if loans:
            for loan in loans:
                emis_paid = getattr(loan, "emis_paid", 0)
                total_emis += loan.tenure_months

                # Calculate expected EMIs based on loan start date
                if hasattr(loan, "start_date"):
                    months_elapsed = (today.year - loan.start_date.year) * 12 + (
                        today.month - loan.start_date.month
                    )
                    expected_emis = min(months_elapsed + 1, loan.tenure_months)
                else:
                    expected_emis = loan.tenure_months

                missed = max(0, expected_emis - emis_paid)
                on_time = emis_paid
                late_payments += missed
                on_time_payments += on_time

            if late_payments == 0:
                impact = "Excellent (+100 points)"
                status = "[SUCCESS] No late payments"
            else:
                penalty = min(200, 50 * late_payments)
                impact = f"Poor (-{penalty} points)"
                status = f"[FAIL] {late_payments} late payment(s)"

            print(f"  Status: {status}")
            print(f"  Total EMIs Paid: {on_time_payments}")
            print(f"  Late/Missed EMIs: {late_payments}")
            print(f"  Impact on Score: {impact}")
        else:
            print("  Status: No loan history")
            print("  Impact: Neutral (Base score)")

        # 2. Credit Utilization
        print("\n💳 CREDIT UTILIZATION")
        # Get credit cards from customer's accounts
        credit_cards = []
        customer_accounts = self.bank.get_customer_accounts(customer)
        for acc in customer_accounts:
            for card in acc.cards:
                if isinstance(card, CreditCard):
                    credit_cards.append(
                        {
                            "limit": card.credit_limit,
                            "used": card.credit_used,
                            "opened": getattr(card, "start_date", BankClock.today()),
                        }
                    )

        if credit_cards:
            total_limit = sum(cc["limit"] for cc in credit_cards)
            total_used = sum(cc["used"] for cc in credit_cards)
            utilization = (total_used / total_limit * 100) if total_limit > 0 else 0

            if utilization < 30:
                impact = "Excellent (+50 points)"
            elif utilization > 75:
                impact = "Poor (-50 points)"
            else:
                impact = "Moderate (0 points)"

            print(f"  Total Credit Limit: ₹{total_limit:,.2f}")
            print(f"  Total Used: ₹{total_used:,.2f}")
            print(f"  Utilization: {utilization:.1f}%")
            print(f"  Impact: {impact}")
        else:
            print("  Status: No credit cards")
            print("  Impact: Neutral")

        # 3. Credit Accounts
        print("\n[INFO] CREDIT ACCOUNTS")
        active_loans = [l for l in loans if l.status == "Active"]
        n_active_loans = len(active_loans)
        n_cards = len(credit_cards)  # Use the credit_cards list from above
        total_accounts = n_active_loans + n_cards

        if total_accounts > 7:
            impact = "Too many accounts (-20 points)"
        elif 2 <= total_accounts <= 5:
            impact = "Optimal (+10 points)"
        else:
            impact = "Neutral"

        print(f"  Active Loans: {n_active_loans}")
        print(f"  Credit Cards: {n_cards}")
        print(f"  Total Accounts: {total_accounts}")
        print(f"  Impact: {impact}")

        # 4. Recent Hard Inquiries
        print("\n[SEARCH] CREDIT INQUIRIES (Last 12 Months)")
        hard_inquiries = getattr(customer, "recent_hard_inquiries", [])
        recent_inquiries = [d for d in hard_inquiries if (today - d).days <= 365]
        n_recent = len(recent_inquiries)

        if n_recent > 3:
            impact = "Too many inquiries (-30 points)"
        elif n_recent > 0:
            impact = "Moderate impact"
        else:
            impact = "No recent inquiries"

        print(f"  Recent Inquiries: {n_recent}")
        if recent_inquiries:
            for idx, inquiry_date in enumerate(recent_inquiries[-5:], 1):
                days_ago = (today - inquiry_date).days
                print(f"    {idx}. {days_ago} days ago ({inquiry_date})")
        print(f"  Impact: {impact}")

        # 5. Credit Mix
        print("\n🎯 CREDIT MIX")
        account_types = set()
        for loan in loans:
            account_types.add("Loan")
        if n_cards > 0:  # Use n_cards from above
            account_types.add("Credit Card")

        if len(account_types) > 1:
            impact = "Good mix (+30 points)"
        else:
            impact = "Limited variety"

        print(
            f"  Account Types: {', '.join(account_types) if account_types else 'None'}"
        )
        print(f"  Impact: {impact}")

        # 6. Credit History Age
        print("\n📅 CREDIT HISTORY AGE")
        account_dates = []
        for loan in loans:
            if hasattr(loan, "start_date"):
                account_dates.append(loan.start_date)
        # Add credit card dates
        for acc in customer_accounts:
            for card in acc.cards:
                if isinstance(card, CreditCard):
                    # Cards don't have start_date, so use today as approximation
                    # or you can add a created_date attribute to cards
                    account_dates.append(BankClock.today())

        if account_dates:
            oldest = min(account_dates)
            age_years = (today - oldest).days // 365
            age_months = ((today - oldest).days % 365) // 30

            if age_years >= 3:
                impact = "Excellent (+20 points)"
            elif age_years >= 1:
                impact = "Good"
            else:
                impact = "New credit history"

            print(f"  Oldest Account: {age_years} years, {age_months} months")
            print(f"  Opened On: {oldest}")
            print(f"  Impact: {impact}")
        else:
            print("  Status: No credit history")
            print("  Impact: New to credit")

        # Loan History Details
        if loans:
            print("\n" + "-" * 70)
            print("DETAILED LOAN HISTORY")
            print("-" * 70)
            for idx, loan in enumerate(loans, 1):
                emis_paid = getattr(loan, "emis_paid", 0)
                total_emi = loan.tenure_months
                outstanding = total_emi - emis_paid
                print(f"\n{idx}. Loan ID: {loan.loan_id}")
                print(f"   Principal: ₹{loan.principal:,.2f}")
                print(f"   Interest Rate: {loan.interest_rate}% p.a.")
                print(f"   Tenure: {loan.tenure_months} months")
                print(f"   EMI Amount: ₹{loan.calculate_emi():,.2f}")
                if hasattr(loan, "start_date"):
                    print(f"   Activation Date: {loan.start_date}")
                print(f"   Status: {loan.status}")
                print(f"   EMIs Paid: {emis_paid}/{total_emi}")
                if loan.status == "Closed" or emis_paid >= total_emi:
                    if hasattr(loan, "closure_date"):
                        print(f"   [SUCCESS] Loan Closed On: {loan.closure_date}")
                    else:
                        print("   [SUCCESS] All EMIs Paid - Loan Fully Repaid")
                elif outstanding > 0:
                    print(f"   Outstanding EMIs: {outstanding}")
                    if hasattr(loan, "start_date"):
                        months_elapsed = (today.year - loan.start_date.year) * 12 + (
                            today.month - loan.start_date.month
                        )
                        expected_emis = min(months_elapsed + 1, loan.tenure_months)
                        if emis_paid < expected_emis:
                            missed = expected_emis - emis_paid
                            print(f"   [WARN]  Overdue EMIs: {missed}")

        # Score Range Guide
        print("\n" + "-" * 70)
        print("SCORE RANGE GUIDE")
        print("-" * 70)
        print("  300-549: Poor       - High risk, loans often denied")
        print("  550-649: Average    - Moderate risk, limited options")
        print("  650-749: Good       - Low risk, favorable terms")
        print("  750-900: Excellent  - Best rates and quick approvals")

        # Recommendations
        print("\n" + "-" * 70)
        print("RECOMMENDATIONS TO IMPROVE YOUR SCORE")
        print("-" * 70)
        recommendations = []

        if late_payments > 0:
            recommendations.append("[OK] Pay all pending EMIs on time")
        if credit_cards and utilization > 50:
            recommendations.append("[OK] Reduce credit card utilization below 30%")
        if n_recent > 3:
            recommendations.append("[OK] Avoid applying for new credit for 6 months")
        if total_accounts < 2:
            recommendations.append(
                "[OK] Consider diversifying credit types (loans + cards)"
            )
        if not recommendations:
            recommendations.append("[OK] Maintain current excellent credit behavior")
            recommendations.append("[OK] Continue making timely payments")

        for rec in recommendations:
            print(f"  {rec}")

        print("\n" + "=" * 70)

        # Save updated score
        self.bank.save()

    def generate_loan_closure_certificate(self, customer: Customer, account: Account):
        """Generate loan closure certificate for closed loans as PDF"""
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        closed_loans = [loan for loan in loans if loan.status == "Closed"]

        if not closed_loans:
            print(
                "\n[FAIL] No closed loans found. You can only generate certificates for fully repaid loans."
            )
            return

        print("\n=== Your Closed Loans ===")
        for idx, loan in enumerate(closed_loans, 1):
            closure_date = getattr(loan, "closure_date", "Not recorded")
            if closure_date != "Not recorded" and hasattr(closure_date, "strftime"):
                closure_date = closure_date.strftime("%d-%m-%Y")
            print(
                f"{idx}. Loan ID: {loan.loan_id} | Principal: Rs. {loan.principal:,.2f} | Closed: {closure_date}"
            )

        choice = self.read_valid_choice(
            f"\nSelect loan number (1-{len(closed_loans)}): ",
            [str(i) for i in range(1, len(closed_loans) + 1)],
        )

        selected_loan = closed_loans[int(choice) - 1]

        # Preview on console
        print("\n[INFO] Generating Official Loan Closure Certificate...")
        
        # Generate PDF
        save = input("\nDownload Loan Closure Certificate (NOC) as PDF? (yes/no): ").strip().lower()
        if save in ["yes", "y"]:
            try:
                from .StatementGenerator import StatementGenerator
                branch_details = Account.get_branch_details()
                filepath = StatementGenerator.generate_loan_closure_pdf(selected_loan, customer, branch_details)
                print(f"\n[SUCCESS] Official Loan Closure Certificate (NOC) generated: {filepath}")
            except Exception as e:
                print(f"[FAIL] Error generating certificate: {e}")
        else:
            print("[INFO] Download skipped.")


    def view_card_details(self, account: Account):
        """View detailed information about a specific card"""
        if not account.cards:
            print("No cards available")
            return

        print("\n--- View Card Details ---")
        account.list_cards()

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card:
            print("Card not found")
            return

        print("\n" + "=" * 60)
        print("CARD DETAILS")
        print("=" * 60)
        print(f"Card Type: {card.card_type}")
        print(f"Card Network: {card.network}")
        print(f"Card Number: **** **** **** {card.card_number[-4:]}")
        print(
            f"Full Card Number: {card.card_number}"
        )  # Show full number (in real banking, never show this!)
        print(f"CVV: {card.cvv}")  # Show CVV (in real banking, never show this!)
        print(f"Card ID: {card.card_id}")
        print(f"Expiry Date: {card.expiry_date.strftime('%m/%Y')}")
        print(
            f"Status: {'Blocked' if card.blocked else ('Expired' if card.is_expired() else 'Active')}"
        )
        print(f"Daily Limit: Rs. {card.daily_limit:,.2f} INR")

        if isinstance(card, CreditCard):
            print("\nCredit Card Specific Details:")
            print(f"Credit Limit: Rs. {card.credit_limit:,.2f} INR")
            print(f"Credit Used: Rs. {card.credit_used:,.2f} INR")
            print(f"Available Credit: Rs. {card.available_credit():,.2f} INR")
            print(f"Credit Utilization: {card.credit_utilization():.1f}%")
            print(f"Billing Day: {card.billing_day} of each month")
            print(f"Interest Rate: {card.interest_rate * 100:.1f}% per annum")
            reward_points = getattr(card, "reward_points", 0.0)
            print(f"Reward Points: {reward_points:.0f}")

            if card.outstanding_balance > 0:
                print("\nBilling Information:")
                print(f"Outstanding Balance: Rs. {card.outstanding_balance:,.2f} INR")
                print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")
                if card.due_date:

                    days_remaining = (card.due_date - BankClock.today()).days
                    print(
                        f"Due Date: {card.due_date.strftime('%d-%m-%Y')} ({days_remaining} days)"
                    )

        print("=" * 60)

        # Card validation
        is_valid = Card.validate_card_number(card.card_number)
        detected_network = Card.get_card_network(card.card_number)
        print(
            f"\n[OK] Card Number Validation: {'Valid' if is_valid else 'Invalid'} (Luhn Check)"
        )
        print(f"[OK] Detected Network from Number: {detected_network}")
        print("=" * 60)

    def manage_card_auto_pay(self, account: Account):
        """Manage auto-pay settings for credit cards"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards available")
            return

        print("\n" + "=" * 60)
        print("CREDIT CARD AUTO-PAY MANAGEMENT")
        print("=" * 60)
        print("\nYour Credit Cards:")

        for idx, card in enumerate(credit_cards, 1):
            policy = getattr(card, "auto_pay_policy", "NONE")
            policy_display = {
                "NONE": "[FAIL] Manual Payment",
                "MINIMUM": "[INFO] Auto-pay Minimum Due",
                "FULL": "[SUCCESS] Auto-pay Full Balance",
            }
            print(f"{idx}. **** **** **** {card.card_number[-4:]} ({card.network})")
            print(f"   Current: {policy_display.get(policy, 'Unknown')}")

        if len(credit_cards) == 1:
            selected_card = credit_cards[0]
        else:
            choice = input(
                f"\nSelect card to configure (1-{len(credit_cards)}): "
            ).strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(credit_cards):
                    selected_card = credit_cards[idx]
                else:
                    print("Invalid selection")
                    return
            except ValueError:
                print("Invalid input")
                return

        print("\n" + "=" * 60)
        print("AUTO-PAY POLICY OPTIONS")
        print("=" * 60)
        print("1. NONE - Manual payment only")
        print("   └─ You'll pay manually each month")
        print("2. MINIMUM - Auto-pay minimum due")
        print(
            "   └─ Minimum due automatically paid from your account when bill is generated"
        )
        print("3. FULL - Auto-pay full balance")
        print("   └─ Complete outstanding balance automatically paid from your account")
        print("=" * 60)

        policy_choice = self.read_valid_choice("Select policy (1-3): ", ["1", "2", "3"])
        policy_map = {"1": "NONE", "2": "MINIMUM", "3": "FULL"}
        new_policy = policy_map[policy_choice]

        old_policy = getattr(selected_card, "auto_pay_policy", "NONE")
        if old_policy == new_policy:
            print(f"\n[WARN]  Policy is already set to {new_policy}")
            return

        selected_card.auto_pay_policy = new_policy
        self.bank.save()

        print("\n" + "=" * 60)
        policy_display = {
            "NONE": "[FAIL] Manual Payment",
            "MINIMUM": "[INFO] Auto-pay Minimum Due",
            "FULL": "[SUCCESS] Auto-pay Full Balance",
        }

        print("[SUCCESS] AUTO-PAY POLICY UPDATED")
        print(
            f"Card: **** **** **** {selected_card.card_number[-4:]} ({selected_card.network})"
        )
        print(f"New Policy: {policy_display[new_policy]}")
        print("=" * 60)

        if new_policy == "NONE":
            print("\nℹ️  You'll need to pay your credit card bill manually each month.")
        elif new_policy == "MINIMUM":
            print("\nℹ️  Minimum due will be automatically deducted from your account")
            print("   when your monthly bill is generated (on billing day).")
            print("   Make sure you have sufficient balance in your account.")
        else:  # FULL
            print(
                "\nℹ️  Your complete outstanding balance will be automatically deducted"
            )
            print("   from your account when the bill is generated.")
            print("   This helps avoid interest charges and late payment fees.")
        print("=" * 60)

    def _get_loan_by_id(self, loan_id: str):
        """Helper method to find a loan by ID from the loans list"""
        for loan in self.bank.loans:
            if loan.loan_id == loan_id:
                return loan
        return None

    def loan_nach_mandate_menu(self, customer: Customer, account: Account):
        """NACH Mandate Management submenu for loan EMI automation"""
        self.current_customer = customer  # Set for use in helper methods

        while True:
            print("\n" + "=" * 60)
            print("[BANK] NACH MANDATE MANAGEMENT (Automatic EMI Deduction)")
            print("=" * 60)

            # Check if customer has any active loans
            active_loans = [
                loan
                for loan in self.bank.get_loans_for_customer(customer.customer_id)
                if loan.status == "Active"
            ]
            if not active_loans:
                print("\n[WARN]  You don't have any active loans.")
                print("NACH mandates can only be created for active loans.\n")
                input("Press Enter to continue...")
                break

            print("\n1. Create NACH Mandate")
            print("2. Verify NACH Mandate (OTP)")
            print("3. View All NACH Mandates")
            print("4. Revoke NACH Mandate")
            print("5. Suspend NACH Mandate")
            print("6. Resume NACH Mandate")
            print("7. View Mandate Details & Deduction History")
            print("8. Back to Loan Menu")

            choice = input("\nSelect option (1-8): ").strip()

            if choice == "1":
                self.create_loan_nach_mandate()
            elif choice == "2":
                self.verify_loan_nach_mandate_otp()
            elif choice == "3":
                self.view_loan_mandates()
            elif choice == "4":
                self.revoke_loan_nach_mandate()
            elif choice == "5":
                self.suspend_loan_nach_mandate()
            elif choice == "6":
                self.resume_loan_nach_mandate()
            elif choice == "7":
                self.view_mandate_details()
            elif choice == "8":
                break
            else:
                print("[FAIL] Invalid option. Please try again.")

    def create_loan_nach_mandate(self):
        """Create a new NACH mandate for automatic EMI deduction"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[INFO] CREATE NACH MANDATE FOR AUTOMATIC EMI DEDUCTION")
        print("=" * 60)

        # Display active loans
        active_loans = [
            loan
            for loan in self.bank.get_loans_for_customer(customer.customer_id)
            if loan.status == "Active"
        ]

        if not active_loans:
            print("\n[WARN]  No active loans available.")
            input("Press Enter to continue...")
            return

        print("\n📌 Your Active Loans:")
        for idx, loan in enumerate(active_loans, 1):
            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Amount: ₹{loan.calculate_emi():,.2f} (Monthly EMI)")
            print(f"   Tenure: {loan.tenure_months} months")
            print(f"   Interest Rate: {loan.interest_rate}%")
            if hasattr(loan, "nach_mandate_id") and loan.nach_mandate_id:
                mandate = LoanNachMandateManager.get_loan_mandate(loan.loan_id)
                if mandate:
                    print(f"   Status: {mandate.status}")

        loan_choice = input("\nSelect loan number: ").strip()

        try:
            loan_idx = int(loan_choice) - 1
            if 0 <= loan_idx < len(active_loans):
                selected_loan = active_loans[loan_idx]
            else:
                print("[FAIL] Invalid loan selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Check if mandate already exists
        existing_mandate = LoanNachMandateManager.get_loan_mandate(
            selected_loan.loan_id
        )
        if existing_mandate:
            print("\n[WARN]  A NACH mandate already exists for this loan.")
            print(f"   Current Status: {existing_mandate.status}")
            if existing_mandate.status in ["Pending", "OTP_Verified"]:
                proceed = (
                    input("\nDo you want to create a new mandate? (yes/no): ")
                    .strip()
                    .lower()
                )
                if proceed != "yes":
                    return

        # Get debit account
        print("\n📌 Select Account for EMI Deduction:")
        customer_accounts = self.bank.get_customer_accounts(customer)
        for idx, acc in enumerate(customer_accounts, 1):
            balance = acc.balance
            print(
                f"{idx}. {acc.account_number} ({acc.account_type}) - Balance: ₹{balance:,.2f}"
            )

        acc_choice = input("\nSelect account number: ").strip()

        selected_account = None
        for acc in customer_accounts:
            if acc.account_number == acc_choice:
                selected_account = acc
                break

        if not selected_account:
            print("[FAIL] Invalid account selection.")
            return

        # Confirm NACH mandate details
        print("\n" + "=" * 60)
        print("[INFO] NACH MANDATE DETAILS")
        print("=" * 60)
        print(f"\nLoan ID: {selected_loan.loan_id}")
        print(f"Loan Amount: ₹{selected_loan.principal:,.2f}")
        print(f"Monthly EMI: ₹{selected_loan.calculate_emi():,.2f}")
        print(f"Tenure: {selected_loan.tenure_months} months")
        print(
            f"Max Debit Limit: ₹{selected_loan.calculate_emi() * 1.5:,.2f} (1.5x safety buffer)"
        )
        print(f"Debit Account: {selected_account.account_number}")

        confirm = (
            input("\n[OK] Proceed with NACH mandate creation? (yes/no): ").strip().lower()
        )
        if confirm != "yes":
            print("[FAIL] Mandate creation cancelled.")
            return

        # Calculate mandate end date (when loan EMI payments end)
        from datetime import datetime, timedelta

        start_date = datetime.now().strftime("%d-%m-%Y")
        loan_end_date = datetime.now() + timedelta(
            days=30 * selected_loan.tenure_months
        )
        end_date = loan_end_date.strftime("%d-%m-%Y")

        # Create mandate with all required parameters
        success, message, mandate_id, otp = LoanNachMandateManager.create_mandate(
            loan_id=selected_loan.loan_id,
            customer_id=customer.customer_id,
            account_number=selected_account.account_number,
            debit_account=selected_account.account_number,
            debit_ifsc="PYTHONIFIED001",  # Default bank IFSC code
            emi_amount=selected_loan.calculate_emi(),
            start_date=start_date,
            end_date=end_date,
        )

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] NACH MANDATE CREATED SUCCESSFULLY")
            print("=" * 60)
            print(f"\nMandate ID: {mandate_id}")
            print("Status: Pending (OTP Verification Required)")
            print("\n📱 OTP sent to registered mobile number")
            print(f"🔐 Verification Code: {otp} (for testing purposes)")
            print("\nPlease verify your mandate with the OTP to activate it.")

            # Update loan with mandate ID
            selected_loan.nach_mandate_id = mandate_id
            self.bank.save_data()
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def verify_loan_nach_mandate_otp(self):
        """Verify NACH mandate with OTP"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("🔐 VERIFY NACH MANDATE (OTP)")
        print("=" * 60)

        # Display pending mandates
        pending_mandates = []
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        for mandate in all_mandates:
            if mandate.status in ["Pending", "OTP_Verified"]:
                # Find the corresponding loan
                loan = self._get_loan_by_id(mandate.loan_id)
                if loan:
                    pending_mandates.append((loan, mandate))

        if not pending_mandates:
            print("\n[WARN]  No pending NACH mandates to verify.")
            input("Press Enter to continue...")
            return

        print("\n📌 Pending NACH Mandates:")
        for idx, (loan, mandate) in enumerate(pending_mandates, 1):
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan.loan_id}")
            print(f"   Status: {mandate.status}")
            print(f"   EMI Amount: ₹{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pending_mandates):
                selected_loan, selected_mandate = pending_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Request OTP
        print(f"\n[INFO] Mandate ID: {selected_mandate.mandate_id}")
        print("🔐 Enter the OTP sent to your registered mobile number:")

        otp_attempts = 0
        max_attempts = 3

        while otp_attempts < max_attempts:
            otp = input("\nEnter OTP (6 digits): ").strip()

            success, message = LoanNachMandateManager.verify_mandate_otp(
                selected_mandate.mandate_id, otp
            )

            if success:
                print("\n" + "=" * 60)
                print("[SUCCESS] OTP VERIFIED SUCCESSFULLY")
                print("=" * 60)
                print(f"\nMandate ID: {selected_mandate.mandate_id}")
                print("Status: ACTIVE")
                print(f"EMI Amount: ₹{selected_mandate.emi_amount:,.2f}")
                print(f"Account: {selected_mandate.bank_account_number}")
                print("\n[OK] NACH mandate is now active.")
                print("[OK] EMI will be deducted automatically from your account.")
                print("[OK] Deduction History: Available in 'View Mandate Details' menu")

                break
            else:
                otp_attempts += 1
                remaining = max_attempts - otp_attempts
                if remaining > 0:
                    print(f"\n[FAIL] {message}")
                    print(f"[WARN]  Remaining attempts: {remaining}")
                else:
                    print(f"\n[FAIL] {message}")
                    print(
                        "[FAIL] Maximum OTP attempts exceeded. Mandate creation cancelled."
                    )
                    # Reset mandate status
                    selected_mandate.status = "Revoked"
                    LoanNachMandateManager._save_mandates()

        input("\nPress Enter to continue...")

    def view_loan_mandates(self):
        """View all NACH mandates for customer"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[INFO] YOUR NACH MANDATES")
        print("=" * 60)

        # Get all mandates using the manager
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )

        if not all_mandates:
            print("\n[WARN]  You don't have any NACH mandates.")
            print("\n💡 Create a NACH mandate to set up automatic EMI deductions.")
        else:
            print("\n")
            mandate_count = {}
            for mandate in all_mandates:
                status = mandate.status
                mandate_count[status] = mandate_count.get(status, 0) + 1

                # Status icon
                status_icon = (
                    "[SUCCESS]"
                    if status == NachMandateStatus.ACTIVE
                    else "⏳"
                    if status == NachMandateStatus.PENDING
                    else "[FAIL]"
                    if status == NachMandateStatus.REVOKED
                    else "[WARN]"
                )

                # Get loan details
                loan = self._get_loan_by_id(mandate.loan_id)
                loan_id = loan.loan_id if loan else mandate.loan_id

                print(f"{status_icon} Loan ID: {loan_id}")
                print(f"   Mandate ID: {mandate.mandate_id}")
                print(f"   Status: {status}")
                print(f"   EMI Amount: ₹{mandate.emi_amount:,.2f}")
                print(f"   Account: {mandate.bank_account_number}")
                print(f"   Period: {mandate.start_date} to {mandate.end_date}")
                print(f"   Deductions Processed: {len(mandate.deduction_history)}")
                print()

            print("=" * 60)
            print("[STATS] MANDATE SUMMARY")
            print("=" * 60)
            for status, count in mandate_count.items():
                if count > 0:
                    print(f"{status}: {count}")

        input("\nPress Enter to continue...")

    def revoke_loan_nach_mandate(self):
        """Revoke a NACH mandate"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("🛑 REVOKE NACH MANDATE")
        print("=" * 60)

        # Get all non-revoked mandates
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        revokable_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status != NachMandateStatus.REVOKED
        ]

        if not revokable_mandates:
            print("\n[WARN]  No active NACH mandates to revoke.")
            input("Press Enter to continue...")
            return

        print("\n📌 NACH Mandates:")
        for idx, (mandate, loan) in enumerate(revokable_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   Status: {mandate.status}")
            print(f"   EMI: ₹{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to revoke (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(revokable_mandates):
                selected_mandate, selected_loan = revokable_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Confirm revocation
        print(
            "\n[WARN]  IMPORTANT: Revoking this mandate will stop automatic EMI deductions."
        )
        print("   You will need to pay EMIs manually.")
        confirm = input("\nProceed with mandate revocation? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("[FAIL] Revocation cancelled.")
            return

        # Revoke mandate
        success, message = LoanNachMandateManager.revoke_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: REVOKED")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def suspend_loan_nach_mandate(self):
        """Suspend a NACH mandate temporarily"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[VIRTUAL]  SUSPEND NACH MANDATE")
        print("=" * 60)

        # Get active mandates
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        suspendable_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status == NachMandateStatus.ACTIVE
        ]

        if not suspendable_mandates:
            print("\n[WARN]  No active NACH mandates to suspend.")
            input("Press Enter to continue...")
            return

        print("\n📌 Active NACH Mandates:")
        for idx, (mandate, loan) in enumerate(suspendable_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   EMI: ₹{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to suspend (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suspendable_mandates):
                selected_mandate, selected_loan = suspendable_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        print("\n[WARN]  Suspending this mandate will temporarily stop EMI deductions.")
        confirm = input("Proceed? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("[FAIL] Suspension cancelled.")
            return

        # Suspend mandate
        success, message = LoanNachMandateManager.suspend_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: SUSPENDED")
            print("\n💡 Use 'Resume NACH Mandate' to reactivate it.")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def resume_loan_nach_mandate(self):
        """Resume a suspended NACH mandate"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("▶️  RESUME NACH MANDATE")
        print("=" * 60)

        # Get suspended mandates
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        suspended_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status == NachMandateStatus.SUSPENDED
        ]

        if not suspended_mandates:
            print("\n[WARN]  No suspended NACH mandates to resume.")
            input("Press Enter to continue...")
            return

        print("\n📌 Suspended NACH Mandates:")
        for idx, (mandate, loan) in enumerate(suspended_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   EMI: ₹{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to resume (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suspended_mandates):
                selected_mandate, selected_loan = suspended_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        confirm = (
            input("\nProceed with resuming this mandate? (yes/no): ").strip().lower()
        )

        if confirm != "yes":
            print("[FAIL] Resume cancelled.")
            return

        # Resume mandate
        success, message = LoanNachMandateManager.resume_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: ACTIVE")
            print("\n[OK] EMI deductions will resume automatically.")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def view_mandate_details(self):
        """View detailed information about a NACH mandate including deduction history"""

        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[STATS] NACH MANDATE DETAILS & DEDUCTION HISTORY")
        print("=" * 60)

        # Get all mandates
        all_mandates = []
        customer_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        for mandate in customer_mandates:
            loan = self._get_loan_by_id(mandate.loan_id)
            if loan:
                all_mandates.append((loan, mandate))

        if not all_mandates:
            print("\n[WARN]  No NACH mandates found.")
            input("Press Enter to continue...")
            return

        print("\n📌 Select a Mandate:")
        for idx, (loan, mandate) in enumerate(all_mandates, 1):
            print(f"{idx}. {mandate.mandate_id} ({mandate.status})")

        choice = input("\nSelect mandate (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_mandates):
                selected_loan, selected_mandate = all_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Display mandate details
        print("\n" + "=" * 60)
        print("[INFO] MANDATE INFORMATION")
        print("=" * 60)
        print(f"\nMandate ID: {selected_mandate.mandate_id}")
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Status: {selected_mandate.status}")
        print(f"Created: {selected_mandate.creation_timestamp}")
        print("\n[MONEY] AMOUNT DETAILS")
        print(f"EMI Amount: ₹{selected_mandate.emi_amount:,.2f}")
        print(f"Max Debit Limit: ₹{selected_mandate.max_debit_amount:,.2f}")
        print("\n📅 PERIOD")
        print(f"Start Date: {selected_mandate.start_date}")
        print(f"End Date: {selected_mandate.end_date}")
        print("\n🔐 ACCOUNT DETAILS")
        print(f"Debit Account: {selected_mandate.bank_account_number}")

        # Display deduction history
        if selected_mandate.deduction_history:
            print(
                f"\n[STATS] DEDUCTION HISTORY ({len(selected_mandate.deduction_history)} deductions)"
            )
            print("=" * 60)

            total_deducted = 0
            for idx, deduction in enumerate(
                selected_mandate.deduction_history[:20], 1
            ):  # Show last 20
                status_icon = (
                    "[SUCCESS]"
                    if deduction["status"] == "Success"
                    else "[FAIL]"
                    if deduction["status"] == "Failed"
                    else "⏳"
                )
                print(f"\n{idx}. {status_icon} {deduction['date']}")
                print(f"   Amount: ₹{deduction['amount']:,.2f}")
                print(f"   Status: {deduction['status']}")
                if deduction["status"] == "Success":
                    total_deducted += deduction["amount"]

            if len(selected_mandate.deduction_history) > 20:
                print(
                    f"\n...and {len(selected_mandate.deduction_history) - 20} more deductions"
                )

            print("\n" + "=" * 60)
            print(f"Total Deducted: ₹{total_deducted:,.2f}")
        else:
            print("\n⏳ No deductions yet.")

        input("\nPress Enter to continue...")

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
                print("\n💳 Fees & Charges:")
                account.show_transactions(limit=limit, transaction_type_filter="FEES")
            elif choice == "20":
                break
            else:
                print("Invalid choice")

    def view_debit_card_transactions(self, account: Account):
        """View transactions by specific debit card"""

        # Load transactions if needed
        account._load_transactions_if_needed()

        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n[FAIL] No debit cards found")
            return

        print("\n--- Select Debit Card ---")
        print("0. All Debit Cards")
        for idx, card in enumerate(debit_cards, 1):
            print(f"{idx}. {card.network} **** **** **** {card.card_number[-4:]}")

        choice_input = input("\nEnter choice: ").strip()

        # Get limit preference
        limit = self._get_transaction_limit()

        if choice_input == "0":
            # Show all debit card transactions
            account.show_transactions(limit=limit, transaction_type_filter="DEBIT_CARD")
        else:
            # Find specific card
            selected_card = None
            if choice_input.isdigit() and 1 <= int(choice_input) <= len(debit_cards):
                selected_card = debit_cards[int(choice_input) - 1]
            else:
                for card in debit_cards:
                    if card.card_number[-4:] == choice_input:
                        selected_card = card
                        break

            if not selected_card:
                print("[FAIL] Card not found")
                return

            print(
                f"\n💳 Transactions for debit card ending in {selected_card.card_number[-4:]}:"
            )
            account.show_transactions(
                limit=limit, card_filter=selected_card.card_number[-4:]
            )

    def view_credit_card_transactions(self, account: Account):
        """View credit card payment transactions"""
        # Load transactions if needed
        account._load_transactions_if_needed()

        limit = self._get_transaction_limit()
        print("\n💳 Credit Card Payments:")
        account.show_transactions(
            limit=limit, transaction_type_filter="CREDIT_CARD_PAYMENT"
        )

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

    def _get_transaction_limit(self) -> int:
        """Helper method to get transaction limit preference"""
        print("\nHow many transactions?")
        print("1. Last 10")
        print("2. Last 20")
        print("3. Last 50")
        print("4. All")

        choice = input("Enter choice (default: 10): ").strip()
        limit_map = {"1": 10, "2": 20, "3": 50, "4": None}
        return limit_map.get(choice, 10)

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

        print("=" * 70)

    def view_swift_transactions(self, account: Account):
        """View all SWIFT/international transfers"""

        # Load transactions if needed
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
                except:
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
        print("=" * 100)

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

        # Show metadata for international transfers
        metadata = self._parse_metadata(txn.metadata)
        
        if txn.type == "SWIFT_SENT" and metadata:
            print("\n" + "-" * 80)
            print("INTERNATIONAL TRANSFER DETAILS")
            print("-" * 80)
            print(f"SWIFT Reference:    {metadata.get('swift_reference', metadata.get('swiftRef', 'N/A'))}")
            print(f"Recipient Name:     {metadata.get('recipient_name', 'N/A')}")
            print(f"Recipient Account:  {metadata.get('recipient_account', 'N/A')}")
            print(f"Bank:               {metadata.get('recipient_bank', 'N/A')}")
            print(f"SWIFT Code:         {metadata.get('swift_code', 'N/A')}")
            print(f"Country:            {metadata.get('country', 'N/A')}")

            currency = metadata.get("currency", "")
            try:
                amount_foreign = float(metadata.get("amount_foreign", metadata.get("foreignAmt", 0)))
                exchange_rate = float(metadata.get("exchange_rate", metadata.get("rate", 0)))
            except:
                amount_foreign = 0
                exchange_rate = 0

            print(f"\nAmount Sent:        {amount_foreign:,.2f} {currency}")
            print(f"Exchange Rate:      1 {currency} = Rs. {exchange_rate:,.2f}")
            print(f"Amount in INR:      Rs. {amount_foreign * exchange_rate:,.2f}")
            print(
                f"SWIFT Charges:      Rs. {float(metadata.get('swift_charges', metadata.get('charges', 0))):,.2f}"
            )
            print(f"Purpose:            {metadata.get('purpose', 'N/A')}")
            print(f"Expected Arrival:   {metadata.get('expected_arrival', 'N/A')}")

            if metadata.get("recipient_address"):
                print(f"Recipient Address:  {metadata.get('recipient_address')}")

        # Show metadata for other transaction types if available
        elif metadata:
            print("\n" + "-" * 80)
            print("ADDITIONAL DETAILS")
            print("-" * 80)
            for key, value in metadata.items():
                # Format key nicely
                formatted_key = key.replace("_", " ").title()
                print(f"{formatted_key:<20}: {value}")

        print("=" * 80)
        input("\nPress Enter to continue...")

    def fd_rd_menu(self, customer: Customer, account: Account):
        """Fixed Deposit and Recurring Deposit Management Menu"""

        while True:
            print("\n" + "=" * 70)
            print("FIXED DEPOSITS & RECURRING DEPOSITS")
            print("=" * 70)
            print("""
Choose an option:
1 Open Fixed Deposit (FD)
2 Open Recurring Deposit (RD)
3 View My FDs
4 View My RDs
5 Pay RD Installment (Manual)
6 Enable/Disable RD Autopay
7 Close FD (Premature)
8 Close RD (Premature)
9 Mature FD
10 Mature RD
11 View FD Details
12 View RD Details
13 RD Authorization Management
14 View RD Statement of Account
15 Download FD Statement (PDF)
16 Download RD Statement (PDF)
17 Back to Main Menu
            """)

            choice = self.read_valid_choice(
                "Enter your choice: ",
                [str(i) for i in range(1, 18)],
                "Invalid choice. Please enter a number from 1 to 17.",
            )

            if choice == "1":
                self.open_fixed_deposit(account)
            elif choice == "2":
                self.open_recurring_deposit(account)
            elif choice == "3":
                self.view_my_fds(account)
            elif choice == "4":
                self.view_my_rds(account)
            elif choice == "5":
                self.pay_rd_installment(account)
            elif choice == "6":
                self.manage_rd_autopay(account)
            elif choice == "7":
                self.close_fd_premature(account)
            elif choice == "8":
                self.close_rd_premature(account)
            elif choice == "9":
                self.mature_fd(account)
            elif choice == "10":
                self.mature_rd(account)
            elif choice == "11":
                self.view_fd_details(account)
            elif choice == "12":
                self.view_rd_details(account)
            elif choice == "13":
                self.rd_authorization_menu(customer, account)
            elif choice == "14":
                self.view_rd_statement(customer, account)
            elif choice == "15":
                self.download_fd_statement(customer, account)
            elif choice == "16":
                self.download_rd_statement(customer, account)
            elif choice == "17":
                break

    def download_loan_statement(self, customer: Customer, account: Account):
        """Download Loan Statement as PDF"""
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("\n[INFO] No active loans found.")
            return

        print("\nSelect Loan for Statement:")
        for idx, loan in enumerate(loans, 1):
            print(f"{idx}. {loan.loan_id} ({loan.loan_type}) - Rs. {loan.principal:,.2f}")

        choice = input(f"\nEnter choice (1-{len(loans)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(loans):
            selected_loan = loans[int(choice) - 1]
            from .StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_loan_soa(selected_loan, customer)
            print(f"\n[SUCCESS] Loan Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")

    def download_fd_statement(self, customer: Customer, account: Account):
        """Download FD Statement as PDF"""
        if not hasattr(self.bank, "fixed_deposits"):
            print("\n[INFO] No FDs found.")
            return
            
        my_fds = [fd for fd in self.bank.fixed_deposits.values() if fd.account_number == account.account_number]
        if not my_fds:
            print("\n[INFO] No active FDs found for this account.")
            return

        print("\nSelect FD for Statement:")
        for idx, fd in enumerate(my_fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f} ({fd.status})")

        choice = input(f"\nEnter choice (1-{len(my_fds)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(my_fds):
            selected_fd = my_fds[int(choice) - 1]
            from .StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_fd_soa(selected_fd, customer)
            print(f"\n[SUCCESS] FD Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")

    def download_rd_statement(self, customer: Customer, account: Account):
        """Download RD Statement as PDF"""
        from .RDStatement import RDStatement
        rd_stmt_helper = RDStatement(self.bank)
        statements = rd_stmt_helper.get_all_rd_statements(account.account_number)
        
        if not statements:
            print("\n[INFO] No active RDs found for this account.")
            return

        print("\nSelect RD for Statement:")
        for idx, stmt in enumerate(statements, 1):
            print(f"{idx}. {stmt['rd_number']} - Rs. {stmt['monthly_installment']:,.2f} ({stmt['status']})")

        choice = input(f"\nEnter choice (1-{len(statements)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(statements):
            selected_stmt = statements[int(choice) - 1]
            from .StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_rd_soa(selected_stmt, customer)
            print(f"\n[SUCCESS] RD Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")


    def open_fixed_deposit(self, account: Account):
        """Open a new Fixed Deposit"""
        print("\n" + "=" * 70)
        print("OPEN FIXED DEPOSIT")
        print("=" * 70)

        print(f"\nCurrent Balance: Rs. {account.balance:,.2f}")
        print(f"Minimum Balance Required: Rs. {account._min_operational_balance:,.2f}")
        print("\nAvailable Tenures and Interest Rates:")
        print("-" * 70)

        from datetime import datetime

        # Check if senior citizen - FIX: Get from customer
        is_senior = False
        customer = self.bank.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior = age >= 60
            except (ValueError, AttributeError):
                pass

        for tenure, rate in sorted(FixedDeposit.INTEREST_RATES.items()):
            senior_rate = (
                rate + FixedDeposit.SENIOR_CITIZEN_BONUS if is_senior else rate
            )
            senior_info = f" (Senior Citizen: {senior_rate}%)" if is_senior else ""
            print(f"  {tenure:2d} months: {rate}% p.a.{senior_info}")

        print("-" * 70)
        print(f"Minimum Amount: Rs. {FixedDeposit.MIN_AMOUNT:,.2f}")
        print(f"Maximum Amount: Rs. {FixedDeposit.MAX_AMOUNT:,.2f}")

        # Get amount
        try:
            amount = float(
                input(
                    f"\nEnter FD amount (Rs. {FixedDeposit.MIN_AMOUNT:,.2f} - {FixedDeposit.MAX_AMOUNT:,.2f}): "
                )
            )
        except ValueError:
            print("[FAIL] Invalid amount")
            return

        # Get tenure
        valid_tenures = list(FixedDeposit.INTEREST_RATES.keys())
        print(f"\nAvailable tenures: {', '.join(str(t) for t in valid_tenures)} months")
        try:
            tenure = int(input("Enter tenure in months: "))
        except ValueError:
            print("[FAIL] Invalid tenure")
            return

        # Show calculation
        if tenure in FixedDeposit.INTEREST_RATES:
            rate = FixedDeposit.get_applicable_rate(tenure, is_senior)

            # Calculate maturity amount preview
            n = 4  # Quarterly
            t = tenure / 12
            maturity = amount * ((1 + rate / 100 / n) ** (n * t))
            interest = maturity - amount

            print("\n" + "-" * 70)
            print("FD PREVIEW")
            print("-" * 70)
            print(f"Principal Amount: Rs. {amount:,.2f}")
            print(f"Interest Rate: {rate}% p.a.")
            print(f"Tenure: {tenure} months")
            print(f"Expected Interest: Rs. {interest:,.2f}")
            print(f"Maturity Amount: Rs. {maturity:,.2f}")
            print("-" * 70)

        confirm = input("\nConfirm FD creation? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] FD creation cancelled")
            return

        # Create FD
        success, message, fd = self.bank.create_fixed_deposit(account, amount, tenure)

        if success:
            print(message)
            self.bank.save()
        else:
            print(f"\n[FAIL] Failed to create FD: {message}")

    def open_recurring_deposit(self, account: Account):
        """Open a new Recurring Deposit"""
        print("\n" + "=" * 70)
        print("OPEN RECURRING DEPOSIT")
        print("=" * 70)

        print(f"\nCurrent Balance: Rs. {account.balance:,.2f}")
        print("\nAvailable Tenures and Interest Rates:")
        print("-" * 70)

        from datetime import datetime

        # Check if senior citizen - FIX: Get from customer
        is_senior = False
        customer = self.bank.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior = age >= 60
            except (ValueError, AttributeError):
                pass

        for tenure, rate in sorted(RecurringDeposit.INTEREST_RATES.items()):
            senior_rate = (
                rate + RecurringDeposit.SENIOR_CITIZEN_BONUS if is_senior else rate
            )
            senior_info = f" (Senior Citizen: {senior_rate}%)" if is_senior else ""
            print(f"  {tenure:2d} months: {rate}% p.a.{senior_info}")

        print("-" * 70)
        print(
            f"Minimum Monthly Installment: Rs. {RecurringDeposit.MIN_MONTHLY_AMOUNT:,.2f}"
        )
        print(
            f"Maximum Monthly Installment: Rs. {RecurringDeposit.MAX_MONTHLY_AMOUNT:,.2f}"
        )

        # Get monthly installment
        try:
            monthly = float(input("\nEnter monthly installment: "))
        except ValueError:
            print("[FAIL] Invalid amount")
            return

        # Get tenure
        valid_tenures = list(RecurringDeposit.INTEREST_RATES.keys())
        print(f"\nAvailable tenures: {', '.join(str(t) for t in valid_tenures)} months")
        try:
            tenure = int(input("Enter tenure in months: "))
        except ValueError:
            print("[FAIL] Invalid tenure")
            return

        # Show calculation
        if tenure in RecurringDeposit.INTEREST_RATES:
            rate = RecurringDeposit.get_applicable_rate(tenure, is_senior)

            # Calculate maturity amount preview
            P = monthly
            n = tenure
            r = rate
            interest = (P * n * (n + 1) * r) / 2400
            maturity = (P * n) + interest

            print("\n" + "-" * 70)
            print("RD PREVIEW")
            print("-" * 70)
            print(f"Monthly Installment: Rs. {monthly:,.2f}")
            print(f"Interest Rate: {rate}% p.a.")
            print(f"Tenure: {tenure} months")
            print(f"Total Investment: Rs. {monthly * tenure:,.2f}")
            print(f"Expected Interest: Rs. {interest:,.2f}")
            print(f"Maturity Amount: Rs. {maturity:,.2f}")
            print("-" * 70)

        # Autopay option
        enable_autopay = input("\nEnable autopay? (yes/no): ").strip().lower() in [
            "yes",
            "y",
        ]
        autopay_day = 1

        if enable_autopay:
            try:
                autopay_day = int(input("Enter autopay day (1-28): "))
                if autopay_day < 1 or autopay_day > 28:
                    print("[FAIL] Invalid day. Using default day 1")
                    autopay_day = 1
            except ValueError:
                print("[FAIL] Invalid input. Using default day 1")
                autopay_day = 1

        confirm = input("\nConfirm RD creation? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] RD creation cancelled")
            return

        # Create RD
        success, message, rd = self.bank.create_recurring_deposit(
            account, monthly, tenure, enable_autopay, autopay_day
        )

        if success:
            print(message)
            self.bank.save()
        else:
            print(f"\n[FAIL] Failed to create RD: {message}")

    def view_my_fds(self, account: Account):
        """View all FDs for current account"""
        fds = self.bank.get_fds_for_account(account.account_number)

        if not fds:
            print("\n📭 No Fixed Deposits found")
            return

        print("\n" + "=" * 100)
        print(f"YOUR FIXED DEPOSITS - Account: {account.account_number}")
        print("=" * 100)
        print(
            f"{'FD Number':<20} {'Principal':<15} {'Rate':<8} {'Tenure':<10} {'Maturity':<15} {'Status':<20}"
        )
        print("-" * 100)

        for fd in fds:
            status = fd.get_status_string()
            print(
                f"{fd.fd_number:<20} Rs. {fd.principal_amount:>10,.2f} {fd.interest_rate:>5.2f}% {fd.tenure_months:>3d} months Rs. {fd.maturity_amount:>10,.2f} {status:<20}"
            )

        print("-" * 100)
        print(f"Total FDs: {len(fds)}")
        print("=" * 100)

    def view_my_rds(self, account: Account):
        """View all RDs for current account"""
        rds = self.bank.get_rds_for_account(account.account_number)

        if not rds:
            print("\n📭 No Recurring Deposits found")
            return

        print("\n" + "=" * 110)
        print(f"YOUR RECURRING DEPOSITS - Account: {account.account_number}")
        print("=" * 110)
        print(
            f"{'RD Number':<20} {'Monthly':<15} {'Rate':<8} {'Paid':<15} {'Status':<25} {'Autopay':<10}"
        )
        print("-" * 110)

        for rd in rds:
            status = rd.get_payment_status()
            autopay = "[OK] Yes" if rd.autopay_enabled else "No"
            print(
                f"{rd.rd_number:<20} Rs. {rd.monthly_installment:>10,.2f} {rd.interest_rate:>5.2f}% {rd.installments_paid:>2d}/{rd.tenure_months:<2d} months {status:<25} {autopay:<10}"
            )

        print("-" * 110)
        print(f"Total RDs: {len(rds)}")
        print("=" * 110)

    def pay_rd_installment(self, account: Account):
        """Pay RD installment manually"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status == "Active"]

        if not active_rds:
            print("\n📭 No active RDs found")
            return

        print("\n" + "=" * 80)
        print("PAY RD INSTALLMENT")
        print("=" * 80)

        print("\nActive RDs:")
        for idx, rd in enumerate(active_rds, 1):
            print(
                f"{idx}. {rd.rd_number} - Rs. {rd.monthly_installment:,.2f}/month ({rd.installments_paid}/{rd.tenure_months} paid)"
            )

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        rd = active_rds[choice - 1]

        print(f"\nRD: {rd.rd_number}")
        print(f"Monthly Installment: Rs. {rd.monthly_installment:,.2f}")
        print(f"Installments Paid: {rd.installments_paid}/{rd.tenure_months}")
        print(f"Your Balance: Rs. {account.balance:,.2f}")

        confirm = input("\nPay installment? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] Payment cancelled")
            return

        success, message = rd.pay_installment_manual(account)

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            self.bank.save()
        else:
            print(f"\n[FAIL] {message}")

    def manage_rd_autopay(self, account: Account):
        """Enable/Disable RD Autopay"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status == "Active"]

        if not active_rds:
            print("\n📭 No active RDs found")
            return

        print("\n" + "=" * 80)
        print("MANAGE RD AUTOPAY")
        print("=" * 80)

        print("\nActive RDs:")
        for idx, rd in enumerate(active_rds, 1):
            autopay = "[OK] Enabled" if rd.autopay_enabled else "✗ Disabled"
            print(f"{idx}. {rd.rd_number} - {autopay}")

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        rd = active_rds[choice - 1]

        if rd.autopay_enabled:
            print("\nAutopay is currently ENABLED")
            print(f"Autopay Day: {rd.autopay_day}")
            print(
                f"Next Autopay: {rd.next_autopay_date.strftime('%d-%m-%Y') if rd.next_autopay_date else 'N/A'}"
            )

            action = input("\nDisable autopay? (yes/no): ").strip().lower()
            if action in ["yes", "y"]:
                success, message = rd.disable_autopay()
                print(f"\n{'[SUCCESS]' if success else '[FAIL]'} {message}")
                if success:
                    self.bank.save()
        else:
            print("\nAutopay is currently DISABLED")
            action = input("\nEnable autopay? (yes/no): ").strip().lower()
            if action in ["yes", "y"]:
                try:
                    day = int(input("Enter autopay day (1-28): "))
                except ValueError:
                    day = 1

                success, message = rd.enable_autopay(day)
                print(f"\n{'[SUCCESS]' if success else '[FAIL]'} {message}")
                if success:
                    self.bank.save()

    def close_fd_premature(self, account: Account):
        """Close FD before maturity"""
        fds = self.bank.get_fds_for_account(account.account_number)
        active_fds = [fd for fd in fds if fd.status == "Active"]

        if not active_fds:
            print("\n📭 No active FDs found")
            return

        print("\n" + "=" * 80)
        print("CLOSE FD (PREMATURE)")
        print("=" * 80)

        print("\nActive FDs:")
        for idx, fd in enumerate(active_fds, 1):
            days_left = fd.get_days_to_maturity()
            print(
                f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f} ({days_left} days to maturity)"
            )

        try:
            choice = int(input(f"\nSelect FD (1-{len(active_fds)}): "))
            if choice < 1 or choice > len(active_fds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        fd = active_fds[choice - 1]

        # Show premature withdrawal calculation
        interest, penalty, payout = fd.calculate_premature_withdrawal()

        print(f"\nFD: {fd.fd_number}")
        print(f"Principal: Rs. {fd.principal_amount:,.2f}")
        print(f"Current Value: Rs. {fd.calculate_current_value():,.2f}")
        print(f"Interest Earned: Rs. {interest:,.2f}")
        print(f"Premature Penalty (1%): Rs. {penalty:,.2f}")
        print(f"Final Payout: Rs. {payout:,.2f}")

        print("\n[WARN]  Warning: Premature closure attracts 1% penalty")
        confirm = input("Confirm premature closure? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] Closure cancelled")
            return

        payout, message = fd.close_prematurely()

        if payout > 0:
            account.balance += payout

            # Create transaction

            txn = Transaction(
                type="FD_CLOSED_PREMATURE",
                amount=payout,
                resulting_balance=account.balance,
                metadata={"fd_number": fd.fd_number},
            )
            account.transactions.append(txn)

            print(message)
            print(f"Amount credited to account: Rs. {payout:,.2f}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            self.bank.save()
        else:
            print(f"[FAIL] {message}")

    def close_rd_premature(self, account: Account):
        """Close RD before maturity"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status in ["Active", "Completed"]]

        if not active_rds:
            print("\n📭 No active RDs found")
            return

        print("\n" + "=" * 80)
        print("CLOSE RD (PREMATURE)")
        print("=" * 80)

        print("\nRDs:")
        for idx, rd in enumerate(active_rds, 1):
            print(
                f"{idx}. {rd.rd_number} - {rd.installments_paid}/{rd.tenure_months} paid"
            )

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        rd = active_rds[choice - 1]

        # Show premature withdrawal calculation
        current_value, penalty, payout = rd.calculate_premature_withdrawal()

        print(f"\nRD: {rd.rd_number}")
        print(f"Installments Paid: {rd.installments_paid}/{rd.tenure_months}")
        print(f"Total Deposited: Rs. {rd.total_deposited:,.2f}")
        print(f"Current Value: Rs. {current_value:,.2f}")
        print(f"Penalty: Rs. {penalty:,.2f}")
        print(f"Final Payout: Rs. {payout:,.2f}")

        print("\n[WARN]  Warning: Premature closure attracts penalty")
        confirm = input("Confirm premature closure? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] Closure cancelled")
            return

        payout, message = rd.close_prematurely()

        if payout > 0:
            account.balance += payout

            # Create transaction

            txn = Transaction(
                type="RD_CLOSED_PREMATURE",
                amount=payout,
                resulting_balance=account.balance,
                metadata={"rd_number": rd.rd_number},
            )
            account.transactions.append(txn)

            print(message)
            print(f"Amount credited to account: Rs. {payout:,.2f}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            self.bank.save()
        else:
            print(f"[FAIL] {message}")

    def mature_fd(self, account: Account):
        """Mature an FD"""
        fds = self.bank.get_fds_for_account(account.account_number)
        matured_fds = [fd for fd in fds if fd.status == "Active" and fd.is_matured()]

        if not matured_fds:
            print("\n📭 No FDs ready for maturity")
            return

        print("\n" + "=" * 80)
        print("MATURE FIXED DEPOSIT")
        print("=" * 80)

        print("\nFDs ready for maturity:")
        for idx, fd in enumerate(matured_fds, 1):
            print(
                f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f} → Rs. {fd.maturity_amount:,.2f}"
            )

        try:
            choice = int(input(f"\nSelect FD (1-{len(matured_fds)}): "))
            if choice < 1 or choice > len(matured_fds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        fd = matured_fds[choice - 1]

        payout, message = fd.mature()

        if payout > 0:
            account.balance += payout

            # Create transaction

            txn = Transaction(
                type="FD_MATURED",
                amount=payout,
                resulting_balance=account.balance,
                metadata={"fd_number": fd.fd_number},
            )
            account.transactions.append(txn)

            print(message)
            print(f"Amount credited to account: Rs. {payout:,.2f}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            self.bank.save()
        else:
            print(f"[FAIL] {message}")

    def mature_rd(self, account: Account):
        """Mature an RD"""
        rds = self.bank.get_rds_for_account(account.account_number)
        completed_rds = [rd for rd in rds if rd.status == "Completed"]

        if not completed_rds:
            print("\n📭 No RDs ready for maturity")
            print("Complete all installments to mature your RD")
            return

        print("\n" + "=" * 80)
        print("MATURE RECURRING DEPOSIT")
        print("=" * 80)

        print("\nRDs ready for maturity:")
        for idx, rd in enumerate(completed_rds, 1):
            maturity = rd.calculate_maturity_amount()
            print(
                f"{idx}. {rd.rd_number} - Rs. {rd.total_deposited:,.2f} → Rs. {maturity:,.2f}"
            )

        try:
            choice = int(input(f"\nSelect RD (1-{len(completed_rds)}): "))
            if choice < 1 or choice > len(completed_rds):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        rd = completed_rds[choice - 1]

        payout, message = rd.mature()

        if payout > 0:
            account.balance += payout

            # Create transaction

            txn = Transaction(
                type="RD_MATURED",
                amount=payout,
                resulting_balance=account.balance,
                metadata={"rd_number": rd.rd_number},
            )
            account.transactions.append(txn)

            print(message)
            print(f"Amount credited to account: Rs. {payout:,.2f}")
            print(f"New Balance: Rs. {account.balance:,.2f}")
            self.bank.save()
        else:
            print(f"[FAIL] {message}")

    def view_fd_details(self, account: Account):
        """View detailed FD information"""
        fds = self.bank.get_fds_for_account(account.account_number)

        if not fds:
            print("\n📭 No Fixed Deposits found")
            return

        print("\nSelect FD to view details:")
        for idx, fd in enumerate(fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f}")

        try:
            choice = int(input(f"\nEnter choice (1-{len(fds)}): "))
            if choice < 1 or choice > len(fds):
                return
        except ValueError:
            return

        fd = fds[choice - 1]

        print("\n" + "=" * 70)
        print("FIXED DEPOSIT DETAILS")
        print("=" * 70)
        print(f"FD Number: {fd.fd_number}")
        print(f"Account Number: {fd.account_number}")
        print(f"Principal Amount: Rs. {fd.principal_amount:,.2f}")
        print(f"Interest Rate: {fd.interest_rate}% p.a.")
        print(f"Tenure: {fd.tenure_months} months")
        print(f"Start Date: {fd.start_date.strftime('%d-%m-%Y')}")
        print(f"Maturity Date: {fd.maturity_date.strftime('%d-%m-%Y')}")
        print(f"Maturity Amount: Rs. {fd.maturity_amount:,.2f}")
        print(f"Status: {fd.get_status_string()}")

        if fd.status == "Active":
            days_left = fd.get_days_to_maturity()
            current_value = fd.calculate_current_value()
            print(f"\nDays to Maturity: {days_left}")
            print(f"Current Value: Rs. {current_value:,.2f}")

        print("=" * 70)

    def view_rd_details(self, account: Account):
        """View detailed RD information"""
        rds = self.bank.get_rds_for_account(account.account_number)

        if not rds:
            print("\n📭 No Recurring Deposits found")
            return

        print("\nSelect RD to view details:")
        for idx, rd in enumerate(rds, 1):
            print(f"{idx}. {rd.rd_number} - Rs. {rd.monthly_installment:,.2f}/month")

        try:
            choice = int(input(f"\nEnter choice (1-{len(rds)}): "))
            if choice < 1 or choice > len(rds):
                return
        except ValueError:
            return

        rd = rds[choice - 1]

        print("\n" + "=" * 70)
        print("RECURRING DEPOSIT DETAILS")
        print("=" * 70)
        print(f"RD Number: {rd.rd_number}")
        print(f"Account Number: {rd.account_number}")
        print(f"Monthly Installment: Rs. {rd.monthly_installment:,.2f}")
        print(f"Interest Rate: {rd.interest_rate}% p.a.")
        print(f"Tenure: {rd.tenure_months} months")
        print(f"Start Date: {rd.start_date.strftime('%d-%m-%Y')}")
        print(f"Maturity Date: {rd.maturity_date.strftime('%d-%m-%Y')}")
        print(f"Expected Maturity: Rs. {rd.calculate_maturity_amount():,.2f}")
        print(f"\nInstallments Paid: {rd.installments_paid}/{rd.tenure_months}")
        print(f"Total Deposited: Rs. {rd.total_deposited:,.2f}")
        print(f"Status: {rd.get_payment_status()}")

        if rd.autopay_enabled:
            print("\nAutopay: [OK] Enabled")
            print(f"Autopay Day: {rd.autopay_day}")
            if rd.next_autopay_date:
                print(f"Next Autopay: {rd.next_autopay_date.strftime('%d-%m-%Y')}")
            print(f"Autopay Failures: {rd.autopay_failures}")
        else:
            print("\nAutopay: ✗ Disabled")

        if rd.missed_payments > 0:
            print(f"\n[WARN]  Missed Payments: {rd.missed_payments}")
            print(
                f"Penalty at Maturity: Rs. {rd.missed_payments * rd.LATE_PAYMENT_PENALTY:,.2f}"
            )

        if rd.status == "Active":
            current_value = rd.calculate_current_value()
            print(f"\nCurrent Value: Rs. {current_value:,.2f}")

        print("=" * 70)

    def rd_authorization_menu(self, customer: Customer, account: Account):
        """RD Authorization Management Menu"""
        while True:
            print("\n" + "=" * 80)
            print("RD AUTHORIZATION MANAGEMENT")
            print("=" * 80)
            print("""
Authorize someone else to pay for your RD, or view/manage existing authorizations.

1  Create New Authorization (Let someone pay for your RD)
2  View Authorizations Where I'm the Payer (I'm paying for someone's RD)
3  View Authorizations Where I'm the Beneficiary (Someone is paying for my RD)
4  Revoke Authorization
5  Update Authorization Limit
6  View Authorization Details
7  Verify Pending Authorizations
8  Back to FD/RD Menu
            """)

            choice = self.read_valid_choice(
                "Enter your choice: ",
                [str(i) for i in range(1, 9)],
                "Invalid choice. Please enter a number from 1 to 8.",
            )

            if choice == "1":
                self.create_rd_authorization(customer, account)
            elif choice == "2":
                self.view_authorizations_as_payer(customer)
            elif choice == "3":
                self.view_authorizations_as_beneficiary(customer)
            elif choice == "4":
                self.revoke_rd_authorization(customer)
            elif choice == "5":
                self.update_authorization_limit(customer)
            elif choice == "6":
                self.view_authorization_details(customer)
            elif choice == "7":
                self.verify_pending_authorizations(customer)
            elif choice == "8":
                break

    def create_rd_authorization(self, customer: Customer, beneficiary_account: Account):
        """Create a new RD authorization with OTP verification"""
        print("\n" + "=" * 80)
        print("CREATE RD AUTHORIZATION")
        print("=" * 80)
        print("""
    This allows someone else to pay monthly installments for YOUR Recurring Deposit.
    The payer's account will be debited, but YOU will receive the maturity amount.
    
    🔐 SECURITY: The payer must verify with a 6-digit code before activation.
        """)

        # Step 1: Select RD
        rds = self.bank.get_rds_for_account(beneficiary_account.account_number)
        active_rds = [rd for rd in rds if rd.status == "Active"]

        if not active_rds:
            print("\n[FAIL] No active RDs found")
            input("\nPress Enter to continue...")
            return

        print("\nYour Active RDs:")
        for idx, rd in enumerate(active_rds, 1):
            # Check if already authorized
            existing_auth = self.bank.get_rd_authorization(rd.rd_number)
            auth_status = ""
            if existing_auth:
                if existing_auth.is_active():
                    auth_status = (
                        f" [[OK] Authorized by {existing_auth.payer_customer_id}]"
                    )
                elif existing_auth.is_pending_verification():
                    auth_status = f" [⏳ Pending Verification from {existing_auth.payer_customer_id}]"

            print(
                f"{idx}. {rd.rd_number} - Rs. {rd.monthly_installment:,.2f}/month "
                f"({rd.installments_paid}/{rd.tenure_months} paid){auth_status}"
            )

        try:
            rd_choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if rd_choice < 1 or rd_choice > len(active_rds):
                print("[FAIL] Invalid choice")
                input("\nPress Enter to continue...")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            input("\nPress Enter to continue...")
            return

        selected_rd = active_rds[rd_choice - 1]

        # Check if already authorized
        existing_auth = self.bank.get_rd_authorization(selected_rd.rd_number)
        if existing_auth:
            if existing_auth.is_active():
                print(
                    f"\n[WARN]  This RD already has an ACTIVE authorization from {existing_auth.payer_customer_id}"
                )
            elif existing_auth.is_pending_verification():
                print(
                    f"\n[WARN]  This RD has a PENDING authorization from {existing_auth.payer_customer_id}"
                )
                otp_status = existing_auth.get_otp_status()
                print(
                    f"   Status: Awaiting verification ({otp_status['minutes_remaining']} minutes remaining)"
                )

            replace = (
                input("Revoke existing and create new authorization? (yes/no): ")
                .strip()
                .lower()
            )
            if replace in ["yes", "y"]:
                self.bank.revoke_rd_authorization(
                    existing_auth.auth_id,
                    "Replaced with new authorization",
                    customer.customer_id,
                )
                print("[OK] Previous authorization revoked")
            else:
                print("[FAIL] Authorization cancelled")
                input("\nPress Enter to continue...")
                return

        # Step 2: Get payer details
        print("\n" + "-" * 80)
        print("PAYER INFORMATION")
        print("-" * 80)
        print("Enter details of the person who will pay the RD installments:")

        payer_customer_id = input("\nPayer's Customer ID: ").strip()
        payer_customer = self.bank.get_customer_by_id(payer_customer_id)

        if not payer_customer:
            print(f"\n[FAIL] Customer ID '{payer_customer_id}' not found")
            input("\nPress Enter to continue...")
            return

        if payer_customer.customer_id == customer.customer_id:
            print("\n[FAIL] You cannot authorize yourself")
            input("\nPress Enter to continue...")
            return

        # Get payer's accounts
        payer_accounts = self.bank.get_customer_accounts(payer_customer)

        if not payer_accounts:
            print(f"\n[FAIL] No accounts found for customer {payer_customer_id}")
            input("\nPress Enter to continue...")
            return

        print(f"\n[OK] Payer: {payer_customer.first_name} {payer_customer.last_name}")
        print(f"  Phone: {payer_customer.phone_number}")
        print(f"  Email: {payer_customer.email}")

        print("\nPayer's Accounts:")
        for idx, acc in enumerate(payer_accounts, 1):
            print(
                f"{idx}. {acc.account_type} - {acc.account_number} (Balance: Rs. {acc.balance:,.2f})"
            )

        try:
            acc_choice = int(
                input(f"\nSelect payer's account (1-{len(payer_accounts)}): ")
            )
            if acc_choice < 1 or acc_choice > len(payer_accounts):
                print("[FAIL] Invalid choice")
                input("\nPress Enter to continue...")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            input("\nPress Enter to continue...")
            return

        payer_account = payer_accounts[acc_choice - 1]

        # Step 3: Confirmation and summary
        monthly_limit = selected_rd.monthly_installment * 1.1  # 10% buffer

        print("\n" + "=" * 80)
        print("AUTHORIZATION SUMMARY")
        print("=" * 80)
        print("\n[INFO] RD Details:")
        print(f"   RD Number: {selected_rd.rd_number}")
        print(f"   Monthly Installment: Rs. {selected_rd.monthly_installment:,.2f}")
        print(f"   Tenure: {selected_rd.tenure_months} months")
        print(
            f"   Installments Paid: {selected_rd.installments_paid}/{selected_rd.tenure_months}"
        )
        print(
            f"   Remaining: {selected_rd.tenure_months - selected_rd.installments_paid} installments"
        )

        print("\n[MONEY] Beneficiary (Receives Maturity Amount):")
        print(f"   Name: {customer.first_name} {customer.last_name}")
        print(f"   Customer ID: {customer.customer_id}")
        print(f"   Account: {beneficiary_account.account_number}")

        print("\n💳 Payer (Pays Monthly Installments):")
        print(f"   Name: {payer_customer.first_name} {payer_customer.last_name}")
        print(f"   Customer ID: {payer_customer.customer_id}")
        print(f"   Account: {payer_account.account_number}")
        print(f"   Current Balance: Rs. {payer_account.balance:,.2f}")

        print("\n[STATS] Authorization Details:")
        print(f"   Monthly Payment Limit: Rs. {monthly_limit:,.2f}")
        print(
            f"   Expected Total: Rs. {selected_rd.monthly_installment * (selected_rd.tenure_months - selected_rd.installments_paid):,.2f}"
        )

        print("\n[WARN]  Important:")
        print("   • Payer's account will be auto-debited monthly")
        print("   • Beneficiary will receive the full maturity amount")
        print("   • Authorization can be revoked anytime by either party")
        print("\n🔐 Security:")
        print("   • A 6-digit verification code will be generated")
        print("   • Share this code with the payer via phone/email")
        print("   • Payer must verify within 30 minutes")
        print("   • Authorization activates ONLY after verification")
        print("=" * 80)

        confirm = input("\nCreate authorization? (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("\n[FAIL] Authorization cancelled")
            input("\nPress Enter to continue...")
            return

        # Create authorization with OTP
        success, message, auth, otp = self.bank.create_rd_authorization(
            rd_number=selected_rd.rd_number,
            payer_customer=payer_customer,
            payer_account=payer_account,
        )

        if success:
            print("\n" + "=" * 80)
            print("[SUCCESS] AUTHORIZATION REQUEST CREATED")
            print("=" * 80)
            print(message)

            # Display OTP prominently
            print("\n" + "╔" + "=" * 78 + "╗")
            print("║" + " " * 20 + "VERIFICATION CODE (OTP)" + " " * 35 + "║")
            print("╠" + "=" * 78 + "╣")
            print("║" + " " * 30 + f"{otp}" + " " * 42 + "║")
            print("╚" + "=" * 78 + "╝")

            print("\n[WARN]  CRITICAL INSTRUCTIONS:")
            print("=" * 80)
            print("1. 📞 SHARE this 6-digit code with the PAYER:")
            print(
                f"   → Payer Name: {payer_customer.first_name} {payer_customer.last_name}"
            )
            print(f"   → Customer ID: {payer_customer.customer_id}")
            print(f"   → Phone: {payer_customer.phone_number}")
            print(f"   → Email: {payer_customer.email}")
            print()
            print("2. 🔐 Payer must VERIFY this code from their account:")
            print("   → Login → FD/RD Menu → RD Authorization → Verify Authorization")
            print()
            print("3. ⏰ CODE EXPIRES in 30 minutes")
            print()
            print("4. 🔢 Maximum 3 verification attempts allowed")
            print()
            print(
                "5. [SUCCESS] Authorization becomes ACTIVE only after successful verification"
            )
            print()
            print(
                "6. 💡 SECURITY TIP: Share this code securely (phone call, encrypted message)"
            )
            print("=" * 80)

            print("\n📝 Next Steps:")
            print("   1. Contact the payer and share the 6-digit code")
            print("   2. Payer logs into their account")
            print("   3. Payer navigates to: RD Authorization → Verify Authorization")
            print("   4. Payer enters the code")
            print("   5. Once verified, autopay will begin")

            print("\n" + "=" * 80)
            print(f"Authorization ID: {auth.auth_id}")
            print(f"Status: {auth.status}")
            print("=" * 80)
        else:
            print(f"\n[FAIL] Failed to create authorization: {message}")

        input("\nPress Enter to continue...")

    def view_authorizations_as_payer(self, customer: Customer):
        """View authorizations where current customer is the payer"""
        print("\n" + "=" * 110)
        print("AUTHORIZATIONS WHERE I'M THE PAYER")
        print("=" * 110)

        auths = self.bank.get_authorizations_as_payer(customer.customer_id)

        if not auths:
            print("\n📭 No authorizations found where you're the payer")
            input("\nPress Enter to continue...")
            return

        # Check for pending verifications
        pending = self.bank.get_pending_authorizations_for_payer(customer.customer_id)
        if pending:
            print(
                f"\n[WARN]  You have {len(pending)} PENDING authorization(s) awaiting your verification!"
            )
            print("   → Go to 'Verify Authorization' menu to activate them")
            print()

        print(f"You are paying for {len(auths)} RD(s):\n")
        print(
            f"{'Auth ID':<25} {'RD Number':<20} {'Beneficiary':<15} {'Monthly Limit':<18} {'Status':<20} {'Paid':<10}"
        )
        print("-" * 110)

        for auth in auths:
            beneficiary = self.bank.get_customer_by_id(auth.beneficiary_customer_id)
            beneficiary_name = (
                f"{beneficiary.first_name} {beneficiary.last_name}"
                if beneficiary
                else "Unknown"
            )

            # Enhanced status display
            status_display = auth.status
            if auth.is_pending_verification():
                otp_status = auth.get_otp_status()
                status_display = f"⏳ Pending ({otp_status['minutes_remaining']}m left)"
            elif auth.is_active():
                status_display = "[SUCCESS] Active"
            elif auth.status == "Suspended":
                status_display = "[VIRTUAL]  Suspended"
            elif auth.status == "Revoked":
                status_display = "[FAIL] Revoked"
            elif auth.status == "Expired":
                status_display = "⌛ Expired"
            elif auth.status == "Blocked":
                status_display = "🚫 Blocked"

            print(
                f"{auth.auth_id:<25} {auth.rd_number:<20} {beneficiary_name:<15} "
                f"Rs. {auth.monthly_limit:>12,.2f} {status_display:<20} {auth.total_payments:>3d}"
            )

        print("=" * 110)

        # Summary
        active_auths = [auth for auth in auths if auth.is_active()]
        pending_auths = [auth for auth in auths if auth.is_pending_verification()]

        total_limit = sum(auth.monthly_limit for auth in active_auths)
        total_paid = sum(auth.total_amount_paid for auth in auths)

        print("\n[STATS] Summary:")
        print(f"   Active Authorizations: {len(active_auths)}/{len(auths)}")
        if pending_auths:
            print(
                f"   ⏳ Pending Verification: {len(pending_auths)} (Action Required!)"
            )
        print(f"   Total Monthly Obligation: Rs. {total_limit:,.2f}")
        print(f"   Total Amount Paid (All Time): Rs. {total_paid:,.2f}")

        # Payment breakdown by status
        if len(auths) > len(active_auths):
            print("\n[INFO] Authorization Status Breakdown:")
            status_counts = {}
            for auth in auths:
                status = auth.status
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in sorted(status_counts.items()):
                icon = {
                    "Active": "[SUCCESS]",
                    "Pending_Verification": "⏳",
                    "Suspended": "[VIRTUAL]",
                    "Revoked": "[FAIL]",
                    "Expired": "⌛",
                    "Blocked": "🚫",
                }.get(status, "•")
                print(f"   {icon} {status.replace('_', ' ')}: {count}")

        print("\n💡 Actions Available:")
        if pending_auths:
            print("   • Use 'Verify Authorization' to activate pending requests")
        print("   • Use 'View Authorization Details' to see payment history")
        print("   • Use 'Revoke Authorization' to stop payments")

        input("\nPress Enter to continue...")

    def view_authorizations_as_beneficiary(self, customer: Customer):
        """View authorizations where current customer is the beneficiary"""
        print("\n" + "=" * 100)
        print("AUTHORIZATIONS WHERE I'M THE BENEFICIARY")
        print("=" * 100)

        auths = self.bank.get_authorizations_as_beneficiary(customer.customer_id)

        if not auths:
            print("\n📭 No authorizations found where you're the beneficiary")
            input("\nPress Enter to continue...")
            return

        print(f"\nOthers are paying for {len(auths)} of your RD(s):\n")
        print(
            f"{'Auth ID':<25} {'RD Number':<20} {'Payer':<15} {'Monthly Limit':<18} {'Status':<15} {'Paid':<10}"
        )
        print("-" * 100)

        for auth in auths:
            payer = self.bank.get_customer_by_id(auth.payer_customer_id)
            payer_name = f"{payer.first_name} {payer.last_name}" if payer else "Unknown"

            print(
                f"{auth.auth_id:<25} {auth.rd_number:<20} {payer_name:<15} "
                f"Rs. {auth.monthly_limit:>12,.2f} {auth.status:<15} {auth.total_payments:>3d}"
            )

        print("=" * 100)

        # Summary
        total_received = sum(auth.total_amount_paid for auth in auths)

        print("\n[STATS] Summary:")
        print(f"   Total Amount Received: Rs. {total_received:,.2f}")
        print(
            f"   Active Authorizations: {sum(1 for auth in auths if auth.is_active())}/{len(auths)}"
        )

        input("\nPress Enter to continue...")

    def revoke_rd_authorization(self, customer: Customer):
        """Revoke an RD authorization"""
        print("\n" + "=" * 80)
        print("REVOKE RD AUTHORIZATION")
        print("=" * 80)

        # Get all authorizations (as payer or beneficiary)
        as_payer = self.bank.get_authorizations_as_payer(customer.customer_id)
        as_beneficiary = self.bank.get_authorizations_as_beneficiary(
            customer.customer_id
        )

        all_auths = []
        for auth in as_payer + as_beneficiary:
            if auth.status not in ["Revoked", "Expired"]:
                all_auths.append(auth)

        if not all_auths:
            print("\n📭 No active authorizations to revoke")
            input("\nPress Enter to continue...")
            return

        print("\nActive Authorizations:")
        for idx, auth in enumerate(all_auths, 1):
            role = (
                "Payer"
                if auth.payer_customer_id == customer.customer_id
                else "Beneficiary"
            )
            other_party = (
                auth.beneficiary_customer_id
                if role == "Payer"
                else auth.payer_customer_id
            )
            other_customer = self.bank.get_customer_by_id(other_party)
            other_name = (
                f"{other_customer.first_name} {other_customer.last_name}"
                if other_customer
                else "Unknown"
            )

            print(f"{idx}. {auth.auth_id}")
            print(f"   RD: {auth.rd_number}")
            print(f"   Your Role: {role}")
            print(f"   Other Party: {other_name} ({other_party})")
            print(f"   Monthly Limit: Rs. {auth.monthly_limit:,.2f}")
            print(f"   Status: {auth.status}")
            print()

        try:
            choice = int(
                input(f"Select authorization to revoke (1-{len(all_auths)}): ")
            )
            if choice < 1 or choice > len(all_auths):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        auth = all_auths[choice - 1]

        reason = input("\nReason for revocation: ").strip() or "User requested"

        confirm = (
            input(f"\n[WARN]  Revoke authorization {auth.auth_id}? (yes/no): ")
            .strip()
            .lower()
        )

        if confirm not in ["yes", "y"]:
            print("\n[FAIL] Revocation cancelled")
            return

        success, message = self.bank.revoke_rd_authorization(
            auth.auth_id, reason, customer.customer_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(
                "\n[WARN]  Note: The RD will revert to manual/autopay from beneficiary's account"
            )
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def update_authorization_limit(self, customer: Customer):
        """Update monthly limit for an authorization"""
        print("\n" + "=" * 80)
        print("UPDATE AUTHORIZATION LIMIT")
        print("=" * 80)

        # Only beneficiary can update limits
        auths = self.bank.get_authorizations_as_beneficiary(customer.customer_id)
        active_auths = [auth for auth in auths if auth.is_active()]

        if not active_auths:
            print("\n📭 No active authorizations found where you're the beneficiary")
            print("   (Only beneficiaries can update authorization limits)")
            input("\nPress Enter to continue...")
            return

        print("\nYour Active Authorizations:")
        for idx, auth in enumerate(active_auths, 1):
            payer = self.bank.get_customer_by_id(auth.payer_customer_id)
            payer_name = f"{payer.first_name} {payer.last_name}" if payer else "Unknown"

            print(f"{idx}. {auth.auth_id}")
            print(f"   RD: {auth.rd_number}")
            print(f"   Payer: {payer_name}")
            print(f"   Current Limit: Rs. {auth.monthly_limit:,.2f}")
            print()

        try:
            choice = int(input(f"Select authorization (1-{len(active_auths)}): "))
            if choice < 1 or choice > len(active_auths):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        auth = active_auths[choice - 1]

        # Get RD details
        rd = self.bank.get_rd_by_number(auth.rd_number)
        if rd:
            print(f"\nRD Monthly Installment: Rs. {rd.monthly_installment:,.2f}")
            print(f"Current Authorization Limit: Rs. {auth.monthly_limit:,.2f}")

        try:
            new_limit = float(input("\nEnter new monthly limit: Rs. "))
            if new_limit <= 0:
                print("[FAIL] Limit must be positive")
                return
        except ValueError:
            print("[FAIL] Invalid amount")
            return

        if rd and new_limit < rd.monthly_installment:
            print("\n[WARN]  Warning: New limit is below the RD installment amount")
            print("   This may cause autopay failures")
            proceed = input("Continue anyway? (yes/no): ").strip().lower()
            if proceed not in ["yes", "y"]:
                print("[FAIL] Update cancelled")
                return

        success, message = auth.update_monthly_limit(new_limit, customer.customer_id)

        if success:
            print(f"\n[SUCCESS] {message}")
            self.bank.save()
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def view_authorization_details(self, customer: Customer):
        """View detailed information about an authorization"""
        print("\n" + "=" * 80)
        print("AUTHORIZATION DETAILS")
        print("=" * 80)

        # Get all authorizations
        as_payer = self.bank.get_authorizations_as_payer(customer.customer_id)
        as_beneficiary = self.bank.get_authorizations_as_beneficiary(
            customer.customer_id
        )
        all_auths = as_payer + as_beneficiary

        if not all_auths:
            print("\n📭 No authorizations found")
            input("\nPress Enter to continue...")
            return

        print("\nYour Authorizations:")
        for idx, auth in enumerate(all_auths, 1):
            role = (
                "Payer"
                if auth.payer_customer_id == customer.customer_id
                else "Beneficiary"
            )
            print(f"{idx}. {auth.auth_id} ({role}) - {auth.status}")

        try:
            choice = int(input(f"\nSelect authorization (1-{len(all_auths)}): "))
            if choice < 1 or choice > len(all_auths):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        auth = all_auths[choice - 1]

        # Display full details
        print(auth.get_summary())

        # Show payment history if any
        if auth.payment_history:
            print("\n" + "=" * 80)
            print("PAYMENT HISTORY")
            print("=" * 80)
            print(f"{'Date':<20} {'Installment':<15} {'Amount':<15} {'Status'}")
            print("-" * 80)

            for payment in auth.payment_history[-10:]:  # Last 10 payments
                status = (
                    "[OK] Success" if payment["success"] else f"✗ {payment['message']}"
                )
                print(
                    f"{payment['date'][:19]:<20} #{payment['installment_number']:<14} "
                    f"Rs. {payment['amount']:>10,.2f} {status}"
                )

            if len(auth.payment_history) > 10:
                print(f"\n... and {len(auth.payment_history) - 10} more payment(s)")

        input("\nPress Enter to continue...")

    def verify_pending_authorizations(self, customer: Customer):
        """Verify RD authorization using OTP (Payer side)"""
        print("\n" + "=" * 80)
        print("VERIFY RD AUTHORIZATION")
        print("=" * 80)

        # Get pending authorizations for this payer
        pending = self.bank.get_pending_authorizations_for_payer(customer.customer_id)

        if not pending:
            print("\n📭 No pending authorizations found")
            print("\nℹ️  Pending authorizations are requests where someone wants YOU")
            print("   to pay for their RD. You need to verify them with an OTP.")
            input("\nPress Enter to continue...")
            return

        print(f"\n⏳ You have {len(pending)} pending authorization(s):\n")
        print(
            f"{'#':<3} {'Auth ID':<25} {'RD Number':<20} {'Beneficiary':<20} {'Monthly':<15} {'Expires In'}"
        )
        print("-" * 100)

        for idx, auth in enumerate(pending, 1):
            beneficiary = self.bank.get_customer_by_id(auth.beneficiary_customer_id)
            beneficiary_name = (
                f"{beneficiary.first_name} {beneficiary.last_name}"
                if beneficiary
                else "Unknown"
            )

            # Calculate time remaining

            time_left = auth.otp_expires_at - BankClock.now()
            minutes_left = max(0, int(time_left.total_seconds() / 60))

            print(
                f"{idx:<3} {auth.auth_id:<25} {auth.rd_number:<20} {beneficiary_name:<20} "
                f"Rs. {auth.monthly_limit:>10,.2f}  {minutes_left} min"
            )

        print("=" * 100)

        try:
            choice = int(
                input(f"\nSelect authorization to verify (1-{len(pending)}): ")
            )
            if choice < 1 or choice > len(pending):
                print("[FAIL] Invalid choice")
                return
        except ValueError:
            print("[FAIL] Invalid input")
            return

        selected_auth = pending[choice - 1]

        # Show details
        print("\n" + "=" * 80)
        print("AUTHORIZATION DETAILS")
        print("=" * 80)

        beneficiary = self.bank.get_customer_by_id(
            selected_auth.beneficiary_customer_id
        )
        rd = self.bank.get_rd_by_number(selected_auth.rd_number)

        print("\n[INFO] RD Details:")
        print(f"   RD Number: {selected_auth.rd_number}")
        if rd:
            print(f"   Monthly Installment: Rs. {rd.monthly_installment:,.2f}")
            print(f"   Tenure: {rd.tenure_months} months")
            print(
                f"   Remaining: {rd.tenure_months - rd.installments_paid} installments"
            )

        print("\n👤 Beneficiary (Will receive maturity):")
        if beneficiary:
            print(f"   Name: {beneficiary.first_name} {beneficiary.last_name}")
            print(f"   Customer ID: {beneficiary.customer_id}")
            print(f"   Phone: {beneficiary.phone_number}")

        print("\n[MONEY] Payment Details:")
        print(f"   Your Monthly Obligation: Rs. {selected_auth.monthly_limit:,.2f}")
        if rd:
            total_remaining = rd.monthly_installment * (
                rd.tenure_months - rd.installments_paid
            )
            print(f"   Total Remaining: Rs. {total_remaining:,.2f}")

        print("\n⏰ OTP Status:")
        print(f"   Attempts Used: {selected_auth.otp_attempts}/3")
        time_left = selected_auth.otp_expires_at - BankClock.now()
        minutes_left = max(0, int(time_left.total_seconds() / 60))
        print(f"   Time Remaining: {minutes_left} minutes")

        print("\n" + "=" * 80)
        print("[WARN]  By verifying, you agree to:")
        print("   • Auto-pay the monthly installments from your account")
        print("   • The beneficiary will receive the maturity amount")
        print("   • You can revoke authorization anytime")
        print("=" * 80)

        proceed = input("\nProceed with verification? (yes/no): ").strip().lower()
        if proceed not in ["yes", "y"]:
            print("\n[FAIL] Verification cancelled")
            return

        # Get OTP
        otp = input("\n🔐 Enter 6-digit verification code: ").strip()

        if len(otp) != 6 or not otp.isdigit():
            print("\n[FAIL] Invalid OTP format. Must be 6 digits.")
            return

        # Verify
        success, message = self.bank.verify_rd_authorization(
            selected_auth.auth_id, otp, customer.customer_id
        )

        print(f"\n{message}")

        if success:
            print("\n🎉 Authorization is now ACTIVE!")
            print("   Monthly installments will be auto-debited from your account")
            self.bank.save()

        input("\nPress Enter to continue...")

    def view_rd_statement(self, customer: Customer, account: Account):
        """View detailed statement for an RD"""
        # Get all RDs for this account
        rdstatement = RDStatement(self.bank)
        statements = rdstatement.get_all_rd_statements(account.account_number)

        if not statements:
            print("📭 No RDs found for this account")
            input("Press Enter to continue...")
            return

        # Display list of RDs
        print("\n" + "=" * 80)
        print(
            f"RECURRING DEPOSITS - {account.first_name} {account.last_name}"
        )  # [SUCCESS] FIXED
        print("=" * 80)

        for idx, stmt in enumerate(statements, 1):
            print(f"\n{idx}. RD: {stmt['rd_number']} | {stmt['status']}")
            print(
                f"   Monthly: Rs. {stmt['monthly_installment']:,.2f} | Paid: {stmt['installments_paid']}/{stmt['tenure_months']} months"
            )
            print(
                f"   Payee: {stmt['payee_name']} | Beneficiary: {stmt['beneficiary_name']}"
            )

        # Select RD
        try:
            rdchoice = int(input("\nSelect RD number (or 0 to go back): "))
            if rdchoice == 0:
                return
            if 1 <= rdchoice <= len(statements):
                selectedstatement = statements[rdchoice - 1]

                # Display full statement
                rdstatement.print_rd_statement(selectedstatement)

                # Option to export
                export = input("\nExport statement to file? (y/n): ").strip().lower()
                if export == "y":
                    filename = rdstatement.export_rd_statement_to_text(
                        selectedstatement["rd_number"]
                    )
                    if filename:
                        print(f"[OK] Statement exported to: {filename}")
                    else:
                        print("[FAIL] Failed to export statement")

                input("\nPress Enter to continue...")
            else:
                print("[FAIL] Invalid selection")
        except ValueError:
            print("[FAIL] Invalid input")

    def change_clock_mode(self):
        """Change clock mode during runtime"""

        print("\n" + "=" * 60)
        print("CHANGE CLOCK MODE")
        print("=" * 60)
        print(f"Current Mode: {BankClock.get_mode()}")
        print(f"Current Time: {BankClock.get_formatted_datetime()}")
        print("\n1. Switch to Real-Time Mode")
        print("2. Switch to Virtual Mode")
        print("3. Cancel")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            if BankClock.get_mode() == "REAL":
                print("[WARN]  Already in Real-Time Mode")
            else:
                switch_to_real_mode()
                print("[SUCCESS] Switched to Real-Time Mode")
                print("[WARN]  Time simulation is now DISABLED")
        elif choice == "2":
            if BankClock.get_mode() == "VIRTUAL":
                print("[WARN]  Already in Virtual Mode")
            else:
                switch_to_virtual_mode(freeze_at_current=True)
                print("[SUCCESS] Switched to Virtual Mode")
                print("[SUCCESS] Time simulation is now ENABLED")

        input("\nPress Enter to continue...")

    def tax_planning_menu(self, customer: Customer, account: Account):
        """Tax Planning & Exemptions Menu"""
        managing = True
        while managing:
            print("\n" + "=" * 60)
            print("TAX PLANNING & EXEMPTIONS [STATS]")
            print("=" * 60)
            print(f"Customer: {customer.first_name} {customer.last_name}")
            print(
                f"Monthly Gross Salary: ₹{account.salary_profile.gross_salary:,.2f}"
                if account.salary_profile
                else "Salary Profile: Not Set"
            )
            print(f"Current Tax Regime: {customer.tax_regime}")
            pan_status = (
                f"PAN: {customer.pan}"
                if hasattr(customer, "pan") and customer.pan
                else "PAN: [FAIL] Not Registered"
            )
            print(f"{pan_status}")
            print("\n1. View Deduction Summary")
            print("2. View Tax Summary (With vs Without Deductions)")
            print("3. Upload Deduction Proof")
            print("4. Declare Additional Deductions")
            print("5. Register/Update PAN")
            print("6. File Annual ITR & Get Refund")
            print("7. View ITR Filing History & Process Refunds")
            print("8. Compare Tax Regimes (Old vs New)")
            print("9. Back to Main Menu")

            choice = self.read_valid_choice(
                "Enter choice: ", ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
            )

            if choice == "1":
                self.view_deductions_summary(customer, account)
            elif choice == "2":
                self.view_tax_summary(customer, account)
            elif choice == "3":
                self.upload_deduction_document(customer, account)
            elif choice == "4":
                self.declare_additional_deductions(customer, account)
            elif choice == "5":
                self.register_pan_menu(customer)
            elif choice == "6":
                self.file_itr_menu(customer, account)
            elif choice == "7":
                self.view_itr_filing_history_menu(customer, account)
            elif choice == "8":
                self.compare_tax_regimes(customer, account)
            elif choice == "9":
                managing = False

    def view_deductions_summary(self, customer: Customer, account: Account):
        """Display auto-detected and self-declared deductions with detailed breakdown"""
        print("\n" + "=" * 70)
        print("DEDUCTION SUMMARY - DETAILED BREAKDOWN")
        print("=" * 70)

        if not account.salary_profile:
            print("[FAIL] No salary profile found. Cannot calculate deductions.")
            input("\nPress Enter to continue...")
            return

        # Determine if metro city
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        annual_salary = account.salary_profile.gross_salary * 12

        # Get all deductions
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        if not deductions:
            print("[SUCCESS] No deductions detected.")
        else:
            print("\n" + "=" * 70)
            print("AUTO-DETECTED DEDUCTIONS")
            print("=" * 70)

            # Section 16 - Standard Deduction
            if "16" in deductions:
                print("\n📌 SECTION 16 - STANDARD DEDUCTION")
                print(f"   Amount: ₹{deductions['16']:>12,.2f}")
                print("   Limit:  ₹50,000 (Fixed - Automatic)")
                print("   Source: Standard deduction for salaried individuals")

            # Section 10(13A) - HRA
            if "10(13A)" in deductions:
                print("\n📌 SECTION 10(13A) - HOUSE RENT ALLOWANCE (HRA)")
                print(f"   Amount: ₹{deductions['10(13A)']:>12,.2f}")
                print("   Limit:  50% of salary (Metro) / 40% (Non-metro)")
                print(
                    "   Sources: Rent transactions in bank account, credit cards, recurring bills"
                )
                # Show rent bills if available
                if hasattr(account, "recurring_bills"):
                    rent_bills = [
                        b
                        for b in account.recurring_bills
                        if "rent" in str(b.name).lower()
                    ]
                    if rent_bills:
                        for bill in rent_bills[:2]:
                            bill_amount = (
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                            print(
                                f"             ├─ {bill.name}: ₹{bill_amount:,.2f}/month"
                            )

            # Section 80C - Savings/Investments
            if "80C" in deductions:
                print(
                    "\n📌 SECTION 80C - SAVINGS & INVESTMENTS (EPF/Insurance/Home Loan Principal)"
                )
                print(f"   Amount: ₹{deductions['80C']:>12,.2f}")
                print("   Limit:  ₹1,50,000")
                # Show EPF if available
                if hasattr(account.salary_profile, "epf_contribution"):
                    epf_annual = account.salary_profile.epf_contribution * 12
                    print(f"   Sources: EPF Contribution: ₹{epf_annual:,.2f}/year")
                else:
                    print(
                        "   Sources: Employee Provident Fund (EPF), Life Insurance, Home Loan Principal"
                    )

            # Section 80D - Medical Insurance
            if "80D" in deductions:
                print("\n📌 SECTION 80D - MEDICAL INSURANCE")
                print(f"   Amount: ₹{deductions['80D']:>12,.2f}")
                print("   Limit:  ₹50,000")
                print(
                    "   Sources: Insurance premium payments from bank transactions, credit cards, or recurring bills"
                )
                # Show insurance bills if available
                if hasattr(account, "recurring_bills"):
                    insurance_bills = [
                        b
                        for b in account.recurring_bills
                        if "insurance" in str(b.name).lower()
                        or "premium" in str(b.name).lower()
                    ]
                    if insurance_bills:
                        for bill in insurance_bills[:2]:
                            bill_amount = (
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                            print(
                                f"             ├─ {bill.name}: ₹{bill_amount:,.2f}/month"
                            )

            # Section 24 - Home Loan Interest
            if "24" in deductions:
                print("\n📌 SECTION 24 - HOME LOAN INTEREST")
                print(f"   Amount: ₹{deductions['24']:>12,.2f}")
                print("   Limit:  ₹2,00,000")
                print("   Sources: Interest on home loans")
                # Show home loans if available
                if hasattr(customer, "loans"):
                    home_loans = [
                        l
                        for l in customer.loans
                        if hasattr(l, "loan_type")
                        and "HOME" in str(l.loan_type).upper()
                    ]
                    if home_loans:
                        for loan in home_loans:
                            loan_amount = (
                                loan.principal if hasattr(loan, "principal") else 0
                            )
                            loan_rate = (
                                loan.interest_rate
                                if hasattr(loan, "interest_rate")
                                else 0
                            )
                            interest_annual = (loan_amount * loan_rate) / 100
                            print(
                                f"             ├─ Home Loan: ₹{interest_annual:,.2f}/year @ {loan_rate}%"
                            )

            total_deductions = sum(deductions.values())
            print("\n" + "=" * 70)
            print(f"TOTAL ANNUAL DEDUCTIONS: ₹{total_deductions:,.2f}")
            print("=" * 70)

        # Show stored deductions with status
        if customer.tax_deductions:
            print("\n\n" + "=" * 70)
            print("SELF-DECLARED DEDUCTIONS")
            print("=" * 70)
            for exemption in customer.tax_deductions:
                status_emoji = (
                    "[OK]"
                    if exemption.status.value == "VERIFIED"
                    else "?"
                    if exemption.status.value == "AUTO_DETECTED"
                    else "!"
                )
                print(f"\n{status_emoji} {exemption.deduction_type.value}")
                print(f"   Amount: ₹{exemption.eligible_amount:>12,.2f}")
                print(f"   Status: {exemption.status.value}")
                if exemption.documents:
                    print(f"   Documents: {len(exemption.documents)} attached")

        input("\nPress Enter to continue...")

    def view_tax_summary(self, customer: Customer, account: Account):
        """Display tax calculation with and without deductions"""
        print("\n" + "=" * 60)
        print("TAX SUMMARY")
        print("=" * 60)

        if not account.salary_profile:
            print("[FAIL] No salary profile found. Cannot calculate tax.")
            input("\nPress Enter to continue...")
            return

        # Get salary info
        annual_salary = account.salary_profile.gross_salary * 12

        # Get deductions
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        # Calculate tax with deductions
        if deductions:
            taxable_with_ded, tax_with_ded, rate_with_ded = (
                TaxCalculator.calculate_tax_with_deductions(annual_salary, deductions)
            )
        else:
            taxable_with_ded = tax_with_ded = rate_with_ded = 0

        # Calculate tax without deductions
        tax_without_ded, rate_without_ded = (
            TaxCalculator.calculate_tax_without_deductions(annual_salary)
        )

        # Calculate monthly equivalents
        monthly_salary = account.salary_profile.gross_salary
        monthly_tax_with_ded = tax_with_ded / 12 if deductions else 0
        monthly_tax_without_ded = tax_without_ded / 12

        print(f"\nGross Annual Salary: ₹{annual_salary:,.2f}")
        print(f"Gross Monthly Salary: ₹{monthly_salary:,.2f}")

        print("\n" + "-" * 60)
        print("WITH DEDUCTIONS (Old Regime)")
        print("-" * 60)
        if deductions:
            total_deductions = sum(deductions.values())
            print(f"Total Annual Deductions: ₹{total_deductions:,.2f}")
            print(f"Taxable Income: ₹{taxable_with_ded:,.2f}")
            print(f"Tax Rate: {rate_with_ded:.2f}%")
            print(f"Annual Tax Liability: ₹{tax_with_ded:,.2f}")
            print(f"Monthly Tax Deduction: ₹{monthly_tax_with_ded:,.2f}")
        else:
            print("No deductions available")

        print("\n" + "-" * 60)
        print("WITHOUT DEDUCTIONS (New Regime)")
        print("-" * 60)
        print(f"Taxable Income: ₹{annual_salary:,.2f}")
        print(f"Tax Rate: {rate_without_ded:.2f}%")
        print(f"Annual Tax Liability: ₹{tax_without_ded:,.2f}")
        print(f"Monthly Tax Deduction: ₹{monthly_tax_without_ded:,.2f}")

        # Calculate savings
        if deductions:
            tax_savings = tax_without_ded - tax_with_ded
            monthly_savings = tax_savings / 12
            savings_percent = (
                (tax_savings / tax_without_ded * 100) if tax_without_ded > 0 else 0
            )

            print("\n" + "-" * 60)
            print("TAX SAVINGS WITH DEDUCTIONS")
            print("-" * 60)
            print(f"Annual Savings: ₹{tax_savings:,.2f}")
            print(f"Monthly Savings: ₹{monthly_savings:,.2f}")
            print(f"Savings %: {savings_percent:.2f}%")

        input("\nPress Enter to continue...")

    def upload_deduction_document(self, customer: Customer, account: Account):
        """Upload proof for deductions (for simulation)"""
        print("\n" + "=" * 60)
        print("UPLOAD DEDUCTION PROOF")
        print("=" * 60)

        if not customer.tax_deductions:
            print("[FAIL] No deductions found to upload proof for.")
            print(
                "💡 Tip: Declare some deductions first (Option 4 in Tax Planning Menu)"
            )
            input("\nPress Enter to continue...")
            return

        print("\nSelect deduction to upload proof for:")
        for i, exemption in enumerate(customer.tax_deductions, 1):
            status_emoji = "[OK]" if exemption.status == "VERIFIED" else "?"
            print(
                f"  {i}. {status_emoji} {exemption.deduction_type.value} - ₹{exemption.eligible_amount:,.2f}"
            )

        try:
            choice = int(input(f"\nEnter number (1-{len(customer.tax_deductions)}): "))
            if 1 <= choice <= len(customer.tax_deductions):
                selected = customer.tax_deductions[choice - 1]

                # Get document details
                doc_type = input(
                    "\nDocument Type (e.g., 'Form 12BA', 'Insurance Receipt', 'Bank Statement'): "
                ).strip()
                file_path = input(
                    "Virtual File Path (for simulation, e.g., '/docs/rent_agreement.pdf'): "
                ).strip()

                if doc_type and file_path:
                    # Add document to exemption
                    selected.add_document(doc_type, file_path)

                    # Mark as verified after upload
                    selected.status = "VERIFIED"

                    print("\n[SUCCESS] Document uploaded successfully!")
                    print(f"   Document: {doc_type}")
                    print(f"   Path: {file_path}")
                    print(f"   Status: {selected.status}")
                    print("\n[INFO] Deduction marked as VERIFIED")
                else:
                    print("[FAIL] Invalid input. Please try again.")
            else:
                print("[FAIL] Invalid choice.")
        except ValueError:
            print("[FAIL] Please enter a valid number.")

        input("\nPress Enter to continue...")

    def declare_additional_deductions(self, customer: Customer, account: Account):
        """Allow user to manually declare deductions"""
        print("\n" + "=" * 60)
        print("DECLARE ADDITIONAL DEDUCTIONS")
        print("=" * 60)

        print("\nSelect deduction type:")
        print("1. Section 80C (Investments) - Max ₹1,50,000")
        print("2. Section 80D (Medical Insurance) - Max ₹50,000")
        print("3. Section 24 (Home Loan Interest) - Max ₹2,00,000")
        print("4. Cancel")

        choice = input("\nEnter choice: ").strip()

        if choice == "4":
            return

        try:
            amount = float(input("\nEnter amount: ₹"))
            doc_type = input(
                "Document Type (e.g., 'Insurance Certificate', 'Bank Statement'): "
            ).strip()

            if choice == "1":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_80C,
                    amount=150000,
                    section="80C",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=150000,
                )
                deduction.eligible_amount = min(amount, 150000)
            elif choice == "2":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_80D,
                    amount=50000,
                    section="80D",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=50000,
                )
                deduction.eligible_amount = min(amount, 50000)
            elif choice == "3":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_24_HOME_LOAN_INTEREST,
                    amount=200000,
                    section="24",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=200000,
                )
                deduction.eligible_amount = min(amount, 200000)
            else:
                print("[FAIL] Invalid choice.")
                return

            # Add document if provided
            if doc_type:
                file_path = input("Virtual File Path (for simulation): ").strip()
                if file_path:
                    deduction.add_document(doc_type, file_path)

            # Add to customer's tax deductions
            customer.tax_deductions.append(deduction)
            self.bank.save()

            print("\n[SUCCESS] Deduction declared successfully!")
            print(f"   Amount: ₹{deduction.eligible_amount:,.2f}")
            print(f"   Status: {deduction.status.value}")
            print(f"   Documents: {len(deduction.documents)} attached")

        except ValueError:
            print("[FAIL] Invalid input. Please enter a valid number.")

        input("\nPress Enter to continue...")

    def register_pan_menu(self, customer: Customer):
        """Register or update PAN for tax filing"""
        print("\n" + "=" * 70)
        print("REGISTER/UPDATE PAN")
        print("=" * 70)

        current_pan = (
            customer.pan if hasattr(customer, "pan") and customer.pan else None
        )

        if current_pan:
            print(f"Current PAN: {current_pan}")
        else:
            print("No PAN registered yet.")

        print("\n1. Register New PAN")
        print("2. Update Existing PAN")
        print("3. Back")

        choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3"])

        if choice == "3":
            return

        pan = input("\nEnter 10-character PAN (e.g., ABCDE1234F): ").strip().upper()

        # Validate PAN format (2 letters + 5 digits + 1 letter + 1 digit + 1 letter)
        if not self.validate_pan(pan):
            print(
                "[FAIL] Invalid PAN format. PAN should be 10 characters: 2 letters, 5 digits, 1 letter, 1 digit, 1 letter"
            )
            input("\nPress Enter to continue...")
            return

        # Check if PAN already exists in system (optional validation)
        customer.pan = pan
        self.bank.save()

        print(f"\n[SUCCESS] PAN {pan} registered successfully!")
        print("You can now file your ITR.")

        input("\nPress Enter to continue...")

    def validate_pan(self, pan: str) -> bool:
        """Validate PAN format"""
        import re

        pattern = (
            r"^[A-Z]{2}[A-Z]{1}[P-Z]{1}[A-Z]{1}[0-9]{7}[A-Z]{1}[0-9]{1}[Z]{1}[0-9]{1}$"
        )
        if re.match(pattern, pan):
            return True
        # Also allow simple format: any 10 chars
        return len(pan) == 10 and pan.isalnum()

    def file_itr_menu(self, customer: Customer, account: Account):
        """File ITR and process refunds"""
        print("\n" + "=" * 70)
        print("FILE ANNUAL INCOME TAX RETURN (ITR)")
        print("=" * 70)

        if not account.salary_profile:
            print("[FAIL] Salary profile not configured. Cannot file ITR.")
            input("\nPress Enter to continue...")
            return

        if not hasattr(customer, "pan") or not customer.pan:
            print("[FAIL] PAN not registered. Cannot file ITR.")
            input("\nPress Enter to continue...")
            return

        # Check for existing ITR filing
        current_fy = ITRFiling.calculate_financial_year()
        existing_filings = ITRFiling.get_filing_history(account)

        # Check for any active (non-AMENDED) filing for current FY
        active_fy_filing = [
            f
            for f in existing_filings
            if f.financial_year == current_fy
            and f.status.value
            != "Amended"  # Allow re-filing only if previous was AMENDED
        ]

        if active_fy_filing:
            existing = active_fy_filing[0]
            print(f"\n[WARN]  WARNING: You already have an ITR filing for FY {current_fy}")
            print(f"   Filed Date: {existing.filed_date.strftime('%d-%b-%Y')}")
            print(
                f"   Status: {ITRFiling.get_status_icon(existing.status)} {existing.status.value}"
            )
            print(f"   Acknowledgment: {existing.ack_number}")

            if existing.refund_amount > 0:
                print(f"   Refund: ₹{existing.refund_amount:,.2f}")
            else:
                tax_due = existing.tax_liability - existing.tds_paid
                print(f"   Tax Due: ₹{tax_due:,.2f}")

            print(
                "\n[WARN]  You CANNOT file another ITR for the same financial year unless:"
            )
            print("   1. You formally AMEND the filing with corrected information")

            amend_choice = (
                input("\nDo you want to AMEND the existing filing? (yes/no): ")
                .strip()
                .lower()
            )

            if amend_choice in ["yes", "y"]:
                print(f"\n[SUCCESS] Preparing to amend ITR for FY {current_fy}...")
                print("[WARN]  The previous filing will be marked as AMENDED.")

                if existing.status.value == "Refund Credited":
                    print(
                        "[WARN]  Note: Refund has already been credited. Amendment will require new calculation."
                    )

                confirm = input("Proceed with amendment? (yes/no): ").strip().lower()

                if confirm in ["yes", "y"]:
                    ITRFiling.void_filing(account, current_fy)
                    print("[SUCCESS] Previous ITR filing marked as AMENDED.")
                else:
                    print("Amendment cancelled.")
                    input("\nPress Enter to continue...")
                    return
            else:
                print(
                    "\n[FAIL] Cannot file new ITR. Existing filing must be amended first."
                )
                input("\nPress Enter to continue...")
                return

        # File ITR
        success, filing_record, message = ITRFiling.file_itr(
            account,
            f"{customer.first_name} {customer.last_name}",
            customer.pan,
            customer,
            self.bank,
        )

        if not success:
            print(f"[FAIL] {message}")
            input("\nPress Enter to continue...")
            return

        # Display summary
        ITRFiling.display_filing_summary(filing_record)
        print(f"\n{message}")

        # Generate comprehensive report
        self.generate_itr_report(customer, account, filing_record)

        # Store filing record ONLY if not already amended and stored
        # (If amended, it's already stored in generate_itr_report)

        if filing_record.status != ITRStatus.AMENDED:
            ITRFiling.store_filing(account, filing_record)
            self.bank.save()
        else:
            # Filing was amended and already stored - return to menu
            print("\n" + "=" * 70)
            input("\nPress Enter to continue...")
            return

        # Process refund if applicable (only if not amended)
        if filing_record.refund_amount > 0:
            print("\n" + "-" * 70)
            process = input("\nProcess refund now? (yes/no): ").strip().lower()

            if process in ["yes", "y"]:
                success, refund_msg = ITRFiling.process_refund(
                    account, filing_record, self.bank
                )

                if success:
                    print(f"\n{refund_msg}")
                else:
                    print(f"\n[FAIL] {refund_msg}")

        # View filing history
        print("\n" + "-" * 70)
        view_history = input("\nView ITR filing history? (yes/no): ").strip().lower()

        if view_history in ["yes", "y"]:
            filings = ITRFiling.get_filing_history(account)
            if not filings:
                print("\n[INFO] No ITR filings yet")
            else:
                print("\n[INFO] ITR FILING HISTORY")
                print("=" * 70)
                for idx, filing in enumerate(filings, 1):
                    # Use status field from ITRStatus enum
                    status_icon = {
                        "Filed - Pending": "⏳",
                        "Refund Credited": "[SUCCESS]",
                        "Tax Paid": "💳",
                        "Amended": "📝",
                    }.get(filing.status.value, "❓")

                    print(
                        f"{idx}. FY {filing.financial_year} - {status_icon} {filing.status.value}"
                    )
                    print(
                        f"   Refund: ₹{filing.refund_amount:,.2f} | Filed: {filing.filed_date.strftime('%d-%b-%Y')}"
                    )

        input("\nPress Enter to continue...")

        input("\nPress Enter to continue...")

    def view_itr_filing_history_menu(self, customer: Customer, account: Account):
        """View ITR filing history and process pending refunds"""

        print("\n" + "=" * 70)
        print("[INFO] ITR FILING HISTORY & REFUND PROCESSING")
        print("=" * 70)

        filings = ITRFiling.get_filing_history(account)

        if not filings:
            print("\n[FAIL] No ITR filings found.")
            print("   File your first ITR using option 6 from the Tax Planning menu.")
            input("\nPress Enter to continue...")
            return

        # Display all filings
        print(f"\nTotal Filings: {len(filings)}")
        print("=" * 70)

        pending_refunds = []

        for idx, filing in enumerate(filings, 1):
            status_icon = ITRFiling.get_status_icon(filing.status)

            print(f"\n{idx}. FINANCIAL YEAR {filing.financial_year}")
            print(f"   Status: {status_icon} {filing.status.value}")
            print(f"   Filed Date: {filing.filed_date.strftime('%d-%b-%Y')}")
            print(f"   Acknowledgment: {filing.ack_number}")
            print(f"   Gross Income: ₹{filing.gross_income:,.2f}")
            print(f"   Tax Liability: ₹{filing.tax_liability:,.2f}")
            print(f"   TDS Paid: ₹{filing.tds_paid:,.2f}")

            if filing.refund_amount > 0:
                print(f"   [MONEY] Refund Amount: ₹{filing.refund_amount:,.2f}")

                # Check if refund is pending
                if (
                    filing.status == ITRStatus.FILED_PENDING
                    and not filing.refund_credited
                ):
                    pending_refunds.append((idx, filing))
                    print("   🔔 ACTION REQUIRED: Refund is pending!")
                elif filing.refund_credited and filing.refund_date:
                    print(
                        f"   [SUCCESS] Refund Credited on: {filing.refund_date.strftime('%d-%b-%Y')}"
                    )
            else:
                tax_due = filing.tax_liability - filing.tds_paid
                print(f"   [WARN]  Tax Due: ₹{tax_due:,.2f}")

            print("-" * 70)

        # Process pending refunds
        if pending_refunds:
            print(f"\n🔔 You have {len(pending_refunds)} pending refund(s) to process!")
            print("=" * 70)

            for idx, filing in pending_refunds:
                print(f"• FY {filing.financial_year}: ₹{filing.refund_amount:,.2f}")

            print("\n")
            process_choice = (
                input("Do you want to process pending refunds now? (yes/no): ")
                .strip()
                .lower()
            )

            if process_choice in ["yes", "y"]:
                for idx, filing in pending_refunds:
                    print(f"\n📝 Processing refund for FY {filing.financial_year}...")

                    success, refund_msg = ITRFiling.process_refund(
                        account, filing, self.bank
                    )

                    if success:
                        print(f"[SUCCESS] {refund_msg}")
                    else:
                        print(f"[FAIL] {refund_msg}")

                # Save updated data
                self.bank.save()
                print("\n[SUCCESS] All pending refunds processed successfully!")
            else:
                print(
                    "\n[WARN]  Refunds not processed. You can process them later from this menu."
                )
        else:
            print("\n[SUCCESS] No pending refunds to process.")
            print("   All filings are either processed or have no refunds due.")

        input("\nPress Enter to continue...")

    def generate_itr_report(self, customer: Customer, account: Account, filing_record):
        """Generate and display comprehensive ITR report"""
        print("\n" + "=" * 70)
        print("[INFO] COMPREHENSIVE ITR FILING REPORT")
        print("=" * 70)

        # Get deductions breakdown
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        # Header Section
        print(f"\n{'TAXPAYER INFORMATION':^70}")
        print("-" * 70)
        print(f"Name:                {customer.first_name} {customer.last_name}")
        print(f"PAN:                 {customer.pan}")
        print(f"Financial Year:      {filing_record.financial_year}")
        print(f"Filing Date:         {filing_record.filed_date.strftime('%d-%b-%Y')}")
        print(f"Acknowledgment #:    {filing_record.ack_number}")

        # Income Section
        print(f"\n{'INCOME BREAKDOWN':^70}")
        print("-" * 70)
        print(f"  Gross Salary:          ₹{filing_record.gross_income:>15,.2f}")

        # Show gross components
        if account.salary_profile:
            monthly_salary = account.salary_profile.gross_salary
            print(f"    └─ Annual (₹{monthly_salary:,.2f} × 12)")

            # Show salary components if available
            if hasattr(account.salary_profile, "basic_salary"):
                print(
                    f"       • Basic Salary:     ₹{account.salary_profile.basic_salary * 12:,.2f}"
                )
            if hasattr(account.salary_profile, "hra_received"):
                print(
                    f"       • HRA Received:     ₹{account.salary_profile.hra_received * 12:,.2f}"
                )
            if hasattr(account.salary_profile, "special_allowance"):
                print(
                    f"       • Allowances:       ₹{account.salary_profile.special_allowance * 12:,.2f}"
                )

        # Deductions Section
        print(f"\n{'DEDUCTIONS SUMMARY':^70}")
        print("-" * 70)

        if deductions:
            deduction_labels = {
                "16": "Section 16 - Standard Deduction",
                "10(13A)": "Section 10(13A) - HRA/Rent",
                "80C": "Section 80C - Savings/EPF",
                "80D": "Section 80D - Medical Insurance",
                "24": "Section 24 - Home Loan Interest",
            }

            for section, amount in sorted(deductions.items()):
                label = deduction_labels.get(section, f"Section {section}")
                print(f"  {label:<45} ₹{amount:>15,.2f}")

        print(f"  {'-' * 45} {'-' * 17}")
        print(f"  {'Total Deductions':<45} ₹{filing_record.total_deductions:>15,.2f}")

        # Tax Calculation Section
        print(f"\n{'TAX CALCULATION':^70}")
        print("-" * 70)
        print(f"  Gross Income (A):      ₹{filing_record.gross_income:>15,.2f}")
        print(f"  Less: Deductions (B):  ₹{filing_record.total_deductions:>15,.2f}")
        print(f"  {'-' * 45} {'-' * 17}")
        print(f"  Taxable Income (A-B):  ₹{filing_record.taxable_income:>15,.2f}")

        # Calculate tax rate
        if filing_record.taxable_income > 0:
            effective_rate = (
                filing_record.tax_liability / filing_record.taxable_income
            ) * 100
            print(f"\n  Applicable Tax Rate:   {effective_rate:.2f}%")

        print(f"  Tax Liability:         ₹{filing_record.tax_liability:>15,.2f}")

        # TDS and Refund Section
        print(f"\n{'REFUND CALCULATION':^70}")
        print("-" * 70)
        print(f"  Tax Liability:         ₹{filing_record.tax_liability:>15,.2f}")
        print(f"  TDS Paid During Year:  ₹{filing_record.tds_paid:>15,.2f}")
        print(f"  {'-' * 45} {'-' * 17}")

        if filing_record.refund_amount > 0:
            print(f"  [MONEY] REFUND DUE:         ₹{filing_record.refund_amount:>15,.2f}")
            print("\n  Status: ⏳ Pending (Apply for refund if not auto-credited)")
        else:
            additional_tax = filing_record.tax_liability - filing_record.tds_paid
            print(f"  Additional Tax Owing:  ₹{additional_tax:>15,.2f}")
            print("\n  Status: [WARN]  No refund due")

        # Summary Section
        print(f"\n{'FILING SUMMARY':^70}")
        print("-" * 70)
        print("[SUCCESS] ITR has been successfully filed with Income Tax Department")
        print(f"[SUCCESS] Acknowledgment receipt: {filing_record.ack_number}")

        # Show next steps
        print(f"\n{'NEXT STEPS':^70}")
        print("-" * 70)
        if filing_record.refund_amount > 0:
            print("1. Track refund status using acknowledgment number")
            print("2. Expected refund processing time: 30-45 days")
            print("3. Refund will be credited to your registered bank account")
        else:
            print("1. Keep this report for your records")
            print(
                "2. If additional tax is due, arrange payment within statutory deadline"
            )
            print("3. Maintain all supporting documents for 5-6 years")

        # AMEND OPTION - Right before file save
        print("\n" + "-" * 70)
        print("⭐ FILING ACTION")
        print("-" * 70)
        amend_now = (
            input("\nDo you want to AMEND this filing? (yes/no): ").strip().lower()
        )

        if amend_now in ["yes", "y"]:
            print(
                f"\n[SUCCESS] Preparing to amend ITR for FY {filing_record.financial_year}..."
            )
            print("[WARN]  This filing will be marked as AMENDED.")
            print("   You can then file a corrected ITR.")


            confirm = input("Proceed with amendment? (yes/no): ").strip().lower()

            if confirm in ["yes", "y"]:
                # Mark the filing record as AMENDED directly (it hasn't been stored yet)
                from .TaxCalculator import ITRStatus
                filing_record.status = ITRStatus.AMENDED
                # Store the AMENDED filing record
                from .TaxCalculator import ITRFiling
                ITRFiling.store_filing(account, filing_record)
                # SAVE to persist the AMENDED status
                self.bank.save()
                print("\n[SUCCESS] ITR filing marked as AMENDED.")
                print(
                    "💡 You can now file a corrected ITR by selecting 'File ITR' again."
                )
                # Return to caller (file_itr_menu) which will handle exit
                return
            else:
                print("Amendment cancelled. Continuing with current filing...")

        # Save report option
        print("\n" + "-" * 70)
        save_option = input("\nGenerate report file? (yes/no): ").strip().lower()

        if save_option in ["yes", "y"]:
            self.save_itr_report_to_file(customer, filing_record, deductions)

    def save_itr_report_to_file(
        self, customer: Customer, filing_record, deductions: Dict
    ):
        """Save ITR report as a professional PDF"""
        try:
            from .StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_itr_report_pdf(customer, filing_record, deductions)
            print(f"\n[SUCCESS] Official ITR Filing Report (PDF) generated: {filepath}")
        except Exception as e:
            print(f"\n[FAIL] Error generating tax report: {e}")


    def compare_tax_regimes(self, customer: Customer, account: Account):
        """Compare Old Regime (with deductions) vs New Regime (no deductions)"""
        print("\n" + "=" * 60)
        print("TAX REGIME COMPARISON")
        print("=" * 60)

        if not account.salary_profile:
            print("[FAIL] No salary profile found.")
            input("\nPress Enter to continue...")
            return

        annual_salary = account.salary_profile.gross_salary * 12

        # Get deductions
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        if not deductions:
            print("[WARN]  No deductions available. Both regimes would result in same tax.")
            input("\nPress Enter to continue...")
            return

        # Get comparison
        recommendation, details = TaxCalculator.compare_regimes(
            annual_salary, deductions
        )

        # Display comparison
        print("\nOLD REGIME (With Deductions)")
        print("-" * 60)
        print(f"Gross Income: ₹{details['old_regime']['gross']:,.2f}")
        print(f"Total Deductions: ₹{details['old_regime']['total_deductions']:,.2f}")
        print(f"Taxable Income: ₹{details['old_regime']['taxable']:,.2f}")
        print(f"Annual Tax: ₹{details['old_regime']['tax']:,.2f}")
        print(f"Tax Rate: {details['old_regime']['tax_rate'] * 100:.2f}%")
        print(f"Monthly Tax: ₹{details['old_regime']['monthly_tax']:,.2f}")
        print(f"Annual Net: ₹{details['old_regime']['net']:,.2f}")

        print("\nNEW REGIME (No Deductions)")
        print("-" * 60)
        print(f"Gross Income: ₹{details['new_regime']['gross']:,.2f}")
        print(f"Taxable Income: ₹{details['new_regime']['taxable']:,.2f}")
        print(f"Annual Tax: ₹{details['new_regime']['tax']:,.2f}")
        print(f"Tax Rate: {details['new_regime']['tax_rate'] * 100:.2f}%")
        print(f"Monthly Tax: ₹{details['new_regime']['monthly_tax']:,.2f}")
        print(f"Annual Net: ₹{details['new_regime']['net']:,.2f}")

        tax_savings = details["tax_savings"]
        print("\n" + "=" * 60)
        print(f"RECOMMENDATION: 🎯 {recommendation}")
        print("=" * 60)
        print(f"Annual Savings with Old Regime: ₹{tax_savings:,.2f}")
        print(f"Monthly Savings: ₹{tax_savings / 12:,.2f}")

        # Ask if user wants to switch regime
        if customer.tax_regime == "NEW_REGIME":
            switch_choice = (
                input("\nSwitch to Old Regime (with deductions)? (yes/no): ")
                .strip()
                .lower()
            )
            if switch_choice in ["yes", "y"]:
                customer.tax_regime = "OLD_REGIME"
                self.bank.save()
                print("[SUCCESS] Tax regime switched to OLD_REGIME")
        elif customer.tax_regime == "OLD_REGIME":
            switch_choice = (
                input("\nSwitch to New Regime (no deductions)? (yes/no): ")
                .strip()
                .lower()
            )
            if switch_choice in ["yes", "y"]:
                customer.tax_regime = "NEW_REGIME"
                self.bank.save()
                print("[SUCCESS] Tax regime switched to NEW_REGIME")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    app = BankingApp()
    app.run()