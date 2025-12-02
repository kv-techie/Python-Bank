from datetime import date
from typing import List

from Account import Account
from Bank import Bank
from BankClock import BankClock
from Card import Card, CreditCard, DebitCard
from CIBIL import add_credit_inquiry, calculate_cibil_score
from ClosureFormalities import ClosureFormalities
from CreditEvaluator import CreditEvaluator
from Customer import Customer
from ExpenseSimulator import ExpenseSimulator
from RecurringBill import RecurringBill


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
    def read_positive_double(prompt: str) -> float:
        """Read and validate a positive number"""
        while True:
            try:
                value = float(input(prompt))
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

        accounts = self.bank.get_customer_accounts(customer)
        if not accounts:
            print("No accounts found for this customer.")
            return

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
7   Switch Account
8   Create Additional Account
9   Manage Recurring Bills
10  Manage Salary
11  Simulate Time (Fast Forward)
12  View Expense Analysis
13  Loan Menu
14  Card Management
15  Close Card
16  Close Account
17  Logout
        """)
            menu_choice = self.read_valid_choice(
                "Enter your choice: ",
                [str(i) for i in range(1, 18)],
                "Invalid choice. Please enter a number from 1 to 17.",
            )

            if menu_choice == "1":
                self.view_balance(selected_account)
            elif menu_choice == "2":
                self.deposit_money(selected_account)
            elif menu_choice == "3":
                self.withdraw_money(selected_account)
            elif menu_choice == "4":
                self.transfer_funds(selected_account, accounts)
            elif menu_choice == "5":
                self.view_transaction_history_menu(selected_account)
            elif menu_choice == "6":
                self.search_transaction()
            elif menu_choice == "7":
                selected_account = self.switch_account(accounts)
            elif menu_choice == "8":
                accounts = self.create_additional_account(customer, accounts)
            elif menu_choice == "9":
                self.manage_recurring_bills(selected_account)
            elif menu_choice == "10":
                self.manage_salary(selected_account)
            elif menu_choice == "11":
                self.simulate_time(selected_account)
            elif menu_choice == "12":
                self.view_expense_analysis(selected_account)
            elif menu_choice == "13":
                self.loan_menu(customer, selected_account)
            elif menu_choice == "14":
                self.card_management_menu(selected_account)
            elif menu_choice == "15":
                ClosureFormalities.close_card_menu(selected_account, self.bank)
            elif menu_choice == "16":
                closure_success = ClosureFormalities.close_account_menu(
                    selected_account, customer, accounts, self.bank
                )
                if closure_success:
                    # Account was closed, exit to main menu
                    active = False
            elif menu_choice == "17":
                print("Logged out successfully.")
                active = False

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
            print("10. Back to Main Menu")
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
                break

            else:
                print("Invalid choice")

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
        print(f"\n✓ {network} Debit card issued successfully!")
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

        print(f"✓ {reason}")
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
        print(f"\n✓ {network} Credit card issued successfully!")
        print(f"Billing Day: {billing_day} of each month")
        print(
            f"Total credit cards: {len([c for c in account.cards if isinstance(c, CreditCard)])}"
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
        """Pay credit card bill"""
        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("No credit cards available")
            return

        print("\n--- Pay Credit Card Bill ---")

        for card in credit_cards:
            print(f"\nCard: **** **** **** {card.card_number[-4:]}")
            print(f"Outstanding: Rs. {card.credit_used:,.2f} INR")
            if card.outstanding_balance > 0:
                print(f"Bill Amount: Rs. {card.outstanding_balance:,.2f} INR")
                print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card or not isinstance(card, CreditCard):
            print("Credit card not found")
            return

        print(f"\nAccount Balance: Rs. {account.balance:,.2f} INR")
        print(f"Amount to Pay (Outstanding: Rs. {card.credit_used:,.2f} INR)")

        try:
            amount = float(input("Enter payment amount: ").strip())
            account.pay_credit_card_bill(card.card_id, amount)
            self.bank.save()

        except ValueError:
            print("Invalid amount")

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

    # ========== LOAN MENU AND OPERATIONS ==========

    def loan_menu(self, customer: Customer, account: Account):
        while True:
            print("""
