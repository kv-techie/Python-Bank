"""
ExternalAPI.py — Scala Bank External API Utilities
Provides lightweight synchronous wrappers for third-party lookups
(IFSC validation, currency rates, etc.)
"""

import re
import urllib.request
import json
from typing import Optional, Dict

# IFSC format: 4-char bank code + 0 + 6-char branch code (total 11 chars)
_IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def fetch_ifsc_details(ifsc: str) -> Optional[Dict]:
    """Fetch bank/branch details for a given IFSC code via Razorpay public API.

    Returns a dict with keys: bank_name, branch, address, city, state, etc.
    Returns None on any network or parse error.
    """
    try:
        url = f"https://ifsc.razorpay.com/{ifsc.upper()}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        return {
            "bank_name": data.get("BANK", ""),
            "branch":    data.get("BRANCH", ""),
            "address":   data.get("ADDRESS", ""),
            "city":      data.get("CITY", ""),
            "state":     data.get("STATE", ""),
            "ifsc":      data.get("IFSC", ifsc),
        }
    except Exception:
        return None


class IFSCValidator:
    """IFSC code validator and bank-details lookup.

    Supports two usage styles:
      - Static / class-method style (used by BankingApp.py):
            IFSCValidator.validate_format(ifsc)
            IFSCValidator.get_bank_details(ifsc)
      - Instance style (used by BeneficiaryManager):
            v = IFSCValidator()
            v.fetch_details_sync(ifsc)
    """

    # ---------- static helpers ----------

    @staticmethod
    def validate_format(ifsc: str) -> bool:
        """Return True if *ifsc* matches the standard 11-char IFSC pattern."""
        if not isinstance(ifsc, str):
            return False
        return bool(_IFSC_RE.match(ifsc.strip().upper()))

    @staticmethod
    def get_bank_details(ifsc: str) -> Optional[Dict]:
        """Return bank/branch details dict, or None if invalid / unreachable."""
        if not IFSCValidator.validate_format(ifsc):
            return None
        return fetch_ifsc_details(ifsc)

    # ---------- instance helpers (same behaviour, for Beneficiary.py) ----------

    def fetch_details_sync(self, ifsc: str) -> Optional[Dict]:
        """Synchronous IFSC lookup — delegates to the module-level helper."""
        return self.get_bank_details(ifsc)
