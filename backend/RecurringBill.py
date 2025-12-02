import os
import random
import threading
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Tuple

from dateutil.relativedelta import relativedelta


# NEW: Payment Method Enum
class PaymentMethod(Enum):
    """How the bill will be paid"""

    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"


class NachIdGenerator:
    _used_nach_ids = set()
    _lock = threading.Lock()
    _storage_file = "data/nach_ids.txt"

    @classmethod
    def _load_used_ids(cls):
        if os.path.exists(cls._storage_file):
            with open(cls._storage_file, "r") as file:
                cls._used_nach_ids = set(line.strip() for line in file if line.strip())

    @classmethod
    def _save_used_ids(cls):
        os.makedirs(os.path.dirname(cls._storage_file), exist_ok=True)
        with open(cls._storage_file, "w") as file:
            for nach_id in cls._used_nach_ids:
                file.write(nach_id + "\n")

    @classmethod
    def generate_nach_id(cls) -> str:
        cls._load_used_ids()
        date_str = datetime.now().strftime("%Y%m%d")

        with cls._lock:
            for _ in range(100):
                suffix = f"{random.randint(0, 999999):06d}"
                nach_id = f"NACH{date_str}{suffix}"

                if nach_id not in cls._used_nach_ids:
                    cls._used_nach_ids.add(nach_id)
                    cls._save_used_ids()
                    return nach_id

            raise Exception("Failed to generate unique NACH ID after 100 attempts")


class RecurringBillFactory:
    """Factory for creating and managing recurring bills"""

    _bill_counter = 1000

    # Predefined templates for common recurring bills
    # Format: (name, category, minAmount, maxAmount, frequency)
    COMMON_BILLS = [
        ("Electricity", "Utilities", 1500.0, 2500.0, "MONTHLY"),
        ("Internet", "Utilities", 800.0, 1200.0, "MONTHLY"),
        ("Mobile", "Utilities", 400.0, 800.0, "MONTHLY"),
        ("Netflix", "Entertainment", 199.0, 649.0, "MONTHLY"),
        ("Amazon Prime", "Entertainment", 299.0, 1499.0, "YEARLY"),
        ("Spotify", "Entertainment", 119.0, 149.0, "MONTHLY"),
        ("Insurance Premium", "Insurance", 5000.0, 15000.0, "QUARTERLY"),
        ("Rent", "Housing", 10000.0, 50000.0, "MONTHLY"),
        ("Gym Membership", "Health", 1000.0, 3000.0, "MONTHLY"),
        ("Newspaper", "Utilities", 150.0, 300.0, "MONTHLY"),
        ("DTH/Cable TV", "Entertainment", 300.0, 600.0, "MONTHLY"),
        ("Water Bill", "Utilities", 200.0, 500.0, "MONTHLY"),
        ("Gas Cylinder", "Utilities", 800.0, 1200.0, "MONTHLY"),
        ("Society Maintenance", "Housing", 2000.0, 5000.0, "MONTHLY"),
        ("Car Loan EMI", "Loans", 10000.0, 30000.0, "MONTHLY"),
        ("Home Loan EMI", "Loans", 15000.0, 50000.0, "MONTHLY"),
        ("Credit Card Bill", "Finance", 5000.0, 20000.0, "MONTHLY"),
    ]

    @staticmethod
    def generate_id() -> str:
        """
        Generates a unique bill ID

        Returns:
            A unique bill identifier in format "BILL####"
        """
        RecurringBillFactory._bill_counter += 1
        return f"BILL{RecurringBillFactory._bill_counter}"

    @staticmethod
    def get_common_bills() -> List[Tuple[str, str, float, float, str]]:
        """
        Get list of common bill templates

        Returns:
            List of tuples (name, category, minAmount, maxAmount, frequency)
        """
        return RecurringBillFactory.COMMON_BILLS.copy()

    @staticmethod
    def create_from_template(
        template_index: int,
        amount: float,
        day_of_month: int,
        auto_debit: bool = True,
        payment_method: PaymentMethod = PaymentMethod.BANK_ACCOUNT,  # NEW
        payment_card_id: Optional[str] = None,  # NEW
    ) -> "RecurringBill":
        """
        Create a bill from a predefined template

        Args:
            template_index: Index of the template in COMMON_BILLS
            amount: The bill amount
            day_of_month: Day of month for payment (1-28)
            auto_debit: Whether to enable auto-debit
            payment_method: How to pay the bill (NEW)
            payment_card_id: Card ID if paying via credit card (NEW)

        Returns:
            New RecurringBill instance
        """
        if template_index < 0 or template_index >= len(
            RecurringBillFactory.COMMON_BILLS
        ):
            raise ValueError(f"Invalid template index: {template_index}")

        name, category, min_amt, max_amt, frequency = RecurringBillFactory.COMMON_BILLS[
            template_index
        ]

        # Validate amount is within range
        if amount < min_amt or amount > max_amt:
            print(
                f"Warning: Amount Rs. {amount:.2f} is outside recommended range (Rs. {min_amt:.2f} - Rs. {max_amt:.2f})"
            )

        return RecurringBill(
            name=name,
            category=category,
            base_amount=amount,
            frequency=frequency,
            day_of_month=day_of_month,
            auto_debit=auto_debit,
            payment_method=payment_method,  # NEW
            payment_card_id=payment_card_id,  # NEW
        )

    @staticmethod
    def create_custom_bill(
        name: str,
        category: str,
        amount: float,
        frequency: str,
        day_of_month: int,
        auto_debit: bool = True,
        payment_method: PaymentMethod = PaymentMethod.BANK_ACCOUNT,  # NEW
        payment_card_id: Optional[str] = None,  # NEW
    ) -> "RecurringBill":
        """
        Create a custom recurring bill

        Args:
            name: Bill name
            category: Bill category
            amount: Bill amount
            frequency: Payment frequency ("MONTHLY", "QUARTERLY", "YEARLY")
            day_of_month: Day of month for payment (1-28)
            auto_debit: Whether to enable auto-debit
            payment_method: How to pay the bill (NEW)
            payment_card_id: Card ID if paying via credit card (NEW)

        Returns:
            New RecurringBill instance
        """
        if frequency not in ["MONTHLY", "QUARTERLY", "YEARLY"]:
            raise ValueError(
                f"Invalid frequency: {frequency}. Must be MONTHLY, QUARTERLY, or YEARLY"
            )

        if day_of_month < 1 or day_of_month > 28:
            raise ValueError(
                f"Invalid day of month: {day_of_month}. Must be between 1 and 28"
            )

        return RecurringBill(
            name=name,
            category=category,
            base_amount=amount,
            frequency=frequency,
            day_of_month=day_of_month,
            auto_debit=auto_debit,
            payment_method=payment_method,  # NEW
            payment_card_id=payment_card_id,  # NEW
        )


