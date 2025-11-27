from typing import List, Optional, Tuple

from Account import Account
from BankClock import BankClock
from Customer import Customer
from DataStore import DataStore
from loan import Loan  # Import Loan class

# EXTENSION: Optional if using LoanEvaluator in your CLI
from LoanEvaluator import LoanEvaluator
from Transaction import Transaction


class Bank:
    """Bank class for managing customers, accounts, and loans"""

    def __init__(self):
        self.accounts: List[Account] = DataStore.load_accounts()
        self.customers: List[Customer] = DataStore.load_customers()
        self.loans: List[Loan] = DataStore.load_loans()

    def save(self):
        """Save all accounts, customers, and loans to persistent storage"""
        DataStore.save_accounts(self.accounts)
        DataStore.save_customers(self.customers)
        DataStore.save_loans(self.loans)

    # ... Existing authentication, registration, account, and transaction methods ...

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

    def get_account(self, account_number: str) -> Optional[Account]:
        for account in self.accounts:
            if account.account_number == account_number:
                return account
        return None

    def search_transaction_by_id(
        self, txn_id: str
    ) -> Optional[Tuple[Account, Transaction]]:
        for account in self.accounts:
            for transaction in account.transactions:
                if transaction.id == txn_id:
                    return (account, transaction)
        return None

    def find_account_by_number(self, account_number: str) -> Optional[Account]:
        return self.get_account(account_number)

    def are_same_customer_accounts(self, acc1: Account, acc2: Account) -> bool:
        return (
            acc1.customer_id == acc2.customer_id
            and acc1.customer_id
            and acc1.customer_id != ""
        )

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

        # Update loan and account
        account.balance -= emi_amount
        loan.emis_paid += 1

        if loan.emis_paid >= loan.tenure_months:
            loan.status = "Closed"
            loan.closure_date = BankClock.today()  # Add closure date
            print("Loan fully repaid and closed.")

        # Log transaction
        from BankClock import BankClock

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

    # ========== LOAN APPLICATION (EVALUATOR/APPROVAL WRAPPER) ==========

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

        from BankClock import BankClock

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

        # Disburse to account - FIXED VERSION
        old_balance = account.balance
        account.balance += principal

        # CREATE TRANSACTION RECORD FOR LOAN DISBURSEMENT
        # Generate unique transaction ID using timestamp
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

        # Add loan to bank's loan list
        self.add_loan(loan)

        # Save everything
        self.save()

        print("\n✅ Loan Disbursed!")
        print(f"Loan ID: {loan_id}")
        print(f"Amount Credited: ₹{principal:,.2f}")
        print(f"Previous Balance: ₹{old_balance:,.2f}")
        print(f"New Balance: ₹{account.balance:,.2f}")

        return True, loan, "Loan approved and credited"


# End of class
