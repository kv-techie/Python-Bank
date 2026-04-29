from datetime import date
from typing import Optional


class Loan:
    # Prepayment penalty rates by loan type (as percentage of outstanding balance)
    PREPAYMENT_PENALTY_RATES = {
        "HOME": 2.0,  # 2% for home loans
        "VEHICLE": 1.5,  # 1.5% for car/auto loans
        "PERSONAL": 0.5,  # 0.5% for personal loans
        "EDUCATION": 0.0,  # No penalty for education loans
        "BUSINESS": 2.0,  # 2% for business loans
    }

    def __init__(
        self,
        loan_id: str,
        customer_id: str,
        principal: float,  # Changed from principal_amount
        interest_rate: float,  # Changed from annual_interest_rate
        tenure_months: int,
        status: str = "Active",
        emis_paid: int = 0,
        approval_reason: str = "",
        start_date: date = None,
        closure_date: date = None,
        nach_mandate_id: Optional[str] = None,  # NACH mandate for auto-deduction
        loan_type: str = "PERSONAL",  # Loan type: PERSONAL, HOME, CAR, EDUCATION
    ):
        self.loan_id = loan_id
        self.customer_id = customer_id
        self.principal = principal  # Changed
        self.interest_rate = interest_rate  # Changed
        self.tenure_months = tenure_months
        self.status = status
        self.emis_paid = emis_paid
        self.approval_reason = approval_reason
        self.start_date = start_date
        self.closure_date = closure_date
        self.nach_mandate_id = nach_mandate_id  # NACH mandate link
        self.loan_type = loan_type  # Loan type for tax deduction identification
        self.prepayment_penalty_charged = 0.0  # Track penalty charged

    def calculate_emi(self) -> float:
        """Calculate monthly EMI using reducing balance method"""
        P = self.principal  # Changed
        r = self.interest_rate / (12 * 100)  # Changed
        n = self.tenure_months
        if r == 0:
            return P / n
        emi = (P * r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(emi, 2)

    def get_remaining_balance(self) -> float:
        """Calculate remaining principal balance after EMIs paid"""
        if self.emis_paid == 0:
            return self.principal

        emi = self.calculate_emi()
        P = self.principal
        r = self.interest_rate / (12 * 100)
        n = self.emis_paid

        if r == 0:
            return P - (emi * n)

        # Remaining balance = P * (1 + r)^n - EMI * [((1 + r)^n - 1) / r]
        remaining = P * ((1 + r) ** n) - emi * (((1 + r) ** n - 1) / r)
        return max(0, round(remaining, 2))

    def calculate_prepayment_penalty(self) -> float:
        """Calculate prepayment penalty based on loan type and outstanding balance"""
        remaining = self.get_remaining_balance()
        
        # Get penalty rate for loan type (default to 0.5% if type not found)
        penalty_rate = self.PREPAYMENT_PENALTY_RATES.get(self.loan_type, 0.5)
        
        # Calculate penalty
        penalty = (remaining * penalty_rate) / 100
        return round(penalty, 2)

    def get_closure_details(self) -> dict:
        """Get complete closure details including penalty"""
        remaining_balance = self.get_remaining_balance()
        penalty = self.calculate_prepayment_penalty()
        total_payment = remaining_balance + penalty
        
        return {
            "remaining_balance": remaining_balance,
            "penalty_amount": penalty,
            "penalty_rate": self.PREPAYMENT_PENALTY_RATES.get(self.loan_type, 0.5),
            "total_payment": total_payment,
            "emis_paid": self.emis_paid,
            "total_emis": self.tenure_months,
        }

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "customer_id": self.customer_id,
            "principal": self.principal,  # Fixed
            "interest_rate": self.interest_rate,  # Fixed
            "tenure_months": self.tenure_months,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "status": self.status,
            "emis_paid": self.emis_paid,
            "approval_reason": self.approval_reason,
            "closure_date": self.closure_date.isoformat()
            if self.closure_date
            else None,
            "nach_mandate_id": self.nach_mandate_id,
            "loan_type": self.loan_type,
            "prepayment_penalty_charged": self.prepayment_penalty_charged,
        }

    @staticmethod
    def from_dict(data):
        loan = Loan(
            loan_id=data["loan_id"],
            customer_id=data["customer_id"],
            principal=data["principal"],  # Fixed
            interest_rate=data["interest_rate"],  # Fixed
            tenure_months=data["tenure_months"],
            status=data.get("status", "Active"),
            emis_paid=data.get("emis_paid", 0),
            start_date=date.fromisoformat(data["start_date"])
            if data.get("start_date")
            else None,
            approval_reason=data.get("approval_reason", ""),
            closure_date=date.fromisoformat(data["closure_date"])
            if data.get("closure_date")
            else None,
            nach_mandate_id=data.get("nach_mandate_id"),
            loan_type=data.get("loan_type", "PERSONAL"),
        )
        loan.prepayment_penalty_charged = data.get("prepayment_penalty_charged", 0.0)
        return loan
