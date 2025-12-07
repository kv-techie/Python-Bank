"""
Form 26AS - Tax Credit Statement
Annual consolidated tax statement showing TDS, advance tax, refunds, and high-value transactions
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass
class TDSEntry:
    """Represents a single TDS deduction entry"""

    deductor_name: str  # Employer/Bank name
    deductor_tan: str  # Tax Deduction Account Number
    amount_paid: float  # Gross amount
    tds_deducted: float  # Tax deducted
    date_of_deduction: date
    date_of_deposit: date  # When TDS was deposited with govt
    financial_year: str  # e.g., "2024-25"
    quarter: str  # Q1, Q2, Q3, Q4
    section: str  # 192 (Salary), 194A (Interest), etc.


@dataclass
class AdvanceTaxEntry:
    """Self-paid advance tax entry"""

    amount: float
    date_of_payment: date
    bsr_code: str  # Bank branch code
    challan_number: str
    financial_year: str


@dataclass
class TaxRefundEntry:
    """Tax refund received"""

    amount: float
    date_of_refund: date
    assessment_year: str
    mode: str  # "Direct credit to bank"


@dataclass
class HighValueTransaction:
    """High-value transactions reported to tax authorities"""

    transaction_type: str  # "Cash deposit", "Credit card payment", etc.
    amount: float
    date: date
    reporting_entity: str  # Bank name


class Form26AS:
    """Generate Form 26AS (Tax Credit Statement)"""

    def __init__(self, pan: str, name: str, address: str):
        self.pan = pan
        self.name = name
        self.address = address
        self.tds_entries: List[TDSEntry] = []
        self.advance_tax_entries: List[AdvanceTaxEntry] = []
        self.refund_entries: List[TaxRefundEntry] = []
        self.high_value_transactions: List[HighValueTransaction] = []

    def add_tds_entry(self, entry: TDSEntry):
        """Add a TDS deduction entry"""
        self.tds_entries.append(entry)

    def add_advance_tax(self, entry: AdvanceTaxEntry):
        """Add advance tax payment"""
        self.advance_tax_entries.append(entry)

    def add_refund(self, entry: TaxRefundEntry):
        """Add tax refund"""
        self.refund_entries.append(entry)

    def add_high_value_transaction(self, entry: HighValueTransaction):
        """Add high-value transaction"""
        self.high_value_transactions.append(entry)

    def get_total_tds_for_fy(self, financial_year: str) -> float:
        """Calculate total TDS deducted in a financial year"""
        return sum(
            entry.tds_deducted
            for entry in self.tds_entries
            if entry.financial_year == financial_year
        )

    def get_tds_by_section(self, financial_year: str) -> Dict[str, float]:
        """Get TDS breakdown by section"""
        by_section = {}
        for entry in self.tds_entries:
            if entry.financial_year == financial_year:
                section = entry.section
                if section not in by_section:
                    by_section[section] = 0.0
                by_section[section] += entry.tds_deducted
        return by_section

    def get_tds_by_quarter(self, financial_year: str) -> Dict[str, float]:
        """Get TDS breakdown by quarter"""
        by_quarter = {"Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0}
        for entry in self.tds_entries:
            if entry.financial_year == financial_year:
                by_quarter[entry.quarter] += entry.tds_deducted
        return by_quarter

    def generate_statement(self, financial_year: str) -> str:
        """Generate Form 26AS text statement"""

        # Filter entries for the financial year
        fy_tds = [e for e in self.tds_entries if e.financial_year == financial_year]
        fy_advance = [
            e for e in self.advance_tax_entries if e.financial_year == financial_year
        ]
        fy_refunds = [
            e for e in self.refund_entries if e.assessment_year == financial_year
        ]

        output = []
        output.append("=" * 100)
        output.append("FORM 26AS - ANNUAL TAX CREDIT STATEMENT")
        output.append("(As per Income Tax Act, 1961)")
        output.append("=" * 100)
        output.append("")
        output.append("PART A - DETAILS OF TAX DEDUCTED AT SOURCE")
        output.append("=" * 100)
        output.append("")

        # Taxpayer details
        output.append(f"PAN: {self.pan}")
        output.append(f"Name: {self.name}")
        output.append(f"Address: {self.address}")
        output.append(f"Financial Year: {financial_year}")
        output.append(f"Assessment Year: {self._get_assessment_year(financial_year)}")
        output.append("")
        output.append("-" * 100)

        # Section-wise TDS summary
        output.append(
            "\nPART A1 - DETAILS OF TAX DEDUCTED AT SOURCE (BY EMPLOYER/BANK)"
        )
        output.append("-" * 100)

        if fy_tds:
            # Group by deductor
            by_deductor = {}
            for entry in fy_tds:
                key = (entry.deductor_name, entry.deductor_tan, entry.section)
                if key not in by_deductor:
                    by_deductor[key] = []
                by_deductor[key].append(entry)

            for (deductor_name, deductor_tan, section), entries in by_deductor.items():
                output.append(f"\nDeductor: {deductor_name}")
                output.append(f"TAN: {deductor_tan}")
                output.append(
                    f"Section: {section} - {self._get_section_description(section)}"
                )
                output.append("")

                # Quarterly breakdown
                output.append(
                    f"{'Quarter':<10} {'Date of Deduction':<20} {'Amount Paid':<18} {'TDS Deducted':<18} {'Deposit Date':<20}"
                )
                output.append("-" * 100)

                total_paid = 0.0
                total_tds = 0.0

                for entry in sorted(entries, key=lambda x: x.date_of_deduction):
                    output.append(
                        f"{entry.quarter:<10} "
                        f"{entry.date_of_deduction.strftime('%d-%b-%Y'):<20} "
                        f"₹{entry.amount_paid:>15,.2f} "
                        f"₹{entry.tds_deducted:>15,.2f} "
                        f"{entry.date_of_deposit.strftime('%d-%b-%Y'):<20}"
                    )
                    total_paid += entry.amount_paid
                    total_tds += entry.tds_deducted

                output.append("-" * 100)
                output.append(
                    f"{'Total':<10} {'':<20} ₹{total_paid:>15,.2f} ₹{total_tds:>15,.2f}"
                )
                output.append("")
        else:
            output.append("No TDS entries for this financial year")

        # Advance tax
        output.append("\n" + "=" * 100)
        output.append("PART B - DETAILS OF TAX PAID (OTHER THAN TDS/TCS)")
        output.append("=" * 100)

        if fy_advance:
            output.append(
                f"\n{'Date':<15} {'BSR Code':<12} {'Challan No':<20} {'Amount':<18}"
            )
            output.append("-" * 100)

            total_advance = 0.0
            for entry in sorted(fy_advance, key=lambda x: x.date_of_payment):
                output.append(
                    f"{entry.date_of_payment.strftime('%d-%b-%Y'):<15} "
                    f"{entry.bsr_code:<12} "
                    f"{entry.challan_number:<20} "
                    f"₹{entry.amount:>15,.2f}"
                )
                total_advance += entry.amount

            output.append("-" * 100)
            output.append(f"{'Total Advance Tax Paid:':<47} ₹{total_advance:>15,.2f}")
        else:
            output.append("\nNo advance tax payments for this financial year")

        # Tax refunds
        output.append("\n" + "=" * 100)
        output.append("PART C - DETAILS OF TAX REFUNDED")
        output.append("=" * 100)

        if fy_refunds:
            output.append(
                f"\n{'Date':<15} {'Assessment Year':<20} {'Amount':<18} {'Mode':<30}"
            )
            output.append("-" * 100)

            total_refund = 0.0
            for entry in fy_refunds:
                output.append(
                    f"{entry.date_of_refund.strftime('%d-%b-%Y'):<15} "
                    f"{entry.assessment_year:<20} "
                    f"₹{entry.amount:>15,.2f} "
                    f"{entry.mode:<30}"
                )
                total_refund += entry.amount

            output.append("-" * 100)
            output.append(f"{'Total Refund Received:':<35} ₹{total_refund:>15,.2f}")
        else:
            output.append("\nNo tax refunds for this assessment year")

        # Summary
        output.append("\n" + "=" * 100)
        output.append("SUMMARY OF TAX CREDITS")
        output.append("=" * 100)

        total_tds = sum(e.tds_deducted for e in fy_tds)
        total_advance = sum(e.amount for e in fy_advance)
        total_refund = sum(e.amount for e in fy_refunds)
        total_tax_credit = total_tds + total_advance - total_refund

        output.append(f"\nTotal TDS (Part A):              ₹{total_tds:>15,.2f}")
        output.append(f"Total Advance Tax (Part B):      ₹{total_advance:>15,.2f}")
        output.append(f"Total Refund (Part C):           ₹{total_refund:>15,.2f}")
        output.append("-" * 100)
        output.append(f"Net Tax Credit Available:        ₹{total_tax_credit:>15,.2f}")
        output.append("=" * 100)

        # High-value transactions
        output.append("\n" + "=" * 100)
        output.append("PART D - DETAILS OF PAID REFUND (OTHER THAN SALARY)")
        output.append("=" * 100)
        output.append("\nNot Applicable")

        output.append("\n" + "=" * 100)
        output.append("PART E - DETAILS OF SFT (STATEMENT OF FINANCIAL TRANSACTIONS)")
        output.append("=" * 100)

        fy_hvt = [
            t
            for t in self.high_value_transactions
            if self._get_financial_year(t.date) == financial_year
        ]

        if fy_hvt:
            output.append(
                f"\n{'Date':<15} {'Transaction Type':<30} {'Amount':<18} {'Reporting Entity':<30}"
            )
            output.append("-" * 100)

            for txn in sorted(fy_hvt, key=lambda x: x.date):
                output.append(
                    f"{txn.date.strftime('%d-%b-%Y'):<15} "
                    f"{txn.transaction_type:<30} "
                    f"₹{txn.amount:>15,.2f} "
                    f"{txn.reporting_entity:<30}"
                )
        else:
            output.append("\nNo high-value transactions reported")

        output.append("\n" + "=" * 100)
        output.append("END OF STATEMENT")
        output.append("=" * 100)
        output.append(
            "\nNote: This is a system-generated statement and does not require signature."
        )
        output.append(f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}")

        return "\n".join(output)

    def _get_section_description(self, section: str) -> str:
        """Get description for TDS section"""
        descriptions = {
            "192": "Salary",
            "193": "Interest on securities",
            "194": "Dividend",
            "194A": "Interest other than securities",
            "194B": "Winnings from lottery/crossword",
            "194C": "Payment to contractors",
            "194D": "Insurance commission",
            "194H": "Commission/brokerage",
            "194I": "Rent",
            "194J": "Professional/technical services",
        }
        return descriptions.get(section, "Other")

    def _get_assessment_year(self, financial_year: str) -> str:
        """Convert financial year to assessment year (next year)"""
        # "2024-25" -> "2025-26"
        start_year = int(financial_year.split("-")[0])
        return f"{start_year + 1}-{str(start_year + 2)[-2:]}"

    def _get_financial_year(self, txn_date: date) -> str:
        """Determine financial year from date"""
        if txn_date.month >= 4:  # April to March
            return f"{txn_date.year}-{str(txn_date.year + 1)[-2:]}"
        else:
            return f"{txn_date.year - 1}-{str(txn_date.year)[-2:]}"

    def export_to_file(self, financial_year: str, filename: Optional[str] = None):
        """Export Form 26AS to text file"""
        if filename is None:
            filename = f"Form26AS_{self.pan}_{financial_year.replace('-', '_')}.txt"

        statement = self.generate_statement(financial_year)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(statement)

        print(f"✓ Form 26AS exported to: {filename}")
        return filename

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "pan": self.pan,
            "name": self.name,
            "address": self.address,
            "tdsEntries": [
                {
                    "deductorName": e.deductor_name,
                    "deductorTan": e.deductor_tan,
                    "amountPaid": e.amount_paid,
                    "tdsDeducted": e.tds_deducted,
                    "dateOfDeduction": e.date_of_deduction.isoformat(),
                    "dateOfDeposit": e.date_of_deposit.isoformat(),
                    "financialYear": e.financial_year,
                    "quarter": e.quarter,
                    "section": e.section,
                }
                for e in self.tds_entries
            ],
            "advanceTaxEntries": [
                {
                    "amount": e.amount,
                    "dateOfPayment": e.date_of_payment.isoformat(),
                    "bsrCode": e.bsr_code,
                    "challanNumber": e.challan_number,
                    "financialYear": e.financial_year,
                }
                for e in self.advance_tax_entries
            ],
            "refundEntries": [
                {
                    "amount": e.amount,
                    "dateOfRefund": e.date_of_refund.isoformat(),
                    "assessmentYear": e.assessment_year,
                    "mode": e.mode,
                }
                for e in self.refund_entries
            ],
            "highValueTransactions": [
                {
                    "transactionType": t.transaction_type,
                    "amount": t.amount,
                    "date": t.date.isoformat(),
                    "reportingEntity": t.reporting_entity,
                }
                for t in self.high_value_transactions
            ],
        }

    @staticmethod
    def from_dict(data: dict) -> "Form26AS":
        """Deserialize from dictionary"""
        form = Form26AS(pan=data["pan"], name=data["name"], address=data["address"])

        for entry_data in data.get("tdsEntries", []):
            entry = TDSEntry(
                deductor_name=entry_data["deductorName"],
                deductor_tan=entry_data["deductorTan"],
                amount_paid=entry_data["amountPaid"],
                tds_deducted=entry_data["tdsDeducted"],
                date_of_deduction=date.fromisoformat(entry_data["dateOfDeduction"]),
                date_of_deposit=date.fromisoformat(entry_data["dateOfDeposit"]),
                financial_year=entry_data["financialYear"],
                quarter=entry_data["quarter"],
                section=entry_data["section"],
            )
            form.add_tds_entry(entry)

        for entry_data in data.get("advanceTaxEntries", []):
            entry = AdvanceTaxEntry(
                amount=entry_data["amount"],
                date_of_payment=date.fromisoformat(entry_data["dateOfPayment"]),
                bsr_code=entry_data["bsrCode"],
                challan_number=entry_data["challanNumber"],
                financial_year=entry_data["financialYear"],
            )
            form.add_advance_tax(entry)

        for entry_data in data.get("refundEntries", []):
            entry = TaxRefundEntry(
                amount=entry_data["amount"],
                date_of_refund=date.fromisoformat(entry_data["dateOfRefund"]),
                assessment_year=entry_data["assessmentYear"],
                mode=entry_data["mode"],
            )
            form.add_refund(entry)

        for txn_data in data.get("highValueTransactions", []):
            txn = HighValueTransaction(
                transaction_type=txn_data["transactionType"],
                amount=txn_data["amount"],
                date=date.fromisoformat(txn_data["date"]),
                reporting_entity=txn_data["reportingEntity"],
            )
            form.add_high_value_transaction(txn)

        return form
