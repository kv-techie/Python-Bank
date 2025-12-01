import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

from BankClock import BankClock
from Card import Card, CreditCard, DebitCard
from DataStore import DataStore
from RecurringBill import RecurringBill
from SalaryProfile import SalaryProfile
from Transaction import Transaction


class Account:
    """Account class for managing bank accounts"""

    BRANCH_IFSC = "SCBA0005621"
    BRANCH_NAME = "Jakkasandra"
    ACCOUNT_NUMBER_PREFIX = "5621"
    _used_account_numbers = set()
    _used_numbers_file = "data/account_numbers.txt"

    def __init__(
        self,
        customer_id: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        account_type: str,
        account_number: str,
        balance: float = 0.0,
        transactions: Optional[List[Transaction]] = None,
        failed_attempts: int = 0,
        locked: bool = False,
        pending_amb_fees: float = 0.0,
    ):
        self.customer_id = customer_id
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.gender = gender
        self.account_type = account_type
        self.account_number = account_number
        self.balance = balance
        self.transactions = transactions if transactions is not None else []
        self.failed_attempts = failed_attempts
        self.locked = locked
        self.pending_amb_fees = pending_amb_fees
        self.cards: List[Card] = []

        # Simulation features
        self.recurring_bills: List[RecurringBill] = []
        self.salary_profile: Optional[SalaryProfile] = None

        # Private constants
        self._min_operational_balance = 300.0
        self._max_deposit_per_txn = 100000.0
        self._minor_daily_withdrawal_limit = 2500.0
        self._minor_daily_transaction_limit = 10000.0
        self._amb_requirements = {
            "Pride": 2000.0,
            "Bespoke": 200000.0,
            "Club": 10000.0,
            "Delite": 5000.0,
            "Future": 0.0,
        }
        self._amb_fee_amount = 300.0

    @property
    def is_minor_account(self) -> bool:
        """Check if this is a minor account (Future type)"""
        return self.account_type == "Future"

    def get_amb_requirement(self) -> float:
        """Get Average Monthly Balance requirement for this account type"""
        return self._amb_requirements.get(self.account_type, 0.0)

    def get_today_withdrawals(self) -> float:
        """Get total withdrawals made today"""
        today = BankClock.today()
        total = 0.0

        for txn in self.transactions:
            if txn.type == "WITHDRAW":
                try:
                    txn_date = datetime.strptime(
                        txn.timestamp, "%d-%m-%Y %H:%M:%S"
                    ).date()
                    if txn_date == today:
                        total += txn.amount
                except:
                    pass

        return total

    def get_today_transactions(self) -> float:
        """Get total transaction amount for today (withdrawals + transfers sent)"""
        today = BankClock.today()
        total = 0.0

        for txn in self.transactions:
            if txn.type == "WITHDRAW" or txn.type.endswith("_SENT"):
                try:
                    txn_date = datetime.strptime(
                        txn.timestamp, "%d-%m-%Y %H:%M:%S"
                    ).date()
                    if txn_date == today:
                        total += txn.amount
                except:
                    pass

        return total

    def _check_and_apply_amb_fee(self):
        """Check and apply Average Monthly Balance fee if applicable"""
        if self.account_type == "Future":
            return

        amb_req = self.get_amb_requirement()

        if self.balance < amb_req and self.balance >= self._amb_fee_amount:
            self.balance -= self._amb_fee_amount
            fee_txn = Transaction(
                type="AMB_FEE",
                amount=self._amb_fee_amount,
                resulting_balance=self.balance,
            )
            self.transactions.append(fee_txn)

            DataStore.append_activity(
                timestamp=fee_txn.timestamp,
                username=self.username,
                account_number=self.account_number,
                action="AMB_FEE",
                amount=self._amb_fee_amount,
                resulting_balance=self.balance,
                txn_id=fee_txn.id,
            )
            print(
                f"AMB fee of Rs. {self._amb_fee_amount} INR charged (balance below Rs. {amb_req} INR)."
            )

        elif self.balance < amb_req and self.balance < self._amb_fee_amount:
            self.pending_amb_fees += self._amb_fee_amount
            print(
                f"AMB fee of Rs. {self._amb_fee_amount} INR accrued. Will be collected on next deposit."
            )

    def _settle_pending_fees(self):
        """Settle any pending AMB fees"""
        if self.pending_amb_fees > 0 and self.balance >= self.pending_amb_fees:
            self.balance -= self.pending_amb_fees
            settle_txn = Transaction(
                type="AMB_FEE_SETTLED",
                amount=self.pending_amb_fees,
                resulting_balance=self.balance,
            )
            self.transactions.append(settle_txn)

            DataStore.append_activity(
                timestamp=settle_txn.timestamp,
                username=self.username,
                account_number=self.account_number,
                action="AMB_FEE_SETTLED",
                amount=self.pending_amb_fees,
                resulting_balance=self.balance,
                txn_id=settle_txn.id,
            )
            print(f"Pending AMB fees of Rs. {self.pending_amb_fees:.2f} INR settled.")
            self.pending_amb_fees = 0.0

    # In Account.py, replace the deposit() and withdraw() methods:

    def deposit(self, amount: float, card: Optional[DebitCard] = None):
        """Deposit money into account (requires debit card)"""
        if amount <= 0:
            print("Amount must be positive.")
            return

        if amount > self._max_deposit_per_txn:
            print(
                f"Maximum allowed per deposit is Rs. {self._max_deposit_per_txn:.2f} INR. Please split large deposits."
            )
            return

        # Validate debit card
        if card is None:
            print("Debit card required for deposit. Please provide a valid debit card.")
            return

        if not isinstance(card, DebitCard):
            print("Only debit cards can be used for deposits.")
            return

        if card not in self.cards:
            print("Card not linked to this account.")
            return

        if card.blocked:
            print("Card is blocked. Cannot proceed with deposit.")
            return

        if card.is_expired():
            print("Card has expired. Cannot proceed with deposit.")
            return

        self.balance += amount
        txn = Transaction(type="DEPOSIT", amount=amount, resulting_balance=self.balance)
        self.transactions.append(txn)

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=self.username,
            account_number=self.account_number,
            action="DEPOSIT",
            amount=amount,
            resulting_balance=self.balance,
            txn_id=txn.id,
            metadata=f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network}",
        )
        print(f"Deposit successful! Transaction ID: {txn.id}")
        print(f"Card used: {card.network} **** **** **** {card.card_number[-4:]}")
        self._settle_pending_fees()

    def withdraw(self, amount: float, card: Optional[DebitCard] = None):
        """Withdraw money from account (requires debit card)"""
        if amount <= 0:
            print("Amount must be positive.")
            return

        # Validate debit card
        if card is None:
            print(
                "Debit card required for withdrawal. Please provide a valid debit card."
            )
            return

        if not isinstance(card, DebitCard):
            print("Only debit cards can be used for withdrawals.")
            return

        if card not in self.cards:
            print("Card not linked to this account.")
            return

        # Card validations
        is_valid, msg = card.validate_transaction(amount)
        if not is_valid:
            print(f"Transaction failed: {msg}")
            return

        if self.is_minor_account:
            today_withdrawals = self.get_today_withdrawals()

            if today_withdrawals >= self._minor_daily_withdrawal_limit:
                print(
                    f"Minor account daily withdrawal limit reached (Rs. {self._minor_daily_withdrawal_limit:.2f} INR per day)."
                )
                print(f"Today's withdrawals: Rs. {today_withdrawals:.2f} INR")
                return

            if today_withdrawals + amount > self._minor_daily_withdrawal_limit:
                remaining = self._minor_daily_withdrawal_limit - today_withdrawals
                print("Withdrawal amount exceeds daily limit for minor accounts.")
                print(
                    f"Daily withdrawal limit: Rs. {self._minor_daily_withdrawal_limit:.2f} INR"
                )
                print(f"Already withdrawn today: Rs. {today_withdrawals:.2f} INR")
                print(f"Remaining limit: Rs. {remaining:.2f} INR")
                return

            today_transactions = self.get_today_transactions()
            if today_transactions + amount > self._minor_daily_transaction_limit:
                remaining = self._minor_daily_transaction_limit - today_transactions
                print(
                    "Withdrawal amount exceeds daily transaction limit for minor accounts."
                )
                print(
                    f"Daily transaction limit: Rs. {self._minor_daily_transaction_limit:.2f} INR"
                )
                print(f"Already transacted today: Rs. {today_transactions:.2f} INR")
                print(f"Remaining limit: Rs. {remaining:.2f} INR")
                return

        if self.balance - amount < self._min_operational_balance:
            print(
                f"Insufficient funds. You must keep at least Rs. {self._min_operational_balance:.2f} INR."
            )
            return

        self.balance -= amount
        txn = Transaction(
            type="WITHDRAW", amount=amount, resulting_balance=self.balance
        )
        self.transactions.append(txn)

        metadata = f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network}"
        if self.is_minor_account:
            metadata += ";minorAccount=true"

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=self.username,
            account_number=self.account_number,
            action="WITHDRAW",
            amount=amount,
            resulting_balance=self.balance,
            txn_id=txn.id,
            metadata=metadata,
        )
        print(f"Withdraw successful! Transaction ID: {txn.id}")
        print(f"Card used: {card.network} **** **** **** {card.card_number[-4:]}")

        if self.is_minor_account:
            new_withdrawals = self.get_today_withdrawals()
            new_transactions = self.get_today_transactions()
            print(
                f"Remaining daily withdrawal limit: Rs. {self._minor_daily_withdrawal_limit - new_withdrawals:.2f} INR"
            )
            print(
                f"Remaining daily transaction limit: Rs. {self._minor_daily_transaction_limit - new_transactions:.2f} INR"
            )

        self._check_and_apply_amb_fee()

    def transfer(self, recipient: "Account", amount: float, requested_mode: str):
        """Transfer money to another account"""
        if recipient.account_number == self.account_number:
            print("Cannot transfer to your own account.")
            return

        if amount <= 0:
            print("Amount must be positive.")
            return

        if self.is_minor_account:
            today_transactions = self.get_today_transactions()
            if today_transactions + amount > self._minor_daily_transaction_limit:
                remaining = self._minor_daily_transaction_limit - today_transactions
                print(
                    "Transfer amount exceeds daily transaction limit for minor accounts."
                )
                print(
                    f"Daily transaction limit: Rs. {self._minor_daily_transaction_limit:.2f} INR"
                )
                print(f"Already transacted today: Rs. {today_transactions:.2f} INR")
                print(f"Remaining limit: Rs. {remaining:.2f} INR")
                return

        # Determine actual transfer mode
        actual_mode = requested_mode
        if requested_mode != "INTER_ACCOUNT":
            if amount >= 200000.0 and requested_mode == "NEFT":
                actual_mode = "RTGS"
                print(
                    f"Amount Rs. {amount:.2f} INR is >= Rs. 2,00,000.00. Automatically routing to RTGS."
                )
            elif amount < 200000.0 and requested_mode == "RTGS":
                actual_mode = "NEFT"
                print(
                    f"Amount Rs. {amount:.2f} INR is below RTGS threshold (Rs. 2,00,000.00). Routing to NEFT instead."
                )

        enforce_min = actual_mode != "INTER_ACCOUNT"
        if enforce_min and (self.balance - amount < self._min_operational_balance):
            print(
                f"Insufficient funds. Must keep at least Rs. {self._min_operational_balance:.2f} INR."
            )
            return

        self.balance -= amount
        recipient.balance += amount

        cheque_id = (
            f"CHQ{random.randint(1000000000, 9999999999)}"
            if actual_mode != "INTER_ACCOUNT"
            else None
        )

        txn_send = Transaction(
            type=f"{actual_mode}_SENT",
            amount=amount,
            resulting_balance=self.balance,
            cheque_id=cheque_id,
        )
        txn_recv = Transaction(
            type=f"{actual_mode}_RECEIVED",
            amount=amount,
            resulting_balance=recipient.balance,
            cheque_id=cheque_id,
        )

        self.transactions.append(txn_send)
        recipient.transactions.append(txn_recv)

        metadata = f"requestedMode={requested_mode};routedMode={actual_mode}"
        if self.is_minor_account:
            metadata += ";minorAccount=true"

        DataStore.append_activity(
            timestamp=txn_send.timestamp,
            username=self.username,
            account_number=self.account_number,
            action=f"{actual_mode}_SENT",
            amount=amount,
            resulting_balance=self.balance,
            txn_id=txn_send.id,
            cheque_id=cheque_id,
            metadata=metadata,
        )
        DataStore.append_activity(
            timestamp=txn_recv.timestamp,
            username=recipient.username,
            account_number=recipient.account_number,
            action=f"{actual_mode}_RECEIVED",
            amount=amount,
            resulting_balance=recipient.balance,
            txn_id=txn_recv.id,
            cheque_id=cheque_id,
        )

        print(
            f"{actual_mode} transfer successful. Sent: Rs. {amount:.2f} INR | Transaction ID: {txn_send.id}"
        )
        if cheque_id:
            print(f"Cheque ID: {cheque_id}")

        if self.is_minor_account:
            new_transactions = self.get_today_transactions()
            print(
                f"Remaining daily transaction limit: Rs. {self._minor_daily_transaction_limit - new_transactions:.2f} INR"
            )

        if enforce_min:
            self._check_and_apply_amb_fee()

    def show_transactions(self):
        """Display all transactions"""
        if not self.transactions:
            print("No transactions found.")
        else:
            print(
                "\nTxn ID           Date/Time           Type         Amount        Balance"
            )
            print("-------------------------------------------------------")
            for t in self.transactions:
                print(
                    f"{t.id:<15} {t.timestamp:<20} {t.type:<10} Rs. {t.amount:<10.2f} Rs. {t.resulting_balance:<10.2f} INR"
                )

            if self.is_minor_account:
                today_withdrawals = self.get_today_withdrawals()
                today_transactions = self.get_today_transactions()
                print("\n-------------------------------------------------------")
                print("Minor Account Daily Limits Summary:")
                print(
                    f"Withdrawal Limit: Rs. {self._minor_daily_withdrawal_limit:.2f} INR (Used: Rs. {today_withdrawals:.2f}, Remaining: Rs. {self._minor_daily_withdrawal_limit - today_withdrawals:.2f} INR)"
                )
                print(
                    f"Transaction Limit: Rs. {self._minor_daily_transaction_limit:.2f} INR (Used: Rs. {today_transactions:.2f}, Remaining: Rs. {self._minor_daily_transaction_limit - today_transactions:.2f} INR)"
                )

    # ========== RECURRING BILLS MANAGEMENT ==========

    def add_recurring_bill(self, bill: RecurringBill):
        """Add a recurring bill to the account"""
        self.recurring_bills.append(bill)
        print(
            f"Recurring bill added: {bill.name} - Rs. {bill.base_amount:.2f} INR ({bill.frequency})"
        )

    def remove_recurring_bill(self, bill_id: str):
        """Remove a recurring bill by ID"""
        self.recurring_bills = [b for b in self.recurring_bills if b.id != bill_id]
        print("Recurring bill removed.")

    def show_recurring_bills(self):
        """Display all recurring bills"""
        if not self.recurring_bills:
            print("No recurring bills set up.")
        else:
            print("\nRecurring Bills")
            print("=" * 70)
            print(
                f"{'ID':<10} {'Name':<20} {'Amount':<15} {'Frequency':<12} {'Due Day':<8}"
            )
            print("=" * 70)
            for bill in self.recurring_bills:
                print(
                    f"{bill.id:<10} {bill.name:<20} Rs. {bill.base_amount:<14.2f} {bill.frequency:<12} {bill.day_of_month:<8}"
                )
            print("=" * 70)

    def process_recurring_bills(self, today, bank) -> int:
        """Process recurring bills for today"""
        processed = 0
        updated_bills = []

        for bill in self.recurring_bills:
            if bill.auto_debit and bill.should_process_today(today):
                amount = bill.get_variable_amount()

                if self.balance - amount >= self._min_operational_balance:
                    self.balance -= amount
                    txn = Transaction(
                        type="BILL_PAYMENT",
                        amount=amount,
                        resulting_balance=self.balance,
                        category=bill.category,
                        merchant=bill.name,
                    )
                    self.transactions.append(txn)

                    DataStore.append_activity(
                        timestamp=txn.timestamp,
                        username=self.username,
                        account_number=self.account_number,
                        action="BILL_PAYMENT",
                        amount=amount,
                        resulting_balance=self.balance,
                        txn_id=txn.id,
                        metadata=f"billId={bill.id};category={bill.category}",
                    )

                    print(f"Bill Paid: {bill.name} - Rs. {amount:.2f} INR")
                    processed += 1
                    bill.last_processed = today
                else:
                    print(f"Insufficient balance to pay {bill.name}")

            updated_bills.append(bill)

        self.recurring_bills = updated_bills
        return processed

    # ========== SALARY MANAGEMENT ==========

    def set_salary(self, gross_salary: float, salary_day: int):
        """Set salary profile for this account"""
        if salary_day < 1 or salary_day > 28:
            print("Salary day must be between 1 and 28")
            return

        self.salary_profile = SalaryProfile(
            gross_salary=gross_salary, salary_day=salary_day
        )
        tax = self.salary_profile.calculate_tax()
        net_salary = self.salary_profile.get_net_salary()
        annual_income = gross_salary * 12

        print("Salary profile set:")
        print(f"   Gross Monthly Salary: Rs. {gross_salary:,.2f} INR")
        print(f"   Annual Income: Rs. {annual_income:,.2f} INR")
        if tax > 0:
            print(f"   Monthly Tax (15%): Rs. {tax:,.2f} INR")
            print(f"   Net Monthly Salary: Rs. {net_salary:,.2f} INR")
        else:
            print(
                f"   Net Monthly Salary: Rs. {net_salary:,.2f} INR (No tax - income below Rs. 18,00,000.00/year)"
            )
        print(f"   Salary Day: {salary_day} of each month")

    def remove_salary(self):
        """Remove salary profile from this account"""
        self.salary_profile = None
        print("Salary profile removed")

    def show_salary_details(self):
        """Display salary profile details"""
        if self.salary_profile:
            profile = self.salary_profile
            tax = profile.calculate_tax()
            net_salary = profile.get_net_salary()
            annual_income = profile.gross_salary * 12

            print("\nSalary Details")
            print("=" * 50)
            print(f"Gross Monthly Salary: Rs. {profile.gross_salary:,.2f} INR")
            print(f"Annual Income: Rs. {annual_income:,.2f} INR")
            if tax > 0:
                print(f"Monthly Tax Deduction (15%): Rs. {tax:,.2f} INR")
                print(f"Net Monthly Salary: Rs. {net_salary:,.2f} INR")
            else:
                print(f"Net Monthly Salary: Rs. {net_salary:,.2f} INR")
                print("(No tax - annual income below Rs. 18,00,000.00)")
            print(f"Salary Credit Day: {profile.salary_day} of each month")
            if profile.last_salary_date:
                print(f"Last Salary Date: {profile.last_salary_date}")
            print("=" * 50)
        else:
            print("No salary profile configured")

    # ========== EXPENSE ANALYSIS ==========

    def show_expense_analysis(self, days: int = 30):
        """Show expense analysis for the last N days"""
        cutoff_date = BankClock.today() - timedelta(days=days)

        recent_expenses = []
        for txn in self.transactions:
            if (txn.type == "EXPENSE" or txn.type == "BILL_PAYMENT") and txn.category:
                try:
                    txn_date = datetime.strptime(
                        txn.timestamp, "%d-%m-%Y %H:%M:%S"
                    ).date()
                    if txn_date >= cutoff_date:
                        recent_expenses.append(txn)
                except:
                    pass

        if not recent_expenses:
            print(f"No expenses found in the last {days} days.")
            return

        # Group by category
        by_category = {}
        for txn in recent_expenses:
            category = txn.category
            if category not in by_category:
                by_category[category] = 0.0
            by_category[category] += txn.amount

        total = sum(by_category.values())
        sorted_categories = sorted(by_category.items(), key=lambda x: -x[1])

        print(f"\nExpense Analysis (Last {days} days)")
        print("=" * 60)
        print(f"{'Category':<25} {'Amount':>15} {'Percentage':>12}")
        print("=" * 60)

        for category, amount in sorted_categories:
            percentage = (amount / total) * 100
            print(f"{category:<25} Rs. {amount:>14.2f} {percentage:>11.1f}%")

        print("=" * 60)
        print(f"{'TOTAL':<25} Rs. {total:>14.2f} {100.0:>11.1f}%")
        print("=" * 60)

    # ========== CARD MANAGEMENT METHODS ==========

    def add_card(self, card: Card):
        """Add a card to this account"""
        self.cards.append(card)
        print(f"{card.card_type} card added successfully")
        print(f"Card Number: {card.card_number[-4:].rjust(16, '*')}")
        print(f"Expiry: {card.expiry_date.strftime('%m/%Y')}")
        if isinstance(card, CreditCard):
            print(f"Credit Limit: Rs. {card.credit_limit:,.2f} INR")

    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        """Get card by card ID"""
        for card in self.cards:
            if card.card_id == card_id:
                return card
        return None

    def get_card_by_number(self, card_number: str) -> Optional[Card]:
        """Get card by card number (last 4 digits also works)"""
        for card in self.cards:
            if card.card_number == card_number or card.card_number.endswith(
                card_number
            ):
                return card
        return None

    def list_cards(self):
        """Display all cards linked to this account"""
        if not self.cards:
            print("No cards linked to this account")
            return

        print("\nLinked Cards")
        print("=" * 95)
        print(
            f"{'Type':<10} {'Network':<12} {'Card Number':<20} {'Expiry':<12} {'Status':<10} {'Details':<25}"
        )
        print("=" * 95)

        for card in self.cards:
            card_num = "**** **** **** " + card.card_number[-4:]
            expiry = card.expiry_date.strftime("%m/%Y")
            status = (
                "Blocked"
                if card.blocked
                else ("Expired" if card.is_expired() else "Active")
            )
            network = card.network  # Display the network (VISA/MASTERCARD/RUPAY)

            details = ""
            if isinstance(card, CreditCard):
                details = f"Limit: Rs. {card.credit_limit:,.0f} | Used: Rs. {card.credit_used:,.0f}"

            print(
                f"{card.card_type:<10} {network:<12} {card_num:<20} {expiry:<12} {status:<10} {details:<25}"
            )

        print("=" * 95)

    def block_card(self, card_id: str):
        """Block a card"""
        card = self.get_card_by_id(card_id)
        if not card:
            print("Card not found")
            return

        card.block()
        print(f"Card ending in {card.card_number[-4:]} has been blocked")

    def unblock_card(self, card_id: str):
        """Unblock a card"""
        card = self.get_card_by_id(card_id)
        if not card:
            print("Card not found")
            return

        card.unblock()
        print(f"Card ending in {card.card_number[-4:]} has been unblocked")

    def make_card_purchase(
        self, card_id: str, amount: float, merchant: str, category: str = "Shopping"
    ):
        """Make a purchase using a card"""
        card = self.get_card_by_id(card_id)
        if not card:
            print("Card not found")
            return

        if isinstance(card, DebitCard):
            success, message, txn_id = card.make_purchase(
                amount, self, merchant, category
            )
        elif isinstance(card, CreditCard):
            success, message, txn_id = card.make_purchase(amount, merchant, category)
        else:
            print("Invalid card type")
            return

        if success:
            print(f"✓ {message}")
            print(f"Transaction ID: {txn_id}")
            print(f"Amount: Rs. {amount:.2f} INR")
            if isinstance(card, CreditCard):
                print(f"Available Credit: Rs. {card.available_credit():.2f} INR")
        else:
            print(f"✗ Transaction failed: {message}")

    def pay_credit_card_bill(self, card_id: str, amount: float):
        """Pay credit card bill from account balance"""
        card = self.get_card_by_id(card_id)
        if not card:
            print("Card not found")
            return

        if not isinstance(card, CreditCard):
            print("This is not a credit card")
            return

        success, message, txn_id = card.pay_bill(amount, self)

        if success:
            print(f"✓ {message}")
            print(f"Transaction ID: {txn_id}")
        else:
            print(f"✗ Payment failed: {message}")

    def show_credit_card_statement(self, card_id: str):
        """Display credit card statement"""
        card = self.get_card_by_id(card_id)
        if not card:
            print("Card not found")
            return

        if not isinstance(card, CreditCard):
            print("This is not a credit card")
            return

        print("\nCredit Card Statement")
        print("=" * 60)
        print(f"Card Number: **** **** **** {card.card_number[-4:]}")
        print(f"Credit Limit: Rs. {card.credit_limit:,.2f} INR")
        print(f"Credit Used: Rs. {card.credit_used:,.2f} INR")
        print(f"Available Credit: Rs. {card.available_credit():,.2f} INR")
        print(f"Credit Utilization: {card.credit_utilization():.1f}%")
        print("=" * 60)

        if card.outstanding_balance > 0:
            print(f"\nOutstanding Balance: Rs. {card.outstanding_balance:,.2f} INR")
            print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")
            if card.due_date:
                days_remaining = (card.due_date - BankClock.today()).days
                print(
                    f"Due Date: {card.due_date.strftime('%d-%m-%Y')} ({days_remaining} days)"
                )
                if days_remaining < 0:
                    print("⚠ PAYMENT OVERDUE!")
        else:
            print("\n✓ No outstanding balance")

        print("=" * 60)

    def process_credit_card_bills(self, today):
        """Process credit card bill generation for all credit cards"""
        for card in self.cards:
            if isinstance(card, CreditCard) and card.check_bill_generation(today):
                bill = card.generate_bill(today)
                if bill["success"]:
                    print(f"\n{'=' * 60}")
                    print("CREDIT CARD BILL GENERATED")
                    print(f"{'=' * 60}")
                    print(f"Card: **** **** **** {card.card_number[-4:]}")
                    print(f"Bill Date: {bill['billDate']}")
                    print(f"Due Date: {bill['dueDate']}")
                    print(f"Total Outstanding: Rs. {bill['totalOutstanding']:,.2f} INR")
                    print(f"Minimum Due: Rs. {bill['minimumDue']:,.2f} INR")
                    if bill["interestCharged"] > 0:
                        print(
                            f"Interest Charged: Rs. {bill['interestCharged']:,.2f} INR"
                        )
                    print(f"{'=' * 60}\n")

                    # Log activity
                    DataStore.append_activity(
                        timestamp=BankClock.get_formatted_datetime(),
                        username=self.username,
                        account_number=self.account_number,
                        action="CREDIT_CARD_BILL_GENERATED",
                        amount=bill["totalOutstanding"],
                        resulting_balance=None,
                        metadata=f"cardId={card.card_id};dueDate={bill['dueDate']}",
                    )

    # ========== STATIC METHODS AND UTILITIES ==========

    @staticmethod
    def generate_account_number() -> str:
        """Generate a unique account number"""
        Account._load_used_numbers()

        while True:
            random_part = "".join([str(random.randint(0, 9)) for _ in range(8)])
            acc_num = Account.ACCOUNT_NUMBER_PREFIX + random_part
            if acc_num not in Account._used_account_numbers:
                Account._used_account_numbers.add(acc_num)
                Account._save_used_numbers()
                return acc_num

    @staticmethod
    def _load_used_numbers():
        """Load used account numbers from file"""
        if os.path.exists(Account._used_numbers_file):
            with open(Account._used_numbers_file, "r") as f:
                Account._used_account_numbers = set(line.strip() for line in f)

    @staticmethod
    def _save_used_numbers():
        """Save used account numbers to file"""
        os.makedirs(os.path.dirname(Account._used_numbers_file), exist_ok=True)
        with open(Account._used_numbers_file, "w") as f:
            for num in Account._used_account_numbers:
                f.write(num + "\n")

    @staticmethod
    def from_storage(
        customer_id: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        account_type: str,
        account_number: str,
        balance: float,
        transactions: List[Transaction],
        failed_attempts: int,
        locked: bool,
        pending_amb_fees: float,
    ) -> "Account":
        """Create an Account instance from storage data"""
        if account_number.startswith(Account.ACCOUNT_NUMBER_PREFIX):
            Account._used_account_numbers.add(account_number)
            Account._save_used_numbers()

        return Account(
            customer_id=customer_id,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            account_type=account_type,
            account_number=account_number,
            balance=balance,
            transactions=transactions,
            failed_attempts=failed_attempts,
            locked=locked,
            pending_amb_fees=pending_amb_fees,
        )

    @staticmethod
    def get_branch_details() -> str:
        """Get branch details as a formatted string"""
        return f"""Branch Details:
IFSC Code: {Account.BRANCH_IFSC}
Branch Name: {Account.BRANCH_NAME}
Branch Code: {Account.ACCOUNT_NUMBER_PREFIX}"""

    @staticmethod
    def create_account(
        customer_id: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        account_type: str,
        account_number: Optional[str] = None,
    ) -> "Account":
        """Factory method to create a new account"""
        if account_number is None:
            account_number = Account.generate_account_number()

        acc = Account(
            customer_id=customer_id,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            account_type=account_type,
            account_number=account_number,
            balance=0.0,
            transactions=[],
            failed_attempts=0,
            locked=False,
            pending_amb_fees=0.0,
        )

        ts = BankClock.get_formatted_datetime()
        DataStore.append_activity(
            timestamp=ts,
            username=username,
            account_number=account_number,
            action="ACCOUNT_CREATED",
            amount=None,
            resulting_balance=None,
            metadata=f"type={account_type};customerId={customer_id}",
        )

        return acc

    # ========== SERIALIZATION ==========

    def to_dict(self) -> dict:
        """Convert account to dictionary for JSON serialization"""
        return {
            "customerId": self.customer_id,
            "username": self.username,
            "password": self.password,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "dob": self.dob,
            "gender": self.gender,
            "accountType": self.account_type,
            "accountNumber": self.account_number,
            "balance": self.balance,
            "transactions": [t.to_dict() for t in self.transactions],
            "failedAttempts": self.failed_attempts,
            "locked": self.locked,
            "pendingAmbFees": self.pending_amb_fees,
            "recurringBills": [b.to_dict() for b in self.recurring_bills],
            "salaryProfile": self.salary_profile.to_dict()
            if self.salary_profile
            else None,
            "cards": [c.to_dict() for c in self.cards],
        }

    @staticmethod
    def from_dict(data: dict) -> "Account":
        """Create an Account instance from dictionary"""
        transactions = [Transaction.from_dict(t) for t in data.get("transactions", [])]

        acc = Account.from_storage(
            customer_id=data["customerId"],
            username=data["username"],
            password=data["password"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            dob=data["dob"],
            gender=data["gender"],
            account_type=data["accountType"],
            account_number=data["accountNumber"],
            balance=data["balance"],
            transactions=transactions,
            failed_attempts=data.get("failedAttempts", 0),
            locked=data.get("locked", False),
            pending_amb_fees=data.get("pendingAmbFees", 0.0),
        )

        # Load recurring bills
        acc.recurring_bills = [
            RecurringBill.from_dict(b) for b in data.get("recurringBills", [])
        ]

        # Load salary profile
        if data.get("salaryProfile"):
            acc.salary_profile = SalaryProfile.from_dict(data["salaryProfile"])

        # Load cards
        acc.cards = [Card.from_dict(c) for c in data.get("cards", [])]

        return acc


# Initialize used numbers on module load
Account._load_used_numbers()
