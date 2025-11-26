from typing import List, Optional
import random
import os
from DataStore import DataStore
from BankClock import BankClock
from datetime import date

class Customer:
    """Customer class for managing customer information and linked accounts"""
    
    CUSTOMER_ID_PREFIX = "CUST"
    _used_customer_ids = set()
    _used_ids_file = "data/customer_ids.txt"
    
    def __init__(self, customer_id: str, username: str, password: str, first_name: str,
                 last_name: str, dob: str, gender: str, phone_number: str, email: str,
                 account_numbers: List[str] = None, failed_attempts: int = 0, locked: bool = False,
                 # --- LOAN/EMPLOYER INFO FIELDS (optional for creation) ---
                 cibil_score: Optional[int] = None,
                 salary: Optional[float] = None,
                 employer_name: Optional[str] = None,
                 employer_type: Optional[str] = None,
                 job_start_date: Optional[str] = None,  # "YYYY-MM-DD"
                 employer_category: Optional[str] = None,
                 city: Optional[str] = None,
                 kyc_completed: bool = False
                 ):
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

        # --- Loan/Employment Info ---
        self.cibil_score = cibil_score
        self.salary = salary
        self.employer_name = employer_name
        self.employer_type = employer_type
        self.job_start_date = job_start_date
        self.employer_category = employer_category
        self.city = city
        self.kyc_completed = kyc_completed

    def get_account_numbers(self) -> List[str]:
        """Get list of all account numbers linked to this customer"""
        return self._account_numbers.copy()
    
    def add_account(self, account_number: str):
        # ...[unchanged as per your code]...
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
                metadata=f"customerId={self.customer_id}"
            )
    
    def remove_account(self, account_number: str):
        # ...[unchanged as per your code]...
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
                metadata=f"customerId={self.customer_id}"
            )

    @property
    def has_multiple_accounts(self) -> bool:
        return len(self._account_numbers) > 1

    @property
    def account_count(self) -> int:
        return len(self._account_numbers)
    
    def get_account_numbers_formatted(self) -> str:
        return ", ".join(self._account_numbers)
    
    def owns_account(self, account_number: str) -> bool:
        return account_number in self._account_numbers
    
    # --- LOAN/EMPLOYER INFO HELPERS ---

    def age(self):
        dob = date.fromisoformat(self.dob)
        today = date.today()
        return today.year - dob.year - (
            (today.month, today.day) < (dob.month, dob.day)
        )

    def get_DTI(self, bank) -> float:
        """
        Calculate Debt-to-Income ratio (total EMIs / monthly salary).
        Only considers active loans.
        """
        emis = sum(
            loan.calculate_emi() for loan in bank.get_loans_for_customer(self.customer_id) if getattr(loan, 'status', 'Active') == "Active"
        )
        return emis / self.salary if self.salary and self.salary > 0 else 0.0

    # ========== STATIC METHODS ==========

    @staticmethod
    def generate_customer_id() -> str:
        # ...[unchanged as per your code]...
        Customer._load_used_ids()
        while True:
            random_part = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            cust_id = Customer.CUSTOMER_ID_PREFIX + random_part
            if cust_id not in Customer._used_customer_ids:
                Customer._used_customer_ids.add(cust_id)
                Customer._save_used_ids()
                return cust_id

    @staticmethod
    def _load_used_ids():
        if os.path.exists(Customer._used_ids_file):
            with open(Customer._used_ids_file, 'r') as f:
                Customer._used_customer_ids = set(line.strip() for line in f)

    @staticmethod
    def _save_used_ids():
        os.makedirs(os.path.dirname(Customer._used_ids_file), exist_ok=True)
        with open(Customer._used_ids_file, 'w') as f:
            for cust_id in Customer._used_customer_ids:
                f.write(cust_id + '\n')

    @staticmethod
    def create_customer(username: str, password: str, first_name: str, last_name: str,
                       dob: str, gender: str, phone_number: str, email: str,
                       initial_account_number: str) -> 'Customer':
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
            locked=False
        )
        ts = BankClock.get_formatted_datetime()
        DataStore.append_activity(
            timestamp=ts,
            username=username,
            account_number=initial_account_number,
            action="CUSTOMER_CREATED",
            amount=None,
            resulting_balance=None,
            metadata=f"customerId={customer_id}"
        )
        return customer

    @staticmethod
    def from_storage(customer_id: str, username: str, password: str, first_name: str,
                     last_name: str, dob: str, gender: str, phone_number: str, email: str,
                     account_numbers: List[str], failed_attempts: int, locked: bool,
                     # Add all new loan fields as Optionals for storage
                     cibil_score=None, salary=None, employer_name=None, employer_type=None,
                     job_start_date=None, employer_category=None, city=None, kyc_completed=False
                     ) -> 'Customer':
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
            kyc_completed=kyc_completed
        )

    # ========== SERIALIZATION ==========

    def to_dict(self) -> dict:
        d = {
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
            # --- LOAN FIELDS ---
            "cibilScore": self.cibil_score,
            "salary": self.salary,
            "employerName": self.employer_name,
            "employerType": self.employer_type,
            "jobStartDate": self.job_start_date,
            "employerCategory": self.employer_category,
            "city": self.city,
            "kycCompleted": self.kyc_completed
        }
        return d

    @staticmethod
    def from_dict(data: dict) -> 'Customer':
        return Customer.from_storage(
            customer_id=data["customerId"],
            username=data["username"],
            password=data["password"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            dob=data["dob"],
            gender=data["gender"],
            phone_number=data["phoneNumber"],
            email=data["email"],
            account_numbers=data["accountNumbers"],
            failed_attempts=data.get("failedAttempts", 0),
            locked=data.get("locked", False),
            cibil_score=data.get("cibilScore"),
            salary=data.get("salary"),
            employer_name=data.get("employerName"),
            employer_type=data.get("employerType"),
            job_start_date=data.get("jobStartDate"),
            employer_category=data.get("employerCategory"),
            city=data.get("city"),
            kyc_completed=data.get("kycCompleted", False)
        )

    def __repr__(self) -> str:
        return f"Customer({self.customer_id}, {self.username}, {self.first_name} {self.last_name})"
    
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

# Initialize used customer IDs on module load
Customer._load_used_ids()
