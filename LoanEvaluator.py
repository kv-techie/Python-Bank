# LoanEvaluator.py
from datetime import date

class LoanEvaluator:
    @staticmethod
    def evaluate(customer, principal, tenure, interest, bank):
        """
        Run all major approval checks according to real bank criteria.
        Returns (approved: bool, message: str).
        """
        # 1. CIBIL score
        if not customer.cibil_score or customer.cibil_score < 700:
            return False, "Low CIBIL score"
        # 2. Salary
        if not customer.salary or customer.salary < 20000:
            return False, "Salary below minimum requirement"
        # 3. Employment - 1 year with current employer
        if not customer.job_start_date:
            return False, "Missing job starting date"
        try:
            job_days = (date.today() - date.fromisoformat(customer.job_start_date)).days
        except Exception:
            return False, "Invalid job start date"
        if job_days < 365:
            return False, "Less than 1 year in current employment"
        # 4. DTI (existing EMIs / monthly salary)
        if customer.get_DTI(bank) > 0.5:
            return False, "High debt-to-income ratio"
        # 5. Age - must be 21-60
        if not (18 <= customer.age() <= 60):
            return False, "Age not in eligible range"
        # 6. KYC must be complete
        if not getattr(customer, "kyc_completed", False):
            return False, "KYC incomplete"
        # 7. Employer category A or B only (not C)
        if customer.employer_category is None or customer.employer_category not in {"A", "B"}:
            return False, "Employer category not supported"
        # 8. City / Location check
        allowed_cities = {"Bengaluru", "Mumbai", "Delhi"}
        if customer.city and customer.city not in allowed_cities:
            return False, f"City not eligible for this loan (only {', '.join(allowed_cities)})"
        # 9. Principal/tenure business rules (optional)
        if principal < 10000 or tenure < 6:
            return False, "Minimum loan Rs. 10,000 and tenure 6 months"
        return True, "Approved"
