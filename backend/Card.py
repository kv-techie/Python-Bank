import string
from datetime import date, timedelta
from random import choice


class Card:
    def __init__(
        self,
        card_number: str,
        customer_id: str,
        account_number: str,
        card_type: str,
        expiry_date: date,
        cvv: str,
    ):
        self.card_number = card_number
        self.customer_id = customer_id
        self.account_number = account_number
        self.card_type = card_type  # "DEBIT" or "CREDIT"
        self.expiry_date = expiry_date
        self.cvv = cvv
        self.blocked = False

    def is_expired(self) -> bool:
        return date.today() > self.expiry_date

    def block(self):
        self.blocked = True

    def unblock(self):
        self.blocked = False

    @staticmethod
    def generate_card_number() -> str:
        # Generate a 16-digit card number as string
        return "".join(choice(string.digits) for _ in range(16))

    @staticmethod
    def generate_cvv() -> str:
        # Generate a 3-digit CVV
        return "".join(choice(string.digits) for _ in range(3))


class DebitCard(Card):
    def __init__(self, customer_id: str, account_number: str):
        card_number = Card.generate_card_number()
        cvv = Card.generate_cvv()
        expiry_date = date.today() + timedelta(days=4 * 365)  # 4 years expiry
        super().__init__(
            card_number, customer_id, account_number, "DEBIT", expiry_date, cvv
        )

    # Debit card transactions deduct from linked account, so no credit limit here


class CreditCard(Card):
    def __init__(self, customer_id: str, account_number: str, credit_limit: float):
        card_number = Card.generate_card_number()
        cvv = Card.generate_cvv()
        expiry_date = date.today() + timedelta(days=4 * 365)
        super().__init__(
            card_number, customer_id, account_number, "CREDIT", expiry_date, cvv
        )
        self.credit_limit = credit_limit
        self.credit_used = 0.0

    def available_credit(self) -> float:
        return self.credit_limit - self.credit_used

    def make_purchase(self, amount: float) -> bool:
        if self.blocked:
            raise Exception("Card is blocked")
        if self.is_expired():
            raise Exception("Card expired")
        if amount > self.available_credit():
            raise Exception("Insufficient credit limit")
        self.credit_used += amount
        return True

    def pay_bill(self, amount: float):
        if amount > self.credit_used:
            raise Exception("Bill payment amount exceeds credit used")
        self.credit_used -= amount