@dataclass
class RecurringBill:
    """Represents a recurring bill with automatic payment capability"""

    # Existing fields
    id: str = field(default_factory=RecurringBillFactory.generate_id)
    name: str = field(default="")
    category: str = field(default="")
    base_amount: float = field(default=0.0)
    frequency: str = field(default="MONTHLY")  # "MONTHLY", "QUARTERLY", "YEARLY"
    day_of_month: int = field(default=1)  # 1-28 for consistency
    auto_debit: bool = True
    last_processed: Optional[date] = None
    variance: float = 0.1  # ±10% variation by default
    nach_id: str = field(default_factory=NachIdGenerator.generate_nach_id)

    # NEW: Credit card bill linking (when THIS bill IS a credit card payment)
    linked_card_id: Optional[str] = None
    is_dynamic: bool = False  # If True, amount auto-updates from card balance

    # NEW: Payment method (HOW this bill is paid)
    payment_method: PaymentMethod = PaymentMethod.BANK_ACCOUNT
    payment_card_id: Optional[str] = None  # Which card to use for payment

    def should_process_today(self, today: date) -> bool:
        """Check if bill should be processed today"""
        if today.day != self.day_of_month:
            return False

        if self.last_processed is None:
            return True

        if self.frequency == "MONTHLY":
            next_due = self.last_processed + relativedelta(months=1)
            return today >= next_due

        elif self.frequency == "QUARTERLY":
            next_due = self.last_processed + relativedelta(months=3)
            return today >= next_due

        elif self.frequency == "YEARLY":
            next_due = self.last_processed + relativedelta(years=1)
            return today >= next_due

        return False

    def get_variable_amount(self) -> float:
        """Get amount with variance applied"""
        variation = random.uniform(-self.variance, self.variance)
        return round(self.base_amount * (1 + variation), 2)

    # NEW METHOD
    def get_current_amount(self, account=None) -> float:
        """
        Get the current bill amount.
        If dynamic and linked to a card, returns card's current balance.
        Otherwise returns variable amount based on base_amount.

        Args:
            account: Account object to fetch card details from

        Returns:
            Current bill amount
        """
        if self.is_dynamic and self.linked_card_id and account:
            card = account.get_card_by_id(self.linked_card_id)
            if card:
                try:
                    from Card import CreditCard

                    if isinstance(card, CreditCard):
                        return card.current_balance
                except ImportError:
                    pass

        return self.get_variable_amount()

    # NEW METHOD
    def get_payment_description(self, account=None) -> str:
        """
        Get human-readable payment method

        Args:
            account: Account object to fetch card details from

        Returns:
            Formatted payment method description
        """
        if self.payment_method == PaymentMethod.BANK_ACCOUNT:
            return "💰 Bank Account"
        elif self.payment_method == PaymentMethod.CREDIT_CARD and self.payment_card_id:
            if account:
                card = account.get_card_by_id(self.payment_card_id)
                if card:
                    return f"💳 {card.network} ****{card.card_number[-4:]}"
            return f"💳 Credit Card ****{self.payment_card_id[-4:]}"
        return "Unknown"

    # NEW METHOD
    def update_from_linked_card(self, account) -> bool:
        """
        Update base_amount from linked credit card if dynamic.

        Args:
            account: Account object to fetch card details from

        Returns:
            True if amount was updated, False otherwise
        """
        if self.is_dynamic and self.linked_card_id and account:
            card = account.get_card_by_id(self.linked_card_id)
            if card:
                try:
                    from Card import CreditCard

                    if isinstance(card, CreditCard):
                        old_amount = self.base_amount
                        self.base_amount = card.current_balance
                        return old_amount != self.base_amount
                except ImportError:
                    pass
        return False

    def copy(self, **changes):
        """Create a copy of the bill with optional changes"""
        import copy

        new_bill = copy.copy(self)
        for key, value in changes.items():
            setattr(new_bill, key, value)
        return new_bill

    def to_dict(self) -> dict:
        """Convert bill to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "baseAmount": self.base_amount,
            "frequency": self.frequency,
            "dayOfMonth": self.day_of_month,
            "autoDebit": self.auto_debit,
            "lastProcessed": self.last_processed.isoformat()
            if self.last_processed
            else None,
            "variance": self.variance,
            "nach_id": self.nach_id,
            # NEW FIELDS
            "linkedCardId": self.linked_card_id,
            "isDynamic": self.is_dynamic,
            "paymentMethod": self.payment_method.value
            if isinstance(self.payment_method, PaymentMethod)
            else self.payment_method,
            "paymentCardId": self.payment_card_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "RecurringBill":
        """Create bill from dictionary"""
        last_processed = None
        if data.get("lastProcessed"):
            last_processed = date.fromisoformat(data["lastProcessed"])

        # Handle payment method
        payment_method = PaymentMethod.BANK_ACCOUNT
        if data.get("paymentMethod"):
            try:
                if isinstance(data["paymentMethod"], str):
                    payment_method = PaymentMethod(data["paymentMethod"])
                else:
                    payment_method = data["paymentMethod"]
            except (ValueError, KeyError):
                payment_method = PaymentMethod.BANK_ACCOUNT

        return RecurringBill(
            id=data.get("id", None) or RecurringBillFactory.generate_id(),
            name=data.get("name", ""),
            category=data.get("category", ""),
            base_amount=data.get("baseAmount", 0.0),
            frequency=data.get("frequency", "MONTHLY"),
            day_of_month=data.get("dayOfMonth", 1),
            auto_debit=data.get("autoDebit", True),
            last_processed=last_processed,
            variance=data.get("variance", 0.1),
            nach_id=data.get("nach_id", None) or NachIdGenerator.generate_nach_id(),
            # NEW FIELDS
            linked_card_id=data.get("linkedCardId"),
            is_dynamic=data.get("isDynamic", False),
            payment_method=payment_method,
            payment_card_id=data.get("paymentCardId"),
        )

    def __repr__(self) -> str:
        payment_info = ""
        if self.payment_method == PaymentMethod.CREDIT_CARD:
            payment_info = f", paid_via_card={self.payment_card_id[-4:] if self.payment_card_id else 'N/A'}"
        return f"RecurringBill({self.id}, {self.name}, Rs. {self.base_amount:.2f}, {self.frequency}, nach_id={self.nach_id}{payment_info})"

    def __str__(self) -> str:
        freq_display = {
            "MONTHLY": "Monthly",
            "QUARTERLY": "Quarterly",
            "YEARLY": "Yearly",
        }
        payment_emoji = (
            "💳" if self.payment_method == PaymentMethod.CREDIT_CARD else "💰"
        )
        return f"{payment_emoji} {self.name} - Rs. {self.base_amount:.2f} ({freq_display.get(self.frequency, self.frequency)})"


# Convenience aliases for backward compatibility
RecurringBill.generate_id = RecurringBillFactory.generate_id
RecurringBill.get_common_bills = RecurringBillFactory.get_common_bills
