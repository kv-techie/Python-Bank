import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

from .BankClock import BankClock
from .Card import Card, CreditCard, DebitCard
from .ChequeBook import ChequeBookManager
from .DataStore import DataStore
from .RecurringBill import RecurringBill
from .SalaryProfile import SalaryProfile
from .Transaction import Transaction


class Account:
    """Account class for managing bank accounts"""

    BRANCH_IFSC = "SCBA0005621"
    BRANCH_NAME = "Jakkasandra"
    ACCOUNT_NUMBER_PREFIX = "5621"
    _used_account_numbers = set()
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _used_numbers_file = os.path.join(_BASE_DIR, "data", "account_numbers.txt")

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
        self.transactions = transactions or []
        self._transactions_loaded = bool(
            transactions
        )  # Track if transactions are loaded
        self.failed_attempts = failed_attempts
        self.locked = locked
        self.pending_amb_fees = pending_amb_fees
        self.cards: List[Card] = []

        # Beneficiaries for transfers during closure
        self.beneficiaries: List = []

        # Cheque book management
        self.cheque_book_manager = ChequeBookManager(account_number)
        # Auto-issue first cheque book
        self.cheque_book_manager.create_and_issue_cheque_book()

        # Simulation features
        self.recurring_bills: List[RecurringBill] = []
        self.salary_profile: Optional[SalaryProfile] = None

        # Tax management
        self.tax_exemptions: List = []  # List of TaxExemption objects
        self.itr_filings: List = []  # List of ITRFilingRecord objects
        self.form_26as: Optional[object] = None  # Form26AS instance

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

    def _load_transactions_if_needed(self):
        """Load all transactions from storage when first accessed"""
        if not self._transactions_loaded:
            from .DataStore import DataStore

            self.transactions = DataStore.load_account_transactions(self.account_number)
            self._transactions_loaded = True

    @property
    def is_minor_account(self) -> bool:
        """Check if this is a minor account (Future type)"""
        return self.account_type == "Future"

    def get_amb_requirement(self) -> float:
        """Get Average Monthly Balance requirement for this account type"""
        return self._amb_requirements.get(self.account_type, 0.0)

    def get_today_withdrawals(self) -> float:
        """Get total withdrawals made today"""
        self._load_transactions_if_needed()  # ADD THIS LINE
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
        self._load_transactions_if_needed()  # ADD THIS LINE
        today = BankClock.today()
        total = 0.0

        for txn in self.transactions:
            if txn.type == "WITHDRAW" or "_SENT" in txn.type:
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

    def deposit(
        self,
        amount: float,
        card: Optional[DebitCard] = None,
        pin: str = None,
        mode: str = "CARD",
        merchant: str = "SELF",
    ):
        """
        Deposit money to account.
        Supported modes: "CARD" (requires debit card/pin), "CASH", "TRANSFER", "LOAN_CREDIT"
        """
        if amount <= 0:
            print("Amount must be positive.")
            return

        # 1. Mode Validation
        if mode == "CARD":
            if card is None:
                print("Debit card required for card deposit.")
                return
            if not isinstance(card, DebitCard):
                print("Only debit cards can be used for deposits.")
                return
            if card not in self.cards:
                print("Card not linked to this account.")
                return
            # PIN Verification
            success, msg = card.verify_pin(pin)
            if not success:
                print(f"PIN Verification Failed: {msg}")
                return
            # Card validations
            is_valid, msg = card.validate_transaction(amount)
            if not is_valid:
                print(f"Transaction failed: {msg}")
                return
        elif mode not in ["CASH", "TRANSFER", "LOAN_CREDIT", "RD_MATURITY", "FD_MATURITY"]:
            print(f"Unsupported deposit mode: {mode}")
            return

        if self.is_minor_account:
            today_transactions = self.get_today_transactions()
            if today_transactions + amount > self._minor_daily_transaction_limit:
                remaining = self._minor_daily_transaction_limit - today_transactions
                print(
                    "Deposit amount exceeds daily transaction limit for minor accounts."
                )
                print(
                    f"Daily transaction limit: Rs. {self._minor_daily_transaction_limit:.2f} INR"
                )
                print(f"Already transacted today: Rs. {today_transactions:.2f} INR")
                print(f"Remaining limit: Rs. {remaining:.2f} INR")
                return

        # Update balance
        self.balance += amount

        # Prepare transaction metadata
        txn_metadata = {
            "mode": mode,
            "merchant": merchant
        }
        if card:
            txn_metadata.update({
                "card_number": card.card_number,
                "card_type": "DEBIT",
                "card_id": card.card_id,
                "network": card.network
            })

        # Create transaction with metadata
        txn = Transaction(
            type="DEPOSIT",
            amount=amount,
            resulting_balance=self.balance,
            metadata=txn_metadata,
        )
        self.transactions.append(txn)

        if card:
            metadata = f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network}"
        else:
            metadata = f"mode={mode};merchant={merchant}"
            
        if self.is_minor_account:
            metadata += ";minorAccount=true"

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=self.username,
            account_number=self.account_number,
            action="DEPOSIT",
            amount=amount,
            resulting_balance=self.balance,
            txn_id=txn.id,
            metadata=metadata,
        )
        if card:
            print(f"Deposit successful! Transaction ID: {txn.id}")
            print(f"Card used: {card.network} **** **** **** {card.card_number[-4:]}")
        else:
            print(f"Deposit successful! Transaction ID: {txn.id}")
            print(f"Mode: {mode} | Source: {merchant}")

        if self.is_minor_account:
            new_transactions = self.get_today_transactions()
            print(
                f"Remaining daily transaction limit: Rs. {self._minor_daily_transaction_limit - new_transactions:.2f} INR"
            )

        self._check_and_apply_amb_fee()

    def withdraw(
        self,
        amount: float,
        card: Optional[DebitCard] = None,
        pin: str = None,
        mode: str = "CARD",
        location: str = "ATM",
    ):
        """
        Withdraw money from account.
        Supported modes: "CARD" (requires debit card/pin), "CASH", "TRANSFER", "LOAN_REPAYMENT"
        """
        if amount <= 0:
            print("Amount must be positive.")
            return

        # 1. Mode Validation
        if mode == "CARD":
            if card is None:
                print("Debit card required for card withdrawal.")
                return
            if not isinstance(card, DebitCard):
                print("Only debit cards can be used for withdrawals.")
                return
            if card not in self.cards:
                print("Card not linked to this account.")
                return
            # PIN Verification
            success, msg = card.verify_pin(pin)
            if not success:
                print(f"PIN Verification Failed: {msg}")
                return
            # Card validations
            is_valid, msg = card.validate_transaction(amount)
            if not is_valid:
                print(f"Transaction failed: {msg}")
                return
        elif mode not in ["CASH", "TRANSFER", "LOAN_REPAYMENT", "RD_INSTALLMENT"]:
            print(f"Unsupported withdrawal mode: {mode}")
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

        # Update balance
        self.balance -= amount

        # Prepare transaction metadata
        txn_metadata = {
            "mode": mode,
            "location": location
        }
        if card:
            txn_metadata.update({
                "card_number": card.card_number,
                "card_type": "DEBIT",
                "card_id": card.card_id,
                "network": card.network
            })

        # Create transaction with metadata
        txn = Transaction(
            type="WITHDRAW",
            amount=-amount,  # Negative for withdrawal
            resulting_balance=self.balance,
            metadata=txn_metadata,
        )
        self.transactions.append(txn)

        if card:
            metadata = f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network}"
        else:
            metadata = f"mode={mode};location={location}"
            
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
        if card:
            print(f"Withdraw successful! Transaction ID: {txn.id}")
            print(f"Card used: {card.network} **** **** **** {card.card_number[-4:]}")
        else:
            print(f"Withdraw successful! Transaction ID: {txn.id}")
            print(f"Mode: {mode} | Location: {location}")

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

    def pay_to_beneficiary(
        self,
        beneficiary_id: str,
        amount: float,
        requested_mode: str,
        beneficiary_manager,
    ) -> bool:
        """
        Pay money to a saved beneficiary

        Args:
            beneficiary_id: ID of the beneficiary to pay
            amount: Amount to pay
            requested_mode: Transfer mode (NEFT, RTGS, etc.)
            beneficiary_manager: BeneficiaryManager instance containing the beneficiary

        Returns:
            True if payment was successful, False otherwise
        """
        # Get the beneficiary
        beneficiary = beneficiary_manager.get_beneficiary(beneficiary_id)
        if not beneficiary:
            print(f"Beneficiary with ID {beneficiary_id} not found.")
            return False

        # Check if beneficiary is active
        if beneficiary.status != "Active":
            print(f"Cannot pay to inactive beneficiary. Status: {beneficiary.status}")
            return False

        if amount <= 0:
            print("Payment amount must be positive.")
            return False

        # Check minor account limits
        if self.is_minor_account:
            today_transactions = self.get_today_transactions()
            if today_transactions + amount > self._minor_daily_transaction_limit:
                remaining = self._minor_daily_transaction_limit - today_transactions
                print(
                    "Payment amount exceeds daily transaction limit for minor accounts."
                )
                print(
                    f"Daily transaction limit: Rs. {self._minor_daily_transaction_limit:.2f} INR"
                )
                print(f"Already transacted today: Rs. {today_transactions:.2f} INR")
                print(f"Remaining limit: Rs. {remaining:.2f} INR")
                return False

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

        # Check operational balance
        enforce_min = actual_mode != "INTER_ACCOUNT"
        if enforce_min and (self.balance - amount < self._min_operational_balance):
            print(
                f"Insufficient funds. Must keep at least Rs. {self._min_operational_balance:.2f} INR."
            )
            return False

        # Process payment
        self.balance -= amount

        cheque_id = (
            f"CHQ{random.randint(1000000000, 9999999999)}"
            if actual_mode != "INTER_ACCOUNT"
            else None
        )

        txn = Transaction(
            type=f"{actual_mode}_SENT",
            amount=amount,
            resulting_balance=self.balance,
            cheque_id=cheque_id,
        )

        self.transactions.append(txn)

        # Update beneficiary usage
        beneficiary.mark_used()

        metadata = (
            f"requestedMode={requested_mode};routedMode={actual_mode};"
            f"beneficiaryId={beneficiary_id};beneficiaryName={beneficiary.beneficiary_name};"
            f"beneficiaryAccount={beneficiary.account_number}"
        )
        if self.is_minor_account:
            metadata += ";minorAccount=true"

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=self.username,
            account_number=self.account_number,
            action=f"{actual_mode}_SENT_TO_BENEFICIARY",
            amount=amount,
            resulting_balance=self.balance,
            txn_id=txn.id,
            cheque_id=cheque_id,
            metadata=metadata,
        )

        print(
            f"{actual_mode} payment to {beneficiary.beneficiary_name} successful. "
            f"Sent: Rs. {amount:.2f} INR | Transaction ID: {txn.id}"
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

        return True

    # ===== Cheque Management Methods =====

    def issue_cheque(
        self, cheque_number: str, amount: float, payee_name: str, date_presentable: str
    ) -> Optional[str]:
        """
        Issue a cheque from the account

        Args:
            cheque_number: Cheque serial number
            amount: Cheque amount
            payee_name: Name of payee
            date_presentable: Date when cheque can be presented (YYYY-MM-DD)

        Returns:
            Cheque ID if successful, None otherwise
        """

        # Validate cheque number exists and is unused
        active_book = self.cheque_book_manager.get_active_cheque_book()
        if not active_book:
            print("No active cheque book available. Please request a new one.")
            return None

        cheque = active_book.get_cheque_by_number(cheque_number)
        if not cheque:
            print(
                f"Cheque number {cheque_number} not found in your active cheque book."
            )
            return None

        if cheque.status.value != "ISSUED":
            print(f"Cheque {cheque_number} is already {cheque.status.value}.")
            return None

        # Update cheque details
        cheque.amount = amount
        cheque.payee_name = payee_name
        cheque.date_presentable = date_presentable

        print(
            f"[OK] Cheque {cheque_number} issued to {payee_name} for Rs. {amount:,.2f}"
        )

        return cheque.cheque_id

    def get_cheque_book_status(self) -> None:
        """Display current cheque book status"""
        books = self.cheque_book_manager.get_all_cheque_books()
        if not books:
            print("No cheque books available.")
            return

        print("\n" + "=" * 70)
        print("CHEQUE BOOK STATUS")
        print("=" * 70)

        for book in books:
            summary = book.get_summary()
            print(f"\n📕 Cheque Book: {book.cheque_book_id}")
            print(f"   Status: {summary['status']}")
            print(f"   Total Cheques: {summary['total_cheques']}")
            print(
                f"   Used: {summary['used_count']} | Unused: {summary['unused_count']}"
            )
            print(f"   Cleared: {summary['cleared']} | Bounced: {summary['bounced']}")
            print(f"   Pending: {summary['pending']}")

    def get_cheque_history(self) -> None:
        """Display cheque history"""
        cheques = self.cheque_book_manager.get_all_cheques()
        if not cheques:
            print("No cheques found.")
            return

        print("\n" + "=" * 70)
        print("CHEQUE HISTORY")
        print("=" * 70)

        for cheque in sorted(
            cheques, key=lambda x: x.issued_on or datetime.now(), reverse=True
        ):
            print(f"\n{cheque}")
            print(f"  Amount: {cheque.get_formatted_amount()}")
            print(f"  Payee: {cheque.payee_name}")
            print(f"  Presentable: {cheque.get_formatted_date()}")
            if cheque.status.value == "BOUNCED":
                print(f"  Bounce Reason: {cheque.bounce_reason}")
                print(f"  Fee Deducted: Rs. {cheque.bounce_fee_deducted:,.2f}")

    def show_transactions(
        self,
        limit: int = 10,
        transaction_type_filter: str = None,
        card_filter: str = None,
    ):
        """
        Display transaction history with filters

        Args:
            limit: Number of transactions to show (None for all)
            transaction_type_filter: Filter by transaction type
            card_filter: Filter by specific card (last 4 digits)
        """
        self._load_transactions_if_needed()  # ADD THIS LINE
        if not self.transactions:
            print("No transactions found.")
            return

        transactions = self.transactions.copy()

        # Helper function to safely get metadata
        def get_metadata(txn):
            """Safely get metadata as dict, handling string or None"""
            if not hasattr(txn, "metadata"):
                return {}
            if txn.metadata is None:
                return {}
            if isinstance(txn.metadata, dict):
                return txn.metadata
            # If it's a string, parse it (format: "key1=val1;key2=val2")
            if isinstance(txn.metadata, str) and txn.metadata:
                parsed = {}
                for pair in txn.metadata.split(";"):
                    if "=" in pair:
                        key, val = pair.split("=", 1)
                        parsed[key] = val
                return parsed
            # If it's a string or other type, return empty dict
            return {}

        # Apply filters
        if transaction_type_filter == "DEPOSIT":
            transactions = [t for t in transactions if t.type == "DEPOSIT"]

        elif transaction_type_filter == "WITHDRAW":
            transactions = [t for t in transactions if t.type == "WITHDRAW"]

        elif transaction_type_filter == "LOAN_EMI":
            transactions = [t for t in transactions if t.type == "LOAN_EMI"]

        elif transaction_type_filter == "LEGACY_BANKING":
            # Legacy: Deposits/Withdrawals without card
            transactions = [
                t
                for t in transactions
                if t.type in ["DEPOSIT", "WITHDRAW"]
                and not get_metadata(t).get("card_number")
                and not get_metadata(t).get("cardNumber")
            ]

        elif transaction_type_filter == "DEBIT_CARD":
            # All debit card transactions (deposits, withdrawals, purchases)
            transactions = [
                t
                for t in transactions
                if (
                    t.type in ["DEPOSIT", "WITHDRAW", "DEBIT_CARD_PURCHASE"]
                    and get_metadata(t).get("card_type") == "DEBIT"
                )
            ]

        elif transaction_type_filter == "CREDIT_CARD_PAYMENT":
            transactions = [t for t in transactions if t.type == "CREDIT_CARD_PAYMENT"]

        elif transaction_type_filter == "NEFT":
            # Both sent and received
            transactions = [
                t for t in transactions if t.type in ["NEFT_SENT", "NEFT_RECEIVED"]
            ]

        elif transaction_type_filter == "RTGS":
            # Both sent and received
            transactions = [
                t for t in transactions if t.type in ["RTGS_SENT", "RTGS_RECEIVED"]
            ]

        elif transaction_type_filter == "INTER_ACCOUNT":
            # Both sent and received
            transactions = [
                t
                for t in transactions
                if t.type in ["INTER_ACCOUNT_SENT", "INTER_ACCOUNT_RECEIVED"]
            ]

        elif transaction_type_filter == "SWIFT":
            # Both sent and received
            transactions = [
                t for t in transactions if t.type in ["SWIFT_SENT", "SWIFT_RECEIVED"]
            ]

        elif transaction_type_filter == "SALARY_TAX":
            transactions = [
                t
                for t in transactions
                if t.type in ["SALARY", "SALARY_CREDIT", "TAX_DEDUCTED"]
            ]

        elif transaction_type_filter == "EXPENSE":
            transactions = [t for t in transactions if t.type == "EXPENSE"]

        elif transaction_type_filter == "BILL_PAYMENT":
            transactions = [t for t in transactions if t.type == "BILL_PAYMENT"]

        elif transaction_type_filter == "CHEQUE":
            # All cheque-related transactions
            transactions = [
                t
                for t in transactions
                if t.type in ["CHEQUE_CLEARED", "CHEQUE_DEPOSITED", "CHEQUE_BOUNCE"]
                or (t.cheque_id and t.cheque_id != "")
            ]

        elif transaction_type_filter == "FEES":
            # All fee-related transactions
            transactions = [
                t
                for t in transactions
                if t.type
                in ["AMB_FEE", "AMB_FEE_SETTLED", "TAX_DEDUCTED", "CHEQUE_BOUNCE"]
            ]

        elif card_filter:
            # Filter by specific card
            transactions = [
                t
                for t in transactions
                if get_metadata(t).get("card_number", "").endswith(card_filter)
            ]

        if not transactions:
            print("No transactions found matching your criteria")
            return

        # Apply limit
        if limit:
            transactions = transactions[-limit:]

        # Display header
        print("\n" + "=" * 130)
        print(f"TRANSACTION HISTORY - {len(transactions)} transaction(s)")
        print("=" * 130)
        print(
            f"{'Txn ID':<20} {'Date/Time':<20} {'Type':<25} {'Card':<12} {'Amount':<18} {'Balance':<15}"
        )
        print("-" * 130)

        for txn in transactions:
            # Extract card info if available
            card_info = ""
            metadata = get_metadata(txn)

            # Check for card info in metadata (supports both dict and CSV string formats)
            if metadata and ("card_number" in metadata or "cardNumber" in metadata):
                # New format: card_number, card_type
                card_number = metadata.get(
                    "card_number", metadata.get("cardNumber", "")
                )
                card_type = metadata.get("card_type", metadata.get("network", ""))
                if card_number:
                    if len(card_type) > 1:
                        # Show network name for CSV format (VISA, MasterCard, etc.)
                        card_info = f"{card_type}"
                    else:
                        # Show abbreviated format for dict format (D****1234, C****5678)
                        card_info = f"{card_type[:1]}****{card_number[-4:]}"
            elif txn.type in ["DEPOSIT", "WITHDRAW"]:
                card_info = "Legacy"
            else:
                card_info = "-"

            # Format amount with direction indicator
            if txn.type in [
                "DEPOSIT",
                "NEFT_RECEIVED",
                "RTGS_RECEIVED",
                "INTER_ACCOUNT_RECEIVED",
                "SALARY",
                "SALARY_TAX_REFUND",  # Tax refund
                "LOAN_CREDIT",
                "SWIFT_RECEIVED",  # ← ADDED
            ]:
                amount_str = f"+ Rs. {abs(txn.amount):>12,.2f}"
            elif txn.type in [
                "WITHDRAW",
                "NEFT_SENT",
                "NEFT_SENT_EXTERNAL",
                "RTGS_SENT",
                "RTGS_SENT_EXTERNAL",
                "INTER_ACCOUNT_SENT",
                "LOAN_EMI",
                "TAX_DEDUCTED",
                "CREDIT_CARD_PAYMENT",
                "EXPENSE",
                "DEBIT_CARD_PURCHASE",
                "SWIFT_SENT",  # ← ADDED
            ]:
                amount_str = f"- Rs. {abs(txn.amount):>12,.2f}"
            else:
                amount_str = f"Rs. {abs(txn.amount):>14,.2f}"

            # Format balance
            balance_str = f"Rs. {txn.resulting_balance:>12,.2f}"

            print(
                f"{txn.id:<20} {txn.timestamp:<20} {txn.type:<25} "
                f"{card_info:<12} {amount_str:<18} {balance_str:<15} INR"
            )

        print("=" * 130)

        # Show summary statistics - use transaction type to classify credits/debits
        from .Transaction import TransactionType

        credit_types = TransactionType.get_all_credit_types()
        debit_types = TransactionType.get_all_debit_types()

        total_credit = sum(t.amount for t in transactions if t.type in credit_types)
        total_debit = sum(t.amount for t in transactions if t.type in debit_types)

        print(
            f"\n[STATS] Summary: Total Credit: Rs. {total_credit:,.2f} | Total Debit: Rs. {total_debit:,.2f}"
        )

        # Show minor account limits if applicable
        if self.is_minor_account:
            today_withdrawals = self.get_today_withdrawals()
            today_transactions = self.get_today_transactions()
            print("\n" + "-" * 130)
            print("[WARN]  Minor Account Daily Limits Summary:")
            print(
                f"   Withdrawal Limit: Rs. {self._minor_daily_withdrawal_limit:.2f} INR "
                f"(Used: Rs. {today_withdrawals:.2f}, Remaining: Rs. {self._minor_daily_withdrawal_limit - today_withdrawals:.2f} INR)"
            )
            print(
                f"   Transaction Limit: Rs. {self._minor_daily_transaction_limit:.2f} INR "
                f"(Used: Rs. {today_transactions:.2f}, Remaining: Rs. {self._minor_daily_transaction_limit - today_transactions:.2f} INR)"
            )
            print("-" * 130)

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

    def update_dynamic_bills(self):
        """Update recurring bills that are linked to credit cards"""
        updated = []

        for bill in self.recurring_bills:
            if bill.is_dynamic and bill.linked_card_id:
                card = self.get_card_by_id(bill.linked_card_id)

                if card and isinstance(card, CreditCard):
                    old_amount = bill.base_amount
                    bill.base_amount = card.current_balance

                    if old_amount != bill.base_amount:
                        updated.append(
                            {
                                "bill_name": bill.name,
                                "old_amount": old_amount,
                                "new_amount": bill.base_amount,
                                "card_network": card.network,
                            }
                        )

        return updated

    def process_recurring_bills(self, today, bank) -> int:
        """Process recurring bills for today with credit card payment support"""
        from .RecurringBill import PaymentMethod

        processed = 0

        for bill in self.recurring_bills:
            # Only attempt to process bills that are set to auto-debit and due today
            if not (bill.auto_debit and bill.should_process_today(today)):
                continue

            # Update dynamic bills first
            if bill.is_dynamic and bill.linked_card_id:
                bill.update_from_linked_card(self)

            amount = bill.get_current_amount(self)

            # CASE 1: Pay from Bank Account
            if bill.payment_method == PaymentMethod.BANK_ACCOUNT:
                # If this is a credit-card-linked bill, use the card's pay_bill
                if bill.linked_card_id:
                    card = self.get_card_by_id(bill.linked_card_id)
                    if card and isinstance(card, CreditCard):
                        success, msg, txn_id = card.pay_bill(amount, self)
                        if success:
                            print(f"[SUCCESS] Auto-paid {bill.name}: Rs. {amount:,.2f}")
                            print(f"   💳 {card.network} credit card paid")
                            DataStore.append_activity(
                                timestamp=BankClock.get_formatted_datetime(),
                                username=self.username,
                                account_number=self.account_number,
                                action="RECURRING_BILL_CREDIT_CARD_PAYMENT",
                                amount=amount,
                                resulting_balance=self.balance,
                                txn_id=txn_id,
                                metadata=f"billId={bill.id};category={bill.category};nachId={bill.nach_id};cardId={card.card_id}",
                            )
                            processed += 1
                            bill.last_processed = today
                        else:
                            print(f"[WARN]  Failed to auto-pay {bill.name}: {msg}")
                    else:
                        print(f"[WARN]  Payment card not found for {bill.name}")
                else:
                    # Pay directly from bank account
                    if self.balance - amount >= self._min_operational_balance:
                        self.balance -= amount

                        txn = Transaction(
                            type="RECURRING_BILL",
                            amount=-amount,
                            resulting_balance=self.balance,
                            category=bill.category,
                            merchant=bill.name,
                        )

                        self.transactions.append(txn)

                        DataStore.append_activity(
                            timestamp=txn.timestamp,
                            username=self.username,
                            account_number=self.account_number,
                            action="RECURRING_BILL",
                            amount=amount,
                            resulting_balance=self.balance,
                            txn_id=txn.id,
                            metadata=f"billId={bill.id};category={bill.category};nachId={bill.nach_id}",
                        )

                        print(f"[SUCCESS] Auto-paid {bill.name}: Rs. {amount:,.2f}")
                        processed += 1
                        bill.last_processed = today
                    else:
                        print(f"[WARN]  Insufficient balance to pay {bill.name}")

            # CASE 2: Pay via Credit Card
            elif bill.payment_method == PaymentMethod.CREDIT_CARD:
                card = self.get_card_by_id(bill.payment_card_id)

                if card and isinstance(card, CreditCard):
                    available = card.credit_limit - card.current_balance

                    if available >= amount:
                        # Charge the credit card (increase amount owed)
                        card.credit_used += amount

                        # Add to card transactions
                        card_txn = Transaction(
                            type="BILL_PAYMENT",
                            amount=-amount,
                            resulting_balance=card.available_credit(),
                            category=bill.category,
                            merchant=bill.name,
                        )
                        card.transactions.append(card_txn)

                        # Calculate and award reward points
                        reward_points = int(amount * card.reward_rate)
                        card.reward_points += reward_points

                        # Create transaction in account (for logging, no balance change)
                        txn = Transaction(
                            type="CREDIT_CARD_BILL_PAYMENT",
                            amount=0,  # No account deduction
                            resulting_balance=self.balance,
                            metadata={
                                "bill_id": bill.id,
                                "bill_name": bill.name,
                                "nach_id": bill.nach_id,
                                "payment_method": "credit_card",
                                "card_id": card.card_id,
                                "card_network": card.network,
                                "reward_points_earned": reward_points,
                                "bill_amount": amount,
                            },
                        )

                        self.transactions.append(txn)

                        DataStore.append_activity(
                            timestamp=txn.timestamp,
                            username=self.username,
                            account_number=self.account_number,
                            action="CREDIT_CARD_BILL_PAYMENT",
                            amount=amount,
                            resulting_balance=self.balance,
                            txn_id=txn.id,
                            metadata=f"billId={bill.id};cardId={card.card_id};rewardPoints={reward_points};nachId={bill.nach_id}",
                        )

                        print(
                            f"[SUCCESS] Auto-paid {bill.name}: Rs. {amount:,.2f} via {card.network}"
                        )
                        print(f"   💎 Earned {reward_points} reward points!")

                        processed += 1
                        bill.last_processed = today
                    else:
                        print(f"[WARN]  Insufficient credit limit for {bill.name}")
                else:
                    print(f"[WARN]  Payment card not found for {bill.name}")

        # Do not overwrite self.recurring_bills here — keep configured bills intact
        return processed

    # ========== SALARY MANAGEMENT ==========

    def set_salary(
        self,
        gross_salary: float,
        salary_day: int,
        employee_epf_contribution: float = 0.0,
        professional_tax: float = 0.0,
        other_deductions: float = 0.0,
    ):
        """Set salary profile for this account"""
        if salary_day < 1 or salary_day > 28:
            print("Salary day must be between 1 and 28")
            return

        self.salary_profile = SalaryProfile(
            gross_salary=gross_salary,
            salary_day=salary_day,
            employee_epf_contribution=employee_epf_contribution,
            professional_tax=professional_tax,
            other_deductions=other_deductions,
        )
        tax = self.salary_profile.calculate_tax()
        tax_rate = (
            self.salary_profile.get_tax_rate()
        )  # [OK] Fixed: use self.salary_profile
        net_salary = self.salary_profile.get_net_salary()
        annual_income = gross_salary * 12
        total_deductions = (
            employee_epf_contribution + professional_tax + other_deductions
        )

        print("Salary profile set:")
        print(f"   Gross Monthly Salary: Rs. {gross_salary:,.2f} INR")
        print(f"   Annual Income: Rs. {annual_income:,.2f} INR")

        # Show company deductions if any
        if total_deductions > 0:
            print("\n   Company Deductions:")
            if employee_epf_contribution > 0:
                print(f"      EPF: Rs. {employee_epf_contribution:,.2f}")
            if professional_tax > 0:
                print(f"      Professional Tax: Rs. {professional_tax:,.2f}")
            if other_deductions > 0:
                print(f"      Other Deductions: Rs. {other_deductions:,.2f}")
            print(f"      Total: Rs. {total_deductions:,.2f}")

        if tax > 0:
            print(
                f"   Monthly Income Tax ({tax_rate:.0f}%): Rs. {tax:,.2f} INR"
            )  # [OK] Dynamic rate
        else:
            print("   Monthly Income Tax: Rs. 0.00 INR")

        print(f"   Net Monthly Salary: Rs. {net_salary:,.2f} INR")

        if annual_income <= 1800000:
            print("   (No tax - annual income below ₹18,00,000)")

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
            tax_rate = profile.get_tax_rate()  # [OK] ADD THIS LINE
            net_salary = profile.get_net_salary()
            annual_income = profile.gross_salary * 12
            total_deductions = (
                profile.employee_epf_contribution
                + profile.professional_tax
                + profile.other_deductions
            )

            print("\nSalary Details")
            print("=" * 60)
            print(f"Gross Monthly Salary: Rs. {profile.gross_salary:,.2f} INR")
            print(f"Annual Income: Rs. {annual_income:,.2f} INR")

            # Show company deductions if any
            if total_deductions > 0:
                print(f"\n{'Company Deductions':<30}")
                if profile.employee_epf_contribution > 0:
                    print(
                        f"  EPF Contribution: Rs. {profile.employee_epf_contribution:>13,.2f}"
                    )
                if profile.professional_tax > 0:
                    print(f"  Professional Tax: Rs. {profile.professional_tax:>13,.2f}")
                if profile.other_deductions > 0:
                    print(f"  Other Deductions: Rs. {profile.other_deductions:>13,.2f}")
                print(f"  Total: Rs. {total_deductions:>24,.2f}")

            if tax > 0:
                print(
                    f"Monthly Income Tax ({tax_rate:.0f}%): Rs. {tax:,.2f} INR"
                )  # [OK] CHANGED
                print(f"Net Monthly Salary: Rs. {net_salary:,.2f} INR")
            else:
                print(f"Net Monthly Salary: Rs. {net_salary:,.2f} INR")
                print("(No tax - annual income below Rs. 18,00,000.00)")

            print(f"Salary Credit Day: {profile.salary_day} of each month")

            if profile.last_salary_date:
                print(f"Last Salary Date: {profile.last_salary_date}")

            print("=" * 60)
        else:
            print("No salary profile configured")

    # ========== EXPENSE ANALYSIS ==========

    def show_expense_analysis(self, days: int = 30):
        """Show expense analysis for the last N days"""
        # Load transactions if needed
        self._load_transactions_if_needed()

        cutoff_date = BankClock.today() - timedelta(days=days)

        recent_expenses = []
        for txn in self.transactions:
            # Include EXPENSE and BILL_PAYMENT transactions (with or without category)
            if txn.type in ["EXPENSE", "BILL_PAYMENT"]:
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

        # Group by category (use "Uncategorized" if no category)
        by_category = {}
        for txn in recent_expenses:
            category = txn.category if txn.category else "Uncategorized"
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
            percentage = (amount / total) * 100 if total > 0 else 0
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

    def add_beneficiary(self, beneficiary):
        """Add a beneficiary to this account"""
        self.beneficiaries.append(beneficiary)

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
            success, message, txn_id = card.make_purchase(
                amount, merchant, category, self
            )
        else:
            print("Invalid card type")
            return

        if success:
            print(f"[OK] {message}")
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
            print(f"[OK] {message}")
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
                    print("[WARN] PAYMENT OVERDUE!")
        else:
            print("\n[OK] No outstanding balance")

        print("=" * 60)

        # Show recent card transactions (if any)
        try:
            txns = getattr(card, "transactions", []) or []
            if not txns:
                print("\nNo transactions found for this card.")
                return

            print("\nRecent Card Transactions")
            print("=" * 100)
            print(
                f"{'Txn ID':<18} {'Date/Time':<20} {'Type':<25} {'Merchant/Category':<25} {'Amount':>12} {'Balance':>12}"
            )
            print("-" * 100)

            # Show last 20 transactions
            for txn in txns[-20:]:
                # Transaction object provides display helpers
                line = txn.get_display_line(show_category=True)
                print(line)

            print("=" * 100)
        except Exception:
            # Be defensive: don't break statement printing
            pass

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

                    # Auto-pay on statement generation if the card is configured
                    try:
                        policy = getattr(card, "auto_pay_policy", "NONE")
                        if policy and policy.upper() != "NONE":
                            # Determine amount to attempt
                            if policy.upper() == "FULL":
                                pay_amount = bill["totalOutstanding"]
                            else:
                                # Treat any other non-NONE policy as MINIMUM
                                pay_amount = bill["minimumDue"]

                            # Attempt payment from this account (owner of the card)
                            success, msg, txn_id = card.pay_bill(pay_amount, self)
                            if success:
                                print(
                                    f"Auto-paid card ****{card.card_number[-4:]}: Rs. {pay_amount:,.2f} via account {self.account_number}"
                                )
                                DataStore.append_activity(
                                    timestamp=BankClock.get_formatted_datetime(),
                                    username=self.username,
                                    account_number=self.account_number,
                                    action="AUTO_PAY_CREDIT_CARD",
                                    amount=pay_amount,
                                    resulting_balance=self.balance,
                                    txn_id=txn_id,
                                    metadata=f"cardId={card.card_id};policy={policy}",
                                )
                            else:
                                print(
                                    f"Auto-pay failed for card ****{card.card_number[-4:]}: {msg}"
                                )
                    except Exception:
                        # Be defensive: any error should not stop daily processing
                        pass

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
            with open(Account._used_numbers_file, "r", encoding="utf-8") as f:
                Account._used_account_numbers = set(line.strip() for line in f)

    @staticmethod
    def _save_used_numbers():
        """Save used account numbers to file"""
        os.makedirs(os.path.dirname(Account._used_numbers_file), exist_ok=True)
        with open(Account._used_numbers_file, "w", encoding="utf-8") as f:
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
            "chequeBookManager": self.cheque_book_manager.to_dict(),
            "itrFilings": [f.to_dict() for f in self.itr_filings],
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

        # Load cheque book manager
        if data.get("chequeBookManager"):
            acc.cheque_book_manager = ChequeBookManager.from_dict(
                data["chequeBookManager"]
            )

        # Load ITR filings
        if data.get("itrFilings"):
            from .ITRFiling import ITRFilingRecord

            acc.itr_filings = [ITRFilingRecord.from_dict(f) for f in data["itrFilings"]]

        return acc


# Initialize used numbers on module load
Account._load_used_numbers()
