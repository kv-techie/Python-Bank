"""Fixed Deposit (FD) Module"""

import random
from datetime import datetime, timedelta
from typing import Tuple

from .BankClock import BankClock


class FixedDeposit:
    """Represents a Fixed Deposit account"""

    # Interest rates based on tenure (in months)
    INTEREST_RATES = {
        3: 6.5,  # 3 months - 6.5% p.a.
        6: 7.0,  # 6 months - 7.0% p.a.
        12: 7.5,  # 1 year - 7.5% p.a.
        24: 8.0,  # 2 years - 8.0% p.a.
        36: 8.5,  # 3 years - 8.5% p.a.
        60: 9.0,  # 5 years - 9.0% p.a.
    }

    SENIOR_CITIZEN_BONUS = 0.5  # Additional 0.5% for senior citizens
    PREMATURE_PENALTY = 1.0  # 1% penalty on premature withdrawal
    MIN_AMOUNT = 1000.0
    MAX_AMOUNT = 10000000.0

    def __init__(
        self,
        fd_number: str,
        account_number: str,
        principal_amount: float,
        tenure_months: int,
        interest_rate: float,
        is_senior_citizen: bool = False,
        start_date: datetime = None,
    ):
        self.fd_number = fd_number
        self.account_number = account_number
        self.principal_amount = principal_amount
        self.tenure_months = tenure_months
        self.interest_rate = interest_rate
        self.is_senior_citizen = is_senior_citizen
        self.start_date = start_date or BankClock.now()
        self.maturity_date = self._calculate_maturity_date()
        self.maturity_amount = self._calculate_maturity_amount()
        self.status = "Active"
        self.closed_date = None
        self.actual_payout = None

    def _calculate_maturity_date(self) -> datetime:
        """Calculate FD maturity date"""
        maturity = self.start_date + timedelta(days=self.tenure_months * 30)
        return maturity

    def _calculate_maturity_amount(self) -> float:
        """Calculate maturity amount with compound interest (quarterly)"""
        # A = P(1 + r/n)^(nt)
        # where n = 4 (quarterly compounding)
        rate = self.interest_rate / 100
        n = 4  # Quarterly compounding
        t = self.tenure_months / 12  # Years

        amount = self.principal_amount * ((1 + rate / n) ** (n * t))
        return round(amount, 2)

    def calculate_current_value(self) -> float:
        """Calculate current value of FD (if withdrawn today)"""
        current_date = BankClock.now()
        days_elapsed = (current_date - self.start_date).days

        if days_elapsed <= 0:
            return self.principal_amount

        months_elapsed = days_elapsed / 30

        # Calculate interest for actual period
        rate = self.interest_rate / 100
        n = 4  # Quarterly compounding
        t = months_elapsed / 12  # Years in decimal

        current_value = self.principal_amount * ((1 + rate / n) ** (n * t))
        return round(current_value, 2)

    def calculate_premature_withdrawal(self) -> Tuple[float, float, float]:
        """
        Calculate premature withdrawal amount
        Returns: (interest_earned, penalty, final_amount)
        """
        current_date = BankClock.now()
        days_elapsed = (current_date - self.start_date).days

        if days_elapsed <= 0:
            return 0.0, 0.0, self.principal_amount

        # Calculate current value
        current_value = self.calculate_current_value()
        interest_earned = current_value - self.principal_amount

        # Apply 1% penalty on total amount
        penalty = current_value * (self.PREMATURE_PENALTY / 100)
        final_amount = current_value - penalty

        return round(interest_earned, 2), round(penalty, 2), round(final_amount, 2)

    def close_prematurely(self) -> Tuple[float, str]:
        """Close FD before maturity"""
        if self.status != "Active":
            return 0.0, "FD is already closed or matured"

        interest, penalty, final_amount = self.calculate_premature_withdrawal()

        self.status = "Closed (Premature)"
        self.closed_date = BankClock.now()
        self.actual_payout = final_amount

        days_held = (self.closed_date - self.start_date).days

        message = f"""
FD closed prematurely!

FD Number: {self.fd_number}
Principal: Rs. {self.principal_amount:,.2f}
Days Held: {days_held} days (of {self.tenure_months * 30} days)
Interest Earned: Rs. {interest:,.2f}
Premature Penalty (1%): Rs. {penalty:,.2f}

Final Payout: Rs. {final_amount:,.2f}
"""
        return final_amount, message

    def mature(self) -> Tuple[float, str]:
        """Mature the FD"""
        if self.status != "Active":
            return 0.0, "FD is already closed or matured"

        self.status = "Matured"
        self.closed_date = BankClock.now()
        self.actual_payout = self.maturity_amount

        interest = self.maturity_amount - self.principal_amount

        message = f"""
🎉 FD Matured Successfully!

FD Number: {self.fd_number}
Principal: Rs. {self.principal_amount:,.2f}
Interest Rate: {self.interest_rate}% p.a.
Tenure: {self.tenure_months} months
Interest Earned: Rs. {interest:,.2f}

Maturity Amount: Rs. {self.maturity_amount:,.2f}
"""
        return self.maturity_amount, message

    def is_matured(self) -> bool:
        """Check if FD has matured"""
        return BankClock.now() >= self.maturity_date

    def get_days_to_maturity(self) -> int:
        """Get number of days until maturity"""
        if self.is_matured():
            return 0
        delta = self.maturity_date - BankClock.now()
        return delta.days

    def get_status_string(self) -> str:
        """Get formatted status string"""
        if self.status == "Matured":
            return "[SUCCESS] Matured"
        elif self.status.startswith("Closed"):
            return "[FAIL] Closed (Premature)"
        else:
            days_left = self.get_days_to_maturity()
            if days_left <= 0:
                return "[SUCCESS] Ready for Maturity"
            return f"Active ({days_left} days to maturity)"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "fd_number": self.fd_number,
            "account_number": self.account_number,
            "principal_amount": self.principal_amount,
            "tenure_months": self.tenure_months,
            "interest_rate": self.interest_rate,
            "is_senior_citizen": self.is_senior_citizen,
            "start_date": self.start_date.isoformat(),
            "maturity_date": self.maturity_date.isoformat(),
            "maturity_amount": self.maturity_amount,
            "status": self.status,
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
            "actual_payout": self.actual_payout,
        }

    @staticmethod
    def from_dict(data: dict) -> "FixedDeposit":
        """Create FD from dictionary"""
        fd = FixedDeposit(
            fd_number=data["fd_number"],
            account_number=data["account_number"],
            principal_amount=data["principal_amount"],
            tenure_months=data["tenure_months"],
            interest_rate=data["interest_rate"],
            is_senior_citizen=data.get("is_senior_citizen", False),
            start_date=datetime.fromisoformat(data["start_date"]),
        )
        fd.maturity_date = datetime.fromisoformat(data["maturity_date"])
        fd.maturity_amount = data["maturity_amount"]
        fd.status = data["status"]
        fd.closed_date = (
            datetime.fromisoformat(data["closed_date"])
            if data.get("closed_date")
            else None
        )
        fd.actual_payout = data.get("actual_payout")
        return fd

    @staticmethod
    def generate_fd_number() -> str:
        """Generate unique FD number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"FD{timestamp}{random_suffix}"

    @staticmethod
    def get_applicable_rate(
        tenure_months: int, is_senior_citizen: bool = False
    ) -> float:
        """Get applicable interest rate"""
        base_rate = FixedDeposit.INTEREST_RATES.get(tenure_months, 7.0)
        if is_senior_citizen:
            base_rate += FixedDeposit.SENIOR_CITIZEN_BONUS
        return base_rate

    def __str__(self) -> str:
        return (
            f"FD {self.fd_number}: Rs. {self.principal_amount:,.2f} @ {self.interest_rate}% "
            f"for {self.tenure_months} months (Status: {self.status})"
        )

    def __repr__(self) -> str:
        return f"FixedDeposit(fd_number='{self.fd_number}', amount={self.principal_amount}, status='{self.status}')"
