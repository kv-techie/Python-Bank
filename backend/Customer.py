import os
import random
from datetime import date
from typing import List, Optional

from BankClock import BankClock
from Beneficiary import BeneficiaryManager
from DataStore import DataStore
from PasswordRecovery import CustomerPasswordRecovery


class Customer(CustomerPasswordRecovery):
    """Customer class for managing customer information and linked accounts"""

    CUSTOMER_ID_PREFIX = "CUST"
    _used_customer_ids = set()
    _used_ids_file = "data/customer_ids.txt"

    def __init__(
        self,
        customer_id: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        phone_number: str,
        email: str,
        account_numbers: Optional[List[str]] = None,
        failed_attempts: int = 0,
        locked: bool = False,
        # --- Loan/Employer Info Fields (optional) ---
        cibil_score: Optional[int] = None,
        salary: Optional[float] = None,
        employer_name: Optional[str] = None,
        employer_type: Optional[str] = None,
        job_start_date: Optional[str] = None,  # "YYYY-MM-DD"
        employer_category: Optional[str] = None,
        city: Optional[str] = None,
        kyc_completed: bool = False,
        # --- New fields for credit card limit assignment ---
        has_salary_account: bool = False,
        credit_cards: Optional[List] = None,  # hold list of CreditCard objects or dicts
        pan: Optional[str] = None,  # Permanent Account Number for tax filing
    ):
        CustomerPasswordRecovery.__init__(self)

        self.customer_id = customer_id
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.gender = gender
        self.phone_number = phone_number
        self.email = email
        self._account_numbers = account_numbers if account_numbers is not None else []
        self.failed_attempts = failed_attempts
        self.locked = locked

        # Loan/employment related
        self.cibil_score = cibil_score
        self.salary = salary
        self.employer_name = employer_name
        self.employer_type = employer_type
        self.job_start_date = job_start_date
        self.employer_category = employer_category
        self.city = city
        self.kyc_completed = kyc_completed

        # New fields
        self.has_salary_account = has_salary_account
        self.credit_cards = credit_cards if credit_cards is not None else []
        self.pan = pan  # PAN for tax filing

        # Bounce tracking for CIBIL impact
        self.bounce_count = 0  # Total cheque bounces
        self.bounce_history = []  # List of bounce events
        self.last_bounce_date: Optional[str] = None  # Most recent bounce date

        # Tax planning fields
        self.tax_deductions = []  # List of TaxExemption objects
        self.tax_regime = "OLD_REGIME"  # OLD_REGIME or NEW_REGIME

        # Beneficiary management
        self.beneficiary_manager = BeneficiaryManager()

    def get_account_numbers(self) -> List[str]:
        return self._account_numbers.copy()

    def add_account(self, account_number: str):
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)
            ts = BankClock.get_formatted_datetime()
            DataStore.append_activity(
                timestamp=ts,
                username=self.username,
                account_number=account_number,
                action="ACCOUNT_LINKED_TO_CUSTOMER",
                amount=None,
                resulting_balance=None,
                metadata=f"customerId={self.customer_id}",
            )

    def remove_account(self, account_number: str):
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)
            ts = BankClock.get_formatted_datetime()
            DataStore.append_activity(
                timestamp=ts,
                username=self.username,
                account_number=account_number,
                action="ACCOUNT_UNLINKED_FROM_CUSTOMER",
                amount=None,
                resulting_balance=None,
                metadata=f"customerId={self.customer_id}",
            )

    @property
    def account_count(self) -> int:
        return len(self._account_numbers)

    def owns_account(self, account_number: str) -> bool:
        return account_number in self._account_numbers

    def calculate_age(self) -> int:
        dob_date = (
            date.fromisoformat(self.dob) if isinstance(self.dob, str) else self.dob
        )
        today = date.today()
        return (
            today.year
            - dob_date.year
            - ((today.month, today.day) < (dob_date.month, dob_date.day))
        )

    def get_DTI(self, bank) -> float:
        """
        Calculate Debt-to-Income ratio (total EMIs / monthly salary).
        Only considers active loans.
        """
        emis = sum(
            loan.calculate_emi()
            for loan in bank.get_loans_for_customer(self.customer_id)
            if getattr(loan, "status", "Active") == "Active"
        )
        return emis / self.salary if self.salary and self.salary > 0 else 0.0

    # ===== Bounce & CIBIL Management =====

    def record_bounce(self, cheque_number: str, account_number: str) -> None:
        """
        Record a cheque bounce for this customer

        Args:
            cheque_number: The cheque number that bounced
            account_number: Account from which cheque was issued
        """
        from BankClock import BankClock

        bounce_event = {
            "date": BankClock.get_formatted_datetime(),
            "cheque_number": cheque_number,
            "account_number": account_number,
        }

        self.bounce_history.append(bounce_event)
        self.bounce_count += 1
        self.last_bounce_date = bounce_event["date"]

    def get_bounce_count(self) -> int:
        """Get total number of bounces for this customer"""
        return self.bounce_count

    def get_cibil_reduction(self) -> int:
        """
        Calculate CIBIL score reduction based on bounce count

        Reduction formula (progressive penalty):
        - 1st bounce: -50 points
        - 2nd bounce: -75 points each
        - 3rd+ bounce: -100 points each

        Returns:
            Total CIBIL reduction amount
        """
        if self.bounce_count == 0:
            return 0
        elif self.bounce_count == 1:
            return 50
        elif self.bounce_count == 2:
            return 50 + 75  # 125 total
        else:
            # 3+ bounces: 50 + 75 + (100 * additional bounces)
            return 50 + 75 + (100 * (self.bounce_count - 2))

    def get_current_cibil(self) -> Optional[int]:
        """
        Get actual CIBIL score after bounce reductions

        Returns:
            Adjusted CIBIL score (original - reduction), or None if no original score
        """
        if self.cibil_score is None:
            return None
        reduction = self.get_cibil_reduction()
        actual_score = max(0, self.cibil_score - reduction)  # Can't go below 0
        return actual_score

    def is_credit_restricted(self, threshold: int = 600) -> bool:
        """
        Check if customer is credit restricted due to low CIBIL

        Args:
            threshold: Minimum CIBIL score to be eligible for credit (default: 600)

        Returns:
            True if customer's current CIBIL is below threshold
        """
        current_cibil = self.get_current_cibil()
        if current_cibil is None:
            return False
        return current_cibil < threshold

    def get_bounce_impact_summary(self) -> dict:
        """Get summary of bounce impact on creditworthiness"""
        return {
            "total_bounces": self.bounce_count,
            "original_cibil": self.cibil_score,
            "cibil_reduction": self.get_cibil_reduction(),
            "current_cibil": self.get_current_cibil(),
            "is_credit_restricted": self.is_credit_restricted(),
            "last_bounce": self.last_bounce_date,
        }

    # ===== Static Methods =====

    @staticmethod
    def generate_customer_id() -> str:
        Customer._load_used_ids()
        while True:
            random_part = "".join([str(random.randint(0, 9)) for _ in range(8)])
            cust_id = Customer.CUSTOMER_ID_PREFIX + random_part
            if cust_id not in Customer._used_customer_ids:
                Customer._used_customer_ids.add(cust_id)
                Customer._save_used_ids()
                return cust_id

    @staticmethod
    def _load_used_ids():
        if os.path.exists(Customer._used_ids_file):
            with open(Customer._used_ids_file, "r", encoding="utf-8") as f:
                Customer._used_customer_ids = set(line.strip() for line in f)

    @staticmethod
    def _save_used_ids():
        os.makedirs(os.path.dirname(Customer._used_ids_file), exist_ok=True)
        with open(Customer._used_ids_file, "w", encoding="utf-8") as f:
            for cust_id in Customer._used_customer_ids:
                f.write(cust_id + "\n")

    @staticmethod
    def create_customer(
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        phone_number: str,
        email: str,
        initial_account_number: str,
    ) -> "Customer":
        customer_id = Customer.generate_customer_id()
        customer = Customer(
            customer_id=customer_id,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            email=email,
            account_numbers=[initial_account_number],
            failed_attempts=0,
            locked=False,
        )
        ts = BankClock.get_formatted_datetime()
        DataStore.append_activity(
            timestamp=ts,
            username=username,
            account_number=initial_account_number,
            action="CUSTOMER_CREATED",
            amount=None,
            resulting_balance=None,
            metadata=f"customerId={customer_id}",
        )
        return customer

    @staticmethod
    def from_storage(
        customer_id: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        phone_number: str,
        email: str,
        account_numbers: List[str],
        failed_attempts: int,
        locked: bool,
        cibil_score=None,
        salary=None,
        employer_name=None,
        employer_type=None,
        job_start_date=None,
        employer_category=None,
        city=None,
        kyc_completed=False,
        has_salary_account=False,
        credit_cards=None,
        pan=None,
    ) -> "Customer":
        if customer_id.startswith(Customer.CUSTOMER_ID_PREFIX):
            Customer._used_customer_ids.add(customer_id)
            Customer._save_used_ids()
        return Customer(
            customer_id=customer_id,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone_number=phone_number,
            email=email,
            account_numbers=account_numbers.copy(),
            failed_attempts=failed_attempts,
            locked=locked,
            cibil_score=cibil_score,
            salary=salary,
            employer_name=employer_name,
            employer_type=employer_type,
            job_start_date=job_start_date,
            employer_category=employer_category,
            city=city,
            kyc_completed=kyc_completed,
            has_salary_account=has_salary_account,
            credit_cards=credit_cards if credit_cards is not None else [],
            pan=pan,
        )

    # ===== Serialization =====

    def to_dict(self) -> dict:
        data = {
            "customerId": self.customer_id,
            "username": self.username,
            "password": self.password,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "dob": self.dob,
            "gender": self.gender,
            "phoneNumber": self.phone_number,
            "email": self.email,
            "accountNumbers": self._account_numbers.copy(),
            "failedAttempts": self.failed_attempts,
            "locked": self.locked,
            "cibilScore": self.cibil_score,
            "salary": self.salary,
            "employerName": self.employer_name,
            "employerType": self.employer_type,
            "jobStartDate": self.job_start_date,
            "employerCategory": self.employer_category,
            "city": self.city,
            "kycCompleted": self.kyc_completed,
            "hasSalaryAccount": self.has_salary_account,
            "creditCards": [
                card.to_dict() if hasattr(card, "to_dict") else card
                for card in self.credit_cards
            ],
            "beneficiaries": self.beneficiary_manager.to_dict(),
            "bounceCount": self.bounce_count,
            "bounceHistory": self.bounce_history,
            "lastBounceDate": self.last_bounce_date,
            "pan": self.pan,
        }

        # ✅ CRITICAL: Add password recovery data to serialization
        data.update(self.get_password_recovery_dict())

        return data

    @staticmethod
    def from_dict(data: dict) -> "Customer":
        customer = Customer.from_storage(
            customer_id=data.get("customerId"),
            username=data.get("username"),
            password=data.get("password"),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            dob=data.get("dob"),
            gender=data.get("gender"),
            phone_number=data.get("phoneNumber"),
            email=data.get("email"),
            account_numbers=data.get("accountNumbers", []),
            failed_attempts=data.get("failedAttempts", 0),
            locked=data.get("locked", False),
            cibil_score=data.get("cibilScore"),
            salary=data.get("salary"),
            employer_name=data.get("employerName"),
            employer_type=data.get("employerType"),
            job_start_date=data.get("jobStartDate"),
            employer_category=data.get("employerCategory"),
            city=data.get("city"),
            kyc_completed=data.get("kycCompleted", False),
            has_salary_account=data.get("hasSalaryAccount", False),
            credit_cards=data.get("creditCards", []),
            pan=data.get("pan"),
        )

        # ✅ CRITICAL: Load password recovery data from JSON
        customer.load_password_recovery_dict(data)

        # Load beneficiary data
        if data.get("beneficiaries"):
            customer.beneficiary_manager = BeneficiaryManager.from_dict(
                data["beneficiaries"]
            )

        # Load bounce tracking data
        customer.bounce_count = data.get("bounceCount", 0)
        customer.bounce_history = data.get("bounceHistory", [])
        customer.last_bounce_date = data.get("lastBounceDate")

        return customer

    def __repr__(self) -> str:
        return f"Customer({self.customer_id}, {self.username}, {self.first_name} {self.last_name})"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.customer_id})"


# Initialize used customer IDs on module load
Customer._load_used_ids()
