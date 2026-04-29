from datetime import datetime, timedelta

from typing import List, Optional

from ..Customer import Customer
from ..Account import Account
from ..Logger import BankLogger
from ..BankClock import BankClock
from ..DataStore import DataStore
from ..Transaction import Transaction
from ..CIBIL import add_credit_inquiry, calculate_cibil_score
from ..LoanNachMandate import LoanNachMandateManager, NachMandateStatus
from ..StatementGenerator import StatementGenerator


class LoanCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.logger = BankLogger.get_logger("LoanCLI")

    def loan_menu(self, customer: Customer, account: Account):
        # Check for loans that might need type update (large loans likely to be home loans)
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        # Consider loans over 10 lakhs as potentially home loans
        loans_needing_type = [
            loan
            for loan in loans
            if getattr(loan, "loan_type", "PERSONAL") == "PERSONAL"
            and loan.status == "Active"
            and loan.principal >= 1000000  # 10 lakhs or more
        ]

        if loans_needing_type:
            print("\n" + "[WARN]" * 30)
            print("[WARN]  IMPORTANT: LOAN TYPE UPDATE RECOMMENDED")
            print("[WARN]" * 30)
            print(
                f"\n[INFO] You have {len(loans_needing_type)} large loan(s) (Rs. 10L+) marked as PERSONAL."
            )
            print("   If any of these are HOME loans, you can claim tax benefits:")
            print("   • HOME loans: Up to Rs. 2,00,000 interest deduction (Section 24)")

            for loan in loans_needing_type:
                emi = loan.calculate_emi()
                print(
                    f"\n   • Loan {loan.loan_id}: Rs. {loan.principal:,.2f} | EMI: Rs. {emi:,.2f}/month"
                )

            print(
                "\n💡 Tip: Use option 7 (Update Loan Type) to classify your loans correctly."
            )
            input("\nPress Enter to continue...")

        while True:
            print("""
    9  Update Loan Type (for tax deductions)
    10 Download Loan Statement of Account (PDF)
    11 Back to Account Menu
            """)
            choice = self.app.read_valid_choice(
                "Enter choice: ", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
            )
            if choice == "1":
                self.apply_for_loan(customer, account)
            elif choice == "2":
                self.bank.show_loans_for_customer(customer.customer_id)
            elif choice == "3":
                self.pay_loan_emi_flow(customer, account)
            elif choice == "4":
                self.view_cibil_report(customer)
            elif choice == "5":
                self.prepay_loan_early(customer, account)
            elif choice == "6":
                self.generate_loan_closure_certificate(customer, account)
            elif choice == "7":
                self.loan_nach_mandate_menu(customer, account)
            elif choice == "8":
                self.update_loan_type(customer, account)
            elif choice == "9":
                break
            elif choice == "10":
                self.download_loan_statement(customer, account)
            elif choice == "11":
                break

    def update_loan_type(self, customer: Customer, account: Account):
        """Update the loan type for existing loans to enable proper tax deductions"""
        print("\n" + "=" * 60)
        print("UPDATE LOAN TYPE FOR TAX DEDUCTIONS")
        print("=" * 60)
        print("""
    ℹ️  Loan types are important for tax deductions:
       • HOME loans: Interest deduction up to Rs. 2,00,000 (Section 24)
       • PERSONAL loans: No tax benefit
       • CAR loans: No direct tax benefit (business use may qualify)
       • EDUCATION loans: Interest deduction (Section 80E)
        """)

        # Get all loans for customer
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("[FAIL] You have no loans on record.")
            input("\nPress Enter to continue...")
            return

        # Show all loans with their current types
        print("\n[INFO] YOUR LOANS:")
        print("=" * 60)
        for idx, loan in enumerate(loans, 1):
            loan_type = getattr(loan, "loan_type", "PERSONAL")
            emi = loan.calculate_emi()
            remaining = (
                loan.get_remaining_balance()
                if hasattr(loan, "get_remaining_balance")
                else loan.principal
            )

            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Type: {loan_type}")
            print(f"   Principal: Rs. {loan.principal:,.2f}")
            print(f"   Remaining Balance: Rs. {remaining:,.2f}")
            print(f"   EMI: Rs. {emi:,.2f}/month")
            print(f"   Status: {loan.status}")
            print(f"   EMIs Paid: {loan.emis_paid}/{loan.tenure_months}")

        print("\n" + "=" * 60)

        # Select loan to update
        loan_choices = [str(i) for i in range(1, len(loans) + 1)]
        loan_choices.append("0")  # Option to cancel

        choice = self.app.read_valid_choice(
            f"\nSelect loan to update (1-{len(loans)}, 0 to cancel): ", loan_choices
        )

        if choice == "0":
            print("Cancelled.")
            return

        selected_loan = loans[int(choice) - 1]
        current_type = getattr(selected_loan, "loan_type", "PERSONAL")

        print(
            f"\n📌 Selected: Loan {selected_loan.loan_id} (Current Type: {current_type})"
        )
        print("\nSelect New Loan Type:")
        print("1. PERSONAL - Personal loans (no tax benefit)")
        print("2. HOME - Housing/Home loans (Rs. 2L interest deduction)")
        print("3. CAR - Vehicle loans (no direct tax benefit)")
        print("4. EDUCATION - Education loans (interest deduction, no limit)")

        type_choice = self.app.read_valid_choice(
            "\nEnter choice (1-4): ", ["1", "2", "3", "4"]
        )

        loan_type_map = {"1": "PERSONAL", "2": "HOME", "3": "CAR", "4": "EDUCATION"}

        new_type = loan_type_map[type_choice]

        # Update the loan type
        selected_loan.loan_type = new_type

        # Save changes
        self.bank.save()

        print("\n" + "=" * 60)
        print("[SUCCESS] LOAN TYPE UPDATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Previous Type: {current_type}")
        print(f"New Type: {new_type}")

        if new_type == "HOME":
            remaining = (
                selected_loan.get_remaining_balance()
                if hasattr(selected_loan, "get_remaining_balance")
                else selected_loan.principal
            )
            monthly_rate = selected_loan.interest_rate / 100 / 12
            monthly_interest = remaining * monthly_rate
            annual_interest = monthly_interest * 12
            deduction = min(annual_interest, 200000)

            print("\n[MONEY] TAX BENEFIT ESTIMATE (Section 24):")
            print(f"   Annual Interest: Rs. {annual_interest:,.2f}")
            print(f"   Deduction Eligible: Rs. {deduction:,.2f}")
            print(f"   Tax Savings (30% bracket): Rs. {deduction * 0.30:,.2f}/year")

        print("\nℹ️  Tax deductions will now be automatically detected in the")
        print("   Tax Planning & Exemptions menu.")

        input("\nPress Enter to continue...")

    def apply_for_loan(self, customer: Customer, account: Account):
        print("\n=== Loan Application ===")

        # Get salary from account's salary profile if available
        if account.salary_profile:
            customer.salary = account.salary_profile.gross_salary
            print(f"[OK] Salary Profile Found: Rs {customer.salary:,.2f}/month")
        else:
            customer.salary = self.app.read_positive_double(
                "Enter your Net Monthly Salary: "
            )

        if not getattr(customer, "employer_name", None):
            customer.employer_name = input("Enter your Employer Name: ").strip()
        if not getattr(customer, "employer_type", None):
            customer.employer_type = input("Type of Employer [MNC/Govt/Pvt]: ").strip()
        if not getattr(customer, "job_start_date", None):
            customer.job_start_date = self.app.read_date("Job Start Date (YYYY-MM-DD): ")
        if not getattr(customer, "employer_category", None):
            customer.employer_category = (
                input("Employer Category (A/B/C): ").strip().upper()
            )
        if not getattr(customer, "city", None):
            customer.city = input("Working City: ").strip()
        if not getattr(customer, "kyc_completed", None):
            completed = input("Is your KYC complete? (y/n): ").strip().lower()
            customer.kyc_completed = completed == "y"

        # Register hard inquiry for this loan application
        add_credit_inquiry(customer)

        # Automatically calculate CIBIL score based on customer's credit history
        print("\n[SEARCH] Calculating your CIBIL score based on credit history...")
        customer.cibil_score = calculate_cibil_score(customer, self.bank)

        # Determine rating for display
        if customer.cibil_score >= 750:
            rating = "Excellent ⭐⭐⭐⭐⭐"
        elif customer.cibil_score >= 650:
            rating = "Good ⭐⭐⭐⭐"
        elif customer.cibil_score >= 550:
            rating = "Average ⭐⭐⭐"
        else:
            rating = "Poor ⭐⭐"

        print(f"[OK] Your current CIBIL Score: {customer.cibil_score} ({rating})")

        # Ask for loan type
        print("\nSelect Loan Type:")
        print("1. Personal Loan")
        print("2. Home Loan")
        print("3. Car Loan")
        print("4. Education Loan")
        loan_type_choice = self.app.read_valid_choice(
            "Enter choice (1-4): ", ["1", "2", "3", "4"]
        )
        loan_type_map = {"1": "PERSONAL", "2": "HOME", "3": "CAR", "4": "EDUCATION"}
        loan_type = loan_type_map[loan_type_choice]
        print(f"[OK] Loan Type: {loan_type}")

        principal = self.app.read_positive_double("\nEnter principal amount (Rs): ")
        interest_rate = self.app.read_positive_double("Enter annual interest rate (%): ")
        tenure_months = int(self.app.read_positive_double("Enter tenure (months): "))

        approved, loan, msg = self.bank.evaluate_and_add_loan(
            customer, principal, interest_rate, tenure_months, account, loan_type
        )
        if approved:
            print(
                f"\n✔ Loan approved! Amount Rs.{principal:,.2f} credited to your account."
            )
            print(f"Loan ID: {loan.loan_id} | EMI: Rs.{loan.calculate_emi():.2f}/month")
            print(f"Interest Rate: {loan.interest_rate:.2f}% p.a.")
        else:
            print(f"\n[FAIL] Loan denied: {msg}")

    def pay_loan_emi_flow(self, customer: Customer, account: Account):
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("You have no loans to pay.")
            return
        print("\nYour Loans:")
        for idx, loan in enumerate(loans, 1):
            outstanding = max(0, loan.tenure_months - getattr(loan, "emis_paid", 0))
            print(
                f"{idx}. {loan.loan_id} | Status: {loan.status} | Outstanding EMIs: {outstanding}"
            )
        choice = self.app.read_valid_choice(
            "Select loan number to pay EMI for: ",
            [str(i) for i in range(1, len(loans) + 1)],
        )
        selected_loan = loans[int(choice) - 1]
        outstanding_emis = max(
            0, selected_loan.tenure_months - getattr(selected_loan, "emis_paid", 0)
        )
        if outstanding_emis <= 0:
            print("All EMIs for this loan have already been paid.")
            return
        if outstanding_emis == 1:
            count = 1
        else:
            while True:
                try:
                    count = int(
                        input(
                            f"How many EMIs would you like to pay now? (1-{outstanding_emis}): "
                        )
                    )
                    if 1 <= count <= outstanding_emis:
                        break
                    else:
                        print(
                            f"Please enter a number between 1 and {outstanding_emis}."
                        )
                except ValueError:
                    print("Please enter a valid number.")
        self.bank.pay_multiple_emis_for_loan(
            selected_loan.loan_id, account.account_number, count
        )
        print(f"\nSuccessfully paid {count} EMI(s) for loan {selected_loan.loan_id}.")

    def prepay_loan_early(self, customer: Customer, account: Account):
        """Prepay loan early and close it (with prepayment penalty)"""
        
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        active_loans = [loan for loan in loans if loan.status == "Active"]
        
        if not active_loans:
            print("[FAIL] You have no active loans to prepay.")
            return
        
        print("\n" + "=" * 70)
        print("LOAN PREPAYMENT (EARLY CLOSURE)")
        print("=" * 70)
        print("\n[INFO] YOUR ACTIVE LOANS:")
        
        for idx, loan in enumerate(active_loans, 1):
            remaining = loan.get_remaining_balance()
            emi = loan.calculate_emi()
            outstanding_emis = loan.tenure_months - loan.emis_paid
            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Type: {loan.loan_type} | Status: {loan.status}")
            print(f"   Principal: Rs. {loan.principal:,.2f} | Rate: {loan.interest_rate}% p.a.")
            print(f"   EMI: Rs. {emi:,.2f}/month | Paid: {loan.emis_paid}/{loan.tenure_months}")
            print(f"   Remaining Balance: Rs. {remaining:,.2f}")
        
        choice = self.app.read_valid_choice(
            f"\nSelect loan to prepay (1-{len(active_loans)}): ",
            [str(i) for i in range(1, len(active_loans) + 1)],
        )
        selected_loan = active_loans[int(choice) - 1]
        
        # Get closure details
        closure_details = selected_loan.get_closure_details()
        
        print("\n" + "=" * 70)
        print("PREPAYMENT CALCULATION")
        print("=" * 70)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Loan Type: {selected_loan.loan_type}")
        print(f"EMIs Paid: {selected_loan.emis_paid}/{selected_loan.tenure_months}")
        print(f"\nOutstanding Principal: Rs. {closure_details['remaining_balance']:,.2f}")
        print(f"Prepayment Penalty Rate: {closure_details['penalty_rate']}%")
        print(f"Prepayment Penalty: Rs. {closure_details['penalty_amount']:,.2f}")
        print("-" * 70)
        print(f"TOTAL AMOUNT DUE: Rs. {closure_details['total_payment']:,.2f}")
        print("=" * 70)
        
        if closure_details['penalty_amount'] == 0:
            print(f"\n[SUCCESS] Good news! No prepayment penalty for {selected_loan.loan_type} loans.")
        else:
            print(f"\n[WARN]  Note: Prepayment penalty of Rs. {closure_details['penalty_amount']:,.2f} will be charged.")
        
        # Confirmation
        confirm = input("\nProceed with loan closure? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] Loan prepayment cancelled.")
            return
        
        # Check account balance
        min_balance = account._min_operational_balance
        required_amount = closure_details['total_payment']
        
        if account.balance - required_amount < min_balance:
            print(f"\n[FAIL] Insufficient balance!")
            print(f"   Required: Rs. {required_amount:,.2f}")
            print(f"   Available: Rs. {account.balance - min_balance:,.2f}")
            print(f"   (Must maintain minimum balance of Rs. {min_balance:,.2f})")
            return
        
        # Process prepayment
        account.balance -= required_amount
        selected_loan.status = "Closed"
        selected_loan.closure_date = BankClock.today()
        selected_loan.prepayment_penalty_charged = closure_details['penalty_amount']
        
        # Log main payment transaction
        main_txn = Transaction(
            type="LOAN_PREPAYMENT",
            amount=closure_details['remaining_balance'],
            resulting_balance=account.balance,
            metadata={"loanId": selected_loan.loan_id, "loanType": selected_loan.loan_type},
        )
        account.transactions.append(main_txn)
        
        # Log penalty transaction separately
        if closure_details['penalty_amount'] > 0:
            penalty_txn = Transaction(
                type="LOAN_PREPAYMENT_PENALTY",
                amount=closure_details['penalty_amount'],
                resulting_balance=account.balance,
                metadata={
                    "loanId": selected_loan.loan_id,
                    "loanType": selected_loan.loan_type,
                    "penaltyRate": closure_details['penalty_rate'],
                },
            )
            account.transactions.append(penalty_txn)
        
        # Log to activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="LOAN_PREPAYMENT",
            amount=required_amount,
            resulting_balance=account.balance,
            txn_id=main_txn.id,
            metadata=f"loanId={selected_loan.loan_id};principal={closure_details['remaining_balance']:.2f};penalty={closure_details['penalty_amount']:.2f}",
        )
        
        self.bank.save()
        
        # Display confirmation
        print("\n" + "=" * 70)
        print("[SUCCESS] LOAN PREPAYMENT SUCCESSFUL")
        print("=" * 70)
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Status: CLOSED")
        print(f"\nPayment Breakdown:")
        print(f"  Principal Outstanding: Rs. {closure_details['remaining_balance']:,.2f}")
        print(f"  Prepayment Penalty: Rs. {closure_details['penalty_amount']:,.2f}")
        print(f"  Total Deducted: Rs. {required_amount:,.2f}")
        print(f"\nNew Account Balance: Rs. {account.balance:,.2f}")
        print("=" * 70)
        print("\n📄 You can view your Loan Closure Certificate from Loan Menu option 6.")

    def generate_loan_closure_certificate(self, customer: Customer, account: Account):
        """Generate loan closure certificate for closed loans as PDF"""
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        closed_loans = [loan for loan in loans if loan.status == "Closed"]

        if not closed_loans:
            print(
                "\n[FAIL] No closed loans found. You can only generate certificates for fully repaid loans."
            )
            return

        print("\n=== Your Closed Loans ===")
        for idx, loan in enumerate(closed_loans, 1):
            closure_date = getattr(loan, "closure_date", "Not recorded")
            if closure_date != "Not recorded" and hasattr(closure_date, "strftime"):
                closure_date = closure_date.strftime("%d-%m-%Y")
            print(
                f"{idx}. Loan ID: {loan.loan_id} | Principal: Rs. {loan.principal:,.2f} | Closed: {closure_date}"
            )

        choice = self.app.read_valid_choice(
            f"\nSelect loan number (1-{len(closed_loans)}): ",
            [str(i) for i in range(1, len(closed_loans) + 1)],
        )

        selected_loan = closed_loans[int(choice) - 1]

        # Preview on console
        print("\n[INFO] Generating Official Loan Closure Certificate...")
        
        # Generate PDF
        save = input("\nDownload Loan Closure Certificate (NOC) as PDF? (yes/no): ").strip().lower()
        if save in ["yes", "y"]:
            try:

                branch_details = Account.get_branch_details()
                filepath = StatementGenerator.generate_loan_closure_pdf(selected_loan, customer, branch_details)
                print(f"\n[SUCCESS] Official Loan Closure Certificate (NOC) generated: {filepath}")
            except Exception as e:
                print(f"[FAIL] Error generating certificate: {e}")
        else:
            print("[INFO] Download skipped.")

    def _get_loan_by_id(self, loan_id: str):
        """Helper method to find a loan by ID from the loans list"""
        for loan in self.bank.loans:
            if loan.loan_id == loan_id:
                return loan
        return None

    def loan_nach_mandate_menu(self, customer: Customer, account: Account):
        """NACH Mandate Management submenu for loan EMI automation"""
        self.current_customer = customer  # Set for use in helper methods

        while True:
            print("\n" + "=" * 60)
            print("[BANK] NACH MANDATE MANAGEMENT (Automatic EMI Deduction)")
            print("=" * 60)

            # Check if customer has any active loans
            active_loans = [
                loan
                for loan in self.bank.get_loans_for_customer(customer.customer_id)
                if loan.status == "Active"
            ]
            if not active_loans:
                print("\n[WARN]  You don't have any active loans.")
                print("NACH mandates can only be created for active loans.\n")
                input("Press Enter to continue...")
                break

            print("\n1. Create NACH Mandate")
            print("2. Verify NACH Mandate (OTP)")
            print("3. View All NACH Mandates")
            print("4. Revoke NACH Mandate")
            print("5. Suspend NACH Mandate")
            print("6. Resume NACH Mandate")
            print("7. View Mandate Details & Deduction History")
            print("8. Back to Loan Menu")

            choice = input("\nSelect option (1-8): ").strip()

            if choice == "1":
                self.create_loan_nach_mandate()
            elif choice == "2":
                self.verify_loan_nach_mandate_otp()
            elif choice == "3":
                self.view_loan_mandates()
            elif choice == "4":
                self.revoke_loan_nach_mandate()
            elif choice == "5":
                self.suspend_loan_nach_mandate()
            elif choice == "6":
                self.resume_loan_nach_mandate()
            elif choice == "7":
                self.view_mandate_details()
            elif choice == "8":
                break
            else:
                print("[FAIL] Invalid option. Please try again.")

    def create_loan_nach_mandate(self):
        """Create a new NACH mandate for automatic EMI deduction"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[INFO] CREATE NACH MANDATE FOR AUTOMATIC EMI DEDUCTION")
        print("=" * 60)

        # Display active loans
        active_loans = [
            loan
            for loan in self.bank.get_loans_for_customer(customer.customer_id)
            if loan.status == "Active"
        ]

        if not active_loans:
            print("\n[WARN]  No active loans available.")
            input("Press Enter to continue...")
            return

        print("\n📌 Your Active Loans:")
        for idx, loan in enumerate(active_loans, 1):
            print(f"\n{idx}. Loan ID: {loan.loan_id}")
            print(f"   Amount: Rs.{loan.calculate_emi():,.2f} (Monthly EMI)")
            print(f"   Tenure: {loan.tenure_months} months")
            print(f"   Interest Rate: {loan.interest_rate}%")
            if hasattr(loan, "nach_mandate_id") and loan.nach_mandate_id:
                mandate = LoanNachMandateManager.get_loan_mandate(loan.loan_id)
                if mandate:
                    print(f"   Status: {mandate.status}")

        loan_choice = input("\nSelect loan number: ").strip()

        try:
            loan_idx = int(loan_choice) - 1
            if 0 <= loan_idx < len(active_loans):
                selected_loan = active_loans[loan_idx]
            else:
                print("[FAIL] Invalid loan selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Check if mandate already exists
        existing_mandate = LoanNachMandateManager.get_loan_mandate(
            selected_loan.loan_id
        )
        if existing_mandate:
            print("\n[WARN]  A NACH mandate already exists for this loan.")
            print(f"   Current Status: {existing_mandate.status}")
            if existing_mandate.status in ["Pending", "OTP_Verified"]:
                proceed = (
                    input("\nDo you want to create a new mandate? (yes/no): ")
                    .strip()
                    .lower()
                )
                if proceed != "yes":
                    return

        # Get debit account
        print("\n📌 Select Account for EMI Deduction:")
        customer_accounts = self.bank.get_customer_accounts(customer)
        for idx, acc in enumerate(customer_accounts, 1):
            balance = acc.balance
            print(
                f"{idx}. {acc.account_number} ({acc.account_type}) - Balance: Rs.{balance:,.2f}"
            )

        acc_choice = input("\nSelect account number: ").strip()

        selected_account = None
        for acc in customer_accounts:
            if acc.account_number == acc_choice:
                selected_account = acc
                break

        if not selected_account:
            print("[FAIL] Invalid account selection.")
            return

        # Confirm NACH mandate details
        print("\n" + "=" * 60)
        print("[INFO] NACH MANDATE DETAILS")
        print("=" * 60)
        print(f"\nLoan ID: {selected_loan.loan_id}")
        print(f"Loan Amount: Rs.{selected_loan.principal:,.2f}")
        print(f"Monthly EMI: Rs.{selected_loan.calculate_emi():,.2f}")
        print(f"Tenure: {selected_loan.tenure_months} months")
        print(
            f"Max Debit Limit: Rs.{selected_loan.calculate_emi() * 1.5:,.2f} (1.5x safety buffer)"
        )
        print(f"Debit Account: {selected_account.account_number}")

        confirm = (
            input("\n[OK] Proceed with NACH mandate creation? (yes/no): ").strip().lower()
        )
        if confirm != "yes":
            print("[FAIL] Mandate creation cancelled.")
            return

        # Calculate mandate end date


        start_date = datetime.now().strftime("%d-%m-%Y")
        loan_end_date = datetime.now() + timedelta(
            days=30 * selected_loan.tenure_months
        )
        end_date = loan_end_date.strftime("%d-%m-%Y")

        # Create mandate
        success, message, mandate_id, otp = LoanNachMandateManager.create_mandate(
            loan_id=selected_loan.loan_id,
            customer_id=customer.customer_id,
            account_number=selected_account.account_number,
            debit_account=selected_account.account_number,
            debit_ifsc="PYTHONIFIED001",
            emi_amount=selected_loan.calculate_emi(),
            start_date=start_date,
            end_date=end_date,
        )

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] NACH MANDATE CREATED SUCCESSFULLY")
            print("=" * 60)
            print(f"\nMandate ID: {mandate_id}")
            print("Status: Pending (OTP Verification Required)")
            print("\n📱 OTP sent to registered mobile number")
            print(f"🔐 Verification Code: {otp} (for testing purposes)")
            print("\nPlease verify your mandate with the OTP to activate it.")

            # Update loan with mandate ID
            selected_loan.nach_mandate_id = mandate_id
            self.bank.save()
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def verify_loan_nach_mandate_otp(self):
        """Verify NACH mandate with OTP"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("🔐 VERIFY NACH MANDATE (OTP)")
        print("=" * 60)

        # Display pending mandates
        pending_mandates = []
        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        for mandate in all_mandates:
            if mandate.status in ["Pending", "OTP_Verified"]:
                loan = self._get_loan_by_id(mandate.loan_id)
                if loan:
                    pending_mandates.append((loan, mandate))

        if not pending_mandates:
            print("\n[WARN]  No pending NACH mandates to verify.")
            input("Press Enter to continue...")
            return

        print("\n📌 Pending NACH Mandates:")
        for idx, (loan, mandate) in enumerate(pending_mandates, 1):
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan.loan_id}")
            print(f"   Status: {mandate.status}")
            print(f"   EMI Amount: Rs.{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pending_mandates):
                selected_loan, selected_mandate = pending_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        # Request OTP
        print(f"\n[INFO] Mandate ID: {selected_mandate.mandate_id}")
        print("🔐 Enter the OTP sent to your registered mobile number:")

        otp_attempts = 0
        max_attempts = 3

        while otp_attempts < max_attempts:
            otp = input("\nEnter OTP (6 digits): ").strip()

            success, message = LoanNachMandateManager.verify_mandate_otp(
                selected_mandate.mandate_id, otp
            )

            if success:
                print("\n" + "=" * 60)
                print("[SUCCESS] OTP VERIFIED SUCCESSFULLY")
                print("=" * 60)
                print(f"\nMandate ID: {selected_mandate.mandate_id}")
                print("Status: ACTIVE")
                print(f"EMI Amount: Rs.{selected_mandate.emi_amount:,.2f}")
                print(f"Account: {selected_mandate.bank_account_number}")
                print("\n[OK] NACH mandate is now active.")
                print("[OK] EMI will be deducted automatically from your account.")
                break
            else:
                otp_attempts += 1
                remaining = max_attempts - otp_attempts
                if remaining > 0:
                    print(f"\n[FAIL] {message}")
                    print(f"[WARN]  Remaining attempts: {remaining}")
                else:
                    print(f"\n[FAIL] {message}")
                    print(
                        "[FAIL] Maximum OTP attempts exceeded. Mandate creation cancelled."
                    )
                    selected_mandate.status = NachMandateStatus.REVOKED
                    LoanNachMandateManager._save_mandates()

        input("\nPress Enter to continue...")

    def view_loan_mandates(self):
        """View all NACH mandates for customer"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[INFO] YOUR NACH MANDATES")
        print("=" * 60)

        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )

        if not all_mandates:
            print("\n[WARN]  You don't have any NACH mandates.")
            print("\n💡 Create a NACH mandate to set up automatic EMI deductions.")
        else:
            print("\n")
            mandate_count = {}
            for mandate in all_mandates:
                status = mandate.status
                mandate_count[status] = mandate_count.get(status, 0) + 1

                status_icon = (
                    "[SUCCESS]"
                    if status == NachMandateStatus.ACTIVE
                    else "⏳"
                    if status == NachMandateStatus.PENDING
                    else "[FAIL]"
                    if status == NachMandateStatus.REVOKED
                    else "[WARN]"
                )

                loan = self._get_loan_by_id(mandate.loan_id)
                loan_id = loan.loan_id if loan else mandate.loan_id

                print(f"{status_icon} Loan ID: {loan_id}")
                print(f"   Mandate ID: {mandate.mandate_id}")
                print(f"   Status: {status}")
                print(f"   EMI Amount: Rs.{mandate.emi_amount:,.2f}")
                print(f"   Account: {mandate.bank_account_number}")
                print(f"   Period: {mandate.start_date} to {mandate.end_date}")
                print(f"   Deductions Processed: {len(mandate.deduction_history)}")
                print()

            print("=" * 60)
            print("[STATS] MANDATE SUMMARY")
            print("=" * 60)
            for status, count in mandate_count.items():
                if count > 0:
                    print(f"{status}: {count}")

        input("\nPress Enter to continue...")

    def revoke_loan_nach_mandate(self):
        """Revoke a NACH mandate"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("🛑 REVOKE NACH MANDATE")
        print("=" * 60)

        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        revokable_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status != NachMandateStatus.REVOKED
        ]

        if not revokable_mandates:
            print("\n[WARN]  No active NACH mandates to revoke.")
            input("Press Enter to continue...")
            return

        print("\n📌 NACH Mandates:")
        for idx, (mandate, loan) in enumerate(revokable_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   Status: {mandate.status}")
            print(f"   EMI: Rs.{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to revoke (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(revokable_mandates):
                selected_mandate, selected_loan = revokable_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        print(
            "\n[WARN]  IMPORTANT: Revoking this mandate will stop automatic EMI deductions."
        )
        print("   You will need to pay EMIs manually.")
        confirm = input("\nProceed with mandate revocation? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("[FAIL] Revocation cancelled.")
            return

        success, message = LoanNachMandateManager.revoke_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: REVOKED")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def suspend_loan_nach_mandate(self):
        """Suspend a NACH mandate temporarily"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[VIRTUAL]  SUSPEND NACH MANDATE")
        print("=" * 60)

        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        suspendable_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status == NachMandateStatus.ACTIVE
        ]

        if not suspendable_mandates:
            print("\n[WARN]  No active NACH mandates to suspend.")
            input("Press Enter to continue...")
            return

        print("\n📌 Active NACH Mandates:")
        for idx, (mandate, loan) in enumerate(suspendable_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   EMI: Rs.{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to suspend (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suspendable_mandates):
                selected_mandate, selected_loan = suspendable_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        print("\n[WARN]  Suspending this mandate will temporarily stop EMI deductions.")
        confirm = input("Proceed? (yes/no): ").strip().lower()

        if confirm != "yes":
            print("[FAIL] Suspension cancelled.")
            return

        success, message = LoanNachMandateManager.suspend_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: SUSPENDED")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def resume_loan_nach_mandate(self):
        """Resume a suspended NACH mandate"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("▶️  RESUME NACH MANDATE")
        print("=" * 60)

        all_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        suspended_mandates = [
            (m, self._get_loan_by_id(m.loan_id))
            for m in all_mandates
            if m.status == NachMandateStatus.SUSPENDED
        ]

        if not suspended_mandates:
            print("\n[WARN]  No suspended NACH mandates to resume.")
            input("Press Enter to continue...")
            return

        print("\n📌 Suspended NACH Mandates:")
        for idx, (mandate, loan) in enumerate(suspended_mandates, 1):
            loan_id = loan.loan_id if loan else mandate.loan_id
            print(f"\n{idx}. Mandate ID: {mandate.mandate_id}")
            print(f"   Loan ID: {loan_id}")
            print(f"   EMI: Rs.{mandate.emi_amount:,.2f}")

        choice = input("\nSelect mandate to resume (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(suspended_mandates):
                selected_mandate, selected_loan = suspended_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        confirm = (
            input("\nProceed with resuming this mandate? (yes/no): ").strip().lower()
        )

        if confirm != "yes":
            print("[FAIL] Resume cancelled.")
            return

        success, message = LoanNachMandateManager.resume_mandate(
            selected_mandate.mandate_id
        )

        if success:
            print(f"\n[SUCCESS] {message}")
            print(f"   Mandate ID: {selected_mandate.mandate_id}")
            print("   Status: ACTIVE")
        else:
            print(f"\n[FAIL] {message}")

        input("\nPress Enter to continue...")

    def view_mandate_details(self):
        """View detailed information about a NACH mandate"""
        customer = self.current_customer

        print("\n" + "=" * 60)
        print("[STATS] NACH MANDATE DETAILS & DEDUCTION HISTORY")
        print("=" * 60)

        all_mandates = []
        customer_mandates = LoanNachMandateManager.get_customer_mandates(
            customer.customer_id
        )
        for mandate in customer_mandates:
            loan = self._get_loan_by_id(mandate.loan_id)
            if loan:
                all_mandates.append((loan, mandate))

        if not all_mandates:
            print("\n[WARN]  No NACH mandates found.")
            input("Press Enter to continue...")
            return

        print("\n📌 Select a Mandate:")
        for idx, (loan, mandate) in enumerate(all_mandates, 1):
            print(f"{idx}. {mandate.mandate_id} ({mandate.status})")

        choice = input("\nSelect mandate (number): ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(all_mandates):
                selected_loan, selected_mandate = all_mandates[idx]
            else:
                print("[FAIL] Invalid selection.")
                return
        except ValueError:
            print("[FAIL] Please enter a valid number.")
            return

        print("\n" + "=" * 60)
        print("[INFO] MANDATE INFORMATION")
        print("=" * 60)
        print(f"\nMandate ID: {selected_mandate.mandate_id}")
        print(f"Loan ID: {selected_loan.loan_id}")
        print(f"Status: {selected_mandate.status}")
        print(f"Created: {selected_mandate.creation_timestamp}")
        print("\n[MONEY] AMOUNT DETAILS")
        print(f"EMI Amount: Rs.{selected_mandate.emi_amount:,.2f}")
        print(f"Max Debit Limit: Rs.{selected_mandate.max_debit_amount:,.2f}")
        print("\n📅 PERIOD")
        print(f"Start Date: {selected_mandate.start_date}")
        print(f"End Date: {selected_mandate.end_date}")
        print("\n🔐 ACCOUNT DETAILS")
        print(f"Debit Account: {selected_mandate.bank_account_number}")

        if selected_mandate.deduction_history:
            print(
                f"\n[STATS] DEDUCTION HISTORY ({len(selected_mandate.deduction_history)} deductions)"
            )
            print("=" * 60)

            total_deducted = 0
            for idx, deduction in enumerate(
                selected_mandate.deduction_history[:20], 1
            ):
                status_icon = (
                    "[SUCCESS]"
                    if deduction["status"] == "Success"
                    else "[FAIL]"
                )
                print(f"\n{idx}. {status_icon} {deduction['date']}")
                print(f"   Amount: Rs.{deduction['amount']:,.2f}")
                print(f"   Status: {deduction['status']}")
                if deduction["status"] == "Success":
                    total_deducted += deduction["amount"]

            print("\n" + "=" * 60)
            print(f"Total Deducted: Rs.{total_deducted:,.2f}")
        else:
            print("\n⏳ No deductions yet.")

        input("\nPress Enter to continue...")

    def download_loan_statement(self, customer: Customer, account: Account):
        """Download Loan Statement as PDF"""
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        if not loans:
            print("\n[INFO] No active loans found.")
            return

        print("\nSelect Loan for Statement:")
        for idx, loan in enumerate(loans, 1):
            print(f"{idx}. {loan.loan_id} ({loan.loan_type}) - Rs. {loan.principal:,.2f}")

        choice = input(f"\nEnter choice (1-{len(loans)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(loans):
            selected_loan = loans[int(choice) - 1]
            from ..StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_loan_soa(selected_loan, customer)
            print(f"\n[SUCCESS] Loan Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")
    
    def view_cibil_report(self, customer: Customer):
        """View detailed CIBIL report and history"""

        
        print("\n" + "=" * 70)
        print("OFFICIAL CIBIL CREDIT REPORT")
        print("=" * 70)
        
        # Recalculate to ensure latest data
        score = calculate_cibil_score(customer, self.bank)
        customer.cibil_score = score
        
        print(f"\nName: {customer.first_name} {customer.last_name}")
        print(f"PAN: {getattr(customer, 'pan_number', 'N/A')}")
        print(f"Date: {BankClock.today().strftime('%d-%m-%Y')}")
        
        print("\n" + "-" * 70)
        print(f"CURRENT CIBIL SCORE: {score}")
        print("-" * 70)
        
        # Score rating
        if score >= 750:
            rating = "EXCELLENT"
            color = "[SUCCESS]"
        elif score >= 700:
            rating = "GOOD"
            color = "[SUCCESS]"
        elif score >= 650:
            rating = "AVERAGE"
            color = "[WARN]"
        else:
            rating = "POOR"
            color = "[FAIL]"
            
        print(f"Rating: {color} {rating}")
        
        # Breakdown
        print("\n[STATS] SCORE BREAKDOWN FACTORS:")
        
        # 1. Payment History (35%)
        loans = self.bank.get_loans_for_customer(customer.customer_id)
        total_emis = sum(loan.tenure_months for loan in loans)
        paid_emis = sum(loan.emis_paid for loan in loans)
        
        payment_ratio = (paid_emis / total_emis * 100) if total_emis > 0 else 100
        status = "[SUCCESS]" if payment_ratio > 90 else "[WARN]" if payment_ratio > 70 else "[FAIL]"
        print(f"{status} Payment History: {payment_ratio:.1f}% on-time")
        
        # 2. Credit Mix (25%)
        loan_types = set(getattr(loan, 'loan_type', 'PERSONAL') for loan in loans)
        status = "[SUCCESS]" if len(loan_types) >= 2 else "[WARN]"
        print(f"{status} Credit Mix: {len(loan_types)} types (Home, Personal, etc.)")
        
        # 3. Hard Inquiries (10%)
        inquiries = getattr(customer, 'credit_inquiries', [])
        recent_inquiries = [i for i in inquiries if (BankClock.today() - i['date']).days < 180]
        status = "[SUCCESS]" if len(recent_inquiries) < 2 else "[WARN]" if len(recent_inquiries) < 5 else "[FAIL]"
        print(f"{status} Recent Hard Inquiries: {len(recent_inquiries)} (Last 6 months)")
        
        # 4. Credit History Length (15%)
        # Just a mock representation for now
        print("[SUCCESS] Credit History Length: Active")
        
        print("\n[INFO] RECENT INQUIRY HISTORY:")
        if not inquiries:
            print("  No recent inquiries found.")
        else:
            for rec in inquiries[-5:]:
                print(f"  • {rec['date'].strftime('%d-%b-%Y')}: {rec['type']}")
                
        print("\n" + "=" * 70)
        input("\nPress Enter to continue...")

