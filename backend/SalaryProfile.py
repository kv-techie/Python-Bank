from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from dateutil.relativedelta import relativedelta


@dataclass
class SalaryProfile:
    """Represents an employee's salary profile with tax calculation"""

    gross_salary: float
    salary_day: int  # Day of month salary is credited (1-28)
    last_salary_date: Optional[date] = None

    def calculate_tax(self) -> float:
        """
        Calculates the monthly tax deduction (15% if annual income > ₹18,00,000)

        Returns:
            Monthly tax amount
        """
        annual_income = self.gross_salary * 12
        if annual_income > 1800000:  # ₹18,00,000 per year (₹1,50,000 per month)
            return round(self.gross_salary * 0.15, 2)  # 15% tax
        return 0.0

    def get_net_salary(self) -> float:
        """
        Calculates the net monthly salary after tax deduction

        Returns:
            Net salary (gross - tax)
        """
        return self.gross_salary - self.calculate_tax()

    def should_credit_today(self, today: date) -> bool:
        """
        Determines if salary should be credited today

        Args:
            today: The current date

        Returns:
            True if it's salary day and hasn't been processed this month
        """
        if today.day != self.salary_day:
            return False

        if self.last_salary_date is None:
            return True

        # Process if it's been at least a month since last salary
        next_salary_date = self.last_salary_date + relativedelta(months=1)
        return today >= next_salary_date

    # Alias for backward compatibility with earlier code
    def should_process_salary(self, today: date) -> bool:
        """Alias for should_credit_today"""
        return self.should_credit_today(today)

    def get_salary_summary(self) -> str:
        """
        Gets a formatted summary of the salary details

        Returns:
            Multi-line string with salary breakdown
        """
        annual_income = self.gross_salary * 12
        tax = self.calculate_tax()
        net_salary = self.get_net_salary()

        if tax > 0:
            tax_info = f"""   Monthly Tax (15%): ₹{tax:,.2f}
   Net Monthly Salary: ₹{net_salary:,.2f}
   Annual Tax: ₹{tax * 12:,.2f}"""
        else:
            tax_info = f"""   Net Monthly Salary: ₹{net_salary:,.2f}
   (No tax - annual income below ₹18,00,000)"""

        last_salary_info = ""
        if self.last_salary_date:
            last_salary_info = f"\n   Last Salary Date: {self.last_salary_date}"

        return f"""Salary Profile:
   Gross Monthly Salary: ₹{self.gross_salary:,.2f}
   Annual Income: ₹{annual_income:,.2f}
{tax_info}
   Salary Credit Day: {self.salary_day} of each month{last_salary_info}"""

    def get_annual_tax(self) -> float:
        """
        Calculates total annual tax

        Returns:
            Annual tax amount (monthly tax × 12)
        """
        return self.calculate_tax() * 12

    def get_annual_net_income(self) -> float:
        """
        Calculates total annual net income

        Returns:
            Annual net income (net salary × 12)
        """
        return self.get_net_salary() * 12

    def get_tax_rate(self) -> float:
        """
        Gets tax percentage (0% or 15%)

        Returns:
            Tax rate as percentage
        """
        return 15.0 if self.calculate_tax() > 0 else 0.0

    def copy(self, **changes):
        """
        Create a copy of this profile with specified changes

        Args:
            **changes: Fields to update in the copy

        Returns:
            New SalaryProfile instance with changes applied
        """
        import copy

        new_profile = copy.copy(self)
        for key, value in changes.items():
            setattr(new_profile, key, value)
        return new_profile

    def to_dict(self) -> dict:
        """
        Convert salary profile to dictionary for JSON serialization

        Returns:
            Dictionary representation of the profile
        """
        return {
            "grossSalary": self.gross_salary,
            "salaryDay": self.salary_day,
            "lastSalaryDate": self.last_salary_date.isoformat()
            if self.last_salary_date
            else None,
        }

    def credit_salary(self, account) -> tuple[bool, str]:
        """
        Credit the net salary to the given account, deducting tax if applicable.

        Args:
            account: Account object to credit salary into

        Returns:
            (success, message)
        """
        try:
            from BankClock import BankClock
            from DataStore import DataStore
            from Transaction import Transaction

            tax = self.calculate_tax()
            net = round(self.gross_salary - tax, 2)

            # Credit account
            account.balance += net

            # Create salary transaction
            txn = Transaction(
                type="SALARY",
                amount=net,
                resulting_balance=account.balance,
                metadata={"grossSalary": self.gross_salary, "tax": tax},
            )
            account.transactions.append(txn)

            # Log activity
            DataStore.append_activity(
                timestamp=txn.timestamp,
                username=account.username,
                account_number=account.account_number,
                action="SALARY",
                amount=net,
                resulting_balance=account.balance,
                txn_id=txn.id,
                metadata=f"gross={self.gross_salary:.2f};tax={tax:.2f}",
            )

            # Update last salary date
            self.last_salary_date = BankClock.today()

            # Round and clamp small float errors
            try:
                account.balance = round(float(account.balance), 2)
                if abs(account.balance) < 0.005:
                    account.balance = 0.0
            except Exception:
                pass

            return True, f"Salary credited: Rs. {net:.2f} INR"
        except Exception as e:
            return False, f"Failed to credit salary: {e}"

    @staticmethod
    def from_dict(data: dict) -> "SalaryProfile":
        """
        Create a SalaryProfile from dictionary

        Args:
            data: Dictionary containing profile data

        Returns:
            SalaryProfile instance
        """
        last_salary_date = None
        if data.get("lastSalaryDate"):
            last_salary_date = date.fromisoformat(data["lastSalaryDate"])

        return SalaryProfile(
            gross_salary=data["grossSalary"],
            salary_day=data["salaryDay"],
            last_salary_date=last_salary_date,
        )

    def __repr__(self) -> str:
        """String representation of the profile"""
        return f"SalaryProfile(gross=₹{self.gross_salary:,.2f}, day={self.salary_day})"

    def __str__(self) -> str:
        """User-friendly string representation"""
        return f"Salary: ₹{self.gross_salary:,.2f}/month (Day {self.salary_day})"


