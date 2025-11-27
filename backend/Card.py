import random
import string
from datetime import date, timedelta
from random import choice, randint
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from Account import Account


class Card:
    """Base class for all card types"""

    # Bank Identification Numbers (BIN) - first 6 digits
    BIN_PREFIXES = {
        "VISA_DEBIT": "450621",
        "VISA_CREDIT": "450622",
        "MASTERCARD_DEBIT": "550621",
        "MASTERCARD_CREDIT": "550622",
        "RUPAY_DEBIT": "650621",
        "RUPAY_CREDIT": "650622",
    }

    def __init__(
        self,
        card_number: str,
        customer_id: str,
        account_number: str,
        card_type: str,
        expiry_date: date,
        cvv: str,
        card_id: Optional[str] = None,
        network: str = "VISA",
    ):
        self.card_id = card_id or self.generate_card_id()
        self.card_number = card_number
        self.customer_id = customer_id
        self.account_number = account_number
        self.card_type = card_type  # "DEBIT" or "CREDIT"
        self.expiry_date = expiry_date
        self.cvv = cvv
        self.network = network  # "VISA", "MASTERCARD", or "RUPAY"
        self.blocked = False
        self.daily_limit = 50000.0  # Default daily transaction limit

    def is_expired(self) -> bool:
        """Check if card has expired"""
        from BankClock import BankClock

        return BankClock.today() > self.expiry_date

    def block(self):
        """Block the card"""
        self.blocked = True

    def unblock(self):
        """Unblock the card"""
        self.blocked = False

    def validate_transaction(self, amount: float) -> tuple[bool, str]:
        """
        Validate if transaction can proceed

        Returns:
            (is_valid, error_message)
        """
        if self.blocked:
            return False, "Card is blocked"
        if self.is_expired():
            return False, "Card has expired"
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > self.daily_limit:
            return (
                False,
                f"Amount exceeds daily limit of Rs. {self.daily_limit:,.2f} INR",
            )
        return True, "Valid"

    def get_masked_number(self) -> str:
        """Get masked card number (e.g., **** **** **** 1234)"""
        return "**** **** **** " + self.card_number[-4:]

    @staticmethod
    def generate_card_number(card_type: str = "DEBIT", network: str = "VISA") -> str:
        """
        Generate a valid 16-digit card number using Luhn algorithm

        Args:
            card_type: "DEBIT" or "CREDIT"
            network: "VISA", "MASTERCARD", or "RUPAY"

        Returns:
            Valid 16-digit card number as string
        """
        # Select appropriate BIN prefix
        bin_key = f"{network}_{card_type}"
        prefix = Card.BIN_PREFIXES.get(bin_key, "450621")

        # Generate random middle digits (9 digits)
        # Total: 6 (BIN) + 9 (random) + 1 (checksum) = 16 digits
        middle_digits = "".join(str(randint(0, 9)) for _ in range(9))

        # Combine prefix and middle digits
        partial_number = prefix + middle_digits

        # Calculate and append Luhn checksum
        checksum = Card._calculate_luhn_checksum(partial_number)

        return partial_number + str(checksum)

    @staticmethod
    def _calculate_luhn_checksum(partial_number: str) -> int:
        """
        Calculate Luhn algorithm checksum digit

        The Luhn algorithm:
        1. Starting from the rightmost digit, double every second digit
        2. If doubling results in a two-digit number, add the digits together
        3. Sum all digits
        4. The check digit is the amount needed to make sum divisible by 10
        """
        digits = [int(d) for d in partial_number]

        # Double every second digit from right to left
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9

        # Calculate checksum
        total = sum(digits)
        checksum = (10 - (total % 10)) % 10

        return checksum

    @staticmethod
    def validate_card_number(card_number: str) -> bool:
        """
        Validate a card number using Luhn algorithm

        Returns:
            True if card number is valid, False otherwise
        """
        if not card_number.isdigit() or len(card_number) != 16:
            return False

        # Extract all digits except the last one (checksum)
        partial_number = card_number[:-1]
        expected_checksum = int(card_number[-1])

        # Calculate what the checksum should be
        calculated_checksum = Card._calculate_luhn_checksum(partial_number)

        return calculated_checksum == expected_checksum

    @staticmethod
    def get_card_network(card_number: str) -> str:
        """
        Determine card network from card number

        Returns:
            "VISA", "MASTERCARD", "RUPAY", or "UNKNOWN"
        """
        if not card_number or len(card_number) < 2:
            return "UNKNOWN"

        first_digit = card_number[0]
        first_two = card_number[:2]

        if first_digit == "4":
            return "VISA"
        elif first_two in ["51", "52", "53", "54", "55"]:
            return "MASTERCARD"
        elif first_two in ["60", "65", "81", "82"]:
            return "RUPAY"
        else:
            return "UNKNOWN"

    @staticmethod
    def generate_cvv() -> str:
        """Generate a 3-digit CVV"""
        return "".join(choice(string.digits) for _ in range(3))

    @staticmethod
    def generate_card_id() -> str:
        """Generate unique card ID"""
        return f"CARD{random.randint(100000000, 999999999)}"

    def to_dict(self) -> dict:
        """Serialize card to dictionary"""
        return {
            "cardId": self.card_id,
            "cardNumber": self.card_number,
            "customerId": self.customer_id,
            "accountNumber": self.account_number,
            "cardType": self.card_type,
            "network": self.network,
            "expiryDate": self.expiry_date.isoformat(),
            "cvv": self.cvv,
            "blocked": self.blocked,
            "dailyLimit": self.daily_limit,
        }

    @staticmethod
    def from_dict(data: dict) -> "Card":
        """Deserialize card from dictionary"""
        card_type = data["cardType"]
        expiry_date = date.fromisoformat(data["expiryDate"])
        network = data.get("network", "VISA")

        if card_type == "CREDIT":
            card = CreditCard.__new__(CreditCard)
            Card.__init__(
                card,
                data["cardNumber"],
                data["customerId"],
                data["accountNumber"],
                card_type,
                expiry_date,
                data["cvv"],
                data.get("cardId"),
                network,
            )
            card.credit_limit = data.get("creditLimit", 0.0)
            card.credit_used = data.get("creditUsed", 0.0)
            card.billing_day = data.get("billingDay", 1)
            card.last_bill_date = (
                date.fromisoformat(data["lastBillDate"])
                if data.get("lastBillDate")
                else None
            )
            card.due_date = (
                date.fromisoformat(data["dueDate"]) if data.get("dueDate") else None
            )
            card.outstanding_balance = data.get("outstandingBalance", 0.0)
            card.minimum_due = data.get("minimumDue", 0.0)
            card.interest_rate = data.get("interestRate", 0.18)
        else:
            card = DebitCard.__new__(DebitCard)
            Card.__init__(
                card,
                data["cardNumber"],
                data["customerId"],
                data["accountNumber"],
                card_type,
                expiry_date,
                data["cvv"],
                data.get("cardId"),
                network,
            )

        card.blocked = data.get("blocked", False)
        card.daily_limit = data.get("dailyLimit", 50000.0)
        return card


