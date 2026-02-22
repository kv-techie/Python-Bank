"""
Cheque Management System for Scala Bank v5.0
Handles cheque issuance, clearing, bouncing, and bounce fee collection
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4


class ChequeStatus(Enum):
    """Cheque status enumeration"""

    ISSUED = "ISSUED"  # Cheque created and issued to customer
    PENDING_CLEARING = "PENDING_CLEARING"  # Cheque presented, awaiting clearing
    CLEARED = "CLEARED"  # Successfully cleared/deposited
    BOUNCED = "BOUNCED"  # Insufficient funds or fraud
    CANCELLED = "CANCELLED"  # Customer cancelled before use
    STALE = "STALE"  # > 6 months old (automatically marked)


@dataclass
class Cheque:
    """Represents a cheque in the banking system"""

    cheque_number: str  # Serial number on cheque
    account_number: str  # Issuing account
    amount: float  # Cheque amount
    payee_name: str  # Who receives the money
    date_presentable: str  # Date cheque can be presented (YYYY-MM-DD)
    status: ChequeStatus = ChequeStatus.ISSUED
    cheque_id: str = field(default_factory=lambda: f"CHQ{str(uuid4())[:12].upper()}")
    issued_on: datetime = field(default_factory=datetime.now)
    cleared_on: Optional[datetime] = None
    bounced_on: Optional[datetime] = None
    bounce_reason: Optional[str] = None
    bounce_fee_deducted: float = 0.0
    cancelled_on: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    metadata: Optional[str] = None  # Arbitrary metadata

    def to_dict(self) -> Dict:
        """Convert cheque to dictionary for storage"""
        return {
            "chequeId": self.cheque_id,
            "chequeNumber": self.cheque_number,
            "accountNumber": self.account_number,
            "amount": self.amount,
            "payeeName": self.payee_name,
            "datePresentable": self.date_presentable,
            "status": self.status.value,
            "issuedOn": self.issued_on.isoformat() if self.issued_on else None,
            "clearedOn": self.cleared_on.isoformat() if self.cleared_on else None,
            "bouncedOn": self.bounced_on.isoformat() if self.bounced_on else None,
            "bounceReason": self.bounce_reason,
            "bounceFeeDeducted": self.bounce_fee_deducted,
            "cancelledOn": self.cancelled_on.isoformat() if self.cancelled_on else None,
            "cancellationReason": self.cancellation_reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Cheque":
        """Create cheque from dictionary"""
        cheque = cls(
            cheque_number=data["chequeNumber"],
            account_number=data["accountNumber"],
            amount=data["amount"],
            payee_name=data["payeeName"],
            date_presentable=data["datePresentable"],
            status=ChequeStatus(data["status"]),
            cheque_id=data["chequeId"],
            bounce_reason=data.get("bounceReason"),
            bounce_fee_deducted=data.get("bounceFeeDeducted", 0.0),
            cancellation_reason=data.get("cancellationReason"),
            metadata=data.get("metadata"),
        )

        # Restore datetimes
        if data.get("issuedOn"):
            cheque.issued_on = datetime.fromisoformat(data["issuedOn"])
        if data.get("clearedOn"):
            cheque.cleared_on = datetime.fromisoformat(data["clearedOn"])
        if data.get("bouncedOn"):
            cheque.bounced_on = datetime.fromisoformat(data["bouncedOn"])
        if data.get("cancelledOn"):
            cheque.cancelled_on = datetime.fromisoformat(data["cancelledOn"])

        return cheque

    def is_post_dated(self) -> bool:
        """Check if cheque is post-dated (presentable date is in future)"""
        today = datetime.now().date()
        presentable_date = datetime.strptime(self.date_presentable, "%Y-%m-%d").date()
        return presentable_date > today

    def is_stale(self) -> bool:
        """Check if cheque is stale (> 6 months old)"""
        six_months_ago = datetime.now() - timedelta(days=180)
        issued_date = datetime.strptime(self.date_presentable, "%Y-%m-%d")
        return issued_date < six_months_ago

    def is_presentable(self) -> bool:
        """Check if cheque can be presented for clearing"""
        today = datetime.now().date()
        presentable_date = datetime.strptime(self.date_presentable, "%Y-%m-%d").date()
        return presentable_date <= today and not self.is_stale()

    def can_be_cleared(self) -> bool:
        """Check if cheque can be cleared"""
        return (
            self.status == ChequeStatus.ISSUED
            and self.is_presentable()
            and not self.is_stale()
        )

    def mark_cleared(self) -> bool:
        """Mark cheque as cleared"""
        if self.status != ChequeStatus.ISSUED:
            return False
        self.status = ChequeStatus.CLEARED
        self.cleared_on = datetime.now()
        return True

    def mark_bounced(self, reason: str, fee: float = 500.0) -> bool:
        """Mark cheque as bounced and deduct fee"""
        if (
            self.status != ChequeStatus.ISSUED
            and self.status != ChequeStatus.PENDING_CLEARING
        ):
            return False
        self.status = ChequeStatus.BOUNCED
        self.bounced_on = datetime.now()
        self.bounce_reason = reason
        self.bounce_fee_deducted = fee
        return True

    def mark_cancelled(self, reason: str) -> bool:
        """Mark cheque as cancelled"""
        if self.status != ChequeStatus.ISSUED:
            return False
        self.status = ChequeStatus.CANCELLED
        self.cancelled_on = datetime.now()
        self.cancellation_reason = reason
        return True

    def mark_stale(self) -> bool:
        """Mark cheque as stale if it's expired"""
        if self.is_stale() and self.status == ChequeStatus.ISSUED:
            self.status = ChequeStatus.STALE
            return True
        return False

    def get_formatted_amount(self) -> str:
        """Get formatted amount string"""
        return f"Rs. {self.amount:,.2f}"

    def get_formatted_date(self) -> str:
        """Get formatted presentable date"""
        return f"{self.date_presentable}"

    def __str__(self) -> str:
        return f"CHQ {self.cheque_number} - {self.payee_name} - {self.get_formatted_amount()} ({self.status.value})"
