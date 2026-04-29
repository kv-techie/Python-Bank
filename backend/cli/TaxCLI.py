from datetime import date
import os
from typing import Dict, Any

from ..Customer import Customer
from ..Account import Account
from ..TaxDeductionAnalyzer import TaxDeductionAnalyzer
from ..TaxExemption import DeductionType, DeductionStatus, TaxExemption
from ..ITRFiling import ITRFiling, ITRStatus
from ..Logger import BankLogger
from ..TaxCalculator import TaxCalculator
from ..SalaryProfile import SalaryProfile


class TaxCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.tax_service = app.tax_service
        self.logger = BankLogger.get_logger("TaxCLI")

    def tax_planning_menu(self, customer: Customer, account: Account):
        """Tax Planning & Exemptions Menu"""
        managing = True
        while managing:
            print("\n" + "=" * 60)
            print("TAX PLANNING & EXEMPTIONS [STATS]")
            print("=" * 60)
            print(f"Customer: {customer.first_name} {customer.last_name}")
            print(
                f"Monthly Gross Salary: Rs. {account.salary_profile.gross_salary:,.2f}"
                if account.salary_profile
                else "Salary Profile: Not Set"
            )
            print(f"Current Tax Regime: {customer.tax_regime}")
            pan_status = (
                f"PAN: {customer.pan}"
                if hasattr(customer, "pan") and customer.pan
                else "PAN: [FAIL] Not Registered"
            )
            print(f"{pan_status}")
            print("\n1. View Deduction Summary")
            print("2. View Tax Summary (With vs Without Deductions)")
            print("3. Upload Deduction Proof")
            print("4. Declare Additional Deductions")
            print("5. Register/Update PAN")
            print("6. File Annual ITR & Get Refund")
            print("7. View ITR Filing History & Process Refunds")
            print("8. Compare Tax Regimes (Old vs New)")
            print("9. Back to Main Menu")

            choice = self.app.read_valid_choice(
                "Enter choice: ", ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
            )

            if choice == "1":
                self.view_deductions_summary(customer, account)
            elif choice == "2":
                self.view_tax_summary(customer, account)
            elif choice == "3":
                self.upload_deduction_document(customer, account)
            elif choice == "4":
                self.declare_additional_deductions(customer, account)
            elif choice == "5":
                self.register_pan_menu(customer)
            elif choice == "6":
                self.file_itr_menu(customer, account)
            elif choice == "7":
                self.view_itr_filing_history_menu(customer, account)
            elif choice == "8":
                self.compare_tax_regimes(customer, account)
            elif choice == "9":
                managing = False

    def view_deductions_summary(self, customer: Customer, account: Account):
        """Display auto-detected and self-declared deductions with detailed breakdown"""
        self.logger.info(f"Viewing tax deductions summary for Customer {customer.customer_id}")
        print("\n" + "=" * 70)
        print("DEDUCTION SUMMARY - DETAILED BREAKDOWN")
        print("=" * 70)

        if not account.salary_profile:
            print("[FAIL] No salary profile found. Cannot calculate deductions.")
            input("\nPress Enter to continue...")
            return

        # Determine if metro city
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        annual_salary = account.salary_profile.gross_salary * 12

        # Get all deductions
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        if not deductions:
            print("[SUCCESS] No deductions detected.")
        else:
            print("\n" + "=" * 70)
            print("AUTO-DETECTED DEDUCTIONS")
            print("=" * 70)

            # Section 16 - Standard Deduction
            if "16" in deductions:
                print("\n📌 SECTION 16 - STANDARD DEDUCTION")
                print(f"   Amount: Rs. {deductions['16']:>12,.2f}")
                print("   Limit:  Rs. 50,000 (Fixed - Automatic)")
                print("   Source: Standard deduction for salaried individuals")

            # Section 10(13A) - HRA
            if "10(13A)" in deductions:
                print("\n📌 SECTION 10(13A) - HOUSE RENT ALLOWANCE (HRA)")
                print(f"   Amount: Rs. {deductions['10(13A)']:>12,.2f}")
                print("   Limit:  50% of salary (Metro) / 40% (Non-metro)")
                print(
                    "   Sources: Rent transactions in bank account, credit cards, recurring bills"
                )
                # Show rent bills if available
                if hasattr(account, "recurring_bills"):
                    rent_bills = [
                        b
                        for b in account.recurring_bills
                        if "rent" in str(b.name).lower()
                    ]
                    if rent_bills:
                        for bill in rent_bills[:2]:
                            bill_amount = (
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                            print(
                                f"             ├─ {bill.name}: Rs. {bill_amount:,.2f}/month"
                            )

            # Section 80C - Savings/Investments
            if "80C" in deductions:
                print(
                    "\n📌 SECTION 80C - SAVINGS & INVESTMENTS (EPF/Insurance/Home Loan Principal)"
                )
                print(f"   Amount: Rs. {deductions['80C']:>12,.2f}")
                print("   Limit:  Rs. 1,50,000")
                # Show EPF if available
                if hasattr(account.salary_profile, "epf_contribution"):
                    epf_annual = account.salary_profile.epf_contribution * 12
                    print(f"   Sources: EPF Contribution: Rs. {epf_annual:,.2f}/year")
                else:
                    print(
                        "   Sources: Employee Provident Fund (EPF), Life Insurance, Home Loan Principal"
                    )

            # Section 80D - Medical Insurance
            if "80D" in deductions:
                print("\n📌 SECTION 80D - MEDICAL INSURANCE")
                print(f"   Amount: Rs. {deductions['80D']:>12,.2f}")
                print("   Limit:  Rs. 50,000")
                print(
                    "   Sources: Insurance premium payments from bank transactions, credit cards, or recurring bills"
                )
                # Show insurance bills if available
                if hasattr(account, "recurring_bills"):
                    insurance_bills = [
                        b
                        for b in account.recurring_bills
                        if "insurance" in str(b.name).lower()
                        or "premium" in str(b.name).lower()
                    ]
                    if insurance_bills:
                        for bill in insurance_bills[:2]:
                            bill_amount = (
                                bill.amount
                                if hasattr(bill, "amount")
                                else bill.base_amount
                                if hasattr(bill, "base_amount")
                                else 0
                            )
                            print(
                                f"             ├─ {bill.name}: Rs. {bill_amount:,.2f}/month"
                            )

            # Section 24 - Home Loan Interest
            if "24" in deductions:
                print("\n📌 SECTION 24 - HOME LOAN INTEREST")
                print(f"   Amount: Rs. {deductions['24']:>12,.2f}")
                print("   Limit:  Rs. 2,00,000")
                print("   Sources: Interest on home loans")
                # Show home loans if available
                if hasattr(customer, "loans"):
                    home_loans = [
                        l
                        for l in customer.loans
                        if hasattr(l, "loan_type")
                        and "HOME" in str(l.loan_type).upper()
                    ]
                    if home_loans:
                        for loan in home_loans:
                            loan_amount = (
                                loan.principal if hasattr(loan, "principal") else 0
                            )
                            loan_rate = (
                                loan.interest_rate
                                if hasattr(loan, "interest_rate")
                                else 0
                            )
                            interest_annual = (loan_amount * loan_rate) / 100
                            print(
                                f"             ├─ Home Loan: Rs. {interest_annual:,.2f}/year @ {loan_rate}%"
                            )

            total_deductions = sum(deductions.values())
            print("\n" + "=" * 70)
            print(f"TOTAL ANNUAL DEDUCTIONS: Rs. {total_deductions:,.2f}")
            print("=" * 70)

        # Show stored deductions with status
        if customer.tax_deductions:
            print("\n\n" + "=" * 70)
            print("SELF-DECLARED DEDUCTIONS")
            print("=" * 70)
            for exemption in customer.tax_deductions:
                status_emoji = (
                    "[OK]"
                    if exemption.status.value == "VERIFIED"
                    else "?"
                    if exemption.status.value == "AUTO_DETECTED"
                    else "!"
                )
                print(f"\n{status_emoji} {exemption.deduction_type.value}")
                print(f"   Amount: Rs. {exemption.eligible_amount:>12,.2f}")
                print(f"   Status: {exemption.status.value}")
                if exemption.documents:
                    print(f"   Documents: {len(exemption.documents)} attached")

        input("\nPress Enter to continue...")

    def view_tax_summary(self, customer: Customer, account: Account):
        """Display tax calculation with and without deductions"""

        print("\n" + "=" * 60)
        print("TAX SUMMARY")
        print("=" * 60)

        if not account.salary_profile:
            print("[FAIL] No salary profile found. Cannot calculate tax.")
            input("\nPress Enter to continue...")
            return

        # Get salary info
        annual_salary = account.salary_profile.gross_salary * 12

        # Get deductions
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        # Calculate tax with deductions
        if deductions:
            taxable_with_ded, tax_with_ded, rate_with_ded = (
                TaxCalculator.calculate_tax_with_deductions(annual_salary, deductions)
            )
        else:
            taxable_with_ded = tax_with_ded = rate_with_ded = 0

        # Calculate tax without deductions
        tax_without_ded, rate_without_ded = (
            TaxCalculator.calculate_tax_without_deductions(annual_salary)
        )

        # Calculate monthly equivalents
        monthly_salary = account.salary_profile.gross_salary
        monthly_tax_with_ded = tax_with_ded / 12 if deductions else 0
        monthly_tax_without_ded = tax_without_ded / 12

        print(f"\nGross Annual Salary: Rs. {annual_salary:,.2f}")
        print(f"Gross Monthly Salary: Rs. {monthly_salary:,.2f}")

        print("\n" + "-" * 60)
        print("WITH DEDUCTIONS (Old Regime)")
        print("-" * 60)
        if deductions:
            total_deductions = sum(deductions.values())
            print(f"Total Annual Deductions: Rs. {total_deductions:,.2f}")
            print(f"Taxable Income: Rs. {taxable_with_ded:,.2f}")
            print(f"Tax Rate: {rate_with_ded:.2f}%")
            print(f"Annual Tax Liability: Rs. {tax_with_ded:,.2f}")
            print(f"Monthly Tax Deduction: Rs. {monthly_tax_with_ded:,.2f}")
        else:
            print("No deductions available")

        print("\n" + "-" * 60)
        print("WITHOUT DEDUCTIONS (New Regime)")
        print("-" * 60)
        print(f"Taxable Income: Rs. {annual_salary:,.2f}")
        print(f"Tax Rate: {rate_without_ded:.2f}%")
        print(f"Annual Tax Liability: Rs. {tax_without_ded:,.2f}")
        print(f"Monthly Tax Deduction: Rs. {monthly_tax_without_ded:,.2f}")

        # Calculate savings
        if deductions:
            tax_savings = tax_without_ded - tax_with_ded
            monthly_savings = tax_savings / 12
            savings_percent = (
                (tax_savings / tax_without_ded * 100) if tax_without_ded > 0 else 0
            )

            print("\n" + "-" * 60)
            print("TAX SAVINGS WITH DEDUCTIONS")
            print("-" * 60)
            print(f"Annual Savings: Rs. {tax_savings:,.2f}")
            print(f"Monthly Savings: Rs. {monthly_savings:,.2f}")
            print(f"Savings %: {savings_percent:.2f}%")

        input("\nPress Enter to continue...")

    def upload_deduction_document(self, customer: Customer, account: Account):
        """Upload proof for deductions (for simulation)"""
        print("\n" + "=" * 60)
        print("UPLOAD DEDUCTION PROOF")
        print("=" * 60)

        if not customer.tax_deductions:
            print("[FAIL] No deductions found to upload proof for.")
            print(
                "💡 Tip: Declare some deductions first (Option 4 in Tax Planning Menu)"
            )
            input("\nPress Enter to continue...")
            return

        print("\nSelect deduction to upload proof for:")
        for i, exemption in enumerate(customer.tax_deductions, 1):
            status_emoji = "[OK]" if exemption.status == "VERIFIED" else "?"
            print(
                f"  {i}. {status_emoji} {exemption.deduction_type.value} - Rs. {exemption.eligible_amount:,.2f}"
            )

        try:
            choice = int(input(f"\nEnter number (1-{len(customer.tax_deductions)}): "))
            if 1 <= choice <= len(customer.tax_deductions):
                selected = customer.tax_deductions[choice - 1]

                # Get document details
                doc_type = input(
                    "\nDocument Type (e.g., 'Form 12BA', 'Insurance Receipt', 'Bank Statement'): "
                ).strip()
                file_path = input(
                    "Virtual File Path (for simulation, e.g., '/docs/rent_agreement.pdf'): "
                ).strip()

                if doc_type and file_path:
                    # Add document to exemption
                    selected.add_document(doc_type, file_path)

                    # Mark as verified after upload
                    selected.status = "VERIFIED"

                    print("\n[SUCCESS] Document uploaded successfully!")
                    print(f"   Document: {doc_type}")
                    print(f"   Path: {file_path}")
                    print(f"   Status: {selected.status}")
                    print("\n[INFO] Deduction marked as VERIFIED")
                else:
                    print("[FAIL] Invalid input. Please try again.")
            else:
                print("[FAIL] Invalid choice.")
        except ValueError:
            print("[FAIL] Please enter a valid number.")

        input("\nPress Enter to continue...")

    def declare_additional_deductions(self, customer: Customer, account: Account):
        """Allow user to manually declare deductions"""
        print("\n" + "=" * 60)
        print("DECLARE ADDITIONAL DEDUCTIONS")
        print("=" * 60)

        print("\nSelect deduction type:")
        print("1. Section 80C (Investments) - Max Rs. 1,50,000")
        print("2. Section 80D (Medical Insurance) - Max Rs. 50,000")
        print("3. Section 24 (Home Loan Interest) - Max Rs. 2,00,000")
        print("4. Cancel")

        choice = input("\nEnter choice: ").strip()

        if choice == "4":
            return

        try:
            amount = float(input("\nEnter amount: Rs. "))
            doc_type = input(
                "Document Type (e.g., 'Insurance Certificate', 'Bank Statement'): "
            ).strip()

            if choice == "1":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_80C,
                    amount=amount,
                    section="80C",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=150000,
                )
                deduction.eligible_amount = min(amount, 150000)
            elif choice == "2":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_80D,
                    amount=amount,
                    section="80D",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=50000,
                )
                deduction.eligible_amount = min(amount, 50000)
            elif choice == "3":
                deduction = TaxExemption(
                    deduction_type=DeductionType.SECTION_24_HOME_LOAN_INTEREST,
                    amount=amount,
                    section="24",
                    status=DeductionStatus.SELF_DECLARED,
                    declared_date=date.today(),
                    annual_limit=200000,
                )
                deduction.eligible_amount = min(amount, 200000)
            else:
                print("[FAIL] Invalid choice.")
                return

            # Add document if provided
            if doc_type:
                file_path = input("Virtual File Path (for simulation): ").strip()
                if file_path:
                    deduction.add_document(doc_type, file_path)

            # Add to customer's tax deductions via helper method
            self.tax_service.add_tax_exemption(customer, deduction)

            print("\n[SUCCESS] Deduction declared successfully!")
            print(f"   Amount: Rs. {deduction.eligible_amount:,.2f}")
            print(f"   Status: {deduction.status.value}")
            print(f"   Documents: {len(deduction.documents)} attached")

        except ValueError:
            print("[FAIL] Invalid input. Please enter a valid number.")

        input("\nPress Enter to continue...")

    def register_pan_menu(self, customer: Customer):
        """Register or update PAN for tax filing"""
        print("\n" + "=" * 70)
        print("REGISTER/UPDATE PAN")
        print("=" * 70)

        current_pan = (
            customer.pan if hasattr(customer, "pan") and customer.pan else None
        )

        if current_pan:
            print(f"Current PAN: {current_pan}")
        else:
            print("No PAN registered yet.")

        print("\n1. Register New PAN")
        print("2. Update Existing PAN")
        print("3. Back")

        choice = self.app.read_valid_choice("Enter choice: ", ["1", "2", "3"])

        if choice == "3":
            return

        pan = input("\nEnter 10-character PAN (e.g., ABCDE1234F): ").strip().upper()

        # Validate PAN format (2 letters + 5 digits + 1 letter + 1 digit + 1 letter)
        if not self.tax_service.validate_pan(pan):
            print(
                "[FAIL] Invalid PAN format. PAN should be 10 characters: 2 letters, 5 digits, 1 letter, 1 digit, 1 letter"
            )
            input("\nPress Enter to continue...")
            return

        # Check if PAN already exists in system (optional validation)
        customer.pan = pan
        self.bank.save()

        print(f"\n[SUCCESS] PAN {pan} registered successfully!")
        print("You can now file your ITR.")

        input("\nPress Enter to continue...")

    def file_itr_menu(self, customer: Customer, account: Account):
        """File ITR and process refunds"""
        print("\n" + "=" * 70)
        print("FILE ANNUAL INCOME TAX RETURN (ITR)")
        print("=" * 70)

        if not account.salary_profile:
            print("[FAIL] Salary profile not configured. Cannot file ITR.")
            input("\nPress Enter to continue...")
            return

        if not hasattr(customer, "pan") or not customer.pan:
            print("[FAIL] PAN not registered. Cannot file ITR.")
            input("\nPress Enter to continue...")
            return

        # Check for existing ITR filing
        current_fy = ITRFiling.calculate_financial_year()
        existing_filings = ITRFiling.get_filing_history(account)

        # Check for any active (non-AMENDED) filing for current FY
        active_fy_filing = [
            f
            for f in existing_filings
            if f.financial_year == current_fy
            and f.status.value
            != "Amended"  # Allow re-filing only if previous was AMENDED
        ]

        if active_fy_filing:
            existing = active_fy_filing[0]
            print(f"\n[WARN]  WARNING: You already have an ITR filing for FY {current_fy}")
            print(f"   Filed Date: {existing.filed_date.strftime('%d-%b-%Y')}")
            print(
                f"   Status: {ITRFiling.get_status_icon(existing.status)} {existing.status.value}"
            )
            print(f"   Acknowledgment: {existing.ack_number}")

            if existing.refund_amount > 0:
                print(f"   Refund: Rs. {existing.refund_amount:,.2f}")
            else:
                tax_due = existing.tax_liability - existing.tds_paid
                print(f"   Tax Due: Rs. {tax_due:,.2f}")

            print(
                "\n[WARN]  You CANNOT file another ITR for the same financial year unless:"
            )
            print("   1. You formally AMEND the filing with corrected information")

            amend_choice = (
                input("\nDo you want to AMEND the existing filing? (yes/no): ")
                .strip()
                .lower()
            )

            if amend_choice in ["yes", "y"]:
                print(f"\n[SUCCESS] Preparing to amend ITR for FY {current_fy}...")
                print("[WARN]  The previous filing will be marked as AMENDED.")

                if existing.status.value == "Refund Credited":
                    print(
                        "[WARN]  Note: Refund has already been credited. Amendment will require new calculation."
                    )

                confirm = input("Proceed with amendment? (yes/no): ").strip().lower()

                if confirm in ["yes", "y"]:
                    ITRFiling.void_filing(account, current_fy)
                    print("[SUCCESS] Previous ITR filing marked as AMENDED.")
                else:
                    print("Amendment cancelled.")
                    input("\nPress Enter to continue...")
                    return
            else:
                print(
                    "\n[FAIL] Cannot file new ITR. Existing filing must be amended first."
                )
                input("\nPress Enter to continue...")
                return

        # File ITR
        success, filing_record, message = ITRFiling.file_itr(
            account,
            f"{customer.first_name} {customer.last_name}",
            customer.pan,
            customer,
            self.bank,
        )

        if not success:
            print(f"[FAIL] {message}")
            input("\nPress Enter to continue...")
            return

        # Display summary
        ITRFiling.display_filing_summary(filing_record)
        print(f"\n{message}")

        # Generate comprehensive report
        self.generate_itr_report(customer, account, filing_record)

        # Store filing record ONLY if not already amended and stored
        if filing_record.status != ITRStatus.AMENDED:
            ITRFiling.store_filing(account, filing_record)
            self.bank.save()
        else:
            # Filing was amended and already stored - return to menu
            print("\n" + "=" * 70)
            input("\nPress Enter to continue...")
            return

        # Process refund if applicable (only if not amended)
        if filing_record.refund_amount > 0:
            print("\n" + "-" * 70)
            process = input("\nProcess refund now? (yes/no): ").strip().lower()

            if process in ["yes", "y"]:
                success, refund_msg = ITRFiling.process_refund(
                    account, filing_record, self.bank
                )

                if success:
                    print(f"\n{refund_msg}")
                else:
                    print(f"\n[FAIL] {refund_msg}")

        # View filing history
        print("\n" + "-" * 70)
        view_history = input("\nView ITR filing history? (yes/no): ").strip().lower()

        if view_history in ["yes", "y"]:
            filings = ITRFiling.get_filing_history(account)
            if not filings:
                print("\n[INFO] No ITR filings yet")
            else:
                print("\n[INFO] ITR FILING HISTORY")
                print("=" * 70)
                for idx, filing in enumerate(filings, 1):
                    status_icon = {
                        "Filed - Pending": "⏳",
                        "Refund Credited": "[SUCCESS]",
                        "Tax Paid": "💳",
                        "Amended": "📝",
                    }.get(filing.status.value, "❓")

                    print(
                        f"{idx}. FY {filing.financial_year} - {status_icon} {filing.status.value}"
                    )
                    print(
                        f"   Refund: Rs. {filing.refund_amount:,.2f} | Filed: {filing.filed_date.strftime('%d-%b-%Y')}"
                    )

        input("\nPress Enter to continue...")

    def view_itr_filing_history_menu(self, customer: Customer, account: Account):
        """View ITR filing history and process pending refunds"""
        print("\n" + "=" * 70)
        print("[INFO] ITR FILING HISTORY & REFUND PROCESSING")
        print("=" * 70)

        filings = ITRFiling.get_filing_history(account)

        if not filings:
            print("\n[FAIL] No ITR filings found.")
            print("   File your first ITR using option 6 from the Tax Planning menu.")
            input("\nPress Enter to continue...")
            return

        # Display all filings
        print(f"\nTotal Filings: {len(filings)}")
        print("=" * 70)

        pending_refunds = []

        for idx, filing in enumerate(filings, 1):
            status_icon = ITRFiling.get_status_icon(filing.status)

            print(f"\n{idx}. FINANCIAL YEAR {filing.financial_year}")
            print(f"   Status: {status_icon} {filing.status.value}")
            print(f"   Filed Date: {filing.filed_date.strftime('%d-%b-%Y')}")
            print(f"   Acknowledgment: {filing.ack_number}")
            print(f"   Gross Income: Rs. {filing.gross_income:,.2f}")
            print(f"   Tax Liability: Rs. {filing.tax_liability:,.2f}")
            print(f"   TDS Paid: Rs. {filing.tds_paid:,.2f}")

            if filing.refund_amount > 0:
                print(f"   [MONEY] Refund Amount: Rs. {filing.refund_amount:,.2f}")

                # Check if refund is pending
                if (
                    filing.status == ITRStatus.FILED_PENDING
                    and not filing.refund_credited
                ):
                    pending_refunds.append((idx, filing))
                    print("   🔔 ACTION REQUIRED: Refund is pending!")
                elif filing.refund_credited and filing.refund_date:
                    print(
                        f"   [SUCCESS] Refund Credited on: {filing.refund_date.strftime('%d-%b-%Y')}"
                    )
            else:
                tax_due = filing.tax_liability - filing.tds_paid
                print(f"   [WARN]  Tax Due: Rs. {tax_due:,.2f}")

            print("-" * 70)

        # Process pending refunds
        if pending_refunds:
            print(f"\n🔔 You have {len(pending_refunds)} pending refund(s) to process!")
            print("=" * 70)

            for idx, filing in pending_refunds:
                print(f"• FY {filing.financial_year}: Rs. {filing.refund_amount:,.2f}")

            print("\n")
            process_choice = (
                input("Do you want to process pending refunds now? (yes/no): ")
                .strip()
                .lower()
            )

            if process_choice in ["yes", "y"]:
                for idx, filing in pending_refunds:
                    print(f"\n📝 Processing refund for FY {filing.financial_year}...")

                    success, refund_msg = ITRFiling.process_refund(
                        account, filing, self.bank
                    )

                    if success:
                        print(f"[SUCCESS] {refund_msg}")
                    else:
                        print(f"[FAIL] {refund_msg}")

                # Save updated data
                self.bank.save()
                print("\n[SUCCESS] All pending refunds processed successfully!")
            else:
                print(
                    "\n[WARN]  Refunds not processed. You can process them later from this menu."
                )
        else:
            print("\n[SUCCESS] No pending refunds to process.")
            print("   All filings are either processed or have no refunds due.")

        input("\nPress Enter to continue...")

    def generate_itr_report(self, customer: Customer, account: Account, filing_record):
        """Generate and display comprehensive ITR report"""
        print("\n" + "=" * 70)
        print("[INFO] COMPREHENSIVE ITR FILING REPORT")
        print("=" * 70)

        # Get deductions breakdown
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        # Header Section
        print(f"\n{'TAXPAYER INFORMATION':^70}")
        print("-" * 70)
        print(f"Name:                {customer.first_name} {customer.last_name}")
        print(f"PAN:                 {customer.pan}")
        print(f"Financial Year:      {filing_record.financial_year}")
        print(f"Filing Date:         {filing_record.filed_date.strftime('%d-%b-%Y')}")
        print(f"Acknowledgment #:    {filing_record.ack_number}")

        # Income Section
        print(f"\n{'INCOME BREAKDOWN':^70}")
        print("-" * 70)
        print(f"  Gross Salary:          Rs. {filing_record.gross_income:>15,.2f}")

        # Show gross components
        if account.salary_profile:
            monthly_salary = account.salary_profile.gross_salary
            print(f"    └─ Annual (Rs. {monthly_salary:,.2f} × 12)")

            # Show salary components if available
            if hasattr(account.salary_profile, "basic_salary"):
                print(
                    f"       • Basic Salary:     Rs. {account.salary_profile.basic_salary * 12:,.2f}"
                )
            if hasattr(account.salary_profile, "hra_received"):
                print(
                    f"       • HRA Received:     Rs. {account.salary_profile.hra_received * 12:,.2f}"
                )
            if hasattr(account.salary_profile, "special_allowance"):
                print(
                    f"       • Allowances:       Rs. {account.salary_profile.special_allowance * 12:,.2f}"
                )

        # Deductions Section
        print(f"\n{'DEDUCTIONS SUMMARY':^70}")
        print("-" * 70)

        if deductions:
            deduction_labels = {
                "16": "Section 16 - Standard Deduction",
                "10(13A)": "Section 10(13A) - HRA/Rent",
                "80C": "Section 80C - Savings/EPF",
                "80D": "Section 80D - Medical Insurance",
                "24": "Section 24 - Home Loan Interest",
            }

            for section, amount in sorted(deductions.items()):
                label = deduction_labels.get(section, f"Section {section}")
                print(f"  {label:<45} Rs. {amount:>15,.2f}")

        print(f"  {'-' * 45} {'-' * 17}")
        print(f"  {'Total Deductions':<45} Rs. {filing_record.total_deductions:>15,.2f}")

        # Tax Calculation Section
        print(f"\n{'TAX CALCULATION':^70}")
        print("-" * 70)
        print(f"  Gross Income (A):      Rs. {filing_record.gross_income:>15,.2f}")
        print(f"  Less: Deductions (B):  Rs. {filing_record.total_deductions:>15,.2f}")
        print(f"  {'-' * 45} {'-' * 17}")
        print(f"  Taxable Income (A-B):  Rs. {filing_record.taxable_income:>15,.2f}")

        # Calculate tax rate
        if filing_record.taxable_income > 0:
            effective_rate = (
                filing_record.tax_liability / filing_record.taxable_income
            ) * 100
            print(f"\n  Applicable Tax Rate:   {effective_rate:.2f}%")

        print(f"  Tax Liability:         Rs. {filing_record.tax_liability:>15,.2f}")

        # TDS and Refund Section
        print(f"\n{'REFUND CALCULATION':^70}")
        print("-" * 70)
        print(f"  Tax Liability:         Rs. {filing_record.tax_liability:>15,.2f}")
        print(f"  TDS Paid During Year:  Rs. {filing_record.tds_paid:>15,.2f}")
        print(f"  {'-' * 45} {'-' * 17}")

        if filing_record.refund_amount > 0:
            print(f"  [MONEY] REFUND DUE:         Rs. {filing_record.refund_amount:>15,.2f}")
            print("\n  Status: ⏳ Pending (Apply for refund if not auto-credited)")
        else:
            additional_tax = filing_record.tax_liability - filing_record.tds_paid
            print(f"  Additional Tax Owing:  Rs. {additional_tax:>15,.2f}")
            print("\n  Status: [WARN]  No refund due")

        # Summary Section
        print(f"\n{'FILING SUMMARY':^70}")
        print("-" * 70)
        print("[SUCCESS] ITR has been successfully filed with Income Tax Department")
        print(f"[SUCCESS] Acknowledgment receipt: {filing_record.ack_number}")

        # Show next steps
        print(f"\n{'NEXT STEPS':^70}")
        print("-" * 70)
        if filing_record.refund_amount > 0:
            print("1. Track refund status using acknowledgment number")
            print("2. Expected refund processing time: 30-45 days")
            print("3. Refund will be credited to your registered bank account")
        else:
            print("1. Keep this report for your records")
            print(
                "2. If additional tax is due, arrange payment within statutory deadline"
            )
            print("3. Maintain all supporting documents for 5-6 years")

        # AMEND OPTION
        print("\n" + "-" * 70)
        print("⭐ FILING ACTION")
        print("-" * 70)
        amend_now = (
            input("\nDo you want to AMEND this filing? (yes/no): ").strip().lower()
        )

        if amend_now in ["yes", "y"]:
            print(
                f"\n[SUCCESS] Preparing to amend ITR for FY {filing_record.financial_year}..."
            )
            print("[WARN]  This filing will be marked as AMENDED.")
            print("   You can then file a corrected ITR.")

            confirm = input("Proceed with amendment? (yes/no): ").strip().lower()

            if confirm in ["yes", "y"]:
                filing_record.status = ITRStatus.AMENDED
                ITRFiling.store_filing(account, filing_record)
                self.bank.save()
                print("\n[SUCCESS] ITR filing marked as AMENDED.")
                print(
                    "💡 You can now file a corrected ITR by selecting 'File ITR' again."
                )
                return
            else:
                print("Amendment cancelled. Continuing with current filing...")

        # Save report option
        print("\n" + "-" * 70)
        save_option = input("\nGenerate report file? (yes/no): ").strip().lower()

        if save_option in ["yes", "y"]:
            success, result = self.tax_service.save_itr_report_to_file(customer, filing_record, deductions)
            if success:
                print(f"\n[SUCCESS] Official ITR Filing Report (PDF) generated: {result}")
            else:
                print(f"\n[FAIL] {result}")

    def compare_tax_regimes(self, customer: Customer, account: Account):
        """Compare Old vs New tax regimes and allow switching"""
        from ..TaxCalculator import TaxCalculator
        print("\n" + "=" * 60)
        print("COMPARE TAX REGIMES (OLD vs NEW)")
        print("=" * 60)

        if not account.salary_profile:
            print("[FAIL] No salary profile found. Cannot compare regimes.")
            input("\nPress Enter to continue...")
            return

        annual_salary = account.salary_profile.gross_salary * 12
        is_metro = getattr(account.salary_profile, "is_metro_city", True)
        deductions = TaxDeductionAnalyzer.get_all_deductions(
            customer, account.salary_profile, is_metro, self.bank
        )

        # Old Regime Calculation
        taxable_old, tax_old, rate_old = (
            TaxCalculator.calculate_tax_with_deductions(annual_salary, deductions)
        )

        # New Regime Calculation
        tax_new, rate_new = (
            TaxCalculator.calculate_tax_without_deductions(annual_salary)
        )

        print(f"\nGross Annual Salary: Rs. {annual_salary:,.2f}")
        print(f"Current Regime: {customer.tax_regime}")

        print("\n" + "-" * 60)
        print(f"{'METRIC':<25} {'OLD REGIME':<15} {'NEW REGIME':<15}")
        print("-" * 60)
        print(f"{'Taxable Income':<25} Rs. {taxable_old:<14,.2f} Rs. {annual_salary:<14,.2f}")
        print(f"{'Tax Rate':<25} {rate_old:<14.2f}% {rate_new:<14.2f}%")
        print(f"{'Annual Tax':<25} Rs. {tax_old:<14,.2f} Rs. {tax_new:<14,.2f}")
        print("-" * 60)

        diff = abs(tax_old - tax_new)
        if tax_old < tax_new:
            print(f"✅ OLD REGIME is better by Rs. {diff:,.2f} per year")
        elif tax_new < tax_old:
            print(f"✅ NEW REGIME is better by Rs. {diff:,.2f} per year")
        else:
            print("⚖️ Both regimes result in the same tax liability")

        print("\n" + "=" * 60)
        print("SWITCH REGIME")
        print("=" * 60)

        if customer.tax_regime == "NEW_REGIME":
            switch_choice = (
                input("\nSwitch to Old Regime (with deductions)? (yes/no): ")
                .strip()
                .lower()
            )
            if switch_choice in ["yes", "y"]:
                customer.tax_regime = "OLD_REGIME"
                self.bank.save()
                print("[SUCCESS] Tax regime switched to OLD_REGIME")
        elif customer.tax_regime == "OLD_REGIME":
            switch_choice = (
                input("\nSwitch to New Regime (no deductions)? (yes/no): ")
                .strip()
                .lower()
            )
            if switch_choice in ["yes", "y"]:
                customer.tax_regime = "NEW_REGIME"
                self.bank.save()
                print("[SUCCESS] Tax regime switched to NEW_REGIME")

        input("\nPress Enter to continue...")
    def manage_salary(self, account: Account):
        """Manage salary profile and track income"""
        print("\n=== Salary Management ===")
        if not account.salary_profile:
            print("[INFO] No salary profile found. Create one to enable tax benefits.")
            print("1. Create Salary Profile")
            print("2. Back")
            choice = self.app.read_valid_choice("Select: ", ["1", "2"])
            if choice == "1":
                self.create_salary_profile(account)
            return

        print(f"\nCurrent Salary: Rs. {account.salary_profile.gross_salary:,.2f}/month")
        print(f"Company: {account.salary_profile.company_name}")
        print("\n1. Update Salary")
        print("2. View Tax Projections")
        print("3. Back")
        
        choice = self.app.read_valid_choice("Select: ", ["1", "2", "3"])
        if choice == "1":
            self.update_salary(account)
        elif choice == "2":
            self.tax_planning_menu(self.bank.get_customer_by_id(account.customer_id), account)

    def create_salary_profile(self, account: Account):
        """Interactive flow to create a salary profile"""

        print("\n--- Create Salary Profile ---")
        gross = self.app.read_positive_double("Gross Monthly Salary (Rs.): ")
        company = input("Company Name: ").strip()
        designation = input("Designation: ").strip()
        
        profile = SalaryProfile(gross, company, designation)
        account.salary_profile = profile
        self.bank.save()
        print("[SUCCESS] Salary profile created.")

    def update_salary(self, account: Account):
        """Update existing salary amount"""
        print("\n--- Update Salary ---")
        new_gross = self.app.read_positive_double("New Gross Monthly Salary (Rs.): ")
        account.salary_profile.gross_salary = new_gross
        self.bank.save()
        print("[SUCCESS] Salary updated.")
