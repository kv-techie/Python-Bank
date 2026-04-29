"""
Tax Deduction Analyzer
Automatically detects and calculates eligible tax deductions from transactions and existing data
"""

from datetime import datetime
from typing import Dict, Optional, Tuple

from .TaxExemption import DeductionStatus, DeductionType, TaxExemption


class TaxDeductionAnalyzer:
    """Analyzes customer data to extract tax deductions"""

    # Standard deduction (fixed)
    STANDARD_DEDUCTION = 50000.0

    # Deduction limits
    DEDUCTION_LIMITS = {
        "80C": 150000.0,  # EPF + Life Insurance + Home Loan Principal
        "80D": 50000.0,  # Medical Insurance
        "24": 200000.0,  # Home Loan Interest
    }

    @staticmethod
    def detect_hra_from_transactions(
        account, monthly_salary: float, is_metro: bool, customer=None
    ) -> Tuple[float, Optional[TaxExemption]]:
        """
        Detect HRA from rent transactions in both account and credit card statements, plus recurring bills
        HRA = MIN(Actual HRA, Rent Paid - 10% of Salary, 50%/40% of Salary)
        Returns: (eligible_amount, TaxExemption object)
        """
        if not hasattr(account, "_load_transactions_if_needed"):
            return 0.0, None

        # Load transactions if needed
        try:
            account._load_transactions_if_needed()
        except (AttributeError, ValueError):
            pass

        # Look for rent transactions in bank account
        rent_transactions = []
        if hasattr(account, "transactions"):
            for txn in account.transactions:
                if hasattr(txn, "metadata") and txn.metadata:
                    metadata_str = str(txn.metadata).lower()
                    if "rent" in metadata_str or "landlord" in metadata_str:
                        rent_transactions.append(txn)
                elif hasattr(txn, "type") and "RENT" in str(txn.type):
                    rent_transactions.append(txn)

        # ALSO scan credit card transactions for rent payments
        if customer and hasattr(customer, "credit_cards"):
            for card in customer.credit_cards:
                if hasattr(card, "transactions"):
                    for txn in card.transactions:
                        # Check category
                        if hasattr(txn, "category"):
                            category_str = str(txn.category).lower()
                            if "rent" in category_str or "housing" in category_str:
                                rent_transactions.append(txn)
                        # Check merchant
                        if hasattr(txn, "merchant"):
                            merchant_str = str(txn.merchant).lower()
                            if (
                                "rent" in merchant_str
                                or "landlord" in merchant_str
                                or "housing" in merchant_str
                            ):
                                rent_transactions.append(txn)

        # ALSO scan recurring bills for rent/housing bills
        if hasattr(account, "recurring_bills"):
            for bill in account.recurring_bills:
                if hasattr(bill, "name"):
                    bill_name_lower = str(bill.name).lower()
                    if "rent" in bill_name_lower or "housing" in bill_name_lower:
                        # Create pseudo-transaction from recurring bill
                        class PseudoTxn:
                            def __init__(self, amount):
                                self.amount = amount

                        rent_transactions.append(
                            PseudoTxn(
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                        )

        if not rent_transactions:
            return 0.0, None

        # Calculate annual rent
        # Assume transactions are recent, try to detect frequency
        annual_rent = 0.0

        # Look for monthly pattern (simple approach)
        monthly_rent_amounts = {}
        for txn in rent_transactions:
            amount = txn.amount if hasattr(txn, "amount") else 0
            if amount > 0:
                # Simplified: assume all rent payments are monthly
                key = f"{amount}"
                monthly_rent_amounts[key] = monthly_rent_amounts.get(key, 0) + 1

        # Take the most frequent amount as monthly rent
        if monthly_rent_amounts:
            monthly_rent = float(
                max(monthly_rent_amounts.keys(), key=lambda x: monthly_rent_amounts[x])
            )
            annual_rent = monthly_rent * 12
        else:
            return 0.0, None

        # Calculate HRA exemption (least of three)
        basic_da = monthly_salary

        option1 = annual_rent  # Actual rent paid
        option2 = max(0, annual_rent - (0.10 * basic_da * 12))  # Rent - 10% of salary
        option3 = (0.50 if is_metro else 0.40) * (basic_da * 12)  # 50/40% of salary

        hra_eligible = min(option1, option2, option3)

        # Create TaxExemption object
        exemption = TaxExemption(
            deduction_type=DeductionType.HRA,
            amount=annual_rent,
            section="10(13A)",
            status=DeductionStatus.AUTO_DETECTED,
            declared_date=datetime.now(),
            auto_detected=True,
            detection_source="TRANSACTION_ANALYSIS",
            annual_limit=None,  # HRA has no fixed limit
        )
        exemption.eligible_amount = hra_eligible

        return hra_eligible, exemption

    @staticmethod
    def detect_insurance_80d_from_transactions(
        account, customer=None
    ) -> Tuple[float, Optional[TaxExemption]]:
        """
        Detect medical insurance premiums from account, credit card transactions, and recurring bills (80D)
        Returns: (eligible_amount capped at ₹50,000, TaxExemption object)
        """
        if not hasattr(account, "_load_transactions_if_needed"):
            return 0.0, None

        # Load transactions if needed
        try:
            account._load_transactions_if_needed()
        except (AttributeError, ValueError):
            pass

        # Look for insurance transactions in bank account
        insurance_transactions = []
        if hasattr(account, "transactions"):
            for txn in account.transactions:
                if hasattr(txn, "type"):
                    if "INSURANCE" in str(txn.type):
                        insurance_transactions.append(txn)
                elif hasattr(txn, "metadata") and txn.metadata:
                    metadata_str = str(txn.metadata).lower()
                    if (
                        "insurance" in metadata_str
                        or "premium" in metadata_str
                        or "health" in metadata_str
                    ):
                        insurance_transactions.append(txn)

        # ALSO scan credit card transactions for insurance payments
        if customer and hasattr(customer, "credit_cards"):
            for card in customer.credit_cards:
                if hasattr(card, "transactions"):
                    for txn in card.transactions:
                        # Check category
                        if hasattr(txn, "category"):
                            category_str = str(txn.category).lower()
                            if (
                                "insurance" in category_str
                                or "health" in category_str
                                or "medical" in category_str
                            ):
                                insurance_transactions.append(txn)
                        # Check merchant
                        if hasattr(txn, "merchant"):
                            merchant_str = str(txn.merchant).lower()
                            if any(
                                keyword in merchant_str
                                for keyword in [
                                    "insurance",
                                    "health",
                                    "mediclaim",
                                    "lic",
                                    "hdfc ergo",
                                    "star health",
                                    "care health",
                                    "bajaj allianz",
                                ]
                            ):
                                insurance_transactions.append(txn)

        # ALSO scan recurring bills for insurance bills
        if hasattr(account, "recurring_bills"):
            for bill in account.recurring_bills:
                if hasattr(bill, "name"):
                    bill_name_lower = str(bill.name).lower()
                    if "insurance" in bill_name_lower or "premium" in bill_name_lower:
                        # Create pseudo-transaction from recurring bill
                        class PseudoTxn:
                            def __init__(self, amount):
                                self.amount = amount

                        insurance_transactions.append(
                            PseudoTxn(
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                        )

        if not insurance_transactions:
            return 0.0, None

        # Calculate annual insurance premium
        annual_premium = sum(
            txn.amount for txn in insurance_transactions if hasattr(txn, "amount")
        )

        # For quarterly transactions, multiply by 4 if only 1 found
        if len(insurance_transactions) == 1:
            annual_premium = insurance_transactions[0].amount * 4  # Assume quarterly

        # Apply 80D limit
        eligible_amount = min(
            annual_premium, TaxDeductionAnalyzer.DEDUCTION_LIMITS["80D"]
        )

        # Create TaxExemption object
        exemption = TaxExemption(
            deduction_type=DeductionType.SECTION_80D,
            amount=annual_premium,
            section="80D",
            status=DeductionStatus.AUTO_DETECTED,
            declared_date=datetime.now(),
            auto_detected=True,
            detection_source="TRANSACTION_ANALYSIS",
            annual_limit=TaxDeductionAnalyzer.DEDUCTION_LIMITS["80D"],
        )

        return eligible_amount, exemption

    @staticmethod
    def detect_80c_from_epf(salary_profile) -> Tuple[float, Optional[TaxExemption]]:
        """
        Detect EPF contribution from salary profile (80C)
        Standard EPF is 12% of basic salary or ₹1,50,000, whichever is lower
        Returns: (eligible_amount capped at ₹1,50,000, TaxExemption object)
        """
        if not salary_profile:
            return 0.0, None

        # Get gross salary
        monthly_salary = (
            salary_profile.gross_salary
            if hasattr(salary_profile, "gross_salary")
            else 0
        )

        # Standard EPF is 12% of basic salary
        # For simplicity, assume basic = gross salary
        annual_epf = monthly_salary * 12 * 0.12

        # Apply 80C limit
        eligible_amount = min(annual_epf, TaxDeductionAnalyzer.DEDUCTION_LIMITS["80C"])

        # Create TaxExemption object
        exemption = TaxExemption(
            deduction_type=DeductionType.SECTION_80C,
            amount=annual_epf,
            section="80C",
            status=DeductionStatus.AUTO_DETECTED,
            declared_date=datetime.now(),
            auto_detected=True,
            detection_source="SALARY_PROFILE",
            annual_limit=TaxDeductionAnalyzer.DEDUCTION_LIMITS["80C"],
            notes="Employee provident fund (EPF) contribution",
        )

        return eligible_amount, exemption

    @staticmethod
    def detect_home_loan_interest_from_loans(
        customer, bank
    ) -> Tuple[float, Optional[TaxExemption]]:
        """
        Detect home loan interest from loan records (Section 24)
        Returns: (eligible_amount capped at ₹2,00,000, TaxExemption object)
        """
        if not bank:
            return 0.0, None

        # Get loans from bank
        loans = bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            return 0.0, None

        total_home_loan_interest = 0.0

        for loan in loans:
            # Check if it's a home loan and active
            if hasattr(loan, "loan_type") and "HOME" in str(loan.loan_type).upper():
                if hasattr(loan, "status") and loan.status != "Active":
                    continue  # Skip closed loans

                # Calculate monthly interest using remaining balance
                if hasattr(loan, "get_remaining_balance") and hasattr(
                    loan, "interest_rate"
                ):
                    remaining_balance = loan.get_remaining_balance()
                    monthly_rate = loan.interest_rate / 100 / 12
                    monthly_interest = remaining_balance * monthly_rate
                    annual_interest = monthly_interest * 12
                    total_home_loan_interest += annual_interest

        # Apply Section 24 limit
        eligible_amount = min(
            total_home_loan_interest, TaxDeductionAnalyzer.DEDUCTION_LIMITS["24"]
        )

        if total_home_loan_interest == 0:
            return 0.0, None

        # Create TaxExemption object
        exemption = TaxExemption(
            deduction_type=DeductionType.SECTION_24_HOME_LOAN_INTEREST,
            amount=total_home_loan_interest,
            section="24",
            status=DeductionStatus.AUTO_DETECTED,
            declared_date=datetime.now(),
            auto_detected=True,
            detection_source="LOAN_RECORDS",
            annual_limit=TaxDeductionAnalyzer.DEDUCTION_LIMITS["24"],
            notes="Home loan interest deduction",
        )

        return eligible_amount, exemption

    @staticmethod
    def add_standard_deduction() -> TaxExemption:
        """
        Add standard deduction (₹50,000 fixed for all salaried employees)
        Returns: TaxExemption object
        """
        exemption = TaxExemption(
            deduction_type=DeductionType.STANDARD_DEDUCTION,
            amount=TaxDeductionAnalyzer.STANDARD_DEDUCTION,
            section="16",
            status=DeductionStatus.AUTO_DETECTED,
            declared_date=datetime.now(),
            auto_detected=True,
            detection_source="STATUTORY",
            annual_limit=TaxDeductionAnalyzer.STANDARD_DEDUCTION,
            notes="Fixed standard deduction for salaried employees",
        )

        return exemption

    @staticmethod
    def get_all_deductions(
        customer, salary_profile, is_metro: bool = False, bank=None
    ) -> Dict[str, float]:
        """
        Get all eligible deductions for a customer
        Returns: Dictionary with section -> eligible_amount mapping
        """
        deductions = {}
        all_exemptions = []

        # Standard Deduction (automatic)
        standard = TaxDeductionAnalyzer.add_standard_deduction()
        all_exemptions.append(standard)
        deductions["16"] = standard.eligible_amount

        # HRA from rent transactions
        account = (
            customer.accounts[0]
            if hasattr(customer, "accounts") and customer.accounts
            else None
        )
        if account and salary_profile:
            hra_amount, hra_exemption = (
                TaxDeductionAnalyzer.detect_hra_from_transactions(
                    account,
                    salary_profile.gross_salary,
                    is_metro,
                    customer,  # Pass customer to scan credit cards
                )
            )
            if hra_exemption:
                all_exemptions.append(hra_exemption)
                deductions["10(13A)"] = hra_amount

        # 80D - Medical Insurance
        if account:
            insurance_amount, insurance_exemption = (
                TaxDeductionAnalyzer.detect_insurance_80d_from_transactions(
                    account, customer
                )
            )  # Pass customer
            if insurance_exemption:
                all_exemptions.append(insurance_exemption)
                deductions["80D"] = insurance_amount

        # 80C - EPF
        if salary_profile:
            epf_amount, epf_exemption = TaxDeductionAnalyzer.detect_80c_from_epf(
                salary_profile
            )
            if epf_exemption:
                all_exemptions.append(epf_exemption)
                deductions["80C"] = epf_amount

        # Section 24 - Home Loan Interest
        if bank:
            home_loan_amount, home_loan_exemption = (
                TaxDeductionAnalyzer.detect_home_loan_interest_from_loans(
                    customer, bank
                )
            )
            if home_loan_exemption:
                all_exemptions.append(home_loan_exemption)
                deductions["24"] = home_loan_amount

        return deductions

    @staticmethod
    def get_deduction_summary(deductions: Dict[str, float]) -> str:
        """
        Get formatted deduction summary
        """
        summary = "\n[STATS] TAX DEDUCTIONS SUMMARY\n"
        summary += "=" * 60 + "\n\n"

        section_names = {
            "16": "Standard Deduction",
            "10(13A)": "HRA - House Rent Allowance",
            "80C": "Section 80C (EPF, Insurance, etc.)",
            "80D": "Section 80D (Medical Insurance)",
            "24": "Section 24 (Home Loan Interest)",
        }

        total = 0.0
        for section, amount in deductions.items():
            if amount > 0:
                name = section_names.get(section, section)
                summary += f"[SUCCESS] {name}\n"
                summary += f"   ₹{amount:,.2f}/year\n\n"
                total += amount

        summary += "=" * 60 + "\n"
        summary += f"TOTAL DEDUCTIONS: ₹{total:,.2f}/year\n"

        return summary