class SalaryProfileFactory:
    """Factory for creating and validating salary profiles"""

    # Common salary brackets in India (in ₹ per month)
    COMMON_SALARY_RANGES: List[Tuple[str, float, float]] = [
        ("Entry Level", 15000.0, 30000.0),
        ("Junior Professional", 30000.0, 50000.0),
        ("Mid-Level Professional", 50000.0, 100000.0),
        ("Senior Professional", 100000.0, 200000.0),
        ("Manager Level", 150000.0, 300000.0),
        ("Senior Manager", 200000.0, 500000.0),
        ("Executive Level", 500000.0, 1000000.0),
    ]

    @staticmethod
    def create(
        gross_salary: float, salary_day: int
    ) -> Tuple[bool, str, Optional[SalaryProfile]]:
        """
        Creates a salary profile with validation

        Args:
            gross_salary: Monthly gross salary
            salary_day: Day of month (1-28)

        Returns:
            Tuple of (success: bool, message: str, profile: Optional[SalaryProfile])
        """
        if gross_salary <= 0:
            return (False, "Gross salary must be positive", None)

        if salary_day < 1 or salary_day > 28:
            return (False, "Salary day must be between 1 and 28", None)

        profile = SalaryProfile(
            gross_salary=gross_salary, salary_day=salary_day, last_salary_date=None
        )

        bracket = SalaryProfileFactory.get_salary_bracket(gross_salary)
        message = f"Salary profile created successfully. Bracket: {bracket}"

        return (True, message, profile)

    @staticmethod
    def get_salary_bracket(monthly_salary: float) -> str:
        """
        Gets salary bracket name for a given monthly salary

        Args:
            monthly_salary: The monthly salary amount

        Returns:
            Salary bracket name
        """
        for bracket_name, min_sal, max_sal in SalaryProfileFactory.COMMON_SALARY_RANGES:
            if min_sal <= monthly_salary < max_sal:
                return bracket_name

        if monthly_salary < 15000:
            return "Below Entry Level"
        else:
            return "Above Executive Level"

    @staticmethod
    def show_salary_brackets():
        """Display all salary brackets"""
        print("\n" + "=" * 70)
        print("COMMON SALARY BRACKETS IN INDIA")
        print("=" * 70)
        print(f"{'Bracket':<25} {'Range':>30} {'Tax Status':<15}")
        print("-" * 70)

        for bracket_name, min_sal, max_sal in SalaryProfileFactory.COMMON_SALARY_RANGES:
            range_str = f"₹{min_sal:>8,.2f} - ₹{max_sal:>10,.2f}"

            # Check tax applicability
            annual_min = min_sal * 12
            annual_max = max_sal * 12

            if annual_max <= 1800000:
                tax_status = "Tax-Free"
            elif annual_min >= 1800000:
                tax_status = "15% Tax"
            else:
                tax_status = "Mixed"

            print(f"{bracket_name:<25} {range_str:>30} {tax_status:<15}")

        print("-" * 70)
        print(
            f"{'Tax Threshold':<25} {'₹1,50,000/month (₹18,00,000/year)':>30} {'15% above':<15}"
        )
        print("=" * 70)

    @staticmethod
    def calculate_take_home(gross_salary: float) -> Tuple[float, float, float, float]:
        """
        Calculate take-home salary details

        Args:
            gross_salary: Monthly gross salary

        Returns:
            Tuple of (gross_salary, tax, net_salary, annual_net)
        """
        annual_income = gross_salary * 12

        if annual_income > 1800000:
            monthly_tax = gross_salary * 0.15
        else:
            monthly_tax = 0.0

        net_salary = gross_salary - monthly_tax
        annual_net = net_salary * 12

        return (gross_salary, monthly_tax, net_salary, annual_net)

    @staticmethod
    def show_salary_breakdown(gross_salary: float):
        """
        Display detailed salary breakdown

        Args:
            gross_salary: Monthly gross salary
        """
        gross, tax, net, annual_net = SalaryProfileFactory.calculate_take_home(
            gross_salary
        )
        annual_gross = gross * 12
        annual_tax = tax * 12
        bracket = SalaryProfileFactory.get_salary_bracket(gross_salary)
        tax_rate = 15.0 if tax > 0 else 0.0

        print("\n" + "=" * 60)
        print("SALARY BREAKDOWN")
        print("=" * 60)
        print(f"Salary Bracket: {bracket}")
        print(f"Tax Rate: {tax_rate}%")
        print("-" * 60)
        print(f"{'Component':<30} {'Monthly':>12} {'Annual':>15}")
        print("-" * 60)
        print(f"{'Gross Salary':<30} ₹{gross:>10,.2f} ₹{annual_gross:>13,.2f}")

        if tax > 0:
            print(f"{'Tax Deduction (15%)':<30} ₹{tax:>10,.2f} ₹{annual_tax:>13,.2f}")
            print("-" * 60)
            print(
                f"{'Net Salary (Take Home)':<30} ₹{net:>10,.2f} ₹{annual_net:>13,.2f}"
            )
        else:
            print(f"{'Tax Deduction':<30} ₹{0.0:>10,.2f} ₹{0.0:>13,.2f}")
            print("-" * 60)
            print(
                f"{'Net Salary (Take Home)':<30} ₹{net:>10,.2f} ₹{annual_net:>13,.2f}"
            )
            print("\n(Income below ₹18,00,000/year - Tax Free)")

        print("=" * 60)


# Convenience aliases for backward compatibility
SalaryProfile.create = SalaryProfileFactory.create
SalaryProfile.get_salary_bracket = SalaryProfileFactory.get_salary_bracket
SalaryProfile.COMMON_SALARY_RANGES = SalaryProfileFactory.COMMON_SALARY_RANGES
