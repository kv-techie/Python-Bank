"""
Tax Exemption & Deduction Tracking
Handles self-declared tax deductions with documentation tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class DeductionType(Enum):
    """Types of tax deductions"""

    STANDARD_DEDUCTION = "STANDARD_DEDUCTION"
    HRA = "HRA"
    SECTION_80C = "80C"
    SECTION_80D = "80D"
    SECTION_24_HOME_LOAN_INTEREST = "24_HOME_LOAN_INTEREST"


class DeductionStatus(Enum):
    """Status of deduction claim"""

    AUTO_DETECTED = "AUTO_DETECTED"
    SELF_DECLARED = "SELF_DECLARED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


@dataclass
class DeductionDocument:
    """Document proof for a deduction"""

    document_type: str  # "RENT_AGREEMENT", "INSURANCE_POLICY", etc.
    file_path: str  # Virtual path for simulation
    upload_date: datetime
    verified: bool = False
    verification_date: Optional[datetime] = None


@dataclass
class TaxExemption:
    """Individual tax deduction"""

    deduction_type: DeductionType
    amount: float  # Annual amount
    section: str  # "80C", "80D", "10(13A)", "16", etc.
    status: DeductionStatus

    # Tracking
    declared_date: datetime
    auto_detected: bool = False
    detection_source: Optional[str] = None  # "TRANSACTION", "LOAN", "SALARY", etc.

    # Documentation
    documents: List[DeductionDocument] = field(default_factory=list)
    notes: Optional[str] = None

    # Limits
    annual_limit: Optional[float] = None  # Max allowed
    eligible_amount: Optional[float] = None  # After applying limit

    def __post_init__(self):
        """Calculate eligible amount after applying limit"""
        if self.annual_limit:
            self.eligible_amount = min(self.amount, self.annual_limit)
        else:
            self.eligible_amount = self.amount

    def add_document(self, doc_type: str, file_path: str) -> bool:
        """Add proof document for this deduction"""
        try:
            doc = DeductionDocument(
                document_type=doc_type, file_path=file_path, upload_date=datetime.now()
            )
            self.documents.append(doc)
            return True, f"[SUCCESS] Document uploaded: {doc_type}"
        except Exception as e:
            return False, f"[FAIL] Failed to upload document: {e}"

    def verify_document(self, doc_index: int) -> tuple[bool, str]:
        """Mark document as verified (simulation)"""
        try:
            if 0 <= doc_index < len(self.documents):
                self.documents[doc_index].verified = True
                self.documents[doc_index].verification_date = datetime.now()
                self.status = DeductionStatus.VERIFIED
                return True, "[SUCCESS] Document verified"
            else:
                return False, "Document not found"
        except Exception as e:
            return False, f"Error: {e}"

    def get_summary(self) -> str:
        """Get formatted summary of this deduction"""
        status_icon = {
            DeductionStatus.AUTO_DETECTED: "[SEARCH]",
            DeductionStatus.SELF_DECLARED: "✋",
            DeductionStatus.VERIFIED: "[SUCCESS]",
            DeductionStatus.REJECTED: "[FAIL]",
        }.get(self.status, "❓")

        summary = f"{status_icon} {self.section}\n"
        summary += f"   Amount: ₹{self.amount:,.2f}/year\n"

        if self.annual_limit:
            summary += f"   Limit: ₹{self.annual_limit:,.2f}\n"
            summary += f"   Eligible: ₹{self.eligible_amount:,.2f}\n"
        else:
            summary += f"   Eligible: ₹{self.eligible_amount:,.2f}\n"

        if self.documents:
            verified_docs = sum(1 for d in self.documents if d.verified)
            summary += f"   Documents: {verified_docs}/{len(self.documents)} verified\n"

        if self.auto_detected:
            summary += f"   Source: {self.detection_source}\n"
        else:
            summary += f"   Declared: {self.declared_date.strftime('%d-%m-%Y')}\n"

        return summary

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "deductionType": self.deduction_type.value,
            "section": self.section,
            "amount": self.amount,
            "eligibleAmount": self.eligible_amount,
            "annualLimit": self.annual_limit,
            "status": self.status.value,
            "declaredDate": self.declared_date.isoformat(),
            "autoDetected": self.auto_detected,
            "detectionSource": self.detection_source,
            "documents": [
                {
                    "type": doc.document_type,
                    "path": doc.file_path,
                    "uploadDate": doc.upload_date.isoformat(),
                    "verified": doc.verified,
                    "verificationDate": doc.verification_date.isoformat()
                    if doc.verification_date
                    else None,
                }
                for doc in self.documents
            ],
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict) -> "TaxExemption":
        """Create from dictionary"""
        exemption = TaxExemption(
            deduction_type=DeductionType(data["deductionType"]),
            section=data["section"],
            amount=data["amount"],
            status=DeductionStatus(data["status"]),
            declared_date=datetime.fromisoformat(data["declaredDate"]),
            auto_detected=data.get("autoDetected", False),
            detection_source=data.get("detectionSource"),
            annual_limit=data.get("annualLimit"),
            notes=data.get("notes"),
        )

        # Add documents
        for doc_data in data.get("documents", []):
            doc = DeductionDocument(
                document_type=doc_data["type"],
                file_path=doc_data["path"],
                upload_date=datetime.fromisoformat(doc_data["uploadDate"]),
                verified=doc_data["verified"],
                verification_date=datetime.fromisoformat(doc_data["verificationDate"])
                if doc_data.get("verificationDate")
                else None,
            )
            exemption.documents.append(doc)

        return exemption


@dataclass
class TaxProfile:
    """Complete tax profile for a customer"""

    customer_id: str
    financial_year: str  # "2025-26"
    tax_regime: str  # "OLD_REGIME" or "NEW_REGIME"

    # Metro/non-metro for HRA calculation
    city: str
    is_metro: bool

    # All deductions
    exemptions: List[TaxExemption] = field(default_factory=list)

    # Calculation results
    total_deductions: float = 0.0
    taxable_income: float = 0.0
    tax_payable: float = 0.0

    # Timestamps
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def get_total_eligible_deductions(self) -> float:
        """Get sum of all eligible deductions"""
        return sum(
            e.eligible_amount
            for e in self.exemptions
            if e.status != DeductionStatus.REJECTED
        )

    def get_deductions_by_section(self) -> Dict[str, float]:
        """Group deductions by section"""
        result = {}
        for exemption in self.exemptions:
            if exemption.status != DeductionStatus.REJECTED:
                key = exemption.section
                result[key] = result.get(key, 0) + exemption.eligible_amount
        return result

    def get_summary(self) -> str:
        """Get formatted tax profile summary"""
        summary = f"""
