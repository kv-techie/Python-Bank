from datetime import date


class Loan:
    def __init__(
        self,
        loan_id,
        customer_id,
        principal_amount,
        annual_interest_rate,
        tenure_months,
        status="Active",
        emis_paid=0,
        approval_reason="",
        start_date=None,
        closure_date=None,
    ):
        self.loan_id = loan_id
        self.customer_id = customer_id
        self.principal_amount = principal_amount
        self.annual_interest_rate = annual_interest_rate
        self.tenure_months = tenure_months
        self.status = status
        self.emis_paid = emis_paid
        self.approval_reason = approval_reason
        self.start_date = start_date
        self.closure_date = closure_date  # Add this field

    def calculate_emi(self):
        """Calculate monthly EMI using reducing balance method"""
        P = self.principal_amount
        r = self.annual_interest_rate / (12 * 100)
        n = self.tenure_months
        if r == 0:
            return P / n
        emi = (P * r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return round(emi, 2)

    def to_dict(self):
        return {
            "loan_id": self.loan_id,
            "customer_id": self.customer_id,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "tenure_months": self.tenure_months,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "status": self.status,
            "emis_paid": self.emis_paid,
            "approval_reason": self.approval_reason,  # <-- Added
        }

    @staticmethod
    def from_dict(data):
        l = Loan(
            loan_id=data["loan_id"],
            customer_id=data["customer_id"],
            principal=data["principal"],
            interest_rate=data["interest_rate"],
            tenure_months=data["tenure_months"],
            status=data.get("status", "Active"),
            emis_paid=data.get("emis_paid", 0),
            start_date=date.fromisoformat(data["start_date"])
            if data.get("start_date")
            else None,
            approval_reason=data.get("approval_reason"),  # <-- Added
        )
        return l