Loan Menu:
1  Apply for Loan
2  View My Loans
3  Pay Loan EMI
4  CIBIL Score Report
5  Generate Loan Closure Certificate                  
6  Back to Account Menu
            """)
            choice = self.read_valid_choice(
                "Enter choice: ", ["1", "2", "3", "4", "5", "6"]
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
                self.generate_loan_closure_certificate(customer, account)
            elif choice == "6":
                break

    def apply_for_loan(self, customer: Customer, account: Account):
        print("\n=== Loan Application ===")
        if not getattr(customer, "salary", None):
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
        print("\n🔍 Calculating your CIBIL score based on credit history...")
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

        print(f"✓ Your current CIBIL Score: {customer.cibil_score} ({rating})")

        principal = self.read_positive_double("\nEnter principal amount (Rs): ")
        interest_rate = self.read_positive_double("Enter annual interest rate (%): ")
        tenure_months = int(self.read_positive_double("Enter tenure (months): "))

        approved, loan, msg = self.bank.evaluate_and_add_loan(
            customer, principal, interest_rate, tenure_months, account
        )
        if approved:
            print(
                f"\n✔ Loan approved! Amount Rs.{principal:,.2f} credited to your account."
            )
            print(f"Loan ID: {loan.loan_id} | EMI: Rs.{loan.calculate_emi():.2f}/month")
        else:
            print(f"\n❌ Loan denied: {msg}")

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

    # ========== ORIGINAL BANKING METHODS CONTINUE BELOW ==========

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
            print("\n❌ No debit card found. You need a debit card to deposit money.")
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
        account.deposit(amount, card=selected_card)
        self.bank.save()

    def withdraw_money(self, account: Account):
        """Handle withdrawal transaction - requires debit card"""
        # Check if account has debit cards
        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n❌ No debit card found. You need a debit card to withdraw money.")
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
        account.withdraw(amount, card=selected_card)
        self.bank.save()

    def transfer_funds(self, account: Account, accounts: List[Account]):
        """Handle fund transfer (Inter-Account, NEFT, RTGS)"""
        if len(accounts) > 1:
            print("""
Choose transfer type:
1  Inter-Account (Between your own accounts)
2  NEFT (Up to Rs. 1,99,999.99)
3  RTGS (From Rs. 2,00,000.00)
            """)
            transfer_choice = self.read_valid_choice(
                "Enter choice (1-3): ", ["1", "2", "3"]
            )

            if transfer_choice == "1":
                self.inter_account_transfer(account, accounts)
            else:
                mode = "NEFT" if transfer_choice == "2" else "RTGS"
                self.external_transfer(account, mode)
        else:
            print("""
Choose transfer mode:
1  NEFT (Up to Rs. 1,99,999.99)
2  RTGS (From Rs. 2,00,000.00)
            """)
            mode = self.read_valid_transfer_mode("Enter choice (1-2): ")
            self.external_transfer(account, mode)

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

    def external_transfer(self, account: Account, mode: str):
        """Handle external transfer (NEFT/RTGS)"""
        while True:
            recipient_acc_num = input("Enter recipient's account number: ").strip()
            if not recipient_acc_num:
                print("Account number cannot be empty. Please try again.")
                continue

            recipient = self.bank.find_account_by_number(recipient_acc_num)
            if recipient and recipient.account_number != account.account_number:
                print(f"Recipient Name: {recipient.first_name} {recipient.last_name}")
                amount = self.read_positive_double("Enter amount to transfer: Rs. ")
                account.transfer(recipient, amount, mode)
                self.bank.save()
                break
            elif recipient:
                print(
                    "Cannot transfer to your own account. Please enter a different account number."
                )
            else:
                print(
                    "Recipient account not found. Please check the account number and try again."
                )

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
            print("""
