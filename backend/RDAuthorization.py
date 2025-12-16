"""
RD Authorization Module - Enables cross-account autopay for Recurring Deposits

This module allows:
- Customer A (Payer) to authorize payments for Customer B's (Beneficiary) RD
- The RD beneficiary receives the maturity payout
- The payer's account is debited for autopay installments
- Authorization management, limits, and audit trails
- OTP-based two-factor verification for security
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from Account import Account
from BankClock import BankClock
from DataStore import DataStore


class RDAuthorization:
    """Represents an authorization for cross-account RD payment"""

    STATUS_PENDING_VERIFICATION = "Pending_Verification"
    STATUS_ACTIVE = "Active"
    STATUS_SUSPENDED = "Suspended"
    STATUS_REVOKED = "Revoked"
    STATUS_EXPIRED = "Expired"
    STATUS_BLOCKED = "Blocked"

    OTP_EXPIRY_MINUTES = 30
    MAX_OTP_ATTEMPTS = 3

    def __init__(
        self,
        auth_id: str,
        rd_number: str,
        beneficiary_customer_id: str,
        beneficiary_account_number: str,
        payer_customer_id: str,
        payer_account_number: str,
        monthly_limit: float,
        created_date: datetime = None,
        status: str = None,
        metadata: Optional[Dict] = None,
    ):
        self.auth_id = auth_id
        self.rd_number = rd_number
        self.beneficiary_customer_id = beneficiary_customer_id
        self.beneficiary_account_number = beneficiary_account_number
        self.payer_customer_id = payer_customer_id
        self.payer_account_number = payer_account_number
        self.monthly_limit = monthly_limit
        self.created_date = created_date or BankClock.now()
        self.status = status or self.STATUS_PENDING_VERIFICATION
        self.metadata = metadata or {}

        # OTP Verification fields
        self.otp: Optional[str] = None
        self.otp_generated_at: Optional[datetime] = None
        self.otp_expires_at: Optional[datetime] = None
        self.otp_verified: bool = False
        self.otp_attempts: int = 0

        # Tracking
        self.total_payments = 0
        self.total_amount_paid = 0.0
        self.last_payment_date: Optional[datetime] = None
        self.payment_history: List[Dict] = []
        self.suspension_history: List[Dict] = []
        self.verification_history: List[Dict] = []

    def generate_otp(self) -> str:
        """Generate a 6-digit OTP for authorization verification"""
        self.otp = str(random.randint(100000, 999999))
        self.otp_generated_at = BankClock.now()
        self.otp_expires_at = self.otp_generated_at + timedelta(
            minutes=self.OTP_EXPIRY_MINUTES
        )
        self.otp_attempts = 0
        self.status = self.STATUS_PENDING_VERIFICATION

        # Log OTP generation
        self.verification_history.append(
            {
                "timestamp": self.otp_generated_at.isoformat(),
                "action": "OTP_GENERATED",
                "details": f"OTP generated, expires in {self.OTP_EXPIRY_MINUTES} minutes",
                "by": "System",
            }
        )

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=f"CUST_{self.beneficiary_customer_id}",
            account_number=self.beneficiary_account_number,
            action="RD_AUTH_OTP_GENERATED",
            amount=None,
            resulting_balance=None,
            metadata=f"authId={self.auth_id}|rdNumber={self.rd_number}|payer={self.payer_customer_id}",
        )

        return self.otp

    def verify_otp(
        self, entered_otp: str, verifier_customer_id: str
    ) -> Tuple[bool, str]:
        """
        Verify the OTP entered by payer
        Returns: (success, message)
        """
        current_time = BankClock.now()

        # Check if OTP exists
        if not self.otp:
            return False, "No OTP generated for this authorization"

        # Check if already verified
        if self.otp_verified:
            return False, "Authorization already verified and active"

        # Verify that the verifier is the payer
        if verifier_customer_id != self.payer_customer_id:
            self.verification_history.append(
                {
                    "timestamp": current_time.isoformat(),
                    "action": "OTP_UNAUTHORIZED_ATTEMPT",
                    "details": f"Customer {verifier_customer_id} tried to verify (not authorized payer)",
                    "by": verifier_customer_id,
                }
            )
            return False, "Only the authorized payer can verify this authorization"

        # Check if blocked due to too many attempts
        if self.status == self.STATUS_BLOCKED:
            return (
                False,
                "Authorization blocked due to too many failed attempts. Contact support.",
            )

        # Check expiry
        if current_time > self.otp_expires_at:
            self.status = self.STATUS_EXPIRED
            self.verification_history.append(
                {
                    "timestamp": current_time.isoformat(),
                    "action": "OTP_EXPIRED",
                    "details": "OTP verification attempted after expiry",
                    "by": verifier_customer_id,
                }
            )
            return (
                False,
                "OTP has expired. Please request a new authorization from beneficiary.",
            )

        # Check max attempts before incrementing
        if self.otp_attempts >= self.MAX_OTP_ATTEMPTS:
            self.status = self.STATUS_BLOCKED
            self.verification_history.append(
                {
                    "timestamp": current_time.isoformat(),
                    "action": "OTP_BLOCKED",
                    "details": "Maximum OTP attempts exceeded",
                    "by": verifier_customer_id,
                }
            )

            # Log blocking activity
            DataStore.append_activity(
                timestamp=BankClock.get_formatted_datetime(),
                username=f"CUST_{self.payer_customer_id}",
                account_number=self.payer_account_number,
                action="RD_AUTH_BLOCKED",
                amount=None,
                resulting_balance=None,
                metadata=f"authId={self.auth_id}|reason=MAX_OTP_ATTEMPTS",
            )

            return False, "Authorization blocked due to too many failed attempts."

        # Increment attempt counter
        self.otp_attempts += 1

        # Verify OTP
        if entered_otp.strip() == self.otp:
            # Success!
            self.otp_verified = True
            self.status = self.STATUS_ACTIVE

            self.verification_history.append(
                {
                    "timestamp": current_time.isoformat(),
                    "action": "OTP_VERIFIED",
                    "details": "Authorization activated successfully",
                    "by": verifier_customer_id,
                }
            )

            # Log successful verification
            DataStore.append_activity(
                timestamp=BankClock.get_formatted_datetime(),
                username=f"CUST_{self.payer_customer_id}",
                account_number=self.payer_account_number,
                action="RD_AUTH_VERIFIED",
                amount=None,
                resulting_balance=None,
                metadata=f"authId={self.auth_id}|rdNumber={self.rd_number}|beneficiary={self.beneficiary_customer_id}",
            )

            return (
                True,
                "✅ Authorization verified successfully! RD autopay is now active.",
            )
        else:
            # Failed attempt
            remaining = self.MAX_OTP_ATTEMPTS - self.otp_attempts

            self.verification_history.append(
                {
                    "timestamp": current_time.isoformat(),
                    "action": "OTP_FAILED",
                    "details": f"Incorrect OTP entered (Attempt {self.otp_attempts}/{self.MAX_OTP_ATTEMPTS})",
                    "by": verifier_customer_id,
                }
            )

            # Log failed attempt
            DataStore.append_activity(
                timestamp=BankClock.get_formatted_datetime(),
                username=f"CUST_{self.payer_customer_id}",
                account_number=self.payer_account_number,
                action="RD_AUTH_OTP_FAILED",
                amount=None,
                resulting_balance=None,
                metadata=f"authId={self.auth_id}|attempt={self.otp_attempts}|remaining={remaining}",
            )

            if remaining > 0:
                return False, f"❌ Incorrect OTP. {remaining} attempt(s) remaining."
            else:
                # This was the last attempt, block it
                self.status = self.STATUS_BLOCKED
                return (
                    False,
                    "❌ Incorrect OTP. Authorization blocked due to too many failed attempts.",
                )

    def is_active(self) -> bool:
        """Check if authorization is active and verified"""
        return self.status == self.STATUS_ACTIVE and self.otp_verified

    def is_pending_verification(self) -> bool:
        """Check if authorization is pending OTP verification"""
        return self.status == self.STATUS_PENDING_VERIFICATION and not self.otp_verified

    def get_otp_status(self) -> Dict:
        """Get OTP verification status information"""
        if not self.otp:
            return {
                "has_otp": False,
                "verified": False,
                "status": "No OTP generated",
            }

        current_time = BankClock.now()
        time_left = (
            self.otp_expires_at - current_time if self.otp_expires_at else timedelta(0)
        )
        minutes_left = max(0, int(time_left.total_seconds() / 60))

        return {
            "has_otp": True,
            "verified": self.otp_verified,
            "attempts_used": self.otp_attempts,
            "max_attempts": self.MAX_OTP_ATTEMPTS,
            "remaining_attempts": self.MAX_OTP_ATTEMPTS - self.otp_attempts,
            "generated_at": self.otp_generated_at.strftime("%d-%m-%Y %H:%M:%S")
            if self.otp_generated_at
            else None,
            "expires_at": self.otp_expires_at.strftime("%d-%m-%Y %H:%M:%S")
            if self.otp_expires_at
            else None,
            "minutes_remaining": minutes_left,
            "is_expired": current_time > self.otp_expires_at
            if self.otp_expires_at
            else True,
            "status": self.status,
        }

    def can_make_payment(self, amount: float) -> Tuple[bool, str]:
        """
        Check if payment can be made under this authorization
        Returns: (can_pay, reason)
        """
        # Must be verified first
        if not self.otp_verified:
            return False, "Authorization not verified. Payer must verify OTP first."

        if not self.is_active():
            return False, f"Authorization is {self.status}"

        if amount > self.monthly_limit:
            return (
                False,
                f"Payment amount Rs. {amount:,.2f} exceeds monthly limit Rs. {self.monthly_limit:,.2f}",
            )

        return True, "Payment authorized"

    def record_payment(
        self, amount: float, installment_number: int, success: bool, message: str = ""
    ):
        """Record a payment attempt"""
        payment_record = {
            "date": BankClock.now().isoformat(),
            "amount": amount,
            "installment_number": installment_number,
            "success": success,
            "message": message,
        }
        self.payment_history.append(payment_record)

        if success:
            self.total_payments += 1
            self.total_amount_paid += amount
            self.last_payment_date = BankClock.now()

    def suspend(self, reason: str, suspended_by: str) -> Tuple[bool, str]:
        """Suspend the authorization"""
        if self.status not in [self.STATUS_ACTIVE, self.STATUS_PENDING_VERIFICATION]:
            return False, f"Cannot suspend - authorization is {self.status}"

        old_status = self.status
        self.status = self.STATUS_SUSPENDED
        suspension_record = {
            "date": BankClock.now().isoformat(),
            "reason": reason,
            "suspended_by": suspended_by,
            "previous_status": old_status,
        }
        self.suspension_history.append(suspension_record)

        return True, f"Authorization suspended: {reason}"

    def reactivate(self, reactivated_by: str) -> Tuple[bool, str]:
        """Reactivate a suspended authorization"""
        if self.status != self.STATUS_SUSPENDED:
            return False, f"Cannot reactivate - authorization is {self.status}"

        # If not verified, go back to pending
        if not self.otp_verified:
            self.status = self.STATUS_PENDING_VERIFICATION
            message = "Authorization reactivated but still requires OTP verification"
        else:
            self.status = self.STATUS_ACTIVE
            message = "Authorization reactivated successfully"

        reactivation_record = {
            "date": BankClock.now().isoformat(),
            "action": "Reactivated",
            "by": reactivated_by,
            "new_status": self.status,
        }
        self.suspension_history.append(reactivation_record)

        return True, message

    def revoke(self, reason: str, revoked_by: str) -> Tuple[bool, str]:
        """Permanently revoke the authorization"""
        if self.status == self.STATUS_REVOKED:
            return False, "Authorization is already revoked"

        self.status = self.STATUS_REVOKED
        revocation_record = {
            "date": BankClock.now().isoformat(),
            "reason": reason,
            "revoked_by": revoked_by,
        }
        self.metadata["revocation"] = revocation_record

        return True, f"Authorization revoked: {reason}"

    def update_monthly_limit(
        self, new_limit: float, updated_by: str
    ) -> Tuple[bool, str]:
        """Update the monthly payment limit"""
        if self.status == self.STATUS_REVOKED:
            return False, "Cannot update revoked authorization"

        old_limit = self.monthly_limit
        self.monthly_limit = new_limit

        update_record = {
            "date": BankClock.now().isoformat(),
            "old_limit": old_limit,
            "new_limit": new_limit,
            "updated_by": updated_by,
        }

        if "limit_updates" not in self.metadata:
            self.metadata["limit_updates"] = []
        self.metadata["limit_updates"].append(update_record)

        return (
            True,
            f"Monthly limit updated from Rs. {old_limit:,.2f} to Rs. {new_limit:,.2f}",
        )

    def get_summary(self) -> str:
        """Get authorization summary"""
        otp_status = self.get_otp_status()

        otp_section = ""
        if otp_status["has_otp"]:
            if otp_status["verified"]:
                otp_section = f"""
