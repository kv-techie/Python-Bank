"""
Cheque Book Management for Scala Bank v5.0
Handles cheque book issuance, tracking, and management
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from .Cheque import Cheque, ChequeStatus


class ChequeBookStatus(Enum):
    """Cheque book status enumeration"""

    ACTIVE = "ACTIVE"  # Currently in use
    EXHAUSTED = "EXHAUSTED"  # All cheques used
    REQUESTED = "REQUESTED"  # Pending approval (future feature)
    CANCELLED = "CANCELLED"  # Cancelled by customer


@dataclass
class ChequeBook:
    """Represents a cheque book issued to a customer"""

    cheque_book_id: str = field(
        default_factory=lambda: f"CB{str(uuid4())[:10].upper()}"
    )
    account_number: str = ""
    starting_cheque_number: int = 0  # e.g., 100001
    total_cheques: int = 50  # Standard: 50 cheques per book
    issued_cheques: List[str] = field(default_factory=list)  # List of cheque IDs
    status: ChequeBookStatus = ChequeBookStatus.ACTIVE
    issued_on: datetime = field(default_factory=datetime.now)
    exhausted_on: Optional[datetime] = None
    cheques: Dict[str, Cheque] = field(default_factory=dict)  # {cheque_id: Cheque}

    def to_dict(self) -> Dict:
        """Convert cheque book to dictionary for storage"""
        return {
            "chequeBooksId": self.cheque_book_id,
            "accountNumber": self.account_number,
            "startingChequeNumber": self.starting_cheque_number,
            "totalCheques": self.total_cheques,
            "issuedCheques": self.issued_cheques,
            "status": self.status.value,
            "issuedOn": self.issued_on.isoformat() if self.issued_on else None,
            "exhaustedOn": self.exhausted_on.isoformat() if self.exhausted_on else None,
            "cheques": {cid: c.to_dict() for cid, c in self.cheques.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChequeBook":
        """Create cheque book from dictionary"""
        cheque_book = cls(
            cheque_book_id=data["chequeBooksId"],
            account_number=data["accountNumber"],
            starting_cheque_number=data["startingChequeNumber"],
            total_cheques=data["totalCheques"],
            issued_cheques=data.get("issuedCheques", []),
            status=ChequeBookStatus(data["status"]),
        )

        # Restore datetimes
        if data.get("issuedOn"):
            cheque_book.issued_on = datetime.fromisoformat(data["issuedOn"])
        if data.get("exhaustedOn"):
            cheque_book.exhausted_on = datetime.fromisoformat(data["exhaustedOn"])

        # Restore cheques
        for cheque_id, cheque_data in data.get("cheques", {}).items():
            cheque_book.cheques[cheque_id] = Cheque.from_dict(cheque_data)

        return cheque_book

    def add_cheque(self, cheque: Cheque) -> bool:
        """Add a cheque to this cheque book"""
        if len(self.cheques) >= self.total_cheques:
            return False

        self.cheques[cheque.cheque_id] = cheque
        self.issued_cheques.append(cheque.cheque_id)

        # Only mark as exhausted if all cheques have been USED (not just added)
        # This means status is EXHAUSTED only when all 50 cheques are in terminal state
        # For now, we don't auto-mark as exhausted on creation

        return True

    def get_cheque(self, cheque_id: str) -> Optional[Cheque]:
        """Get a cheque by ID"""
        return self.cheques.get(cheque_id)

    def get_cheque_by_number(self, cheque_number: str) -> Optional[Cheque]:
        """Get a cheque by cheque number"""
        for cheque in self.cheques.values():
            if cheque.cheque_number == cheque_number:
                return cheque
        return None

    def get_unused_cheques(self) -> List[Cheque]:
        """Get all unused cheques"""
        return [c for c in self.cheques.values() if c.status == ChequeStatus.ISSUED]

    def get_cheques_by_status(self, status: ChequeStatus) -> List[Cheque]:
        """Get all cheques with specific status"""
        return [c for c in self.cheques.values() if c.status == status]

    def get_cleared_cheques(self) -> List[Cheque]:
        """Get all cleared cheques"""
        return self.get_cheques_by_status(ChequeStatus.CLEARED)

    def get_bounced_cheques(self) -> List[Cheque]:
        """Get all bounced cheques"""
        return self.get_cheques_by_status(ChequeStatus.BOUNCED)

    def get_pending_cheques(self) -> List[Cheque]:
        """Get all pending cheques"""
        return self.get_cheques_by_status(ChequeStatus.PENDING_CLEARING)

    @property
    def used_count(self) -> int:
        """Count of cheques used (cleared, bounced, cancelled, etc)"""
        return len(
            [c for c in self.cheques.values() if c.status != ChequeStatus.ISSUED]
        )

    @property
    def unused_count(self) -> int:
        """Count of unused cheques"""
        return len(self.get_unused_cheques())

    @property
    def is_exhausted(self) -> bool:
        """Check if cheque book is exhausted"""
        return self.status == ChequeBookStatus.EXHAUSTED

    def get_summary(self) -> Dict:
        """Get cheque book summary"""
        return {
            "cheque_book_id": self.cheque_book_id,
            "account_number": self.account_number,
            "total_cheques": self.total_cheques,
            "used_count": self.used_count,
            "unused_count": self.unused_count,
            "cleared": len(self.get_cleared_cheques()),
            "bounced": len(self.get_bounced_cheques()),
            "pending": len(self.get_pending_cheques()),
            "status": self.status.value,
        }


class ChequeBookManager:
    """Manages cheque books for an account"""

    def __init__(self, account_number: str, starting_cheque_number: int = 100001):
        """Initialize cheque book manager for an account

        Args:
            account_number: The account this manager belongs to
            starting_cheque_number: Starting cheque number (default 100001 for backward compatibility)
        """
        self.account_number = account_number
        self.cheque_books: Dict[str, ChequeBook] = {}
        self.next_cheque_number = starting_cheque_number  # Can be overridden by bank

    def create_and_issue_cheque_book(self, starting_number: int = None) -> ChequeBook:
        """Create and issue a new cheque book for the account

        Args:
            starting_number: Starting cheque number for this book. If None, uses internal counter.
        """
        # Use provided starting number or fall back to internal counter
        cheque_start = (
            starting_number if starting_number is not None else self.next_cheque_number
        )

        cheque_book = ChequeBook(
            account_number=self.account_number,
            starting_cheque_number=cheque_start,
        )
        self.cheque_books[cheque_book.cheque_book_id] = cheque_book

        # Generate 50 cheques for the book
        for i in range(50):
            cheque_number = str(cheque_start + i)
            cheque = Cheque(
                cheque_number=cheque_number,
                account_number=self.account_number,
                amount=0.0,  # Amount will be filled by customer
                payee_name="",  # Payee will be filled by customer
                date_presentable=datetime.now().strftime("%Y-%m-%d"),
            )
            cheque_book.add_cheque(cheque)

        # Update internal counter only if not using external starting number
        if starting_number is None:
            self.next_cheque_number += 50

        return cheque_book

    def get_active_cheque_book(self) -> Optional[ChequeBook]:
        """Get the current active cheque book"""
        for book in self.cheque_books.values():
            if book.status == ChequeBookStatus.ACTIVE:
                return book
        return None

    def get_cheque_book(self, cheque_book_id: str) -> Optional[ChequeBook]:
        """Get a specific cheque book"""
        return self.cheque_books.get(cheque_book_id)

    def get_all_cheque_books(self) -> List[ChequeBook]:
        """Get all cheque books"""
        return list(self.cheque_books.values())

    def get_cheque(self, cheque_id: str) -> Optional[Cheque]:
        """Get a cheque by ID across all books"""
        for book in self.cheque_books.values():
            cheque = book.get_cheque(cheque_id)
            if cheque:
                return cheque
        return None

    def get_cheque_by_number(self, cheque_number: str) -> Optional[Cheque]:
        """Get a cheque by cheque number"""
        for book in self.cheque_books.values():
            cheque = book.get_cheque_by_number(cheque_number)
            if cheque:
                return cheque
        return None

    def find_cheque_book_for_cheque(self, cheque_id: str) -> Optional[ChequeBook]:
        """Find which cheque book contains a specific cheque"""
        for book in self.cheque_books.values():
            if book.get_cheque(cheque_id):
                return book
        return None

    def get_all_cheques(self) -> List[Cheque]:
        """Get all cheques across all books"""
        all_cheques = []
        for book in self.cheque_books.values():
            all_cheques.extend(book.cheques.values())
        return all_cheques

    def get_cheques_by_status(self, status: ChequeStatus) -> List[Cheque]:
        """Get all cheques with specific status"""
        cheques = []
        for book in self.cheque_books.values():
            cheques.extend(book.get_cheques_by_status(status))
        return cheques

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "account_number": self.account_number,
            "next_cheque_number": self.next_cheque_number,
            "cheque_books": {
                bid: book.to_dict() for bid, book in self.cheque_books.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ChequeBookManager":
        """Create from dictionary"""
        manager = cls(account_number=data["account_number"])
        manager.next_cheque_number = data.get("next_cheque_number", 100001)

        for book_id, book_data in data.get("cheque_books", {}).items():
            manager.cheque_books[book_id] = ChequeBook.from_dict(book_data)

        return manager