TAX PROFILE - FINANCIAL YEAR {self.financial_year}
{"=" * 60}

{self.tax_regime} REGIME
City: {self.city} {"(Metro)" if self.is_metro else "(Non-Metro)"}

DEDUCTIONS:
"""
        for exemption in self.exemptions:
            if exemption.status != DeductionStatus.REJECTED:
                summary += exemption.get_summary() + "\n"

        summary += f"""
SUMMARY:
   Total Deductions: ₹{self.get_total_eligible_deductions():,.2f}
   Taxable Income: ₹{self.taxable_income:,.2f}
   Tax Payable: ₹{self.tax_payable:,.2f}
"""
        return summary

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "customerId": self.customer_id,
            "financialYear": self.financial_year,
            "taxRegime": self.tax_regime,
            "city": self.city,
            "isMetro": self.is_metro,
            "exemptions": [e.to_dict() for e in self.exemptions],
            "totalDeductions": self.total_deductions,
            "taxableIncome": self.taxable_income,
            "taxPayable": self.tax_payable,
            "createdDate": self.created_date.isoformat(),
            "lastUpdated": self.last_updated.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "TaxProfile":
        """Create from dictionary"""
        profile = TaxProfile(
            customer_id=data["customerId"],
            financial_year=data["financialYear"],
            tax_regime=data["taxRegime"],
            city=data["city"],
            is_metro=data["isMetro"],
            total_deductions=data.get("totalDeductions", 0),
            taxable_income=data.get("taxableIncome", 0),
            tax_payable=data.get("taxPayable", 0),
            created_date=datetime.fromisoformat(data["createdDate"]),
            last_updated=datetime.fromisoformat(data["lastUpdated"]),
        )

        # Add exemptions
        for exemption_data in data.get("exemptions", []):
            profile.exemptions.append(TaxExemption.from_dict(exemption_data))

        return profile