┌─ Verification Status ───────────────────────────────────┐
│ ✅ VERIFIED - Authorization Active
│ Verified at: {self.verification_history[-1]["timestamp"] if self.verification_history else "N/A"}
└─────────────────────────────────────────────────────────┘
"""
            else:
                otp_section = f"""
┌─ Verification Status ───────────────────────────────────┐
│ ⏳ PENDING VERIFICATION
│ OTP Attempts: {otp_status["attempts_used"]}/{otp_status["max_attempts"]}
│ Time Remaining: {otp_status["minutes_remaining"]} minutes
│ Status: {otp_status["status"]}
└─────────────────────────────────────────────────────────┘
"""

        return f"""
╔════════════════════════════════════════════════════════════╗
║           RD AUTHORIZATION DETAILS                         ║
╚════════════════════════════════════════════════════════════╝

Authorization ID: {self.auth_id}
RD Number: {self.rd_number}
Status: {self.status}
{otp_section}
┌─ Beneficiary (Receives Payout) ─────────────────────────┐
│ Customer ID: {self.beneficiary_customer_id}
│ Account: {self.beneficiary_account_number}
└─────────────────────────────────────────────────────────┘

┌─ Payer (Makes Payments) ────────────────────────────────┐
│ Customer ID: {self.payer_customer_id}
│ Account: {self.payer_account_number}
└─────────────────────────────────────────────────────────┘

