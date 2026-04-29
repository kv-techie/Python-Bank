"""
NACH (National Automated Clearing House) Mandate System for Loan EMI Payments

Implements realistic NACH mandate creation and management as per RBI guidelines:
- Mandate creation with OTP verification
- Mandate status tracking (Pending, Active, Suspended, Revoked)
- Automatic EMI deductions from designated bank account
- Mandate amendment and cancellation
- Audit trail and transaction history
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .BankClock import BankClock
from .DataStore import DataStore


class NachMandateStatus:
    """Mandate status constants"""

    PENDING = "Pending"  # Awaiting OTP verification
    ACTIVE = "Active"  # Mandate is active and can be used
    OTP_VERIFIED = "OTP_Verified"  # OTP verified, awaiting bank confirmation
    SUSPENDED = "Suspended"  # Mandate temporarily suspended
    REVOKED = "Revoked"  # Mandate cancelled/revoked
    EXPIRED = "Expired"  # Mandate validity period expired


class LoanNachMandate:
    """Represents a NACH mandate for automatic EMI deduction"""

    def __init__(
        self,
        mandate_id: str,
        loan_id: str,
        customer_id: str,
        account_number: str,
        bank_account_number: str,
        bank_ifsc: str,
        emi_amount: float,
        max_debit_amount: float,  # Usually 1.5x of EMI for safety
        start_date: str,
        end_date: str,
        status: str = NachMandateStatus.PENDING,
        creation_timestamp: str = None,
        verification_timestamp: str = None,
        otp: str = None,
        otp_expiry: str = None,
        otp_attempts: int = 0,
    ):
        self.mandate_id = mandate_id
        self.loan_id = loan_id
        self.customer_id = customer_id
        self.account_number = account_number  # Account where loan is given
        self.bank_account_number = bank_account_number  # Account to deduct EMI from
        self.bank_ifsc = bank_ifsc
        self.emi_amount = emi_amount
        self.max_debit_amount = max_debit_amount
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.creation_timestamp = (
            creation_timestamp or BankClock.get_formatted_datetime()
        )
        self.verification_timestamp = verification_timestamp
        self.otp = otp
        self.otp_expiry = otp_expiry
        self.otp_attempts = otp_attempts
        self.deduction_history: List[Dict] = []  # Track EMI deductions

    def to_dict(self) -> dict:
        """Convert mandate to dictionary"""
        return {
            "mandate_id": self.mandate_id,
            "loan_id": self.loan_id,
            "customer_id": self.customer_id,
            "account_number": self.account_number,
            "bank_account_number": self.bank_account_number,
            "bank_ifsc": self.bank_ifsc,
            "emi_amount": self.emi_amount,
            "max_debit_amount": self.max_debit_amount,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "creation_timestamp": self.creation_timestamp,
            "verification_timestamp": self.verification_timestamp,
            "otp": self.otp,
            "otp_expiry": self.otp_expiry,
            "otp_attempts": self.otp_attempts,
            "deduction_history": self.deduction_history,
        }

    @staticmethod
    def from_dict(data: dict) -> "LoanNachMandate":
        """Create mandate from dictionary"""
        mandate = LoanNachMandate(
            mandate_id=data["mandate_id"],
            loan_id=data["loan_id"],
            customer_id=data["customer_id"],
            account_number=data["account_number"],
            bank_account_number=data["bank_account_number"],
            bank_ifsc=data["bank_ifsc"],
            emi_amount=data["emi_amount"],
            max_debit_amount=data["max_debit_amount"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=data.get("status", NachMandateStatus.PENDING),
            creation_timestamp=data.get("creation_timestamp"),
            verification_timestamp=data.get("verification_timestamp"),
            otp=data.get("otp"),
            otp_expiry=data.get("otp_expiry"),
            otp_attempts=data.get("otp_attempts", 0),
        )
        mandate.deduction_history = data.get("deduction_history", [])
        return mandate

    def is_otp_valid(self) -> bool:
        """Check if OTP is still valid"""
        if not self.otp_expiry:
            return False
        try:
            expiry = datetime.strptime(self.otp_expiry, "%d-%m-%Y %H:%M:%S")
            return datetime.now() < expiry
        except (ValueError, TypeError):
            return False

    def verify_otp(self, entered_otp: str) -> Tuple[bool, str]:
        """Verify OTP for mandate activation"""
        if self.otp_attempts >= 3:
            return False, "Maximum OTP attempts exceeded. Mandate creation failed."

        if not self.is_otp_valid():
            return False, "OTP has expired. Please create mandate again."

        if entered_otp != self.otp:
            self.otp_attempts += 1
            remaining = 3 - self.otp_attempts
            return False, f"Invalid OTP. {remaining} attempts remaining."

        # Correct OTP
        self.status = NachMandateStatus.ACTIVE
        self.verification_timestamp = BankClock.get_formatted_datetime()
        self.otp = None  # Clear OTP after verification
        self.otp_attempts = 0
        return True, "OTP verified successfully. Mandate is now ACTIVE."

    def record_deduction(self, amount: float, status: str = "Success") -> bool:
        """Record an EMI deduction"""
        if self.status != NachMandateStatus.ACTIVE:
            return False

        self.deduction_history.append(
            {
                "date": BankClock.get_formatted_datetime(),
                "amount": amount,
                "status": status,
            }
        )
        return True


class LoanNachMandateManager:
    """Manages NACH mandates for loans"""

    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MANDATES_FILE = os.path.join(_BASE_DIR, "data", "loan_nach_mandates.json")

    @staticmethod
    def _load_mandates() -> Dict[str, LoanNachMandate]:
        """Load all NACH mandates from storage"""
        mandates = {}
        if os.path.exists(LoanNachMandateManager.MANDATES_FILE):
            try:
                with open(LoanNachMandateManager.MANDATES_FILE, "r") as f:
                    data = json.load(f)
                    for mandate_id, mandate_data in data.items():
                        mandates[mandate_id] = LoanNachMandate.from_dict(mandate_data)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        return mandates

    @staticmethod
    def _save_mandates(mandates: Dict[str, LoanNachMandate]):
        """Save all NACH mandates to storage"""
        os.makedirs(
            os.path.dirname(LoanNachMandateManager.MANDATES_FILE), exist_ok=True
        )
        with open(LoanNachMandateManager.MANDATES_FILE, "w") as f:
            data = {mid: m.to_dict() for mid, m in mandates.items()}
            json.dump(data, f, indent=2)

    @staticmethod
    def create_mandate(
        loan_id: str,
        customer_id: str,
        account_number: str,
        debit_account: str,
        debit_ifsc: str,
        emi_amount: float,
        start_date: str,
        end_date: str,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new NACH mandate for automatic EMI deduction

        Returns: (success, message, mandate_id)
        """
        # Generate mandate ID
        mandate_id = f"NACH{BankClock.today().strftime('%Y%m%d')}{random.randint(100000, 999999)}"

        # Create new mandate (will be in Pending status with OTP)
        otp = f"{random.randint(100000, 999999)}"
        otp_expiry = (datetime.now() + timedelta(minutes=30)).strftime(
            "%d-%m-%Y %H:%M:%S"
        )

        mandate = LoanNachMandate(
            mandate_id=mandate_id,
            loan_id=loan_id,
            customer_id=customer_id,
            account_number=account_number,
            bank_account_number=debit_account,
            bank_ifsc=debit_ifsc,
            emi_amount=emi_amount,
            max_debit_amount=emi_amount * 1.5,  # 1.5x safety buffer
            start_date=start_date,
            end_date=end_date,
            status=NachMandateStatus.PENDING,
            otp=otp,
            otp_expiry=otp_expiry,
        )

        # Save mandate
        mandates = LoanNachMandateManager._load_mandates()
        mandates[mandate_id] = mandate
        LoanNachMandateManager._save_mandates(mandates)

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=customer_id,
            account_number=account_number,
            action="LOAN_NACH_MANDATE_CREATED",
            amount=0,
            resulting_balance=0,
            metadata=f"mandateId={mandate_id};loanId={loan_id};emiAmount={emi_amount}",
        )

        return (
            True,
            f"NACH mandate created. OTP sent to registered mobile. Mandate ID: {mandate_id}",
            mandate_id,
            otp,  # Return OTP for testing (in real system, would be sent via SMS)
        )

    @staticmethod
    def verify_mandate_otp(
        mandate_id: str,
        entered_otp: str,
    ) -> Tuple[bool, str]:
        """Verify OTP for mandate activation"""
        mandates = LoanNachMandateManager._load_mandates()

        if mandate_id not in mandates:
            return False, "Mandate not found."

        mandate = mandates[mandate_id]
        success, message = mandate.verify_otp(entered_otp)

        if success:
            LoanNachMandateManager._save_mandates(mandates)

            # Log successful verification
            DataStore.append_activity(
                timestamp=BankClock.get_formatted_datetime(),
                username=mandate.customer_id,
                account_number=mandate.account_number,
                action="LOAN_NACH_MANDATE_VERIFIED",
                amount=0,
                resulting_balance=0,
                metadata=f"mandateId={mandate_id};loanId={mandate.loan_id}",
            )

        return success, message

    @staticmethod
    def get_mandate(mandate_id: str) -> Optional[LoanNachMandate]:
        """Get a specific mandate"""
        mandates = LoanNachMandateManager._load_mandates()
        return mandates.get(mandate_id)

    @staticmethod
    def get_loan_mandate(loan_id: str) -> Optional[LoanNachMandate]:
        """Get mandate for a specific loan"""
        mandates = LoanNachMandateManager._load_mandates()
        for mandate in mandates.values():
            if (
                mandate.loan_id == loan_id
                and mandate.status == NachMandateStatus.ACTIVE
            ):
                return mandate
        return None

    @staticmethod
    def get_customer_mandates(customer_id: str) -> List[LoanNachMandate]:
        """Get all mandates for a customer"""
        mandates = LoanNachMandateManager._load_mandates()
        return [m for m in mandates.values() if m.customer_id == customer_id]

    @staticmethod
    def revoke_mandate(mandate_id: str, reason: str = "") -> Tuple[bool, str]:
        """Revoke a NACH mandate"""
        mandates = LoanNachMandateManager._load_mandates()

        if mandate_id not in mandates:
            return False, "Mandate not found."

        mandate = mandates[mandate_id]
        mandate.status = NachMandateStatus.REVOKED

        LoanNachMandateManager._save_mandates(mandates)

        # Log revocation
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=mandate.customer_id,
            account_number=mandate.account_number,
            action="LOAN_NACH_MANDATE_REVOKED",
            amount=0,
            resulting_balance=0,
            metadata=f"mandateId={mandate_id};loanId={mandate.loan_id};reason={reason}",
        )

        return True, f"Mandate {mandate_id} has been revoked."

    @staticmethod
    def suspend_mandate(mandate_id: str) -> Tuple[bool, str]:
        """Temporarily suspend a mandate"""
        mandates = LoanNachMandateManager._load_mandates()

        if mandate_id not in mandates:
            return False, "Mandate not found."

        mandate = mandates[mandate_id]
        previous_status = mandate.status
        mandate.status = NachMandateStatus.SUSPENDED

        LoanNachMandateManager._save_mandates(mandates)

        return True, f"Mandate {mandate_id} suspended (was {previous_status})."

    @staticmethod
    def resume_mandate(mandate_id: str) -> Tuple[bool, str]:
        """Resume a suspended mandate"""
        mandates = LoanNachMandateManager._load_mandates()

        if mandate_id not in mandates:
            return False, "Mandate not found."

        mandate = mandates[mandate_id]
        if mandate.status != NachMandateStatus.SUSPENDED:
            return False, f"Cannot resume. Current status: {mandate.status}"

        mandate.status = NachMandateStatus.ACTIVE

        LoanNachMandateManager._save_mandates(mandates)

        return True, f"Mandate {mandate_id} resumed and is ACTIVE."

    @staticmethod
    def process_emi_deduction(
        mandate: LoanNachMandate, emi_amount: float
    ) -> Tuple[bool, str]:
        """
        Process automatic EMI deduction using NACH mandate

        This would be called during time simulation or automatic payment processing
        """
        if mandate.status != NachMandateStatus.ACTIVE:
            return False, f"Mandate is {mandate.status}. Cannot process deduction."

        # Check if deduction amount is within limit
        if emi_amount > mandate.max_debit_amount:
            return (
                False,
                f"Deduction amount exceeds mandate limit of Rs. {mandate.max_debit_amount:.2f}",
            )

        # Record deduction
        mandate.record_deduction(emi_amount, "Success")

        # Save updated mandate
        mandates = LoanNachMandateManager._load_mandates()
        mandates[mandate.mandate_id] = mandate
        LoanNachMandateManager._save_mandates(mandates)

        return (
            True,
            f"EMI of Rs. {emi_amount:.2f} deducted successfully via NACH mandate.",
        )

    @staticmethod
    def get_mandate_summary(mandate: LoanNachMandate) -> str:
        """Get formatted mandate summary"""
        summary = f"""
NACH MANDATE SUMMARY
{"=" * 70}
Mandate ID:           {mandate.mandate_id}
Loan ID:              {mandate.loan_id}
Status:               {mandate.status}
Created:              {mandate.creation_timestamp}
Verified:             {mandate.verification_timestamp or "Pending"}

MANDATE DETAILS
{"=" * 70}
Debit Account:        {mandate.bank_account_number}
Bank IFSC:            {mandate.bank_ifsc}
EMI Amount:           Rs. {mandate.emi_amount:,.2f}
Max Debit Limit:      Rs. {mandate.max_debit_amount:,.2f}
Validity Period:      {mandate.start_date} to {mandate.end_date}

DEDUCTION HISTORY
{"=" * 70}
Total Deductions:     {len(mandate.deduction_history)}
"""
        if mandate.deduction_history:
            summary += f"\n{'Date':<20} {'Amount':<15} {'Status':<15}\n"
            summary += "-" * 70 + "\n"
            for deduction in mandate.deduction_history[-5:]:  # Show last 5
                summary += f"{deduction['date']:<20} Rs. {deduction['amount']:>12,.2f} {deduction['status']:<15}\n"

        summary += "=" * 70
        return summary
