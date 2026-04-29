"""
ITR Filing System
Processes annual Income Tax Returns, calculates refunds, and credits accounts
Designed for bank simulation with automatic refund processing
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .Account import Account
from .BankClock import BankClock
from .Form26AS import TaxRefundEntry
from .TaxCalculator import TaxCalculator
from .TaxDeductionAnalyzer import TaxDeductionAnalyzer
from .TaxExemption import DeductionStatus, TaxExemption


class ITRStatus(Enum):
    """Status of ITR filing"""

    FILED_PENDING = "Filed - Pending"  # Filed but not yet processed
    REFUND_CREDITED = "Refund Credited"  # Refund has been credited
    TAX_PAID = "Tax Paid"  # Additional tax has been paid
    AMENDED = "Amended"  # Original filing voided, amended version filed


@dataclass
class ITRFilingRecord:
    """ITR filing record for tracking submitted returns"""

    financial_year: str  # "2024-25"
    filed_date: date
    gross_income: float
    total_deductions: float
    taxable_income: float
    tax_liability: float
    tds_paid: float
    refund_amount: float
    refund_credited: bool = False
    refund_date: Optional[date] = None
    ack_number: str = ""  # Receipt acknowledgment
    status: ITRStatus = ITRStatus.FILED_PENDING  # Status of filing

    def to_dict(self) -> dict:
        """Convert ITRFilingRecord to dictionary for serialization"""
        return {
            "financial_year": self.financial_year,
            "filed_date": self.filed_date.isoformat(),
            "gross_income": self.gross_income,
            "total_deductions": self.total_deductions,
            "taxable_income": self.taxable_income,
            "tax_liability": self.tax_liability,
            "tds_paid": self.tds_paid,
            "refund_amount": self.refund_amount,
            "refund_credited": self.refund_credited,
            "refund_date": self.refund_date.isoformat() if self.refund_date else None,
            "ack_number": self.ack_number,
            "status": self.status.value,  # Store the string value of enum
        }

    @staticmethod
    def from_dict(data: dict) -> "ITRFilingRecord":
        """Create ITRFilingRecord from dictionary"""
        from datetime import date

        # Parse dates
        filed_date = date.fromisoformat(data["filed_date"])
        refund_date = (
            date.fromisoformat(data["refund_date"]) if data.get("refund_date") else None
        )

        # Parse status enum
        status_value = data.get("status", "Filed - Pending")
        status = ITRStatus.FILED_PENDING
        for s in ITRStatus:
            if s.value == status_value:
                status = s
                break

        return ITRFilingRecord(
            financial_year=data["financial_year"],
            filed_date=filed_date,
            gross_income=data["gross_income"],
            total_deductions=data["total_deductions"],
            taxable_income=data["taxable_income"],
            tax_liability=data["tax_liability"],
            tds_paid=data["tds_paid"],
            refund_amount=data["refund_amount"],
            refund_credited=data.get("refund_credited", False),
            refund_date=refund_date,
            ack_number=data.get("ack_number", ""),
            status=status,
        )


class ITRFiling:
    """Process ITR filing with automatic refund calculation"""

    @staticmethod
    def calculate_financial_year() -> str:
        """Get current financial year in FY format (e.g., '2025-26')"""
        today = BankClock.today()
        if today.month >= 4:  # April onwards
            return f"{today.year}-{today.year + 1}"
        else:  # Jan-March
            return f"{today.year - 1}-{today.year}"

    @staticmethod
    def get_financial_year_for_period(start_date: date, end_date: date) -> str:
        """Get FY for a given period"""
        if start_date.month >= 4:
            return f"{start_date.year}-{start_date.year + 1}"
        else:
            return f"{start_date.year - 1}-{start_date.year}"

    @staticmethod
    def calculate_annual_tds(account: Account) -> float:
        """
        Calculate total TDS for the financial year (projected for full 12 months)

        Args:
            account: Bank account with salary profile

        Returns:
            Total TDS for full year (monthly tax × 12)
        """
        if not account.salary_profile:
            return 0.0

        # Get monthly tax (TDS per month)
        salary_profile = account.salary_profile
        monthly_tax = salary_profile.calculate_tax()

        # Project for full financial year (12 months)
        total_tds = monthly_tax * 12
        return round(total_tds, 2)

    @staticmethod
    @staticmethod
    def get_applicable_deductions(account: Account) -> Dict[str, float]:
        """
        Collect all applicable deductions for the account
        Filters by status (VERIFIED or AUTO_DETECTED)

        Args:
            account: Bank account to check for deductions

        Returns:
            Dictionary of {section: eligible_amount}
        """
        deductions = {}

        # Check if account stores tax exemptions
        if hasattr(account, "tax_exemptions"):
            for exemption in account.tax_exemptions:
                if isinstance(exemption, TaxExemption):
                    # Only count VERIFIED or AUTO_DETECTED deductions
                    if exemption.status in [
                        DeductionStatus.VERIFIED,
                        DeductionStatus.AUTO_DETECTED,
                    ]:
                        deductions[exemption.section] = exemption.amount

        return deductions

    @staticmethod
    def file_itr(
        account: Account,
        customer_name: str,
        pan: str,
        customer=None,
        bank=None,
    ) -> Tuple[bool, ITRFilingRecord, str]:
        """
        File ITR and process refund if applicable

        Args:
            account: Bank account to file ITR for
            customer_name: Customer full name
            pan: PAN for tax identification
            customer: Customer object (optional, for detailed deduction analysis)
            bank: Bank object (optional, for accessing all customer data)

        Returns:
            (success, filing_record, message)
        """
        if not account.salary_profile:
            return (
                False,
                None,
                "[FAIL] Salary profile not configured. Cannot file ITR.",
            )

        fy = ITRFiling.calculate_financial_year()

        # Step 1: Get gross income (annualized for full FY)
        gross_annual = account.salary_profile.gross_salary * 12

        # Step 2: Get applicable deductions (use comprehensive analyzer if customer provided)
        if customer:
            # Use comprehensive TaxDeductionAnalyzer for full deduction detection
            is_metro = getattr(account.salary_profile, "is_metro_city", True)
            deductions_dict = TaxDeductionAnalyzer.get_all_deductions(
                customer, account.salary_profile, is_metro, bank
            )
        else:
            # Fallback to basic deductions
            deductions_dict = ITRFiling.get_applicable_deductions(account)
        total_deductions = sum(deductions_dict.values())

        # Step 3: Calculate taxable income
        taxable_income = max(0, gross_annual - total_deductions)

        # Step 4: Calculate tax liability
        tax_rate = TaxCalculator._get_tax_rate(taxable_income)
        tax_liability = round(taxable_income * tax_rate, 2)

        # Step 5: Get TDS paid
        tds_paid = ITRFiling.calculate_annual_tds(account)

        # Step 6: Calculate refund
        refund_amount = max(0, tds_paid - tax_liability)

        # Step 7: Create filing record
        today = BankClock.today()
        ack_number = ITRFiling.generate_ack_number(pan, fy)

        filing_record = ITRFilingRecord(
            financial_year=fy,
            filed_date=today,
            gross_income=gross_annual,
            total_deductions=total_deductions,
            taxable_income=taxable_income,
            tax_liability=tax_liability,
            tds_paid=tds_paid,
            refund_amount=refund_amount,
            refund_credited=False,
            ack_number=ack_number,
        )

        message = (
            f"[SUCCESS] ITR filed successfully for FY {fy}\n"
            f"   Acknowledgment: {ack_number}\n"
            f"   Gross Income: ₹{gross_annual:,.2f}\n"
            f"   Deductions: ₹{total_deductions:,.2f}\n"
            f"   Taxable Income: ₹{taxable_income:,.2f}\n"
            f"   Tax Liability: ₹{tax_liability:,.2f}\n"
            f"   TDS Paid: ₹{tds_paid:,.2f}\n"
        )

        if refund_amount > 0:
            message += f"   [MONEY] Refund Due: ₹{refund_amount:,.2f}"
        else:
            message += f"   No refund due (additional tax owing: ₹{tax_liability - tds_paid:,.2f})"

        return (True, filing_record, message)

    @staticmethod
    def process_refund(
        account: Account, filing_record: ITRFilingRecord, bank
    ) -> Tuple[bool, str]:
        """
        Process refund: Credit to account and update Form 26 AS

        Args:
            account: Account to credit refund to
            filing_record: ITR filing record with refund details
            bank: Bank instance for updating records

        Returns:
            (success, message)
        """
        if filing_record.refund_amount <= 0:
            return (
                False,
                "[FAIL] No refund to process (tax liability >= TDS paid)",
            )

        if filing_record.refund_credited:
            return (
                False,
                "[WARN]  Refund already credited for this filing",
            )

        # Process refund
        from .Transaction import Transaction

        today = BankClock.today()
        refund_amount = filing_record.refund_amount

        # Create refund transaction
        new_balance = account.balance + refund_amount
        txn = Transaction(
            type="SALARY_TAX_REFUND",
            amount=refund_amount,
            resulting_balance=new_balance,
            category="REFUND",
            metadata={
                "itr_fy": filing_record.financial_year,
                "itr_ack_number": filing_record.ack_number,
                "tax_liability": filing_record.tax_liability,
                "tds_paid": filing_record.tds_paid,
                "status": "PROCESSED",
            },
        )

        # Credit to account (direct balance update + transaction record)
        account.balance += refund_amount
        account.transactions.append(txn)

        # Log transaction to CSV for persistence
        from .DataStore import DataStore

        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=account.username,
            account_number=account.account_number,
            action="SALARY_TAX_REFUND",
            amount=refund_amount,
            resulting_balance=new_balance,
            txn_id=txn.id,
            metadata=f"itr_fy={filing_record.financial_year};ack={filing_record.ack_number}",
        )

        # Update filing record
        filing_record.refund_credited = True
        filing_record.refund_date = today
        filing_record.status = ITRStatus.REFUND_CREDITED

        # Save changes
        bank.save()

        # Update Form 26AS if available
        if hasattr(account, "form_26as") and account.form_26as:
            refund_entry = TaxRefundEntry(
                amount=refund_amount,
                date_of_refund=today,
                assessment_year=filing_record.financial_year.split("-")[0],
                mode="Direct credit to bank account",
            )
            account.form_26as.add_refund(refund_entry)

        message = (
            f"[SUCCESS] Refund processed!\n"
            f"   Amount: ₹{refund_amount:,.2f}\n"
            f"   Credited to: {account.account_number}\n"
            f"   Date: {today.strftime('%d-%b-%Y')}\n"
            f"   New Balance: ₹{account.balance:,.2f}"
        )

        return (True, message)

    @staticmethod
    def generate_ack_number(pan: str, financial_year: str) -> str:
        """Generate ITR acknowledgment number"""
        # Format: ITR-ACK-PAN-FY-DATETIME
        fy_code = financial_year.replace("-", "")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ITR-{fy_code}-{pan[-4:]}-{timestamp}"

    @staticmethod
    def void_filing(account: Account, financial_year: str) -> bool:
        """
        Mark an ITR filing as AMENDED (void the old one)

        Args:
            account: Bank account
            financial_year: FY to void (e.g., '2025-26')

        Returns:
            True if filing was marked as amended, False if not found
        """
        if not hasattr(account, "itr_filings"):
            return False

        for filing in account.itr_filings:
            if (
                filing.financial_year == financial_year
                and filing.status == ITRStatus.FILED_PENDING
            ):
                filing.status = ITRStatus.AMENDED
                return True

        return False

    @staticmethod
    def get_filing_history(account: Account) -> List[ITRFilingRecord]:
        """Get all ITR filings for an account"""
        if not hasattr(account, "itr_filings"):
            account.itr_filings = []
        return account.itr_filings

    @staticmethod
    def store_filing(account: Account, filing_record: ITRFilingRecord):
        """Store ITR filing record in account"""
        if not hasattr(account, "itr_filings"):
            account.itr_filings = []
        account.itr_filings.append(filing_record)

    @staticmethod
    def get_status_icon(status: ITRStatus) -> str:
        """
        Get display icon for ITR status

        Args:
            status: ITRStatus enum value

        Returns:
            Icon string for the status
        """
        status_icons = {
            "Filed - Pending": "⏳",
            "Refund Credited": "[SUCCESS]",
            "Tax Paid": "💳",
            "Amended": "📝",
        }
        return status_icons.get(status.value, "❓")

    @staticmethod
    def display_filing_summary(filing_record: ITRFilingRecord):
        """Display ITR filing summary"""
        print("\n" + "=" * 70)
        print("INCOME TAX RETURN (ITR) FILING SUMMARY")
        print("=" * 70)
        print(f"Financial Year: {filing_record.financial_year}")
        print(f"Filed Date: {filing_record.filed_date.strftime('%d-%b-%Y')}")
        print(f"Acknowledgment: {filing_record.ack_number}")

        print(f"\n{'INCOME DETAILS':<40}")
        print("-" * 70)
        print(f"{'Gross Annual Income':<40} ₹{filing_record.gross_income:>15,.2f}")
        print(
            f"{'Less: Total Deductions':<40} ₹{filing_record.total_deductions:>15,.2f}"
        )
        print("-" * 70)
        print(f"{'Taxable Income':<40} ₹{filing_record.taxable_income:>15,.2f}")

        print(f"\n{'TAX COMPUTATION':<40}")
        print("-" * 70)
        tax_rate = (
            filing_record.tax_liability / filing_record.taxable_income * 100
            if filing_record.taxable_income > 0
            else 0
        )
        print(
            f"{'Tax Liable @ {:.0f}%':<40} ₹{filing_record.tax_liability:>15,.2f}".format(
                tax_rate
            )
        )
        print(f"{'Less: TDS Paid':<40} ₹{filing_record.tds_paid:>15,.2f}")
        print("-" * 70)

        if filing_record.refund_amount > 0:
            print(f"{'[MONEY] Refund Due':<40} ₹{filing_record.refund_amount:>15,.2f}")
        else:
            balance_due = filing_record.tax_liability - filing_record.tds_paid
            print(f"{'[WARN]  Tax Due':<40} ₹{balance_due:>15,.2f}")

        # Display filing status
        status_icon = ITRFiling.get_status_icon(filing_record.status)

        print(f"\n{'Filing Status':<40} {status_icon} {filing_record.status.value}")

        if (
            filing_record.status.value == "Refund Credited"
            and filing_record.refund_date
        ):
            print(
                f"{'Credited Date':<40} {filing_record.refund_date.strftime('%d-%b-%Y')}"
            )

        print("=" * 70)