┌─ Payment Details ───────────────────────────────────────┐
│ Monthly Limit: Rs. {self.monthly_limit:,.2f}
│ Total Payments: {self.total_payments}
│ Total Amount Paid: Rs. {self.total_amount_paid:,.2f}
│ Last Payment: {self.last_payment_date.strftime("%d-%m-%Y %H:%M") if self.last_payment_date else "N/A"}
└─────────────────────────────────────────────────────────┘

Created: {self.created_date.strftime("%d-%m-%Y %H:%M")}
"""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "auth_id": self.auth_id,
            "rd_number": self.rd_number,
            "beneficiary_customer_id": self.beneficiary_customer_id,
            "beneficiary_account_number": self.beneficiary_account_number,
            "payer_customer_id": self.payer_customer_id,
            "payer_account_number": self.payer_account_number,
            "monthly_limit": self.monthly_limit,
            "created_date": self.created_date.isoformat(),
            "status": self.status,
            "metadata": self.metadata,
            # OTP fields
            "otp": self.otp,
            "otp_generated_at": self.otp_generated_at.isoformat()
            if self.otp_generated_at
            else None,
            "otp_expires_at": self.otp_expires_at.isoformat()
            if self.otp_expires_at
            else None,
            "otp_verified": self.otp_verified,
            "otp_attempts": self.otp_attempts,
            # Tracking
            "total_payments": self.total_payments,
            "total_amount_paid": self.total_amount_paid,
            "last_payment_date": (
                self.last_payment_date.isoformat() if self.last_payment_date else None
            ),
            "payment_history": self.payment_history,
            "suspension_history": self.suspension_history,
            "verification_history": self.verification_history,
        }

    @staticmethod
    def from_dict(data: dict) -> "RDAuthorization":
        """Create authorization from dictionary"""
        auth = RDAuthorization(
            auth_id=data["auth_id"],
            rd_number=data["rd_number"],
            beneficiary_customer_id=data["beneficiary_customer_id"],
            beneficiary_account_number=data["beneficiary_account_number"],
            payer_customer_id=data["payer_customer_id"],
            payer_account_number=data["payer_account_number"],
            monthly_limit=data["monthly_limit"],
            created_date=datetime.fromisoformat(data["created_date"]),
            status=data.get("status", RDAuthorization.STATUS_PENDING_VERIFICATION),
            metadata=data.get("metadata", {}),
        )

        # Load OTP fields
        auth.otp = data.get("otp")
        if data.get("otp_generated_at"):
            auth.otp_generated_at = datetime.fromisoformat(data["otp_generated_at"])
        if data.get("otp_expires_at"):
            auth.otp_expires_at = datetime.fromisoformat(data["otp_expires_at"])
        auth.otp_verified = data.get("otp_verified", False)
        auth.otp_attempts = data.get("otp_attempts", 0)

        # Load tracking data
        auth.total_payments = data.get("total_payments", 0)
        auth.total_amount_paid = data.get("total_amount_paid", 0.0)
        auth.last_payment_date = (
            datetime.fromisoformat(data["last_payment_date"])
            if data.get("last_payment_date")
            else None
        )
        auth.payment_history = data.get("payment_history", [])
        auth.suspension_history = data.get("suspension_history", [])
        auth.verification_history = data.get("verification_history", [])

        return auth

    @staticmethod
    def generate_auth_id() -> str:
        """Generate unique authorization ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"AUTH{timestamp}{random_suffix}"

    def __str__(self) -> str:
        verified_marker = "✓" if self.otp_verified else "⏳"
        return f"RDAuth {self.auth_id}: {self.payer_customer_id} → {self.beneficiary_customer_id} (RD: {self.rd_number}) [{self.status} {verified_marker}]"

    def __repr__(self) -> str:
        return f"RDAuthorization(auth_id='{self.auth_id}', rd='{self.rd_number}', status='{self.status}', verified={self.otp_verified})"