class DebitCard(Card):
    """Debit card class - transactions deduct directly from account balance"""

    def __init__(self, customer_id: str, account_number: str, network: str = "VISA"):
        card_number = Card.generate_card_number("DEBIT", network)
        cvv = Card.generate_cvv()
        expiry_date = date.today() + timedelta(days=4 * 365)  # 4 years validity
        super().__init__(
            card_number,
            customer_id,
            account_number,
            "DEBIT",
            expiry_date,
            cvv,
            network=network,
        )

    def make_purchase(
        self,
        amount: float,
        account: "Account",
        merchant: str,
        category: str = "Shopping",
    ) -> tuple[bool, str, Optional[str]]:
        """
        Make a debit card purchase

        Args:
            amount: Transaction amount
            account: Account object to debit from
            merchant: Merchant name
            category: Transaction category

        Returns:
            (success, message, transaction_id)
        """
        # Validate transaction
        is_valid, msg = self.validate_transaction(amount)
        if not is_valid:
            return False, msg, None

        # Check account balance
        min_balance = account._min_operational_balance
        if account.balance - amount < min_balance:
            return (
                False,
                f"Insufficient funds. Must maintain Rs. {min_balance:.2f} INR",
                None,
            )

        # Check daily limits for minor accounts
        if account.is_minor_account:
            today_transactions = account.get_today_transactions()
            if today_transactions + amount > account._minor_daily_transaction_limit:
                remaining = account._minor_daily_transaction_limit - today_transactions
                return (
                    False,
                    f"Daily transaction limit exceeded. Remaining: Rs. {remaining:.2f} INR",
                    None,
                )

        # Process transaction
        from DataStore import DataStore
        from Transaction import Transaction

        account.balance -= amount
        txn = Transaction(
            type="DEBIT_CARD_PURCHASE",
            amount=amount,
            resulting_balance=account.balance,
            category=category,
            merchant=merchant,
        )
        account.transactions.append(txn)

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=account.username,
            account_number=account.account_number,
            action="DEBIT_CARD_PURCHASE",
            amount=amount,
            resulting_balance=account.balance,
            txn_id=txn.id,
            metadata=f"cardId={self.card_id};merchant={merchant};category={category};network={self.network}",
        )

        # Check AMB fee
        account._check_and_apply_amb_fee()

        return True, f"Purchase successful at {merchant}", txn.id

    def withdraw_atm(
        self, amount: float, account: "Account", atm_location: str = "Unknown"
    ) -> tuple[bool, str, Optional[str]]:
        """
        Withdraw cash from ATM using debit card

        Args:
            amount: Withdrawal amount
            account: Account object to debit from
            atm_location: ATM location

        Returns:
            (success, message, transaction_id)
        """
        # Validate transaction
        is_valid, msg = self.validate_transaction(amount)
        if not is_valid:
            return False, msg, None

        # ATM withdrawal limit check (typically lower than daily limit)
        atm_limit = min(self.daily_limit, 20000.0)  # Rs. 20,000 per ATM withdrawal
        if amount > atm_limit:
            return (
                False,
                f"ATM withdrawal limit is Rs. {atm_limit:,.2f} INR per transaction",
                None,
            )

        # Check account balance
        min_balance = account._min_operational_balance
        if account.balance - amount < min_balance:
            return (
                False,
                f"Insufficient funds. Must maintain Rs. {min_balance:.2f} INR",
                None,
            )

        # Process withdrawal
        from DataStore import DataStore
        from Transaction import Transaction

        account.balance -= amount
        txn = Transaction(
            type="ATM_WITHDRAWAL",
            amount=amount,
            resulting_balance=account.balance,
            merchant=atm_location,
        )
        account.transactions.append(txn)

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=account.username,
            account_number=account.account_number,
            action="ATM_WITHDRAWAL",
            amount=amount,
            resulting_balance=account.balance,
            txn_id=txn.id,
            metadata=f"cardId={self.card_id};location={atm_location};network={self.network}",
        )

        # Check AMB fee
        account._check_and_apply_amb_fee()

        return True, f"ATM withdrawal successful at {atm_location}", txn.id


