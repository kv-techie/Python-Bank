"""
Beneficiary Management System for Scala Bank v5.0
Handles management of beneficiaries for bill payments and transfers
"""

import json
import re
import urllib.request
import urllib.error
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

class IFSCValidator:
    """Validates IFSC codes using the Razorpay IFSC API with local caching"""
    
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _CACHE_FILE = os.path.join(_BASE_DIR, "data", "ifsc_cache.json")
    _cache = {}

    @staticmethod
    def _load_cache():
        """Load the local IFSC cache from disk"""
        if not IFSCValidator._cache:
            if os.path.exists(IFSCValidator._CACHE_FILE):
                try:
                    with open(IFSCValidator._CACHE_FILE, "r", encoding="utf-8") as f:
                        IFSCValidator._cache = json.load(f)
                except Exception:
                    IFSCValidator._cache = {}
            else:
                IFSCValidator._cache = {}

    @staticmethod
    def _save_cache():
        """Save the current IFSC cache to disk"""
        try:
            os.makedirs(os.path.dirname(IFSCValidator._CACHE_FILE), exist_ok=True)
            with open(IFSCValidator._CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(IFSCValidator._cache, f, indent=4)
        except Exception:
            pass

    @staticmethod
    def validate_format(ifsc_code: str) -> bool:
        """Check if IFSC format is valid (4 letters, 0, 6 alphanumeric)"""
        pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        return bool(re.match(pattern, ifsc_code.upper()))
        
    @staticmethod
    def get_bank_details(ifsc_code: str) -> Optional[Dict]:
        """Fetch bank details from local cache or Razorpay IFSC API"""
        ifsc_code = ifsc_code.upper().strip()
        if not IFSCValidator.validate_format(ifsc_code):
            return None
            
        # 1. Check local cache first (Offline mode support)
        IFSCValidator._load_cache()
        if ifsc_code in IFSCValidator._cache:
            return IFSCValidator._cache[ifsc_code]
            
        # 2. Fetch from API if not cached
        url = f"https://ifsc.razorpay.com/{ifsc_code}"
        try:
            # Set a tight timeout (3s) to prevent CLI hangs in poor network
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    details = {
                        "bank_name": data.get("BANK", ""),
                        "branch": data.get("BRANCH", ""),
                        "city": data.get("CITY", ""),
                        "state": data.get("STATE", ""),
                        "swift": data.get("SWIFT", "")
                    }
                    # 3. Update cache for future use
                    IFSCValidator._cache[ifsc_code] = details
                    IFSCValidator._save_cache()
                    return details

        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            # Gracefully handle network issues or non-existent codes
            pass
            
        return None


@dataclass
class Beneficiary:
    """Represents a beneficiary for bill payments and transfers"""

    beneficiary_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    swift_code: str = ""
    account_type: str = "Savings"

    beneficiary_id: str = field(
        default_factory=lambda: f"BEN{str(uuid4())[:8].upper()}"
    )
    status: str = "Active"
    added_on: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    transaction_count: int = 0

    def mark_used(self):
        """Mark this beneficiary as used (for tracking recent/frequent)"""
        self.last_used = datetime.now()
        self.transaction_count += 1

    def to_dict(self) -> Dict:
        """Convert beneficiary to dictionary for storage"""
        return {
            "beneficiary_id": self.beneficiary_id,
            "beneficiary_name": self.beneficiary_name,
            "account_number": self.account_number,
            "ifsc_code": self.ifsc_code,
            "bank_name": self.bank_name,
            "swift_code": self.swift_code,
            "account_type": self.account_type,

            "status": self.status,
            "added_on": self.added_on.isoformat() if self.added_on else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "transaction_count": self.transaction_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Beneficiary":
        """Create beneficiary from dictionary"""
        beneficiary = cls(
            beneficiary_name=data["beneficiary_name"],
            account_number=data["account_number"],
            ifsc_code=data["ifsc_code"],
            bank_name=data["bank_name"],
            swift_code=data.get("swift_code", ""),
            account_type=data.get("account_type", "Savings"),

            beneficiary_id=data.get("beneficiary_id", f"BEN{str(uuid4())[:8].upper()}"),
            status=data.get("status", "Active"),
            transaction_count=data.get("transaction_count", 0),
        )

        # Restore datetimes
        if data.get("added_on"):
            beneficiary.added_on = datetime.fromisoformat(data["added_on"])
        if data.get("last_used"):
            beneficiary.last_used = datetime.fromisoformat(data["last_used"])

        return beneficiary


class BeneficiaryManager:
    """Manages a collection of beneficiaries for a customer"""

    def __init__(self):
        """Initialize the beneficiary manager"""
        self.beneficiaries: Dict[str, Beneficiary] = {}

    def add_beneficiary(
        self,
        beneficiary_name: str,
        account_number: str,
        ifsc_code: str,
        bank_name: str,
        account_type: str = "Savings",
    ) -> Beneficiary:
        """
        Add a new beneficiary

        Args:
            beneficiary_name: Name of the beneficiary
            account_number: Bank account number
            ifsc_code: IFSC code of the bank
            bank_name: Name of the bank
            account_type: Type of account (Savings, Current, etc.)

        Returns:
            The created Beneficiary object
        """
        beneficiary = Beneficiary(
            beneficiary_name=beneficiary_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            account_type=account_type,
        )
        self.beneficiaries[beneficiary.beneficiary_id] = beneficiary
        return beneficiary

    def get_beneficiary(self, beneficiary_id: str) -> Optional[Beneficiary]:
        """Get a beneficiary by ID"""
        return self.beneficiaries.get(beneficiary_id)

    def remove_beneficiary(self, beneficiary_id: str) -> bool:
        """
        Remove a beneficiary

        Args:
            beneficiary_id: ID of the beneficiary to remove

        Returns:
            True if removed, False if not found
        """
        if beneficiary_id in self.beneficiaries:
            del self.beneficiaries[beneficiary_id]
            return True
        return False

    def update_beneficiary(
        self,
        beneficiary_id: str,
        beneficiary_name: Optional[str] = None,
        account_number: Optional[str] = None,
        ifsc_code: Optional[str] = None,
        bank_name: Optional[str] = None,
        account_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """
        Update a beneficiary's details

        Args:
            beneficiary_id: ID of the beneficiary to update
            beneficiary_name: New name (optional)
            account_number: New account number (optional)
            ifsc_code: New IFSC code (optional)
            bank_name: New bank name (optional)
            account_type: New account type (optional)
            status: New status (optional)

        Returns:
            True if updated, False if not found
        """
        beneficiary = self.beneficiaries.get(beneficiary_id)
        if not beneficiary:
            return False

        if beneficiary_name is not None:
            beneficiary.beneficiary_name = beneficiary_name
        if account_number is not None:
            beneficiary.account_number = account_number
        if ifsc_code is not None:
            beneficiary.ifsc_code = ifsc_code
        if bank_name is not None:
            beneficiary.bank_name = bank_name
        if account_type is not None:
            beneficiary.account_type = account_type
        if status is not None:
            beneficiary.status = status

        return True

    def list_all(self) -> List[Beneficiary]:
        """Get all beneficiaries"""
        return list(self.beneficiaries.values())

    def find_by_account_number(self, account_number: str) -> Optional[Beneficiary]:
        """
        Find a beneficiary by account number

        Args:
            account_number: Account number to search for

        Returns:
            The Beneficiary if found, None otherwise
        """
        for beneficiary in self.beneficiaries.values():
            if beneficiary.account_number == account_number:
                return beneficiary
        return None

    def find_by_name(self, name: str) -> List[Beneficiary]:
        """
        Find beneficiaries by name (partial, case-insensitive match)

        Args:
            name: Name or partial name to search for

        Returns:
            List of matching Beneficiary objects
        """
        search_term = name.lower()
        return [
            b
            for b in self.beneficiaries.values()
            if search_term in b.beneficiary_name.lower()
        ]

    def get_recent(self, count: int = 5) -> List[Beneficiary]:
        """
        Get the most recently used beneficiaries

        Args:
            count: Number of beneficiaries to return

        Returns:
            List of recently used beneficiaries, sorted by last_used (most recent first)
        """
        # Filter beneficiaries that have been used (last_used is not None)
        used_beneficiaries = [
            b for b in self.beneficiaries.values() if b.last_used is not None
        ]
        # Sort by last_used in descending order (most recent first)
        sorted_beneficiaries = sorted(
            used_beneficiaries, key=lambda b: b.last_used, reverse=True
        )
        return sorted_beneficiaries[:count]

    def get_frequent(self, count: int = 5) -> List[Beneficiary]:
        """
        Get the most frequently used beneficiaries

        Args:
            count: Number of beneficiaries to return

        Returns:
            List of frequently used beneficiaries, sorted by transaction_count (highest first)
        """
        sorted_beneficiaries = sorted(
            self.beneficiaries.values(),
            key=lambda b: b.transaction_count,
            reverse=True,
        )
        return sorted_beneficiaries[:count]

    def to_dict(self) -> Dict:
        """Convert beneficiary manager to dictionary for storage"""
        return {"beneficiaries": [b.to_dict() for b in self.beneficiaries.values()]}

    @classmethod
    def from_dict(cls, data: Dict) -> "BeneficiaryManager":
        """Create beneficiary manager from dictionary"""
        manager = cls()
        for beneficiary_data in data.get("beneficiaries", []):
            beneficiary = Beneficiary.from_dict(beneficiary_data)
            manager.beneficiaries[beneficiary.beneficiary_id] = beneficiary
        return manager
