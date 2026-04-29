"""
Beneficiary Management Module for Scala Bank v11.2
Handles safe beneficiary management with async validations and detailed logging.
"""

import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field

from .ExternalAPI import IFSCValidator
from .Logger import BankLogger

logger = BankLogger.get_logger("Beneficiary")

@dataclass
class Beneficiary:
    """Represents a beneficiary for bill payments and transfers"""
    name: str
    account_number: str
    ifsc: str
    bank_name: str
    branch: str = ""
    beneficiary_id: str = field(default_factory=lambda: f"BEN{str(uuid4())[:8].upper()}")
    added_on: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    transaction_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "account_number": self.account_number,
            "ifsc": self.ifsc,
            "bank_name": self.bank_name,
            "branch": self.branch,
            "beneficiary_id": self.beneficiary_id,
            "added_on": self.added_on,
            "last_used": self.last_used,
            "transaction_count": self.transaction_count
        }

class BeneficiaryManager:
    """
    Manages a customer's beneficiaries.
    Integrates with ExternalAPI for validation and BankLogger for audit trails.
    """
    
    def __init__(self, customer_id: str = "GLOBAL"):
        self.customer_id = customer_id
        self.ifsc_validator = IFSCValidator()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, "data", "beneficiaries")
        self.data_file = os.path.join(self.data_dir, f"{customer_id}_beneficiaries.json")
        self.beneficiaries: List[Beneficiary] = self._load_beneficiaries()

    def _load_beneficiaries(self) -> List[Beneficiary]:
        """Load beneficiaries from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    return [Beneficiary(**b) for b in data]
        except Exception as e:
            logger.error(f"Failed to load beneficiaries for {self.customer_id}: {e}")
        return []

    def _save_beneficiaries(self):
        """Save beneficiaries to JSON file"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.data_file, 'w', encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self.beneficiaries], f, indent=4)
            logger.debug(f"Saved beneficiaries for {self.customer_id}")
        except Exception as e:
            logger.error(f"Failed to save beneficiaries for {self.customer_id}: {e}")

    def add_beneficiary(self, name: str, account_number: str, ifsc: str) -> bool:
        """Add a new beneficiary with sync-wrapped async IFSC validation"""
        logger.info(f"Adding beneficiary: {name} (Account: {account_number}, IFSC: {ifsc})")
        
        # Check for duplicates first
        if any(b.account_number == account_number for b in self.beneficiaries):
            logger.warning(f"Beneficiary with account {account_number} already exists.")
            return False

        # Validate IFSC using the new ExternalAPI
        details = self.ifsc_validator.fetch_details_sync(ifsc)
        if not details:
            logger.warning(f"Invalid or unknown IFSC code: {ifsc}")
            return False

        new_beneficiary = Beneficiary(
            name=name,
            account_number=account_number,
            ifsc=ifsc.upper(),
            bank_name=details['bank_name'],
            branch=details['branch']
        )
        
        self.beneficiaries.append(new_beneficiary)
        self._save_beneficiaries()
        logger.info(f"Successfully added beneficiary {name} at {details['bank_name']} ({details['branch']})")
        return True

    def remove_beneficiary(self, account_number: str) -> bool:
        """Remove a beneficiary by account number"""
        initial_count = len(self.beneficiaries)
        self.beneficiaries = [b for b in self.beneficiaries if b.account_number != account_number]
        
        if len(self.beneficiaries) < initial_count:
            self._save_beneficiaries()
            logger.info(f"Removed beneficiary with account {account_number}")
            return True
            
        logger.warning(f"Beneficiary with account {account_number} not found.")
        return False

    def list_all(self) -> List[Beneficiary]:
        """Return all beneficiaries"""
        return self.beneficiaries

    def find_by_name(self, name: str) -> List[Beneficiary]:
        """Search beneficiaries by name (case-insensitive)"""
        search_term = name.lower()
        return [b for b in self.beneficiaries if search_term in b.name.lower()]

    def mark_used(self, account_number: str):
        """Update last used timestamp and count"""
        for b in self.beneficiaries:
            if b.account_number == account_number:
                b.last_used = datetime.now().isoformat()
                b.transaction_count += 1
                self._save_beneficiaries()
                break

    def to_dict(self) -> List[Dict[str, Any]]:
        """Serialize beneficiaries"""
        return [b.to_dict() for b in self.beneficiaries]

    @classmethod
    def from_dict(cls, data: Any, customer_id: str = "GLOBAL") -> "BeneficiaryManager":
        """Deserialize beneficiaries"""
        manager = cls(customer_id)
        b_list = data.get("beneficiaries", []) if isinstance(data, dict) else (data or [])
        manager.beneficiaries = [Beneficiary(**b) for b in b_list]
        return manager