Recurring Bills Management
1  View Recurring Bills
2  Add Recurring Bill
3  Remove Recurring Bill
4  Back to Main Menu
            """)

            choice = self.read_valid_choice("Enter choice: ", ["1", "2", "3", "4"])

            if choice == "1":
                account.show_recurring_bills()
            elif choice == "2":
                self.add_recurring_bill(account)
            elif choice == "3":
                self.remove_recurring_bill(account)
            elif choice == "4":
                managing = False

    def add_recurring_bill(self, account: Account):
        """Add a recurring bill"""
        print("\n=== Add Recurring Bill ===")
        print("Common bills:")

        common_bills = RecurringBill.get_common_bills()
        for idx, (name, cat, min_amt, max_amt, freq) in enumerate(common_bills, 1):
            print(
                f"{idx}. {name} ({cat}) - Rs. {min_amt:.2f}-Rs. {max_amt:.2f} ({freq})"
            )
        print(f"{len(common_bills) + 1}. Custom Bill")

        template_choice = self.read_valid_choice(
            "Select bill template: ", [str(i) for i in range(1, len(common_bills) + 2)]
        )

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
            amount = self.read_positive_double("Amount: Rs. ")
            print("Frequency: 1=Monthly, 2=Quarterly, 3=Yearly")
            freq_choice = self.read_valid_choice("Select: ", ["1", "2", "3"])
            frequency = {"1": "MONTHLY", "2": "QUARTERLY", "3": "YEARLY"}[freq_choice]

        day_of_month = int(input("Due day of month (1-28): "))

        bill = RecurringBill(
            name=name,
            base_amount=amount,
            frequency=frequency,
            day_of_month=day_of_month,
            category=category,
            auto_debit=True,
        )

        account.add_recurring_bill(bill)
        self.bank.save()

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
                account.set_salary(gross_salary, salary_day)
                self.bank.save()
            elif choice == "3":
                account.remove_salary()
                self.bank.save()
            elif choice == "4":
                managing = False

    def simulate_time(self, account: Account):
        """Simulate time passage with recurring bills and expenses"""
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

            bills_processed = account.process_recurring_bills(current_date, self.bank)
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
3  Track Cheque ID
4  Exit
            """)

            choice = self.read_valid_choice(
                "Enter your choice: ",
                ["1", "2", "3", "4"],
                "Invalid option. Please enter 1, 2, 3, or 4.",
            )

            if choice == "1":
                self.open_new_account()
            elif choice == "2":
                self.handle_login()
            elif choice == "3":
                self.track_cheque()
            elif choice == "4":
                print("Thank you for using Scala Bank!")
                self.running = False

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
        print("\n📊 REPAYMENT HISTORY")
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
                status = "✅ No late payments"
            else:
                penalty = min(200, 50 * late_payments)
                impact = f"Poor (-{penalty} points)"
                status = f"❌ {late_payments} late payment(s)"

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
        print("\n📋 CREDIT ACCOUNTS")
        n_loans = len(loans)
        n_cards = len(credit_cards)  # Use the credit_cards list from above
        total_accounts = n_loans + n_cards

        if total_accounts > 7:
            impact = "Too many accounts (-20 points)"
        elif 2 <= total_accounts <= 5:
            impact = "Optimal (+10 points)"
        else:
            impact = "Neutral"

        print(f"  Active Loans: {n_loans}")
        print(f"  Credit Cards: {n_cards}")
        print(f"  Total Accounts: {total_accounts}")
        print(f"  Impact: {impact}")

        # 4. Recent Hard Inquiries
        print("\n🔍 CREDIT INQUIRIES (Last 12 Months)")
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
                        print(f"   ✅ Loan Closed On: {loan.closure_date}")
                    else:
                        print("   ✅ All EMIs Paid - Loan Fully Repaid")
                elif outstanding > 0:
                    print(f"   Outstanding EMIs: {outstanding}")
                    if hasattr(loan, "start_date"):
                        months_elapsed = (today.year - loan.start_date.year) * 12 + (
                            today.month - loan.start_date.month
                        )
                        expected_emis = min(months_elapsed + 1, loan.tenure_months)
                        if emis_paid < expected_emis:
                            missed = expected_emis - emis_paid
                            print(f"   ⚠️  Overdue EMIs: {missed}")

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
            recommendations.append("✓ Pay all pending EMIs on time")
        if credit_cards and utilization > 50:
            recommendations.append("✓ Reduce credit card utilization below 30%")
        if n_recent > 3:
            recommendations.append("✓ Avoid applying for new credit for 6 months")
        if total_accounts < 2:
            recommendations.append(
                "✓ Consider diversifying credit types (loans + cards)"
            )
        if not recommendations:
            recommendations.append("✓ Maintain current excellent credit behavior")
            recommendations.append("✓ Continue making timely payments")

        for rec in recommendations:
            print(f"  {rec}")

        print("\n" + "=" * 70)

        # Save updated score
        self.bank.save()

    def generate_loan_closure_certificate(self, customer: Customer, account: Account):
        """Generate loan closure certificate for closed loans"""
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        closed_loans = [loan for loan in loans if loan.status == "Closed"]

        if not closed_loans:
            print(
                "\n❌ No closed loans found. You can only generate certificates for fully repaid loans."
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

        # Calculate total amount paid
        total_emi_payments = selected_loan.tenure_months * selected_loan.calculate_emi()
        total_interest = total_emi_payments - selected_loan.principal

        # Format dates
        start_date = getattr(selected_loan, "start_date", "Not available")
        if start_date != "Not available" and hasattr(start_date, "strftime"):
            start_date_str = start_date.strftime("%d-%m-%Y")
        else:
            start_date_str = "Not available"

        closure_date = getattr(selected_loan, "closure_date", "Not recorded")
        if closure_date != "Not recorded" and hasattr(closure_date, "strftime"):
            closure_date_str = closure_date.strftime("%d-%m-%Y")
        else:
            closure_date_str = "Not recorded"

        # Generate certificate
        print("\n")
        print("=" * 80)
        print(" " * 20 + "SCALA BANK - LOAN CLOSURE CERTIFICATE")
        print("=" * 80)
        print(f"\n{Account.get_branch_details()}")
        print("\n" + "-" * 80)
        print("CUSTOMER INFORMATION")
        print("-" * 80)
        print(f"Customer Name          : {customer.first_name} {customer.last_name}")
        print(f"Customer ID            : {customer.customer_id}")
        print(f"Date of Birth          : {customer.dob}")
        print(f"Contact Number         : {customer.phone_number}")
        print(f"Email Address          : {customer.email}")

        print("\n" + "-" * 80)
        print("LOAN DETAILS")
        print("-" * 80)
        print(f"Loan ID                : {selected_loan.loan_id}")
        print(f"Loan Account Number    : {account.account_number}")
        print(f"Loan Sanction Date     : {start_date_str}")
        print(f"Loan Closure Date      : {closure_date_str}")
        print(f"Loan Status            : {selected_loan.status}")

        print("\n" + "-" * 80)
        print("FINANCIAL DETAILS")
        print("-" * 80)
        print(f"Principal Amount       : Rs. {selected_loan.principal:>15,.2f} INR")
        print(
            f"Interest Rate          : {selected_loan.interest_rate:>15.2f}% per annum"
        )
        print(f"Loan Tenure            : {selected_loan.tenure_months:>15} months")
        print(
            f"Monthly EMI            : Rs. {selected_loan.calculate_emi():>15,.2f} INR"
        )
        print(
            f"Total EMIs Paid        : {selected_loan.tenure_months:>15} / {selected_loan.tenure_months}"
        )
        print(f"\nTotal Interest Paid    : Rs. {total_interest:>15,.2f} INR")
        print(f"Total Amount Paid      : Rs. {total_emi_payments:>15,.2f} INR")
        print("                         (Principal + Interest)")

        print("\n" + "-" * 80)
        print("CLOSURE CONFIRMATION")
        print("-" * 80)
        print(
            "\nThis is to certify that the above-mentioned loan has been fully repaid and"
        )
        print(
            "closed. All outstanding dues, including principal and interest, have been"
        )
        print("settled in full. No further payments are due on this loan account.")

        print(
            f"\nThe customer, {customer.first_name} {customer.last_name}, has no liability"
        )
        print(
            f"with respect to this loan (ID: {selected_loan.loan_id}) as of {closure_date_str}."
        )

        print("\n" + "-" * 80)
        print("AUTHORIZATION")
        print("-" * 80)
        print(f"\nIssued by              : Scala Bank, {Account.BRANCH_NAME} Branch")
        print(f"Certificate Date       : {BankClock.get_formatted_date()}")
        print(f"Generated At           : {BankClock.get_formatted_datetime()}")
        print(
            f"Reference Number       : CLOSURE/{selected_loan.loan_id}/{BankClock.today().strftime('%Y%m%d')}"
        )

        print("\n" + "=" * 80)
        print(" " * 15 + "*** This is a system-generated certificate ***")
        print(" " * 20 + "No signature required")
        print("=" * 80)
        print("\n")

        # Ask if user wants to save
        save = (
            input("Would you like to save this certificate? (yes/no): ").strip().lower()
        )
        if save in ["yes", "y"]:
            filename = (
                f"loan_closure_{selected_loan.loan_id}_{customer.customer_id}.txt"
            )
            try:
                with open(filename, "w") as f:
                    f.write("=" * 80 + "\n")
                    f.write(" " * 20 + "SCALA BANK - LOAN CLOSURE CERTIFICATE\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"\n{Account.get_branch_details()}\n")
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("CUSTOMER INFORMATION\n")
                    f.write("-" * 80 + "\n")
                    f.write(
                        f"Customer Name          : {customer.first_name} {customer.last_name}\n"
                    )
                    f.write(f"Customer ID            : {customer.customer_id}\n")
                    f.write(f"Date of Birth          : {customer.dob}\n")
                    f.write(f"Contact Number         : {customer.phone_number}\n")
                    f.write(f"Email Address          : {customer.email}\n")
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("LOAN DETAILS\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"Loan ID                : {selected_loan.loan_id}\n")
                    f.write(f"Loan Account Number    : {account.account_number}\n")
                    f.write(f"Loan Sanction Date     : {start_date_str}\n")
                    f.write(f"Loan Closure Date      : {closure_date_str}\n")
                    f.write(f"Loan Status            : {selected_loan.status}\n")
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("FINANCIAL DETAILS\n")
                    f.write("-" * 80 + "\n")
                    f.write(
                        f"Principal Amount       : Rs. {selected_loan.principal:>15,.2f} INR\n"
                    )
                    f.write(
                        f"Interest Rate          : {selected_loan.interest_rate:>15.2f}% per annum\n"
                    )
                    f.write(
                        f"Loan Tenure            : {selected_loan.tenure_months:>15} months\n"
                    )
                    f.write(
                        f"Monthly EMI            : Rs. {selected_loan.calculate_emi():>15,.2f} INR\n"
                    )
                    f.write(
                        f"Total EMIs Paid        : {selected_loan.tenure_months:>15} / {selected_loan.tenure_months}\n"
                    )
                    f.write(
                        f"\nTotal Interest Paid    : Rs. {total_interest:>15,.2f} INR\n"
                    )
                    f.write(
                        f"Total Amount Paid      : Rs. {total_emi_payments:>15,.2f} INR\n"
                    )
                    f.write("                         (Principal + Interest)\n")
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("CLOSURE CONFIRMATION\n")
                    f.write("-" * 80 + "\n")
                    f.write(
                        "\nThis is to certify that the above-mentioned loan has been fully repaid and\n"
                    )
                    f.write(
                        "closed. All outstanding dues, including principal and interest, have been\n"
                    )
                    f.write(
                        "settled in full. No further payments are due on this loan account.\n"
                    )
                    f.write(
                        f"\nThe customer, {customer.first_name} {customer.last_name}, has no liability\n"
                    )
                    f.write(
                        f"with respect to this loan (ID: {selected_loan.loan_id}) as of {closure_date_str}.\n"
                    )
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("AUTHORIZATION\n")
                    f.write("-" * 80 + "\n")
                    f.write(
                        f"\nIssued by              : Scala Bank, {Account.BRANCH_NAME} Branch\n"
                    )
                    f.write(
                        f"Certificate Date       : {BankClock.get_formatted_date()}\n"
                    )
                    f.write(
                        f"Generated At           : {BankClock.get_formatted_datetime()}\n"
                    )
                    f.write(
                        f"Reference Number       : CLOSURE/{selected_loan.loan_id}/{BankClock.today().strftime('%Y%m%d')}\n"
                    )
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(
                        " " * 15 + "*** This is a system-generated certificate ***\n"
                    )
                    f.write(" " * 20 + "No signature required\n")
                    f.write("=" * 80 + "\n")
                print(f"\n✓ Certificate saved as: {filename}")
            except Exception as e:
                print(f"\n❌ Error saving certificate: {e}")

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
                    from BankClock import BankClock

                    days_remaining = (card.due_date - BankClock.today()).days
                    print(
                        f"Due Date: {card.due_date.strftime('%d-%m-%Y')} ({days_remaining} days)"
                    )

        print("=" * 60)

        # Card validation
        is_valid = Card.validate_card_number(card.card_number)
        detected_network = Card.get_card_network(card.card_number)
        print(
            f"\n✓ Card Number Validation: {'Valid' if is_valid else 'Invalid'} (Luhn Check)"
        )
        print(f"✓ Detected Network from Number: {detected_network}")
        print("=" * 60)

    def view_transaction_history_menu(self, account: Account):
        """Interactive menu for viewing transaction history"""

        while True:
            print("\n" + "=" * 60)
            print("TRANSACTION HISTORY")
            print("=" * 60)

            # Quick View Options
            print("\n📊 QUICK VIEW:")
            print("1. Mini Statement (Last 10 transactions)")
            print("2. Last 20 transactions")
            print("3. Last 30 transactions")
            print("4. Last 50 transactions")
            print("5. All transactions")

            # Filter by Category
            print("\n🔍 FILTER BY CATEGORY:")
            print("6. Debit Card Transactions")
            print("7. Credit Card Transactions")
            print("8. Legacy Banking (No card)")
            print("9. Loan EMI Payments")
            print("10. NEFT Transactions")
            print("11. RTGS Transactions")
            print("12. Inter-Account Transfers")
            print("13. Salary & Tax")
            print("14. Expenses")

            print("\n15. Back to Account Menu")
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
                self.view_debit_card_transactions(account)
            elif choice == "7":
                self.view_credit_card_transactions(account)
            elif choice == "8":
                self.view_legacy_transactions(account)
            elif choice == "9":
                self.view_loan_emi_transactions(account)
            elif choice == "10":
                self.view_neft_transactions(account)
            elif choice == "11":
                self.view_rtgs_transactions(account)
            elif choice == "12":
                self.view_inter_account_transactions(account)
            elif choice == "13":
                self.view_salary_tax_transactions(account)
            elif choice == "14":
                self.view_expense_transactions(account)
            elif choice == "15":
                break
            else:
                print("Invalid choice")

    def view_debit_card_transactions(self, account: Account):
        """View transactions by specific debit card"""
        from Card import DebitCard

        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n❌ No debit cards found")
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
                print("❌ Card not found")
                return

            print(
                f"\n💳 Transactions for debit card ending in {selected_card.card_number[-4:]}:"
            )
            account.show_transactions(
                limit=limit, card_filter=selected_card.card_number[-4:]
            )

    def view_credit_card_transactions(self, account: Account):
        """View credit card payment transactions"""
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
        print("\n🏦 Loan EMI Payments:")
        account.show_transactions(limit=limit, transaction_type_filter="LOAN_EMI")

    def view_neft_transactions(self, account: Account):
        """View NEFT transactions"""
        limit = self._get_transaction_limit()
        print("\n💸 NEFT Transactions:")
        account.show_transactions(limit=limit, transaction_type_filter="NEFT")

    def view_rtgs_transactions(self, account: Account):
        """View RTGS transactions"""
        limit = self._get_transaction_limit()
        print("\n💰 RTGS Transactions:")
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


if __name__ == "__main__":
    app = BankingApp()
    app.run()
