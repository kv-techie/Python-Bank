from datetime import date
from typing import Dict, List
import sys
import os

# Add parent directory to sys.path to support both direct execution and package imports
if __name__ == "__main__" and __package__ is None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
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
    from .Logger import BankLogger
    from .PasswordRecovery import PasswordRecoveryUI
    from .RDStatement import RDStatement
    from .RecurringBill import PaymentMethod, RecurringBill, RecurringBillFactory
    from .RecurringDeposit import RecurringDeposit
    from .TaxCalculator import TaxCalculator
    from .TaxDeductionAnalyzer import TaxDeductionAnalyzer
    from .TaxExemption import DeductionStatus, DeductionType, TaxExemption
    from .Transaction import Transaction
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
    from .Logger import BankLogger
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
        self.logger = BankLogger.get_logger("BankingApp")
        
        # Initialize services
        from .services.TaxService import TaxService
        from .services.CardService import CardService
        from .services.TransferService import TransferService
        self.tax_service = TaxService(self.bank, self.logger)
        self.card_service = CardService(self.bank, self.logger)
        self.transfer_service = TransferService(self.bank, self.logger)
        
        # Initialize CLI Handlers
        from backend.cli.TaxCLI import TaxCLI
        from backend.cli.CardCLI import CardCLI
        from backend.cli.TransferCLI import TransferCLI
        from backend.cli.LoanCLI import LoanCLI
        from backend.cli.ChequeCLI import ChequeCLI
        from backend.cli.DepositCLI import DepositCLI
        from backend.cli.TransactionCLI import TransactionCLI
        self.tax_cli = TaxCLI(self.bank, self)
        self.card_cli = CardCLI(self.bank, self)
        self.transfer_cli = TransferCLI(self.bank, self)
        self.loan_cli = LoanCLI(self.bank, self)
        self.cheque_cli = ChequeCLI(self.bank, self)
        self.deposit_cli = DepositCLI(self.bank, self)
        self.transaction_cli = TransactionCLI(self.bank, self)

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
                self.transaction_cli.view_balance(selected_account)
            elif menu_choice == "2":
                self.transaction_cli.deposit_money(selected_account)
            elif menu_choice == "3":
                self.transaction_cli.withdraw_money(selected_account)
            elif menu_choice == "4":
                self.transfer_cli.transfer_funds(customer, selected_account, accounts)
            elif menu_choice == "5":
                self.transaction_cli.view_transaction_history_menu(selected_account)
            elif menu_choice == "6":
                self.transaction_cli.search_transaction()
            elif menu_choice == "7":
                self.transaction_cli.view_swift_transactions(selected_account)
            elif menu_choice == "8":
                selected_account = self.switch_account(accounts)
            elif menu_choice == "9":
                accounts = self.create_additional_account(customer, accounts)
            elif menu_choice == "10":
                self.card_cli.manage_recurring_bills(selected_account)
            elif menu_choice == "11":
                self.tax_cli.manage_salary(selected_account)
            elif menu_choice == "12":
                self.simulate_time(selected_account)
            elif menu_choice == "13":
                self.transaction_cli.view_expense_analysis(selected_account)
            elif menu_choice == "14":
                self.loan_cli.loan_menu(customer, selected_account)
            elif menu_choice == "15":
                self.card_cli.card_management_menu(selected_account)
            elif menu_choice == "16":
                self.cheque_cli.cheque_management_menu(selected_account)
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
                self.deposit_cli.fd_rd_menu(customer, selected_account)
            elif menu_choice == "20":
                self.change_clock_mode()
            elif menu_choice == "21":
                self.tax_cli.tax_planning_menu(customer, selected_account)
            elif menu_choice == "22":
                self.transfer_cli.manage_beneficiaries_menu(customer)
            elif menu_choice == "23":
                print("Logged out successfully.")
                active = False


    # ========== BENEFICIARY MANAGEMENT ==========
    


    # ========== CARD MANAGEMENT ==========



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

