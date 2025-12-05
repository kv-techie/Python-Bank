from typing import TYPE_CHECKING, Tuple

from CIBIL import calculate_cibil_score

if TYPE_CHECKING:
    from Account import Account
    from Bank import Bank
    from Card import CreditCard
    from Customer import Customer


class CreditLimitEnhancement:
    """Handle credit limit enhancement requests for credit cards"""

    # Minimum requirements for credit limit enhancement
    MIN_CARD_AGE_MONTHS = 6  # Card must be at least 6 months old
    MIN_CIBIL_SCORE = 700  # Minimum CIBIL score required
    MIN_UTILIZATION = 30  # Must use at least 30% of current limit
    MAX_UTILIZATION = 90  # Should not exceed 90% utilization
    MIN_ON_TIME_PAYMENTS = 0.95  # 95% on-time payment history
    COOLDOWN_MONTHS = 6  # Can request enhancement only once every 6 months

    @staticmethod
    def check_eligibility(
        card: "CreditCard", customer: "Customer", bank: "Bank", account: "Account"
    ) -> Tuple[bool, str, dict]:
        """
        Check if customer is eligible for credit limit enhancement

        Returns:
            (eligible, reason, details_dict)
        """
        from BankClock import BankClock

        today = BankClock.today()
        details = {}

        # 1. Check card age (at least 6 months old)
        card_age_months = 0
        if hasattr(card, "created_date"):
            card_age_months = (today.year - card.created_date.year) * 12 + (
                today.month - card.created_date.month
            )
        else:
            # If no created_date, assume card is old enough (legacy data)
            card_age_months = 12

        details["card_age_months"] = card_age_months

        if card_age_months < CreditLimitEnhancement.MIN_CARD_AGE_MONTHS:
            return (
                False,
                f"Card must be at least {CreditLimitEnhancement.MIN_CARD_AGE_MONTHS} months old. Current age: {card_age_months} months",
                details,
            )

        # 2. Check CIBIL score
        cibil_score = calculate_cibil_score(customer, bank)
        details["cibil_score"] = cibil_score

        if cibil_score < CreditLimitEnhancement.MIN_CIBIL_SCORE:
            return (
                False,
                f"CIBIL score too low. Required: {CreditLimitEnhancement.MIN_CIBIL_SCORE}, Current: {cibil_score:.0f}",
                details,
            )

        # 3. Check credit utilization (should be using the card, but not maxed out)
        utilization = card.credit_utilization()
        details["utilization"] = utilization

        if utilization < CreditLimitEnhancement.MIN_UTILIZATION:
            return (
                False,
                f"Credit utilization too low. You must use at least {CreditLimitEnhancement.MIN_UTILIZATION}% of your limit. Current: {utilization:.1f}%",
                details,
            )

        if utilization > CreditLimitEnhancement.MAX_UTILIZATION:
            return (
                False,
                f"Credit utilization too high. Please reduce usage below {CreditLimitEnhancement.MAX_UTILIZATION}%. Current: {utilization:.1f}%",
                details,
            )

        # 4. Check payment history (on-time payments)
        payment_transactions = [
            t for t in card.transactions if t.type == "CREDIT_CARD_PAYMENT"
        ]

        total_payments = len(payment_transactions)
        details["total_payments"] = total_payments

        if total_payments < 3:
            return (
                False,
                f"Insufficient payment history. Need at least 3 payments. Current: {total_payments}",
                details,
            )

        # Check for late payments (simplified: if outstanding balance exists and due date passed)
        late_payments = 0
        if hasattr(card, "payment_history"):
            late_payments = sum(1 for p in card.payment_history if p.get("late", False))

        on_time_ratio = (
            (total_payments - late_payments) / total_payments
            if total_payments > 0
            else 0
        )
        details["on_time_ratio"] = on_time_ratio
        details["late_payments"] = late_payments

        if on_time_ratio < CreditLimitEnhancement.MIN_ON_TIME_PAYMENTS:
            return (
                False,
                f"Payment history not strong enough. Required: {CreditLimitEnhancement.MIN_ON_TIME_PAYMENTS * 100:.0f}% on-time. Current: {on_time_ratio * 100:.0f}%",
                details,
            )

        # 5. Check cooldown period (can't request too frequently)
        if hasattr(card, "last_limit_enhancement_date"):
            months_since_last = (
                today.year - card.last_limit_enhancement_date.year
            ) * 12 + (today.month - card.last_limit_enhancement_date.month)
            details["months_since_last_enhancement"] = months_since_last

            if months_since_last < CreditLimitEnhancement.COOLDOWN_MONTHS:
                return (
                    False,
                    f"Too soon since last enhancement. Wait {CreditLimitEnhancement.COOLDOWN_MONTHS - months_since_last} more months",
                    details,
                )

        # 6. Check if there are any defaulted loans
        loans = bank.get_loans_for_customer(customer.customer_id)
        defaulted_loans = [l for l in loans if l.status == "Defaulted"]
        details["defaulted_loans"] = len(defaulted_loans)

        if defaulted_loans:
            return (
                False,
                f"Cannot enhance limit with {len(defaulted_loans)} defaulted loan(s). Clear defaults first",
                details,
            )

        # All checks passed
        return (True, "Eligible for credit limit enhancement", details)

    @staticmethod
    def calculate_new_limit(
        current_limit: float,
        cibil_score: float,
        utilization: float,
        income: float,
    ) -> float:
        """
        Calculate the new credit limit based on various factors

        Args:
            current_limit: Current credit limit
            cibil_score: Customer's CIBIL score
            utilization: Current credit utilization percentage
            income: Annual income

        Returns:
            New credit limit
        """
        # Base enhancement: 20-50% increase based on CIBIL score
        if cibil_score >= 800:
            enhancement_factor = 0.50  # 50% increase
        elif cibil_score >= 750:
            enhancement_factor = 0.40  # 40% increase
        elif cibil_score >= 700:
            enhancement_factor = 0.30  # 30% increase
        else:
            enhancement_factor = 0.20  # 20% increase

        # Adjust based on utilization (reward high but not maxed out usage)
        if 50 <= utilization <= 75:
            enhancement_factor += 0.10  # Bonus 10% for optimal usage
        elif utilization > 75:
            enhancement_factor -= 0.05  # Penalty for too high usage

        # Calculate new limit
        new_limit = current_limit * (1 + enhancement_factor)

        # Cap at 3x annual income (responsible lending)
        max_limit = income * 3
        new_limit = min(new_limit, max_limit)

        # Round to nearest 10,000
        new_limit = round(new_limit / 10000) * 10000

        return new_limit

    @staticmethod
    def request_enhancement(
        card: "CreditCard", customer: "Customer", bank: "Bank", account: "Account"
    ) -> Tuple[bool, str, float]:
        """
        Request credit limit enhancement

        Returns:
            (approved, message, new_limit)
        """
        from BankClock import BankClock

        # Check eligibility
        eligible, reason, details = CreditLimitEnhancement.check_eligibility(
            card, customer, bank, account
        )

        if not eligible:
            return (False, reason, card.credit_limit)

        # Calculate new limit
        annual_income = 0
        if account.salary_profile:
            annual_income = account.salary_profile.gross_salary * 12
        else:
            # Fallback to a conservative estimate
            annual_income = 300000  # Rs. 3 lakhs default

        new_limit = CreditLimitEnhancement.calculate_new_limit(
            current_limit=card.credit_limit,
            cibil_score=details["cibil_score"],
            utilization=details["utilization"],
            income=annual_income,
        )

        # Update card
        old_limit = card.credit_limit
        card.credit_limit = new_limit
        card.last_limit_enhancement_date = BankClock.today()

        # Record enhancement in card history
        if not hasattr(card, "limit_enhancement_history"):
            card.limit_enhancement_history = []

        card.limit_enhancement_history.append(
            {
                "date": BankClock.today().isoformat(),
                "old_limit": old_limit,
                "new_limit": new_limit,
                "cibil_score": details["cibil_score"],
                "reason": "Requested by customer",
            }
        )

        increase_amount = new_limit - old_limit
        increase_percentage = (increase_amount / old_limit) * 100

        message = (
            f"✅ Credit limit enhanced!\n"
            f"Previous Limit: Rs. {old_limit:,.2f}\n"
            f"New Limit: Rs. {new_limit:,.2f}\n"
            f"Increase: Rs. {increase_amount:,.2f} ({increase_percentage:.1f}%)"
        )

        return (True, message, new_limit)
