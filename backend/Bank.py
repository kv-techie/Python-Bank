from typing import List, Optional, Tuple

from Account import Account
from BankClock import BankClock
from Card import CreditCard, DebitCard
from CreditEvaluator import CreditEvaluator
from Customer import Customer
from DataStore import DataStore
from FixedDeposit import FixedDeposit
from loan import Loan
from LoanEvaluator import LoanEvaluator
from RDAuthorization import RDAuthorization  # NEW: Import authorization manager
from RecurringDeposit import RecurringDeposit
from Transaction import Transaction


class Bank:
    """Bank class for managing customers, accounts, loans, and cards"""

    def __init__(self):
        self.accounts: List[Account] = []
        self.customers: List[Customer] = []
        self.loans: List[Loan] = []
        self.credit_cards: List[CreditCard] = []
        self.international_registry = None
        self.fixed_deposits = {}
        self.recurring_deposits = {}
        self.rd_authorizations = None  # NEW: RD authorization manager
        self.load()  # Load all data

    def load(self):
        """Load all bank data from JSON files"""
        self.accounts = DataStore.load_accounts()
        self.customers = DataStore.load_customers()
        self.loans = DataStore.load_loans()
        self.international_registry = DataStore.load_international_accounts()
        self.fixed_deposits = DataStore.load_fixed_deposits()
        self.recurring_deposits = DataStore.load_recurring_deposits()
        self.rd_authorizations = (
            DataStore.load_rd_authorizations()
        )  # NEW: Load authorizations

    def save(self):
        """Save all accounts, customers, and loans to persistent storage"""
        DataStore.save_accounts(self.accounts)
        DataStore.save_customers(self.customers)
        DataStore.save_loans(self.loans)

        if hasattr(self, "international_registry") and self.international_registry:
            DataStore.save_international_accounts(
                self.international_registry, verbose=False
            )
        DataStore.save_fixed_deposits(self.fixed_deposits)
        DataStore.save_recurring_deposits(self.recurring_deposits)

        # NEW: Save authorizations
        if hasattr(self, "rd_authorizations") and self.rd_authorizations:
            DataStore.save_rd_authorizations(self.rd_authorizations)

    def save_data(self):
        """Alias for save() method for compatibility"""
        self.save()

    # ========== AUTHENTICATION AND REGISTRATION ==========

    def authenticate(self, username: str, password: str) -> Optional[Customer]:
        for customer in self.customers:
            if (
                customer.username == username
                and customer.password == password
                and not customer.locked
            ):
                return customer
        return None

    def username_exists(self, username: str) -> bool:
        return any(cust.username == username for cust in self.customers)

    def register_customer(
        self,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        phone_number: str,
        email: str,
        account_type: str,
    ) -> Tuple[Customer, Account]:
        account_number = Account.generate_account_number()
        customer = Customer.create_customer(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            email=email,
            initial_account_number=account_number,
        )
        account = Account.create_account(
            customer_id=customer.customer_id,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            account_type=account_type,
            account_number=account_number,
        )
        self.customers.append(customer)
        self.accounts.append(account)
        self.save()
        return (customer, account)

    def add_account_to_customer(self, customer: Customer, account_type: str) -> Account:
        account = Account.create_account(
            customer_id=customer.customer_id,
            username=customer.username,
            password=customer.password,
            first_name=customer.first_name,
            last_name=customer.last_name,
            dob=customer.dob,
            gender=customer.gender,
            account_type=account_type,
        )
        customer.add_account(account.account_number)
        self.accounts.append(account)
        self.save()
        return account

    # ========== CUSTOMER MANAGEMENT ==========

    def get_customer(self, username: str) -> Optional[Customer]:
        for customer in self.customers:
            if customer.username == username:
                return customer
        return None

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        for customer in self.customers:
            if customer.customer_id == customer_id:
                return customer
        return None

    def get_customer_accounts(self, customer: Customer) -> List[Account]:
        account_numbers = customer.get_account_numbers()
        customer_accounts = []
        for acc_num in account_numbers:
            account = self.get_account(acc_num)
            if account:
                customer_accounts.append(account)
        return customer_accounts

    # ========== ACCOUNT MANAGEMENT ==========

    def get_account(self, account_number: str) -> Optional[Account]:
        for account in self.accounts:
            if account.account_number == account_number:
                return account
        return None

    def find_account_by_number(self, account_number: str) -> Optional[Account]:
        return self.get_account(account_number)

    def are_same_customer_accounts(self, acc1: Account, acc2: Account) -> bool:
        return (
            acc1.customer_id == acc2.customer_id
            and acc1.customer_id
            and acc1.customer_id != ""
        )

    # ========== TRANSACTION MANAGEMENT ==========

    def search_transaction_by_id(
        self, txn_id: str
    ) -> Optional[Tuple[Account, Transaction]]:
        for account in self.accounts:
            for transaction in account.transactions:
                if transaction.id == txn_id:
                    return (account, transaction)
        return None

    def search_transaction_by_cheque_id(
        self, cheque_id: str
    ) -> Optional[Tuple[Account, Transaction]]:
        for account in self.accounts:
            for transaction in account.transactions:
                if transaction.cheque_id == cheque_id and transaction.type.endswith(
                    "_SENT"
                ):
                    return (account, transaction)
        return None

    def show_cheque_details(self, cheque_id: str):
        result = self.search_transaction_by_cheque_id(cheque_id)
        if result:
            sender_acc, txn = result
            print("\n=== Cheque Details ===")
            print(f"Cheque ID: {cheque_id}")
            print(f"Sender Name: {sender_acc.first_name} {sender_acc.last_name}")
            print(f"Sender Account Number: {sender_acc.account_number}")
            print(f"Sender IFSC: {Account.BRANCH_IFSC}")
            print(f"Sender Branch: {Account.BRANCH_NAME}")
            print(f"Amount Transferred: ₹{txn.amount:.2f}")
            if txn.type.startswith("NEFT"):
                mode = "NEFT"
            elif txn.type.startswith("RTGS"):
                mode = "RTGS"
            elif txn.type.startswith("INTER_ACCOUNT"):
                mode = "Inter-Account"
            else:
                mode = "Other"
            print(f"Transfer Mode: {mode}")
            print(f"Timestamp: {txn.timestamp}")
            print(f"Transaction ID: {txn.id}")
        else:
            print(f"❌ No transaction found for Cheque ID: {cheque_id}")

    # ========== STATISTICS ==========

    def get_total_accounts(self) -> int:
        return len(self.accounts)

    def get_total_customers(self) -> int:
        return len(self.customers)

    def get_total_balance(self) -> float:
        return sum(account.balance for account in self.accounts)

    def get_accounts_by_type(self, account_type: str) -> List[Account]:
        return [
            account for account in self.accounts if account.account_type == account_type
        ]

    def get_minor_accounts(self) -> List[Account]:
        return [
            account for account in self.accounts if account.account_type == "Future"
        ]

    # ========== LOAN MANAGEMENT ==========

    def add_loan(self, loan: Loan):
        """Add a new loan to the bank and persist."""
        self.loans.append(loan)
        DataStore.save_loans(self.loans)

    def get_loans_for_customer(self, customer_id: str) -> List[Loan]:
        """Retrieve all loans for a given customer_id."""
        return [loan for loan in self.loans if loan.customer_id == customer_id]

    def pay_emi_for_loan(self, loan_id: str, account_number: str):
        """
        Process EMI payment for a loan, debiting account balance and updating loan.
        """
        loan = next((ln for ln in self.loans if ln.loan_id == loan_id), None)
        account = self.get_account(account_number)
        if not loan or not account:
            print("Invalid loan or account.")
            return

        emi_amount = loan.calculate_emi()
        if account.balance < emi_amount:
            print("Insufficient balance to pay EMI.")
            return

        account.balance -= emi_amount
        loan.emis_paid += 1

        if loan.emis_paid >= loan.tenure_months:
            loan.status = "Closed"
            loan.closure_date = BankClock.today()
            print("Loan fully repaid and closed.")

        ts = BankClock.get_formatted_datetime()
        txn_id = f"EMI{loan.loan_id}{loan.emis_paid:02d}"
        txn = Transaction(
            id=txn_id,
            type="LOAN_EMI",
            amount=emi_amount,
            resulting_balance=account.balance,
            timestamp=ts,
            cheque_id=None,
            metadata=f"loan_id={loan.loan_id};emi_no={loan.emis_paid}",
        )
        account.transactions.append(txn)
        self.save()
        print(
            f"EMI of Rs.{emi_amount} paid for loan {loan.loan_id}. Remaining EMIs: {loan.tenure_months - loan.emis_paid}"
        )

    def pay_multiple_emis_for_loan(self, loan_id: str, account_number: str, count: int):
        """
        Process payment for multiple EMIs at once, if sufficient balance.
        """
        loan = next((ln for ln in self.loans if ln.loan_id == loan_id), None)
        account = self.get_account(account_number)
        if not loan or not account:
            print("Invalid loan or account.")
            return

        pending = loan.tenure_months - loan.emis_paid
        if count > pending:
            print("Trying to pay too many EMIs.")
            return

        emi_amount = loan.calculate_emi()
        total_amount = emi_amount * count
        if account.balance < total_amount:
            print(
                f"Insufficient balance for {count} EMIs (You need Rs. {total_amount:.2f})"
            )
            return

        for _ in range(count):
            self.pay_emi_for_loan(loan_id, account_number)

    def show_loans_for_customer(self, customer_id: str):
        loans = self.get_loans_for_customer(customer_id)
        if not loans:
            print("No loans found for this customer.")
            return
        print("\n=== Loan Summary ===")
        for loan in loans:
            print(
                f"Loan ID: {loan.loan_id} | Principal: ₹{loan.principal:.2f} | EMI: ₹{loan.calculate_emi():.2f} | Tenure: {loan.tenure_months} months"
            )
            print(
                f"Status: {loan.status} | EMIs Paid: {loan.emis_paid}/{loan.tenure_months}"
            )
            if getattr(loan, "approval_reason", None):
                print(f"Notes: {loan.approval_reason}")
            print("")

    def evaluate_and_add_loan(
        self,
        customer: Customer,
        principal: float,
        interest_rate: float,
        tenure_months: int,
        account: Account,
    ) -> Tuple[bool, Optional[Loan], str]:
        """
        Evaluates, creates, and (if approved) adds/disburses the loan. Returns (approved, Loan/None, reason).
        """
        approved, reason = LoanEvaluator.evaluate(
            customer, principal, tenure_months, interest_rate, self
        )
        if not approved:
            return False, None, reason

        from datetime import datetime

        loan_id = f"LOAN{len(self.loans) + 1:06d}"

        loan = Loan(
            loan_id=loan_id,
            customer_id=customer.customer_id,
            principal=principal,
            interest_rate=interest_rate,
            tenure_months=tenure_months,
            approval_reason=reason,
            status="Active",
            start_date=BankClock.today(),
        )

        old_balance = account.balance
        account.balance += principal

        timestamp_int = int(datetime.now().timestamp())
        txn_id = f"TXN{timestamp_int}{len(account.transactions):04d}"

        loan_disbursement = Transaction(
            id=txn_id,
            type="LOAN_CREDIT",
            amount=principal,
            resulting_balance=account.balance,
            timestamp=BankClock.get_formatted_datetime(),
            cheque_id=None,
            metadata=f"loan_id={loan_id};principal={principal:.2f};tenure={tenure_months}months;rate={interest_rate}%",
        )
        account.transactions.append(loan_disbursement)

        self.add_loan(loan)
        self.save()

        print("\n✅ Loan Disbursed!")
        print(f"Loan ID: {loan_id}")
        print(f"Amount Credited: ₹{principal:,.2f}")
        print(f"Previous Balance: ₹{old_balance:,.2f}")
        print(f"New Balance: ₹{account.balance:,.2f}")

        return True, loan, "Loan approved and credited"

    # ========== CREDIT CARD MANAGEMENT ==========

    def get_credit_cards_for_customer(self, customer_id: str) -> List[CreditCard]:
        """Get all credit cards for a specific customer"""
        all_cards = []
        for account in self.accounts:
            if account.customer_id == customer_id:
                for card in account.cards:
                    if isinstance(card, CreditCard):
                        all_cards.append(card)
        return all_cards

    def issue_debit_card(self, customer: Customer, account: Account) -> DebitCard:
        """Issue a new debit card for an account"""
        debit_card = DebitCard(customer.customer_id, account.account_number)
        account.add_card(debit_card)
        self.save()
        return debit_card

    def issue_credit_card(
        self, customer: Customer, account: Account, credit_limit: float = None
    ) -> CreditCard:
        """Issue a new credit card for an account"""
        if credit_limit is None:
            from datetime import datetime

            dob = datetime.strptime(customer.dob, "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365

            if hasattr(customer, "salary") and customer.salary:
                annual_income = customer.salary * 12
            else:
                annual_income = 180000

            cibil_score = getattr(customer, "cibil_score", 650)

            credit_limit = CreditEvaluator.calculate_credit_limit(
                cibil_score=cibil_score,
                annual_income=annual_income,
                age=age,
                existing_debt=0.0,
                employer_category=getattr(customer, "employer_category", "pvt"),
                has_salary_account=getattr(customer, "has_salary_account", False),
            )

        credit_card = CreditCard(
            customer.customer_id, account.account_number, credit_limit
        )
        account.add_card(credit_card)

        if not hasattr(customer, "credit_cards"):
            customer.credit_cards = []
        customer.credit_cards.append(
            {
                "card_id": credit_card.card_id,
                "limit": credit_limit,
                "used": 0.0,
                "opened": BankClock.today(),
            }
        )

        self.save()
        print(
            f"Credit card issued with limit: Rs. {credit_limit:,}, Number: {credit_card.card_number}"
        )
        return credit_card

    # ========== DAILY AUTOMATED TASKS ==========

    def process_daily_tasks(self):
        """Process all daily automated tasks"""
        today = BankClock.today()

        print(f"\n{'=' * 60}")
        print(f"Processing Daily Tasks for {today.strftime('%d-%m-%Y')}")
        print(f"{'=' * 60}\n")
        total_processed = 0

        for account in self.accounts:
            bills_processed = account.process_recurring_bills(today, self)
            total_processed += bills_processed

            if account.salary_profile and account.salary_profile.should_credit_today(
                today
            ):
                print(f"  💰 Crediting salary for {account.username}")
                success, msg = account.salary_profile.credit_salary(account)
                print(f"  Result: {msg}")
            else:
                if account.salary_profile:
                    print(
                        f"  ⏭️  Skipping salary for {account.username} (not due today or already processed)"
                    )

            account.process_credit_card_bills(today)

        self.save()
        print(f"\n{'=' * 60}")
        print("Daily tasks completed")
        print(f"{'=' * 60}\n")

        return total_processed

    # ========== FIXED DEPOSITS ==========

    def create_fixed_deposit(
        self,
        account: "Account",
        principal_amount: float,
        tenure_months: int,
    ) -> Tuple[bool, str, Optional[FixedDeposit]]:
        """Create a new Fixed Deposit"""

        if principal_amount < FixedDeposit.MIN_AMOUNT:
            return (
                False,
                f"Minimum FD amount is Rs. {FixedDeposit.MIN_AMOUNT:,.2f}",
                None,
            )

        if principal_amount > FixedDeposit.MAX_AMOUNT:
            return (
                False,
                f"Maximum FD amount is Rs. {FixedDeposit.MAX_AMOUNT:,.2f}",
                None,
            )

        if tenure_months not in FixedDeposit.INTEREST_RATES:
            valid_tenures = ", ".join(
                str(t) for t in sorted(FixedDeposit.INTEREST_RATES.keys())
            )
            return False, f"Invalid tenure. Valid options: {valid_tenures} months", None

        min_balance = account._min_operational_balance
        if account.balance - principal_amount < min_balance:
            return (
                False,
                f"Insufficient balance. Required: Rs. {principal_amount:,.2f} + Rs. {min_balance:,.2f} minimum balance",
                None,
            )

        account.balance -= principal_amount

        from datetime import datetime

        is_senior_citizen = False
        customer = self.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior_citizen = age >= 60
            except (ValueError, AttributeError):
                pass

        interest_rate = FixedDeposit.get_applicable_rate(
            tenure_months, is_senior_citizen
        )

        fd_number = FixedDeposit.generate_fd_number()
        fd = FixedDeposit(
            fd_number=fd_number,
            account_number=account.account_number,
            principal_amount=principal_amount,
            tenure_months=tenure_months,
            interest_rate=interest_rate,
            is_senior_citizen=is_senior_citizen,
        )

        self.fixed_deposits[fd_number] = fd

        txn = Transaction(
            type="FD_OPENED",
            amount=-principal_amount,
            resulting_balance=account.balance,
            metadata={
                "fd_number": fd_number,
                "tenure_months": tenure_months,
                "interest_rate": interest_rate,
                "maturity_amount": fd.maturity_amount,
                "maturity_date": fd.maturity_date.strftime("%d-%m-%Y"),
            },
        )
        account.transactions.append(txn)

        message = f"""
✅  Fixed Deposit Created Successfully!

FD Number: {fd_number}
Principal: Rs. {principal_amount:,.2f}
Tenure: {tenure_months} months
Interest Rate: {interest_rate}% p.a.
{"(Senior Citizen Rate)" if is_senior_citizen else ""}
Maturity Date: {fd.maturity_date.strftime("%d-%m-%Y")}
Maturity Amount: Rs. {fd.maturity_amount:,.2f}

Your account has been debited Rs. {principal_amount:,.2f}
New Balance: Rs. {account.balance:,.2f}
"""
        return True, message, fd

    def get_fds_for_account(self, account_number: str) -> List[FixedDeposit]:
        """Get all FDs for a specific account"""
        return [
            fd
            for fd in self.fixed_deposits.values()
            if fd.account_number == account_number
        ]

    def get_fd_by_number(self, fd_number: str) -> Optional[FixedDeposit]:
        """Get FD by FD number"""
        return self.fixed_deposits.get(fd_number)

    # ========== RECURRING DEPOSITS ==========

    def create_recurring_deposit(
        self,
        account: "Account",
        monthly_installment: float,
        tenure_months: int,
        enable_autopay: bool = False,
        autopay_day: int = 1,
    ) -> Tuple[bool, str, Optional[RecurringDeposit]]:
        """Create a new Recurring Deposit"""

        if monthly_installment < RecurringDeposit.MIN_MONTHLY_AMOUNT:
            return (
                False,
                f"Minimum monthly installment is Rs. {RecurringDeposit.MIN_MONTHLY_AMOUNT:,.2f}",
                None,
            )

        if monthly_installment > RecurringDeposit.MAX_MONTHLY_AMOUNT:
            return (
                False,
                f"Maximum monthly installment is Rs. {RecurringDeposit.MAX_MONTHLY_AMOUNT:,.2f}",
                None,
            )

        if tenure_months not in RecurringDeposit.INTEREST_RATES:
            valid_tenures = ", ".join(
                str(t) for t in sorted(RecurringDeposit.INTEREST_RATES.keys())
            )
            return False, f"Invalid tenure. Valid options: {valid_tenures} months", None

        from datetime import datetime

        is_senior_citizen = False
        customer = self.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior_citizen = age >= 60
            except (ValueError, AttributeError):
                pass

        interest_rate = RecurringDeposit.get_applicable_rate(
            tenure_months, is_senior_citizen
        )

        rd_number = RecurringDeposit.generate_rd_number()
        rd = RecurringDeposit(
            rd_number=rd_number,
            account_number=account.account_number,
            monthly_installment=monthly_installment,
            tenure_months=tenure_months,
            interest_rate=interest_rate,
            is_senior_citizen=is_senior_citizen,
            autopay_enabled=enable_autopay,
            autopay_day=autopay_day,
        )

        self.recurring_deposits[rd_number] = rd

        txn = Transaction(
            type="RD_OPENED",
            amount=0.0,
            resulting_balance=account.balance,
            metadata={
                "rd_number": rd_number,
                "monthly_installment": monthly_installment,
                "tenure_months": tenure_months,
                "interest_rate": interest_rate,
                "maturity_amount": rd.calculate_maturity_amount(),
                "maturity_date": rd.maturity_date.strftime("%d-%m-%Y"),
                "autopay_enabled": enable_autopay,
            },
        )
        account.transactions.append(txn)

        autopay_info = ""
        if enable_autopay:
            autopay_info = f"\n✓ Autopay enabled: Rs. {monthly_installment:,.2f} on day {autopay_day} of each month"
            autopay_info += (
                f"\nNext Autopay: {rd.next_autopay_date.strftime('%d-%m-%Y')}"
            )

        message = f"""
✅ Recurring Deposit Created Successfully!

RD Number: {rd_number}
Monthly Installment: Rs. {monthly_installment:,.2f}
Tenure: {tenure_months} months
Interest Rate: {interest_rate}% p.a.
{" (Senior Citizen Rate)" if is_senior_citizen else ""}
Maturity Date: {rd.maturity_date.strftime("%d-%m-%Y")}
Expected Maturity Amount: Rs. {rd.calculate_maturity_amount():,.2f}
{autopay_info}
"""
        return True, message, rd

    def process_all_autopay_rds(self) -> List[Tuple[str, bool, str]]:
        """
        Process autopay for all active RDs (WITH AUTHORIZATION SUPPORT)
        Returns: List of (rd_number, success, message)
        """
        results = []

        for rd in self.recurring_deposits.values():
            if rd.autopay_enabled and rd.status == "Active":
                # NEW: Check if there's an authorization
                auth = self.rd_authorizations.get_authorization_for_rd(rd.rd_number)

                if auth and auth.is_active():
                    # Use payer's account for authorized payment
                    payer_account = self.get_account(auth.payer_account_number)
                    if payer_account:
                        success, message = (
                            self.rd_authorizations.process_authorized_payment(
                                rd.rd_number,
                                rd.monthly_installment,
                                rd.installments_paid + 1,
                                payer_account,
                            )
                        )

                        if success:
                            # Update RD's payment tracking
                            payment = {
                                "date": BankClock.now().isoformat(),
                                "amount": rd.monthly_installment,
                                "installment_number": rd.installments_paid + 1,
                                "method": "Autopay (Authorized)",
                            }
                            rd.payment_history.append(payment)
                            rd.installments_paid += 1
                            rd.total_deposited += rd.monthly_installment

                            # Check if completed
                            if rd.installments_paid >= rd.tenure_months:
                                rd.status = "Completed"
                            else:
                                rd.next_autopay_date = rd._calculate_next_autopay_date()

                        results.append((rd.rd_number, success, message))
                else:
                    # No authorization - use beneficiary's own account (original logic)
                    account = self.get_account(rd.account_number)
                    if account:
                        success, message = rd.process_autopay(account)
                        if success or "Failed" in message:
                            results.append((rd.rd_number, success, message))

        return results

    def get_rds_for_account(self, account_number: str) -> List[RecurringDeposit]:
        """Get all RDs for a specific account"""
        return [
            rd
            for rd in self.recurring_deposits.values()
            if rd.account_number == account_number
        ]

    def get_rd_by_number(self, rd_number: str) -> Optional[RecurringDeposit]:
        """Get RD by RD number"""
        return self.recurring_deposits.get(rd_number)

    # ========== RD AUTHORIZATION MANAGEMENT (NEW) ==========

    def create_rd_authorization(
        self,
        rd_number: str,
        payer_customer: Customer,
        payer_account: Account,
    ) -> Tuple[bool, str, Optional["RDAuthorization"], Optional[str]]:
        """
        Create authorization for cross-account RD payment
        Returns: (success, message, authorization, otp)
        """
        rd = self.get_rd_by_number(rd_number)
        if not rd:
            return False, f"RD {rd_number} not found", None, None

        beneficiary_account = self.get_account(rd.account_number)
        if not beneficiary_account:
            return False, "Beneficiary account not found", None, None

        # Set limit with 10% buffer for flexibility
        monthly_limit = rd.monthly_installment * 1.1

        # Create authorization with OTP
        success, message, auth, otp = self.rd_authorizations.create_authorization(
            rd_number=rd_number,
            beneficiary_customer_id=beneficiary_account.customer_id,
            beneficiary_account_number=rd.account_number,
            payer_customer_id=payer_customer.customer_id,
            payer_account_number=payer_account.account_number,
            monthly_limit=monthly_limit,
        )

        if success:
            self.save()

        return success, message, auth, otp

    def verify_rd_authorization(
        self, auth_id: str, otp: str, verifier_customer_id: str
    ) -> Tuple[bool, str]:
        """Verify RD authorization with OTP from payer's side"""
        success, message = self.rd_authorizations.verify_authorization(
            auth_id, otp, verifier_customer_id
        )

        if success:
            self.save()

        return success, message

    def get_rd_authorization_by_id(self, auth_id: str) -> Optional["RDAuthorization"]:
        """Get authorization by ID"""
        return self.rd_authorizations.get_authorization_by_id(auth_id)

    def get_pending_authorizations_for_payer(
        self, customer_id: str
    ) -> List["RDAuthorization"]:
        """Get authorizations pending OTP verification for a payer"""
        return self.rd_authorizations.get_pending_authorizations_for_payer(customer_id)

    def get_rd_authorization(self, rd_number: str):
        """Get authorization for an RD"""
        return self.rd_authorizations.get_authorization_for_rd(rd_number)

    def get_authorizations_as_payer(self, customer_id: str):
        """Get all authorizations where customer is paying"""
        return self.rd_authorizations.get_authorizations_by_payer(customer_id)

    def get_authorizations_as_beneficiary(self, customer_id: str):
        """Get all authorizations where customer is beneficiary"""
        return self.rd_authorizations.get_authorizations_by_beneficiary(customer_id)

    def revoke_rd_authorization(
        self, auth_id: str, reason: str, revoked_by: str
    ) -> Tuple[bool, str]:
        """Revoke an RD authorization"""
        success, message = self.rd_authorizations.revoke_authorization(
            auth_id, reason, revoked_by
        )
        if success:
            self.save()
        return success, message


# End of Bank class
