from datetime import datetime
from typing import Tuple, Optional

from ..Card import CreditCard, DebitCard
from ..Customer import Customer
from ..Account import Account
from ..Bank import Bank
from ..CIBIL import calculate_cibil_score
from ..CreditEvaluator import CreditEvaluator

class CardService:
    """Handles business logic for credit and debit card issuance, limits, and blocking."""
    
    def __init__(self, bank: Bank, logger):
        self.bank = bank
        self.logger = logger
        
    def check_credit_card_eligibility(self, customer: Customer, account: Account) -> Tuple[bool, str, float, float, float]:
        """
        Evaluate customer eligibility for a new credit card.
        Returns: (is_eligible, reason, cibil_score, annual_income, approved_limit)
        """
        if not account.salary_profile:
            return False, "Credit card requires a salary profile. Please set up salary first.", 0, 0, 0
            
        dob = datetime.strptime(account.dob, "%Y-%m-%d")
        age = (datetime.now() - dob).days // 365
        
        cibil_score = calculate_cibil_score(customer, self.bank)
        annual_income = account.salary_profile.gross_salary * 12
        
        eligible, reason = CreditEvaluator.is_eligible_for_credit_card(cibil_score, annual_income, age)
        if not eligible:
            return False, reason, cibil_score, annual_income, 0
            
        credit_limit = CreditEvaluator.calculate_credit_limit(
            cibil_score=cibil_score,
            annual_income=annual_income,
            age=age,
            existing_debt=0.0,
            employer_category=getattr(customer, "employer_category", "pvt"),
            has_salary_account=True,
        )
        return True, reason, cibil_score, annual_income, credit_limit
        
    def issue_credit_card(self, account: Account, limit: float, billing_day: int, network: str, auto_pay_policy: str):
        """Issue a credit card and add it to the account"""
        card = CreditCard(account.customer_id, account.account_number, limit, billing_day, network)
        card.auto_pay_policy = auto_pay_policy
        account.add_card(card)
        self.bank.save()
        self.logger.info(f"Issued {network} credit card to {account.account_number} with limit {limit}")
        return card

    def issue_debit_card(self, account: Account, network: str):
        """Issue a new debit card"""
        card = DebitCard(account.customer_id, account.account_number, network)
        account.add_card(card)
        self.bank.save()
        self.logger.info(f"Issued {network} debit card to {account.account_number}")
        return card
        
    def toggle_card_block_status(self, card, block: bool):
        """Block or unblock a card"""
        card.blocked = block
        self.bank.save()
        status = "blocked" if block else "unblocked"
        self.logger.info(f"Card {card.card_number[-4:]} {status}")
        
    def update_card_pin(self, card, new_pin: str):
        """Update a card's PIN"""
        card.pin = new_pin
        self.bank.save()
        self.logger.info(f"PIN updated for card {card.card_number[-4:]}")

    def update_auto_pay_policy(self, card, policy: str):
        """Update auto pay policy"""
        card.auto_pay_policy = policy
        self.bank.save()
        self.logger.info(f"Auto-pay policy for {card.card_number[-4:]} set to {policy}")