class RDAuthorizationManager:
    """Manages all RD authorizations in the system"""

    def __init__(self):
        self.authorizations: Dict[str, RDAuthorization] = {}  # auth_id -> Authorization
        self.rd_to_auth: Dict[str, str] = {}  # rd_number -> auth_id
        self.payer_auths: Dict[str, List[str]] = {}  # payer_customer_id -> [auth_ids]
        self.beneficiary_auths: Dict[
            str, List[str]
        ] = {}  # beneficiary_customer_id -> [auth_ids]

    def create_authorization(
        self,
        rd_number: str,
        beneficiary_customer_id: str,
        beneficiary_account_number: str,
        payer_customer_id: str,
        payer_account_number: str,
        monthly_limit: float,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str, Optional[RDAuthorization], Optional[str]]:
        """
        Create a new RD authorization with OTP
        Returns: (success, message, authorization, otp)
        """
        # Check if RD already has an active authorization
        if rd_number in self.rd_to_auth:
            existing_auth = self.authorizations[self.rd_to_auth[rd_number]]
            if existing_auth.is_active():
                return (
                    False,
                    f"RD {rd_number} already has an active authorization",
                    None,
                    None,
                )
            elif existing_auth.is_pending_verification():
                return (
                    False,
                    f"RD {rd_number} has a pending authorization. Please verify or revoke it first.",
                    None,
                    None,
                )

        # Validate beneficiary and payer are different
        if beneficiary_customer_id == payer_customer_id:
            return (
                False,
                "Beneficiary and payer cannot be the same customer",
                None,
                None,
            )

        # Create authorization
        auth_id = RDAuthorization.generate_auth_id()
        auth = RDAuthorization(
            auth_id=auth_id,
            rd_number=rd_number,
            beneficiary_customer_id=beneficiary_customer_id,
            beneficiary_account_number=beneficiary_account_number,
            payer_customer_id=payer_customer_id,
            payer_account_number=payer_account_number,
            monthly_limit=monthly_limit,
            metadata=metadata,
        )

        # Generate OTP
        otp = auth.generate_otp()

        # Store authorization
        self.authorizations[auth_id] = auth
        self.rd_to_auth[rd_number] = auth_id

        # Index by payer
        if payer_customer_id not in self.payer_auths:
            self.payer_auths[payer_customer_id] = []
        self.payer_auths[payer_customer_id].append(auth_id)

        # Index by beneficiary
        if beneficiary_customer_id not in self.beneficiary_auths:
            self.beneficiary_auths[beneficiary_customer_id] = []
        self.beneficiary_auths[beneficiary_customer_id].append(auth_id)

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=f"CUST_{beneficiary_customer_id}",
            account_number=beneficiary_account_number,
            action="RD_AUTH_CREATED",
            amount=None,
            resulting_balance=None,
            metadata=f"authId={auth_id}|rdNumber={rd_number}|payer={payer_customer_id}|payerAccount={payer_account_number}|limit={monthly_limit}",
        )

        message = f"""
╔════════════════════════════════════════════════════════════╗
║     ✅ RD AUTHORIZATION CREATED SUCCESSFULLY               ║
╚════════════════════════════════════════════════════════════╝

Authorization ID: {auth_id}
RD Number: {rd_number}
Status: PENDING VERIFICATION

Payer: {payer_customer_id}
  Account: {payer_account_number}
  Will pay monthly installments

Beneficiary: {beneficiary_customer_id}
  Account: {beneficiary_account_number}
  Will receive maturity payout

Monthly Payment Limit: Rs. {monthly_limit:,.2f}

⚠️  IMPORTANT: This authorization requires verification!
"""
        return True, message, auth, otp

    def get_authorization_by_id(self, auth_id: str) -> Optional[RDAuthorization]:
        """Get authorization by ID"""
        return self.authorizations.get(auth_id)

    def get_authorization_for_rd(self, rd_number: str) -> Optional[RDAuthorization]:
        """Get active authorization for an RD"""
        if rd_number in self.rd_to_auth:
            auth_id = self.rd_to_auth[rd_number]
            auth = self.authorizations.get(auth_id)
            # Return only if active and verified
            if auth and auth.is_active():
                return auth
        return None

    def get_pending_authorizations_for_payer(
        self, payer_customer_id: str
    ) -> List[RDAuthorization]:
        """Get authorizations pending verification for a payer"""
        auth_ids = self.payer_auths.get(payer_customer_id, [])
        pending = []

        for auth_id in auth_ids:
            if auth_id in self.authorizations:
                auth = self.authorizations[auth_id]
                if auth.is_pending_verification():
                    # Check if not expired
                    if auth.otp_expires_at and BankClock.now() < auth.otp_expires_at:
                        pending.append(auth)

        return pending

    def get_authorizations_by_payer(
        self, payer_customer_id: str
    ) -> List[RDAuthorization]:
        """Get all authorizations where customer is the payer"""
        auth_ids = self.payer_auths.get(payer_customer_id, [])
        return [
            self.authorizations[aid] for aid in auth_ids if aid in self.authorizations
        ]

    def get_authorizations_by_beneficiary(
        self, beneficiary_customer_id: str
    ) -> List[RDAuthorization]:
        """Get all authorizations where customer is the beneficiary"""
        auth_ids = self.beneficiary_auths.get(beneficiary_customer_id, [])
        return [
            self.authorizations[aid] for aid in auth_ids if aid in self.authorizations
        ]

    def verify_authorization(
        self, auth_id: str, otp: str, verifier_customer_id: str
    ) -> Tuple[bool, str]:
        """Verify authorization with OTP"""
        if auth_id not in self.authorizations:
            return False, f"Authorization {auth_id} not found"

        auth = self.authorizations[auth_id]
        return auth.verify_otp(otp, verifier_customer_id)

    def revoke_authorization(
        self, auth_id: str, reason: str, revoked_by: str
    ) -> Tuple[bool, str]:
        """Revoke an authorization"""
        if auth_id not in self.authorizations:
            return False, f"Authorization {auth_id} not found"

        auth = self.authorizations[auth_id]
        success, message = auth.revoke(reason, revoked_by)

        if success:
            # Remove from rd_to_auth mapping if this RD's auth
            if (
                auth.rd_number in self.rd_to_auth
                and self.rd_to_auth[auth.rd_number] == auth_id
            ):
                del self.rd_to_auth[auth.rd_number]

            # Log activity
            DataStore.append_activity(
                timestamp=BankClock.get_formatted_datetime(),
                username=f"CUST_{auth.beneficiary_customer_id}",
                account_number=auth.beneficiary_account_number,
                action="RD_AUTH_REVOKED",
                amount=None,
                resulting_balance=None,
                metadata=f"authId={auth_id}|reason={reason}|revokedBy={revoked_by}",
            )

        return success, message

    def process_authorized_payment(
        self,
        rd_number: str,
        amount: float,
        installment_number: int,
        payer_account: "Account",
    ) -> Tuple[bool, str]:
        """
        Process an authorized payment for RD
        Returns: (success, message)
        """
        auth = self.get_authorization_for_rd(rd_number)
        if not auth:
            return False, f"No active authorization found for RD {rd_number}"

        # Check if authorization allows payment
        can_pay, reason = auth.can_make_payment(amount)
        if not can_pay:
            auth.record_payment(amount, installment_number, False, reason)
            return False, reason

        # Verify payer account matches
        if payer_account.account_number != auth.payer_account_number:
            return False, "Payer account mismatch"

        # Check sufficient balance
        min_balance = payer_account._min_operational_balance
        if payer_account.balance - amount < min_balance:
            message = f"Insufficient balance in payer's account. Required: Rs. {amount:,.2f} + Rs. {min_balance:,.2f} minimum balance"
            auth.record_payment(amount, installment_number, False, message)
            return False, message

        # Deduct from payer's account
        payer_account.balance -= amount

        # Record successful payment
        auth.record_payment(
            amount, installment_number, True, "Payment successful via authorization"
        )

        # Create transaction
        from Transaction import Transaction

        txn = Transaction(
            type="RD_AUTH_PAYMENT",
            amount=-amount,
            resulting_balance=payer_account.balance,
            metadata={
                "rd_number": rd_number,
                "auth_id": auth.auth_id,
                "beneficiary_customer_id": auth.beneficiary_customer_id,
                "installment_number": installment_number,
            },
        )
        payer_account.transactions.append(txn)

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=f"CUST_{auth.payer_customer_id}",
            account_number=auth.payer_account_number,
            action="RD_AUTH_PAYMENT",
            amount=-amount,
            resulting_balance=payer_account.balance,
            metadata=f"authId={auth.auth_id}|rdNumber={rd_number}|beneficiary={auth.beneficiary_customer_id}|installment={installment_number}",
        )

        return (
            True,
            f"Payment of Rs. {amount:,.2f} processed successfully via authorization {auth.auth_id}",
        )

    def to_dict(self) -> dict:
        """Convert manager to dictionary for JSON storage"""
        return {
            "authorizations": {
                auth_id: auth.to_dict() for auth_id, auth in self.authorizations.items()
            },
            "rd_to_auth": self.rd_to_auth,
            "payer_auths": self.payer_auths,
            "beneficiary_auths": self.beneficiary_auths,
        }

    @staticmethod
    def from_dict(data: dict) -> "RDAuthorizationManager":
        """Create manager from dictionary"""
        manager = RDAuthorizationManager()
        manager.authorizations = {
            auth_id: RDAuthorization.from_dict(auth_data)
            for auth_id, auth_data in data.get("authorizations", {}).items()
        }
        manager.rd_to_auth = data.get("rd_to_auth", {})
        manager.payer_auths = data.get("payer_auths", {})
        manager.beneficiary_auths = data.get("beneficiary_auths", {})
        return manager

    def __repr__(self) -> str:
        active_count = sum(
            1 for auth in self.authorizations.values() if auth.is_active()
        )
        pending_count = sum(
            1 for auth in self.authorizations.values() if auth.is_pending_verification()
        )
        return f"RDAuthorizationManager(total={len(self.authorizations)}, active={active_count}, pending={pending_count})"
