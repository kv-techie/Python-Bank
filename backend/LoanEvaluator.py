# LoanEvaluator.py
from datetime import date


class LoanEvaluator:
    """Evaluates loan applications based on customer profile and CIBIL score"""

    # Loan-to-Value thresholds - max loan as multiple of annual income
    LOAN_TO_INCOME_RATIOS = {
        "A": 10.0,  # Category A: 10x annual income
        "B": 7.5,  # Category B: 7.5x annual income
        "C": 5.0,  # Category C: 5x annual income
    }

    # Interest rate adjustments based on CIBIL score
    CIBIL_RATE_ADJUSTMENTS = {
        800: 0.0,  # 800+ : 0% premium
        750: 0.25,  # 750-799: +0.25%
        700: 0.75,  # 700-749: +0.75%
    }

    @staticmethod
    def evaluate(
        customer, principal: float, tenure_months: int, interest_rate: float, bank
    ) -> tuple[bool, str, dict]:
        """
        Run all major approval checks according to real bank criteria.
        Returns (approved: bool, reason: str, details: dict).
        """

        details = {
            "cibil_score": 0,
            "dti_ratio": 0.0,
            "max_affordable_loan": 0.0,
            "recommended_tenure": 0,
            "adjusted_interest_rate": interest_rate,
            "processing_fee": 0.0,
        }

        # 1. CIBIL Score Check (Minimum 700)
        cibil_score = getattr(customer, "cibil_score", 0)
        details["cibil_score"] = cibil_score

        if not cibil_score or cibil_score < 700:
            return (
                False,
                f"CIBIL score too low ({cibil_score}). Minimum required: 700",
                details,
            )

        # 2. Salary Check (Minimum Rs. 20,000)
        salary = getattr(customer, "salary", 0)
        if not salary or salary < 20000:
            return False, "Salary below minimum requirement (Rs. 20,000)", details

        # 3. Employment Check - 1 year with current employer
        job_start_date = getattr(customer, "job_start_date", None)
        if not job_start_date:
            return False, "Missing job starting date", details

        try:
            job_days = (date.today() - date.fromisoformat(job_start_date)).days
        except Exception:
            return False, "Invalid job start date", details

        if job_days < 365:
            return False, "Less than 1 year in current employment", details

        # 4. Bounce/Default History Check
        bounces = getattr(customer, "bounce_count", 0)
        if bounces > 0:
            return (
                False,
                f"Cheque bounces detected ({bounces}). Must have clean record for loan",
                details,
            )

        # 5. DTI (Debt-to-Income) Check
        dti_ratio = customer.get_DTI(bank)
        details["dti_ratio"] = dti_ratio

        if dti_ratio > 0.5:
            return (
                False,
                f"High debt-to-income ratio ({dti_ratio * 100:.1f}% > 50%)",
                details,
            )

        # 6. Age Check - must be 18-60
        customer_age = customer.calculate_age()
        if not (18 <= customer_age <= 60):
            return (
                False,
                f"Age not in eligible range (18-60). Current age: {customer_age}",
                details,
            )

        # 7. KYC Check
        kyc_completed = getattr(customer, "kyc_completed", False)
        if not kyc_completed:
            return False, "KYC verification pending", details

        # 8. Employer Category Check (A or B only, not C)
        employer_category = getattr(customer, "employer_category", None)
        if employer_category is None or employer_category not in {"A", "B"}:
            return (
                False,
                "Employer category not supported (Only A or B category employers)",
                details,
            )

        # 9. City / Location Check
        allowed_cities = {"Bengaluru", "Mumbai", "Delhi"}
        customer_city = getattr(customer, "city", None)
        if customer_city and customer_city not in allowed_cities:
            return (
                False,
                f"City not eligible for this loan (Only {', '.join(allowed_cities)})",
                details,
            )

        # 10. Loan-to-Value Check - Principal shouldn't exceed max allowed
        annual_income = salary * 12
        max_loan_multiplier = LoanEvaluator.LOAN_TO_INCOME_RATIOS.get(
            employer_category, 5.0
        )
        max_loan_amount = annual_income * max_loan_multiplier
        details["max_affordable_loan"] = max_loan_amount

        if principal > max_loan_amount:
            return (
                False,
                f"Loan amount (Rs. {principal:,.0f}) exceeds max limit (Rs. {max_loan_amount:,.0f}) for category {employer_category}",
                details,
            )

        # 11. Principal and Tenure Business Rules
        if principal < 10000:
            return False, "Minimum loan amount is Rs. 10,000", details
        if tenure_months < 6:
            return False, "Minimum loan tenure is 6 months", details

        # 12. EMI Affordability Check
        monthly_rate = (interest_rate / 100) / 12
        emi = (
            principal
            * monthly_rate
            * ((1 + monthly_rate) ** tenure_months)
            / (((1 + monthly_rate) ** tenure_months) - 1)
        )

        # EMI should not exceed 50% of monthly income
        if emi > salary * 0.5:
            return (
                False,
                f"EMI (Rs. {emi:.2f}) exceeds 50% of monthly income (Rs. {salary:.2f})",
                details,
            )

        # 13. Total Debt Obligations Check
        existing_loans = bank.get_loans_for_customer(customer.customer_id)
        total_emi = sum(
            loan.calculate_emi() for loan in existing_loans if loan.status == "Active"
        )

        total_obligations = total_emi + emi
        dti_ratio = total_obligations / salary
        details["dti_ratio"] = dti_ratio

        if dti_ratio > 0.6:
            return (
                False,
                f"Total debt obligations too high ({dti_ratio * 100:.1f}%). Maximum allowed: 60%",
                details,
            )

        # 14. Calculate adjusted interest rate based on CIBIL score
        adjusted_rate = interest_rate
        for score_threshold in sorted(
            LoanEvaluator.CIBIL_RATE_ADJUSTMENTS.keys(), reverse=True
        ):
            if cibil_score >= score_threshold:
                adjusted_rate = (
                    interest_rate
                    + LoanEvaluator.CIBIL_RATE_ADJUSTMENTS[score_threshold]
                )
                break
        details["adjusted_interest_rate"] = adjusted_rate

        # 15. Calculate processing fee (0.5% to 1.5% based on CIBIL)
        if cibil_score >= 750:
            processing_fee = principal * 0.005  # 0.5%
        else:
            processing_fee = principal * 0.01  # 1%
        details["processing_fee"] = processing_fee

        # 16. Recommend optimal tenure (max 60 months for better rates)
        recommended_tenure = min(tenure_months, 60)
        details["recommended_tenure"] = recommended_tenure

        # All checks passed - Determine approval message based on CIBIL score
        if cibil_score >= 800:
            return (
                True,
                f"Excellent credit profile - Loan approved at premium rate ({adjusted_rate:.2f}%)",
                details,
            )
        elif cibil_score >= 750:
            return (
                True,
                f"Good credit profile - Loan approved ({adjusted_rate:.2f}%)",
                details,
            )
        elif cibil_score >= 700:
            return (
                True,
                f"Fair credit profile - Loan approved with processing fee ({adjusted_rate:.2f}%)",
                details,
            )
        else:
            return True, "Loan approved", details

    @staticmethod
    def calculate_max_loan_amount(customer, salary_multiplier: float = 10.0) -> float:
        """
        Calculate maximum affordable loan based on income

        Args:
            customer: Customer object
            salary_multiplier: Max loan as multiple of annual income (default: 10x)

        Returns:
            Maximum loan amount
        """
        salary = getattr(customer, "salary", 0)
        employer_category = getattr(customer, "employer_category", "C")

        max_multiplier = LoanEvaluator.LOAN_TO_INCOME_RATIOS.get(employer_category, 5.0)
        return (salary * 12) * max_multiplier

    @staticmethod
    def calculate_suggested_interest_rate(
        cibil_score: int, base_rate: float = 9.5
    ) -> float:
        """
        Calculate interest rate based on CIBIL score

        Args:
            cibil_score: Customer's CIBIL score
            base_rate: Base interest rate

        Returns:
            Adjusted interest rate
        """
        for score_threshold in sorted(
            LoanEvaluator.CIBIL_RATE_ADJUSTMENTS.keys(), reverse=True
        ):
            if cibil_score >= score_threshold:
                return base_rate + LoanEvaluator.CIBIL_RATE_ADJUSTMENTS[score_threshold]
        return base_rate + 1.0  # Fallback for score < 700


# End of LoanEvaluator.py
