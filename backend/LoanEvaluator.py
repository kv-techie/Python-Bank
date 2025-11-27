# LoanEvaluator.py
from datetime import date


class LoanEvaluator:
    """Evaluates loan applications based on customer profile and CIBIL score"""

    @staticmethod
    def evaluate(
        customer, principal: float, tenure_months: int, interest_rate: float, bank
    ) -> tuple[bool, str]:
        """
        Run all major approval checks according to real bank criteria.
        Returns (approved: bool, reason: str).
        """

        # 1. CIBIL Score Check (Minimum 700)
        cibil_score = getattr(customer, "cibil_score", 0)
        if not cibil_score or cibil_score < 700:
            return False, f"CIBIL score too low ({cibil_score}). Minimum required: 700"

        # 2. Salary Check (Minimum Rs. 20,000)
        salary = getattr(customer, "salary", 0)
        if not salary or salary < 20000:
            return False, "Salary below minimum requirement (Rs. 20,000)"

        # 3. Employment Check - 1 year with current employer
        job_start_date = getattr(customer, "job_start_date", None)
        if not job_start_date:
            return False, "Missing job starting date"

        try:
            job_days = (date.today() - date.fromisoformat(job_start_date)).days
        except Exception:
            return False, "Invalid job start date"

        if job_days < 365:
            return False, "Less than 1 year in current employment"

        # 4. DTI (Debt-to-Income) Check
        if customer.get_DTI(bank) > 0.5:
            return False, "High debt-to-income ratio (exceeds 50%)"

        # 5. Age Check - must be 18-60
        customer_age = customer.calculate_age()
        if not (18 <= customer_age <= 60):
            return (
                False,
                f"Age not in eligible range (18-60). Current age: {customer_age}",
            )

        # 6. KYC Check
        kyc_completed = getattr(customer, "kyc_completed", False)
        if not kyc_completed:
            return False, "KYC verification pending"

        # 7. Employer Category Check (A or B only, not C)
        employer_category = getattr(customer, "employer_category", None)
        if employer_category is None or employer_category not in {"A", "B"}:
            return (
                False,
                "Employer category not supported (Only A or B category employers)",
            )

        # 8. City / Location Check
        allowed_cities = {"Bengaluru", "Mumbai", "Delhi"}
        customer_city = getattr(customer, "city", None)
        if customer_city and customer_city not in allowed_cities:
            return (
                False,
                f"City not eligible for this loan (Only {', '.join(allowed_cities)})",
            )

        # 9. Principal and Tenure Business Rules
        if principal < 10000:
            return False, "Minimum loan amount is Rs. 10,000"
        if tenure_months < 6:
            return False, "Minimum loan tenure is 6 months"

        # 10. EMI Affordability Check
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
            )

        # 11. Total Debt Obligations Check
        existing_loans = bank.get_loans_for_customer(customer.customer_id)
        total_emi = sum(
            loan.calculate_emi() for loan in existing_loans if loan.status == "Active"
        )

        total_obligations = total_emi + emi
        dti_ratio = total_obligations / salary

        if dti_ratio > 0.6:
            return (
                False,
                f"Total debt obligations too high ({dti_ratio * 100:.1f}%). Maximum allowed: 60%",
            )

        # All checks passed - Determine approval message based on CIBIL score
        if cibil_score >= 750:
            return True, "Excellent credit profile - Loan approved at best rate"
        elif cibil_score >= 700:
            return True, "Good credit profile - Loan approved"
        else:
            return True, "Loan approved"


# End of LoanEvaluator.py