class CreditCard(Card):
    """Credit card class - transactions use credit limit, not account balance"""

    def __init__(
        self,
        customer_id: str,
        account_number: str,
        credit_limit: float,
        billing_day: int = 1,
        network: str = "VISA",
    ):
        card_number = Card.generate_card_number("CREDIT", network)
        cvv = Card.generate_cvv()
        expiry_date = date.today() + timedelta(days=4 * 365)  # 4 years validity
        super().__init__(
            card_number,
            customer_id,
            account_number,
            "CREDIT",
            expiry_date,
            cvv,
            network=network,
        )
        self.credit_limit = credit_limit
        self.credit_used = 0.0
        self.billing_day = billing_day  # Day of month when bill is generated (1-28)
        self.last_bill_date: Optional[date] = None
        self.due_date: Optional[date] = None
        self.outstanding_balance = 0.0
        self.minimum_due = 0.0
        self.interest_rate = 0.18  # 18% annual interest (1.5% monthly)
        self.reward_points = 0.0  # Reward points earned

    def available_credit(self) -> float:
        """Get available credit limit"""
        return self.credit_limit - self.credit_used

    def credit_utilization(self) -> float:
        """
        Calculate credit utilization percentage
        High utilization (>30%) negatively impacts CIBIL score
        """
        if self.credit_limit == 0:
            return 0.0
        return (self.credit_used / self.credit_limit) * 100

    def make_purchase(
        self, amount: float, merchant: str, category: str = "Shopping"
    ) -> tuple[bool, str, Optional[str]]:
        """
        Make a credit card purchase

        Args:
            amount: Transaction amount
            merchant: Merchant name
            category: Transaction category

        Returns:
            (success, message, transaction_id)
        """
        # Validate transaction
        is_valid, msg = self.validate_transaction(amount)
        if not is_valid:
            return False, msg, None

        if amount > self.available_credit():
            return (
                False,
                f"Insufficient credit limit. Available: Rs. {self.available_credit():.2f} INR",
                None,
            )

        # Process transaction
        from Transaction import Transaction

        self.credit_used += amount

        # Calculate reward points (1 point per Rs. 100 spent)
        points_earned = amount / 100
        self.reward_points += points_earned

        # Create transaction record
        txn = Transaction(
            type="CREDIT_CARD_PURCHASE",
            amount=amount,
            resulting_balance=self.credit_used,
            category=category,
            merchant=merchant,
        )

        return (
            True,
            f"Purchase successful at {merchant}. Reward points earned: {points_earned:.0f}",
            txn.id,
        )

    def pay_bill(
        self, amount: float, account: "Account"
    ) -> tuple[bool, str, Optional[str]]:
        """
        Pay credit card bill from linked account

        Args:
            amount: Payment amount
            account: Account object to debit from

        Returns:
            (success, message, transaction_id)
        """
        if amount <= 0:
            return False, "Payment amount must be positive", None

        # Can't pay more than what's owed
        max_payable = (
            self.outstanding_balance
            if self.outstanding_balance > 0
            else self.credit_used
        )
        if amount > max_payable:
            return (
                False,
                f"Payment amount exceeds outstanding balance (Rs. {max_payable:.2f} INR)",
                None,
            )

        # Check if account has sufficient balance
        min_balance = account._min_operational_balance
        if account.balance - amount < min_balance:
            return (
                False,
                f"Insufficient account balance. Must maintain Rs. {min_balance:.2f} INR",
                None,
            )

        # Process payment
        from DataStore import DataStore
        from Transaction import Transaction

        account.balance -= amount
        self.credit_used -= amount

        if self.outstanding_balance > 0:
            self.outstanding_balance -= amount
            # Recalculate minimum due
            if self.outstanding_balance > 0:
                self.minimum_due = max(self.outstanding_balance * 0.05, 500.0)
                self.minimum_due = min(self.minimum_due, self.outstanding_balance)
            else:
                self.minimum_due = 0.0

        # Account transaction
        txn = Transaction(
            type="CREDIT_CARD_PAYMENT",
            amount=amount,
            resulting_balance=account.balance,
            metadata={"cardId": self.card_id},
        )
        account.transactions.append(txn)

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=account.username,
            account_number=account.account_number,
            action="CREDIT_CARD_PAYMENT",
            amount=amount,
            resulting_balance=account.balance,
            txn_id=txn.id,
            metadata=f"cardId={self.card_id};creditUsed={self.credit_used:.2f};network={self.network}",
        )

        return (
            True,
            f"Payment of Rs. {amount:.2f} INR successful. Remaining balance: Rs. {self.credit_used:.2f} INR",
            txn.id,
        )

    def generate_bill(self, today: date) -> dict:
        """
        Generate monthly credit card bill

        Returns:
            Dictionary with bill details
        """
        if self.credit_used == 0 and self.outstanding_balance == 0:
            return {"success": False, "message": "No outstanding balance"}

        # Calculate due date (15 days from bill date)
        self.last_bill_date = today
        self.due_date = today + timedelta(days=15)

        # Calculate interest on any previous outstanding balance (unpaid amount)
        interest_charged = 0.0
        if self.outstanding_balance > 0:
            monthly_rate = self.interest_rate / 12
            interest_charged = self.outstanding_balance * monthly_rate
            self.credit_used += interest_charged

        # Set new outstanding balance
        self.outstanding_balance = self.credit_used

        # Minimum due is 5% of outstanding or Rs. 500, whichever is higher
        self.minimum_due = max(self.outstanding_balance * 0.05, 500.0)
        self.minimum_due = min(self.minimum_due, self.outstanding_balance)

        bill_details = {
            "success": True,
            "billDate": self.last_bill_date.isoformat(),
            "dueDate": self.due_date.isoformat(),
            "totalOutstanding": self.outstanding_balance,
            "minimumDue": self.minimum_due,
            "interestCharged": interest_charged,
            "creditUsed": self.credit_used,
            "creditLimit": self.credit_limit,
            "availableCredit": self.available_credit(),
            "rewardPoints": self.reward_points,
        }

        return bill_details

    def check_bill_generation(self, today: date) -> bool:
        """Check if bill should be generated today"""
        if today.day == self.billing_day:
            # Check if bill already generated this month
            if self.last_bill_date is None or self.last_bill_date.month != today.month:
                return True
        return False

    def is_payment_overdue(self, today: date) -> bool:
        """Check if payment is overdue"""
        if self.due_date and self.outstanding_balance > 0:
            return today > self.due_date
        return False

    def apply_late_fee(self, today: date) -> float:
        """
        Apply late payment fee if payment is overdue

        Returns:
            Late fee amount charged
        """
        if not self.is_payment_overdue(today):
            return 0.0

        # Late fee: Rs. 500 or 2% of outstanding, whichever is higher
        late_fee = max(500.0, self.outstanding_balance * 0.02)
        late_fee = min(late_fee, 1500.0)  # Cap at Rs. 1,500

        self.credit_used += late_fee
        self.outstanding_balance += late_fee

        return late_fee

    def redeem_reward_points(self, points: float) -> tuple[bool, str, float]:
        """
        Redeem reward points (1 point = Rs. 0.25)

        Returns:
            (success, message, amount_redeemed)
        """
        if points <= 0:
            return False, "Points must be positive", 0.0

        if points > self.reward_points:
            return (
                False,
                f"Insufficient points. Available: {self.reward_points:.0f}",
                0.0,
            )

        # 1 reward point = Rs. 0.25
        redemption_value = points * 0.25

        # Can only redeem against outstanding balance
        if redemption_value > self.credit_used:
            redemption_value = self.credit_used
            points = redemption_value / 0.25

        self.credit_used -= redemption_value
        self.reward_points -= points

        if self.outstanding_balance > 0:
            self.outstanding_balance -= redemption_value

        return (
            True,
            f"Redeemed {points:.0f} points for Rs. {redemption_value:.2f} INR",
            redemption_value,
        )

    def to_dict(self) -> dict:
        """Serialize credit card to dictionary"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "creditLimit": self.credit_limit,
                "creditUsed": self.credit_used,
                "billingDay": self.billing_day,
                "lastBillDate": self.last_bill_date.isoformat()
                if self.last_bill_date
                else None,
                "dueDate": self.due_date.isoformat() if self.due_date else None,
                "outstandingBalance": self.outstanding_balance,
                "minimumDue": self.minimum_due,
                "interestRate": self.interest_rate,
                "rewardPoints": self.reward_points,
            }
        )
        return base_dict


# Example usage and testing
if __name__ == "__main__":
    # Test card number generation
    print("Testing Card Number Generation:")
    print("=" * 60)

    for network in ["VISA", "MASTERCARD", "RUPAY"]:
        for card_type in ["DEBIT", "CREDIT"]:
            card_num = Card.generate_card_number(card_type, network)
            is_valid = Card.validate_card_number(card_num)
            detected_network = Card.get_card_network(card_num)

            print(f"{network} {card_type}: {card_num}")
            print(f"  Valid: {is_valid}, Detected: {detected_network}")
            print()

    print("=" * 60)
