"""Recurring Deposit (RD) Module with Autopay Support"""

import random
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from Account import Account
from BankClock import BankClock


class RecurringDeposit:
    """Represents a Recurring Deposit account with autopay functionality"""

    # Interest rates based on tenure (in months)
    INTEREST_RATES = {
        12: 7.25,  # 1 year - 7.25% p.a.
        24: 7.75,  # 2 years - 7.75% p.a.
        36: 8.25,  # 3 years - 8.25% p.a.
        60: 8.75,  # 5 years - 8.75% p.a.
    }

    SENIOR_CITIZEN_BONUS = 0.5
    PREMATURE_PENALTY = 1.0
    LATE_PAYMENT_PENALTY = 50.0  # Rs. 50 per missed installment
    MIN_MONTHLY_AMOUNT = 500.0
    MAX_MONTHLY_AMOUNT = 100000.0

    def __init__(
        self,
        rd_number: str,
        account_number: str,
        monthly_installment: float,
        tenure_months: int,
        interest_rate: float,
        is_senior_citizen: bool = False,
        start_date: datetime = None,
        autopay_enabled: bool = False,
        autopay_day: int = 1,
    ):
        self.rd_number = rd_number
        self.account_number = account_number
        self.monthly_installment = monthly_installment
        self.tenure_months = tenure_months
        self.interest_rate = interest_rate
        self.is_senior_citizen = is_senior_citizen
        self.start_date = start_date or BankClock.now()
        self.maturity_date = self._calculate_maturity_date()
        self.installments_paid = 0
        self.total_deposited = 0.0
        self.status = "Active"
        self.payment_history: List[dict] = []
        self.missed_payments = 0
        self.penalties_charged = 0.0
        self.closed_date = None
        self.actual_payout = None

        # Autopay features
        self.autopay_enabled = autopay_enabled
        self.autopay_day = autopay_day  # Day of month (1-28)
        self.next_autopay_date = (
            self._calculate_next_autopay_date() if autopay_enabled else None
        )
        self.autopay_failures = 0
        self.last_autopay_attempt = None

    def _calculate_maturity_date(self) -> datetime:
        """Calculate RD maturity date"""
        return self.start_date + timedelta(days=self.tenure_months * 30)

    def _calculate_next_autopay_date(self) -> Optional[datetime]:
        """Calculate the next autopay date"""
        if not self.autopay_enabled:
            return None

        current_date = BankClock.now()

        # If we haven't paid any installments yet, start from start_date
        if self.installments_paid == 0:
            next_date = self.start_date.replace(day=self.autopay_day)
            if next_date < current_date:
                # Move to next month
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
            return next_date

        # Calculate next payment date based on last payment
        if self.payment_history:
            last_payment_date = datetime.fromisoformat(self.payment_history[-1]["date"])
            next_date = last_payment_date.replace(day=self.autopay_day)

            # Move to next month
            if next_date.month == 12:
                next_date = next_date.replace(year=next_date.year + 1, month=1)
            else:
                next_date = next_date.replace(month=next_date.month + 1)

            return next_date

        return current_date.replace(day=self.autopay_day)

    def enable_autopay(self, autopay_day: int = 1) -> Tuple[bool, str]:
        """Enable autopay for RD"""
        if autopay_day < 1 or autopay_day > 28:
            return False, "Autopay day must be between 1 and 28"

        if self.status != "Active":
            return False, "RD is not active"

        self.autopay_enabled = True
        self.autopay_day = autopay_day
        self.next_autopay_date = self._calculate_next_autopay_date()

        return (
            True,
            f"Autopay enabled! Amount Rs. {self.monthly_installment:,.2f} will be auto-debited on day {autopay_day} of each month",
        )

    def disable_autopay(self) -> Tuple[bool, str]:
        """Disable autopay for RD"""
        if not self.autopay_enabled:
            return False, "Autopay is not enabled"

        self.autopay_enabled = False
        self.next_autopay_date = None

        return (
            True,
            "Autopay disabled successfully. You will need to pay installments manually.",
        )

    def process_autopay(self, account: "Account") -> Tuple[bool, str]:
        """
        Process autopay - called by Bank's automated system
        Returns: (success, message)
        """
        if not self.autopay_enabled:
            return False, "Autopay is not enabled"

        if self.status != "Active":
            return False, "RD is not active"

        today = BankClock.today()  # ✅ Get date object like RecurringBill does

        # Check if it's time for autopay
        if self.next_autopay_date:
            # Convert next_autopay_date to date if it's datetime
            if isinstance(self.next_autopay_date, datetime):
                next_autopay_as_date = self.next_autopay_date.date()
            else:
                next_autopay_as_date = self.next_autopay_date

            if today >= next_autopay_as_date:
                self.last_autopay_attempt = BankClock.now()  # Timestamp uses now()

                # Check if account has sufficient balance
                min_balance = account._min_operational_balance
                if account.balance - self.monthly_installment < min_balance:
                    self.autopay_failures += 1
                    self.missed_payments += 1

                    message = f"""
❌ Autopay Failed - Insufficient Balance
RD: {self.rd_number}
Required: Rs. {self.monthly_installment:,.2f}
Available: Rs. {account.balance:,.2f}
Minimum Balance Required: Rs. {min_balance:,.2f}
Missed Payments: {self.missed_payments}
Penalty: Rs. {self.LATE_PAYMENT_PENALTY} will be charged at maturity
"""
                    # Calculate next autopay date
                    self.next_autopay_date = self._calculate_next_autopay_date()

                    return False, message

                # Deduct from account
                account.balance -= self.monthly_installment

                # Record payment
                payment = {
                    "date": BankClock.now().isoformat(),
                    "amount": self.monthly_installment,
                    "installment_number": self.installments_paid + 1,
                    "method": "Autopay",
                }
                self.payment_history.append(payment)
                self.installments_paid += 1
                self.total_deposited += self.monthly_installment

                # Create transaction in account
                from Transaction import Transaction

                txn = Transaction(
                    type="RD_AUTOPAY",
                    amount=-self.monthly_installment,
                    resulting_balance=account.balance,
                    metadata={
                        "rd_number": self.rd_number,
                        "installment_number": self.installments_paid,
                        "total_installments": self.tenure_months,
                    },
                )
                account.transactions.append(txn)

                # Check if completed
                if self.installments_paid >= self.tenure_months:
                    self.status = "Completed"
                    maturity_amount = self.calculate_maturity_amount()
                    message = f"""
✅ RD Autopay Successful - RD COMPLETED!
RD: {self.rd_number}
Installment: {self.installments_paid}/{self.tenure_months}
Amount: Rs. {self.monthly_installment:,.2f}
New Balance: Rs. {account.balance:,.2f}

🎉 All installments paid! Your RD is now ready for maturity.
Expected Maturity Amount: Rs. {maturity_amount:,.2f}
You can now mature your RD to receive the funds.
"""
                else:
                    # Calculate next autopay date
                    self.next_autopay_date = self._calculate_next_autopay_date()

                    message = f"""
✅ RD Autopay Successful
RD: {self.rd_number}
Installment: {self.installments_paid}/{self.tenure_months}
Amount: Rs. {self.monthly_installment:,.2f}
New Balance: Rs. {account.balance:,.2f}
Next Autopay: {self.next_autopay_date.strftime("%d-%m-%Y")}
"""

                return True, message

        return False, "Autopay not due yet"

    def calculate_maturity_amount(self) -> float:
        """
        Calculate RD maturity amount using formula:
        M = P × n + [P × n × (n + 1) × r] / 2400
        where P = monthly installment, n = number of months, r = interest rate
        """
        P = self.monthly_installment
        n = self.tenure_months
        r = self.interest_rate

        # Principal amount
        principal = P * n

        # Interest calculation
        interest = (P * n * (n + 1) * r) / 2400

        maturity_amount = principal + interest

        return round(maturity_amount, 2)

    def pay_installment_manual(self, account: "Account") -> Tuple[bool, str]:
        """Pay monthly installment manually"""
        if self.status != "Active":
            return False, "RD is not active"

        if self.installments_paid >= self.tenure_months:
            return False, "All installments already paid"

        # Check if account has sufficient balance
        min_balance = account._min_operational_balance
        if account.balance - self.monthly_installment < min_balance:
            return (
                False,
                f"Insufficient balance. Required: Rs. {self.monthly_installment:,.2f} + Rs. {min_balance:,.2f} minimum balance",
            )

        # Deduct from account
        account.balance -= self.monthly_installment

        # Record payment
        payment = {
            "date": BankClock.now().isoformat(),
            "amount": self.monthly_installment,
            "installment_number": self.installments_paid + 1,
            "method": "Manual",
        }
        self.payment_history.append(payment)
        self.installments_paid += 1
        self.total_deposited += self.monthly_installment

        # Create transaction in account
        from Transaction import Transaction

        txn = Transaction(
            type="RD_PAYMENT",
            amount=-self.monthly_installment,
            resulting_balance=account.balance,
            metadata={
                "rd_number": self.rd_number,
                "installment_number": self.installments_paid,
                "total_installments": self.tenure_months,
            },
        )
        account.transactions.append(txn)

        # Check if completed
        if self.installments_paid >= self.tenure_months:
            self.status = "Completed"
            return (
                True,
                f"Installment #{self.installments_paid} paid successfully. RD is now COMPLETED and ready for maturity!",
            )

        return (
            True,
            f"Installment #{self.installments_paid}/{self.tenure_months} paid successfully",
        )

    def calculate_current_value(self) -> float:
        """Calculate current value of RD with interest on paid installments"""
        if self.installments_paid == 0:
            return 0.0

        # Simple interest calculation for current value
        P = self.monthly_installment
        n = self.installments_paid
        r = self.interest_rate

        principal = P * n
        interest = (P * n * (n + 1) * r) / 2400

        current_value = principal + interest

        return round(current_value, 2)

    def calculate_premature_withdrawal(self) -> Tuple[float, float, float]:
        """
        Calculate premature withdrawal amount
        Returns: (current_value, total_penalty, final_amount)
        """
        if self.installments_paid == 0:
            return 0.0, 0.0, 0.0

        current_value = self.calculate_current_value()

        # Calculate penalties
        # 1% premature withdrawal penalty
        premature_penalty = current_value * (self.PREMATURE_PENALTY / 100)

        # Late payment penalties
        late_penalties = self.missed_payments * self.LATE_PAYMENT_PENALTY

        total_penalty = premature_penalty + late_penalties
        final_amount = current_value - total_penalty

        return round(current_value, 2), round(total_penalty, 2), round(final_amount, 2)

    def close_prematurely(self) -> Tuple[float, str]:
        """Close RD before maturity"""
        if self.status not in ["Active", "Completed"]:
            return 0.0, "RD is already closed"

        if self.installments_paid == 0:
            return 0.0, "No installments paid yet. Cannot close RD."

        current_value, penalty, final_amount = self.calculate_premature_withdrawal()

        self.status = "Closed (Premature)"
        self.closed_date = BankClock.now()
        self.actual_payout = final_amount
        self.autopay_enabled = False  # Disable autopay on closure

        interest_earned = current_value - self.total_deposited

        message = f"""
RD closed prematurely!

Installments Paid: {self.installments_paid}/{self.tenure_months}
Total Deposited: Rs. {self.total_deposited:,.2f}
Interest Earned: Rs. {interest_earned:,.2f}
Current Value: Rs. {current_value:,.2f}

Penalties:
  Premature Penalty (1%): Rs. {current_value * 0.01:,.2f}
  Late Payment Penalty: Rs. {self.missed_payments * self.LATE_PAYMENT_PENALTY:,.2f}
  Total Penalty: Rs. {penalty:,.2f}

Final Payout: Rs. {final_amount:,.2f}
"""
        return final_amount, message

    def mature(self) -> Tuple[float, str]:
        """Mature the RD"""
        if self.status != "Completed":
            return (
                0.0,
                f"RD is not completed yet. Installments paid: {self.installments_paid}/{self.tenure_months}",
            )

        maturity_amount = self.calculate_maturity_amount()
        late_penalties = self.missed_payments * self.LATE_PAYMENT_PENALTY
        final_amount = maturity_amount - late_penalties

        self.status = "Matured"
        self.closed_date = BankClock.now()
        self.actual_payout = final_amount
        self.autopay_enabled = False  # Disable autopay on maturity

        interest_earned = maturity_amount - self.total_deposited

        message = f"""
🎉 RD Matured Successfully!

Total Deposited: Rs. {self.total_deposited:,.2f}
Interest Earned: Rs. {interest_earned:,.2f}
Maturity Amount: Rs. {maturity_amount:,.2f}
Late Payment Penalties: Rs. {late_penalties:,.2f}

Final Payout: Rs. {final_amount:,.2f}
"""
        return final_amount, message

    def is_matured(self) -> bool:
        """Check if RD has matured (all installments paid)"""
        return self.installments_paid >= self.tenure_months

    def get_payment_status(self) -> str:
        """Get payment status string"""
        if self.status == "Matured":
            return "✅ Matured"
        elif self.status == "Completed":
            return "✅ Completed (Ready for Maturity)"
        elif self.status.startswith("Closed"):
            return "❌ Closed"
        else:
            autopay_info = " (Autopay)" if self.autopay_enabled else ""
            return f"Active - {self.installments_paid}/{self.tenure_months} paid{autopay_info}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "rd_number": self.rd_number,
            "account_number": self.account_number,
            "monthly_installment": self.monthly_installment,
            "tenure_months": self.tenure_months,
            "interest_rate": self.interest_rate,
            "is_senior_citizen": self.is_senior_citizen,
            "start_date": self.start_date.isoformat(),
            "maturity_date": self.maturity_date.isoformat(),
            "installments_paid": self.installments_paid,
            "total_deposited": self.total_deposited,
            "status": self.status,
            "payment_history": self.payment_history,
            "missed_payments": self.missed_payments,
            "penalties_charged": self.penalties_charged,
            "closed_date": self.closed_date.isoformat() if self.closed_date else None,
            "actual_payout": self.actual_payout,
            # Autopay fields
            "autopay_enabled": self.autopay_enabled,
            "autopay_day": self.autopay_day,
            "next_autopay_date": (
                self.next_autopay_date.isoformat() if self.next_autopay_date else None
            ),
            "autopay_failures": self.autopay_failures,
            "last_autopay_attempt": (
                self.last_autopay_attempt.isoformat()
                if self.last_autopay_attempt
                else None
            ),
        }

    @staticmethod
    def from_dict(data: dict) -> "RecurringDeposit":
        """Create RD from dictionary"""
        rd = RecurringDeposit(
            rd_number=data["rd_number"],
            account_number=data["account_number"],
            monthly_installment=data["monthly_installment"],
            tenure_months=data["tenure_months"],
            interest_rate=data["interest_rate"],
            is_senior_citizen=data.get("is_senior_citizen", False),
            start_date=datetime.fromisoformat(data["start_date"]),
            autopay_enabled=data.get("autopay_enabled", False),
            autopay_day=data.get("autopay_day", 1),
        )
        rd.maturity_date = datetime.fromisoformat(data["maturity_date"])
        rd.installments_paid = data["installments_paid"]
        rd.total_deposited = data["total_deposited"]
        rd.status = data["status"]
        rd.payment_history = data.get("payment_history", [])
        rd.missed_payments = data.get("missed_payments", 0)
        rd.penalties_charged = data.get("penalties_charged", 0.0)
        rd.closed_date = (
            datetime.fromisoformat(data["closed_date"])
            if data.get("closed_date")
            else None
        )
        rd.actual_payout = data.get("actual_payout")
        rd.next_autopay_date = (
            datetime.fromisoformat(data["next_autopay_date"])
            if data.get("next_autopay_date")
            else None
        )
        rd.autopay_failures = data.get("autopay_failures", 0)
        rd.last_autopay_attempt = (
            datetime.fromisoformat(data["last_autopay_attempt"])
            if data.get("last_autopay_attempt")
            else None
        )
        return rd

    @staticmethod
    def generate_rd_number() -> str:
        """Generate unique RD number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"RD{timestamp}{random_suffix}"

    @staticmethod
    def get_applicable_rate(
        tenure_months: int, is_senior_citizen: bool = False
    ) -> float:
        """Get applicable interest rate"""
        base_rate = RecurringDeposit.INTEREST_RATES.get(tenure_months, 7.25)
        if is_senior_citizen:
            base_rate += RecurringDeposit.SENIOR_CITIZEN_BONUS
        return base_rate

    def __str__(self) -> str:
        autopay_status = "✓ Autopay" if self.autopay_enabled else "Manual"
        return (
            f"RD {self.rd_number}: Rs. {self.monthly_installment:,.2f}/month × {self.tenure_months} months "
            f"@ {self.interest_rate}% (Paid: {self.installments_paid}/{self.tenure_months}) [{autopay_status}]"
        )

    def __repr__(self) -> str:
        return f"RecurringDeposit(rd_number='{self.rd_number}', amount={self.monthly_installment}, status='{self.status}')"
