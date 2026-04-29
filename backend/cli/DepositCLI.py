from datetime import datetime, date
from typing import List, Optional

from ..Account import Account
from ..Customer import Customer
from ..Transaction import Transaction
from ..FixedDeposit import FixedDeposit
from ..RecurringDeposit import RecurringDeposit
from ..Logger import BankLogger
from ..RDStatement import RDStatement
from ..RDAuthorization import RDAuthorization

class DepositCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.logger = BankLogger.get_logger("DepositCLI")

    def fd_rd_menu(self, customer: Customer, account: Account):
        """Fixed Deposit and Recurring Deposit Management Menu"""
        while True:
            print("\n" + "=" * 70)
            print("FIXED DEPOSITS & RECURRING DEPOSITS")
            print("=" * 70)
            print("""
Choose an option:
1 Open Fixed Deposit (FD)
2 Open Recurring Deposit (RD)
3 View My FDs
4 View My RDs
5 Pay RD Installment (Manual)
6 Enable/Disable RD Autopay
7 Close FD (Premature)
8 Close RD (Premature)
9 Mature FD
10 Mature RD
11 View FD Details
12 View RD Details
13 RD Authorization Management
14 View RD Statement of Account
15 Download FD Statement (PDF)
16 Download RD Statement (PDF)
17 Back to Main Menu
            """)

            choice = self.app.read_valid_choice(
                "Enter your choice: ",
                [str(i) for i in range(1, 18)],
                "Invalid choice. Please enter a number from 1 to 17.",
            )

            if choice == "1":
                self.open_fixed_deposit(account)
            elif choice == "2":
                self.open_recurring_deposit(account)
            elif choice == "3":
                self.view_my_fds(account)
            elif choice == "4":
                self.view_my_rds(account)
            elif choice == "5":
                self.pay_rd_installment(account)
            elif choice == "6":
                self.manage_rd_autopay(account)
            elif choice == "7":
                self.close_fd_premature(account)
            elif choice == "8":
                self.close_rd_premature(account)
            elif choice == "9":
                self.mature_fd(account)
            elif choice == "10":
                self.mature_rd(account)
            elif choice == "11":
                self.view_fd_details(account)
            elif choice == "12":
                self.view_rd_details(account)
            elif choice == "13":
                self.rd_authorization_menu(customer, account)
            elif choice == "14":
                self.view_rd_statement(customer, account)
            elif choice == "15":
                self.download_fd_statement(customer, account)
            elif choice == "16":
                self.download_rd_statement(customer, account)
            elif choice == "17":
                break

    def download_fd_statement(self, customer: Customer, account: Account):
        """Download FD Statement as PDF"""
        if not hasattr(self.bank, "fixed_deposits"):
            print("\n[INFO] No FDs found.")
            return
            
        my_fds = [fd for fd in self.bank.fixed_deposits.values() if fd.account_number == account.account_number]
        if not my_fds:
            print("\n[INFO] No active FDs found for this account.")
            return

        print("\nSelect FD for Statement:")
        for idx, fd in enumerate(my_fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f} ({fd.status})")

        choice = input(f"\nEnter choice (1-{len(my_fds)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(my_fds):
            selected_fd = my_fds[int(choice) - 1]
            from ..StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_fd_soa(selected_fd, customer)
            print(f"\n[SUCCESS] FD Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")

    def download_rd_statement(self, customer: Customer, account: Account):
        """Download RD Statement as PDF"""
        from ..RDStatement import RDStatement
        rd_stmt_helper = RDStatement(self.bank)
        statements = rd_stmt_helper.get_all_rd_statements(account.account_number)
        
        if not statements:
            print("\n[INFO] No active RDs found for this account.")
            return

        print("\nSelect RD for Statement:")
        for idx, stmt in enumerate(statements, 1):
            print(f"{idx}. {stmt['rd_number']} - Rs. {stmt['monthly_installment']:,.2f} ({stmt['status']})")

        choice = input(f"\nEnter choice (1-{len(statements)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(statements):
            selected_stmt = statements[int(choice) - 1]
            from ..StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_rd_soa(selected_stmt, customer)
            print(f"\n[SUCCESS] RD Statement generated: {filepath}")
        else:
            print("[FAIL] Invalid selection.")

    def open_fixed_deposit(self, account: Account):
        """Open a new Fixed Deposit"""
        print("\n" + "=" * 70)
        print("OPEN FIXED DEPOSIT")
        print("=" * 70)

        print(f"\nCurrent Balance: Rs. {account.balance:,.2f}")
        print(f"Minimum Balance Required: Rs. {account._min_operational_balance:,.2f}")
        print("\nAvailable Tenures and Interest Rates:")
        print("-" * 70)

        # Check if senior citizen
        is_senior = False
        customer = self.bank.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior = age >= 60
            except (ValueError, AttributeError):
                pass

        for tenure, rate in sorted(FixedDeposit.INTEREST_RATES.items()):
            senior_rate = (
                rate + FixedDeposit.SENIOR_CITIZEN_BONUS if is_senior else rate
            )
            senior_info = f" (Senior Citizen: {senior_rate}%)" if is_senior else ""
            print(f"  {tenure:2d} months: {rate}% p.a.{senior_info}")

        print("-" * 70)
        print(f"Minimum Amount: Rs. {FixedDeposit.MIN_AMOUNT:,.2f}")
        print(f"Maximum Amount: Rs. {FixedDeposit.MAX_AMOUNT:,.2f}")

        # Get amount
        try:
            amount = float(
                input(
                    f"\nEnter FD amount (Rs. {FixedDeposit.MIN_AMOUNT:,.2f} - {FixedDeposit.MAX_AMOUNT:,.2f}): "
                )
            )
        except ValueError:
            print("[FAIL] Invalid amount")
            return

        # Get tenure
        valid_tenures = list(FixedDeposit.INTEREST_RATES.keys())
        print(f"\nAvailable tenures: {', '.join(str(t) for t in valid_tenures)} months")
        try:
            tenure = int(input("Enter tenure in months: "))
        except ValueError:
            print("[FAIL] Invalid tenure")
            return

        # Show calculation
        if tenure in FixedDeposit.INTEREST_RATES:
            rate = FixedDeposit.get_applicable_rate(tenure, is_senior)
            n = 4  # Quarterly
            t = tenure / 12
            maturity = amount * ((1 + rate / 100 / n) ** (n * t))
            interest = maturity - amount

            print("\n" + "-" * 70)
            print("FD PREVIEW")
            print("-" * 70)
            print(f"Principal Amount: Rs. {amount:,.2f}")
            print(f"Interest Rate: {rate}% p.a.")
            print(f"Tenure: {tenure} months")
            print(f"Expected Interest: Rs. {interest:,.2f}")
            print(f"Maturity Amount: Rs. {maturity:,.2f}")
            print("-" * 70)

        confirm = input("\nConfirm FD creation? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] FD creation cancelled")
            return

        success, message, fd = self.bank.create_fixed_deposit(account, amount, tenure)
        if success:
            print(message)
            self.bank.save()
        else:
            print(f"\n[FAIL] Failed to create FD: {message}")

    def open_recurring_deposit(self, account: Account):
        """Open a new Recurring Deposit"""
        print("\n" + "=" * 70)
        print("OPEN RECURRING DEPOSIT")
        print("=" * 70)

        print(f"\nCurrent Balance: Rs. {account.balance:,.2f}")
        print("\nAvailable Tenures and Interest Rates:")
        print("-" * 70)

        # Check if senior citizen
        is_senior = False
        customer = self.bank.get_customer_by_id(account.customer_id)
        if customer and hasattr(customer, "dob"):
            try:
                dob = datetime.strptime(customer.dob, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                is_senior = age >= 60
            except (ValueError, AttributeError):
                pass

        for tenure, rate in sorted(RecurringDeposit.INTEREST_RATES.items()):
            senior_rate = (
                rate + RecurringDeposit.SENIOR_CITIZEN_BONUS if is_senior else rate
            )
            senior_info = f" (Senior Citizen: {senior_rate}%)" if is_senior else ""
            print(f"  {tenure:2d} months: {rate}% p.a.{senior_info}")

        print("-" * 70)
        print(f"Minimum Monthly Installment: Rs. {RecurringDeposit.MIN_MONTHLY_AMOUNT:,.2f}")
        print(f"Maximum Monthly Installment: Rs. {RecurringDeposit.MAX_MONTHLY_AMOUNT:,.2f}")

        try:
            monthly = float(input("\nEnter monthly installment: "))
        except ValueError:
            print("[FAIL] Invalid amount")
            return

        valid_tenures = list(RecurringDeposit.INTEREST_RATES.keys())
        print(f"\nAvailable tenures: {', '.join(str(t) for t in valid_tenures)} months")
        try:
            tenure = int(input("Enter tenure in months: "))
        except ValueError:
            print("[FAIL] Invalid tenure")
            return

        if tenure in RecurringDeposit.INTEREST_RATES:
            rate = RecurringDeposit.get_applicable_rate(tenure, is_senior)
            P = monthly
            n = tenure
            r = rate
            interest = (P * n * (n + 1) * r) / 2400
            maturity = (P * n) + interest

            print("\n" + "-" * 70)
            print("RD PREVIEW")
            print("-" * 70)
            print(f"Monthly Installment: Rs. {monthly:,.2f}")
            print(f"Interest Rate: {rate}% p.a.")
            print(f"Tenure: {tenure} months")
            print(f"Total Investment: Rs. {monthly * tenure:,.2f}")
            print(f"Expected Interest: Rs. {interest:,.2f}")
            print(f"Maturity Amount: Rs. {maturity:,.2f}")
            print("-" * 70)

        enable_autopay = input("\nEnable autopay? (yes/no): ").strip().lower() in ["yes", "y"]
        autopay_day = 1
        if enable_autopay:
            try:
                autopay_day = int(input("Enter autopay day (1-28): "))
                if autopay_day < 1 or autopay_day > 28:
                    autopay_day = 1
            except ValueError:
                autopay_day = 1

        confirm = input("\nConfirm RD creation? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("[FAIL] RD creation cancelled")
            return

        success, message, rd = self.bank.create_recurring_deposit(account, monthly, tenure, enable_autopay, autopay_day)
        if success:
            print(message)
            self.bank.save()
        else:
            print(f"\n[FAIL] Failed to create RD: {message}")

    def view_my_fds(self, account: Account):
        """View all FDs for current account"""
        fds = self.bank.get_fds_for_account(account.account_number)
        if not fds:
            print("\n📭 No Fixed Deposits found")
            return

        print("\n" + "=" * 100)
        print(f"YOUR FIXED DEPOSITS - Account: {account.account_number}")
        print("=" * 100)
        print(f"{'FD Number':<20} {'Principal':<15} {'Rate':<8} {'Tenure':<10} {'Maturity':<15} {'Status':<20}")
        print("-" * 100)
        for fd in fds:
            print(f"{fd.fd_number:<20} Rs. {fd.principal_amount:>10,.2f} {fd.interest_rate:>5.2f}% {fd.tenure_months:>3d} months Rs. {fd.maturity_amount:>10,.2f} {fd.get_status_string():<20}")
        print("-" * 100)
        print(f"Total FDs: {len(fds)}")
        print("=" * 100)

    def view_my_rds(self, account: Account):
        """View all RDs for current account"""
        rds = self.bank.get_rds_for_account(account.account_number)
        if not rds:
            print("\n📭 No Recurring Deposits found")
            return

        print("\n" + "=" * 110)
        print(f"YOUR RECURRING DEPOSITS - Account: {account.account_number}")
        print("=" * 110)
        print(f"{'RD Number':<20} {'Monthly':<15} {'Rate':<8} {'Paid':<15} {'Status':<25} {'Autopay':<10}")
        print("-" * 110)
        for rd in rds:
            autopay = "[OK] Yes" if rd.autopay_enabled else "No"
            print(f"{rd.rd_number:<20} Rs. {rd.monthly_installment:>10,.2f} {rd.interest_rate:>5.2f}% {rd.installments_paid:>2d}/{rd.tenure_months:<2d} months {rd.get_payment_status():<25} {autopay:<10}")
        print("-" * 110)
        print(f"Total RDs: {len(rds)}")
        print("=" * 110)

    def pay_rd_installment(self, account: Account):
        """Pay RD installment manually"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status == "Active"]
        if not active_rds:
            print("\n📭 No active RDs found")
            return

        print("\n" + "=" * 80)
        print("PAY RD INSTALLMENT")
        print("=" * 80)
        for idx, rd in enumerate(active_rds, 1):
            print(f"{idx}. {rd.rd_number} - Rs. {rd.monthly_installment:,.2f}/month ({rd.installments_paid}/{rd.tenure_months} paid)")

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                return
        except ValueError:
            return

        rd = active_rds[choice - 1]
        confirm = input("\nPay installment? (yes/no): ").strip().lower()
        if confirm in ["yes", "y"]:
            success, message = rd.pay_installment_manual(account)
            if success:
                print(f"\n[SUCCESS] {message}")
                self.bank.save()
            else:
                print(f"\n[FAIL] {message}")

    def manage_rd_autopay(self, account: Account):
        """Enable/Disable RD Autopay"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status == "Active"]
        if not active_rds:
            print("\n📭 No active RDs found")
            return

        for idx, rd in enumerate(active_rds, 1):
            autopay = "[OK] Enabled" if rd.autopay_enabled else "✗ Disabled"
            print(f"{idx}. {rd.rd_number} - {autopay}")

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                return
        except ValueError:
            return

        rd = active_rds[choice - 1]
        if rd.autopay_enabled:
            action = input("\nDisable autopay? (yes/no): ").strip().lower()
            if action in ["yes", "y"]:
                success, message = rd.disable_autopay()
                if success: self.bank.save()
                print(f"\n{'[SUCCESS]' if success else '[FAIL]'} {message}")
        else:
            action = input("\nEnable autopay? (yes/no): ").strip().lower()
            if action in ["yes", "y"]:
                try: day = int(input("Enter autopay day (1-28): "))
                except ValueError: day = 1
                success, message = rd.enable_autopay(day)
                if success: self.bank.save()
                print(f"\n{'[SUCCESS]' if success else '[FAIL]'} {message}")

    def close_fd_premature(self, account: Account):
        """Close FD before maturity"""
        fds = self.bank.get_fds_for_account(account.account_number)
        active_fds = [fd for fd in fds if fd.status == "Active"]
        if not active_fds:
            print("\n📭 No active FDs found")
            return

        for idx, fd in enumerate(active_fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f}")

        try:
            choice = int(input(f"\nSelect FD (1-{len(active_fds)}): "))
            if choice < 1 or choice > len(active_fds):
                return
        except ValueError:
            return

        fd = active_fds[choice - 1]
        interest, penalty, payout = fd.calculate_premature_withdrawal()
        print(f"\nFinal Payout: Rs. {payout:,.2f}")
        confirm = input("Confirm premature closure? (yes/no): ").strip().lower()
        if confirm in ["yes", "y"]:
            payout, message = fd.close_prematurely()
            if payout > 0:
                account.balance += payout
                txn = Transaction(type="FD_CLOSED_PREMATURE", amount=payout, resulting_balance=account.balance, metadata={"fd_number": fd.fd_number})
                account.transactions.append(txn)
                self.bank.save()
                print(f"[SUCCESS] {message}. Credited: Rs. {payout:,.2f}")
            else:
                print(f"[FAIL] {message}")

    def close_rd_premature(self, account: Account):
        """Close RD before maturity"""
        rds = self.bank.get_rds_for_account(account.account_number)
        active_rds = [rd for rd in rds if rd.status in ["Active", "Completed"]]
        if not active_rds:
            print("\n📭 No active RDs found")
            return

        for idx, rd in enumerate(active_rds, 1):
            print(f"{idx}. {rd.rd_number}")

        try:
            choice = int(input(f"\nSelect RD (1-{len(active_rds)}): "))
            if choice < 1 or choice > len(active_rds):
                return
        except ValueError:
            return

        rd = active_rds[choice - 1]
        current_value, penalty, payout = rd.calculate_premature_withdrawal()
        print(f"\nFinal Payout: Rs. {payout:,.2f}")
        confirm = input("Confirm premature closure? (yes/no): ").strip().lower()
        if confirm in ["yes", "y"]:
            payout, message = rd.close_prematurely()
            if payout > 0:
                account.balance += payout
                txn = Transaction(type="RD_CLOSED_PREMATURE", amount=payout, resulting_balance=account.balance, metadata={"rd_number": rd.rd_number})
                account.transactions.append(txn)
                self.bank.save()
                print(f"[SUCCESS] {message}. Credited: Rs. {payout:,.2f}")
            else:
                print(f"[FAIL] {message}")

    def mature_fd(self, account: Account):
        """Mature an FD"""
        fds = self.bank.get_fds_for_account(account.account_number)
        matured_fds = [fd for fd in fds if fd.status == "Active" and fd.is_matured()]
        if not matured_fds:
            print("\n📭 No FDs ready for maturity")
            return

        for idx, fd in enumerate(matured_fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.maturity_amount:,.2f}")

        try:
            choice = int(input(f"\nSelect FD (1-{len(matured_fds)}): "))
            if choice < 1 or choice > len(matured_fds):
                return
        except ValueError:
            return

        fd = matured_fds[choice - 1]
        payout, message = fd.mature()
        if payout > 0:
            account.balance += payout
            txn = Transaction(type="FD_MATURED", amount=payout, resulting_balance=account.balance, metadata={"fd_number": fd.fd_number})
            account.transactions.append(txn)
            self.bank.save()
            print(f"[SUCCESS] {message}. Credited: Rs. {payout:,.2f}")
        else:
            print(f"[FAIL] {message}")

    def mature_rd(self, account: Account):
        """Mature an RD"""
        rds = self.bank.get_rds_for_account(account.account_number)
        completed_rds = [rd for rd in rds if rd.status == "Completed"]
        if not completed_rds:
            print("\n📭 No RDs ready for maturity")
            return

        for idx, rd in enumerate(completed_rds, 1):
            print(f"{idx}. {rd.rd_number}")

        try:
            choice = int(input(f"\nSelect RD (1-{len(completed_rds)}): "))
            if choice < 1 or choice > len(completed_rds):
                return
        except ValueError:
            return

        rd = completed_rds[choice - 1]
        payout, message = rd.mature()
        if payout > 0:
            account.balance += payout
            txn = Transaction(type="RD_MATURED", amount=payout, resulting_balance=account.balance, metadata={"rd_number": rd.rd_number})
            account.transactions.append(txn)
            self.bank.save()
            print(f"[SUCCESS] {message}. Credited: Rs. {payout:,.2f}")
        else:
            print(f"[FAIL] {message}")

    def view_fd_details(self, account: Account):
        """View detailed FD information"""
        fds = self.bank.get_fds_for_account(account.account_number)
        if not fds: return
        for idx, fd in enumerate(fds, 1):
            print(f"{idx}. {fd.fd_number} - Rs. {fd.principal_amount:,.2f}")
        try:
            choice = int(input(f"\nEnter choice: "))
            fd = fds[choice - 1]
            print(f"\nFD Number: {fd.fd_number}\nPrincipal: Rs. {fd.principal_amount:,.2f}\nRate: {fd.interest_rate}%\nTenure: {fd.tenure_months} months\nStatus: {fd.get_status_string()}")
        except (ValueError, IndexError):
            pass

    def view_rd_details(self, account: Account):
        """View detailed RD information"""
        rds = self.bank.get_rds_for_account(account.account_number)
        if not rds: return
        for idx, rd in enumerate(rds, 1):
            print(f"{idx}. {rd.rd_number} - Rs. {rd.monthly_installment:,.2f}/month")
        try:
            choice = int(input(f"\nEnter choice: "))
            rd = rds[choice - 1]
            print(f"\nRD Number: {rd.rd_number}\nMonthly: Rs. {rd.monthly_installment:,.2f}\nRate: {rd.interest_rate}%\nTenure: {rd.tenure_months} months\nStatus: {rd.get_payment_status()}")
        except (ValueError, IndexError):
            pass

    def rd_authorization_menu(self, customer: Customer, account: Account):
        """RD Authorization Management Menu"""
        while True:
            print("\n" + "=" * 60)
            print("RD AUTHORIZATION MANAGEMENT")
            print("=" * 60)
            print("1. View My Authorizations (As Beneficiary)")
            print("2. View My Authorizations (As Payer)")
            print("3. Create New RD Authorization (Beneficiary Request)")
            print("4. Verify Pending Authorization (Payer Verification)")
            print("5. Revoke Authorization")
            print("6. Back to RD Menu")
            print("=" * 60)

            choice = self.app.read_valid_choice("Enter choice: ", ["1", "2", "3", "4", "5", "6"])

            if choice == "1":
                auths = self.bank.rd_authorizations.get_authorizations_by_beneficiary(customer.customer_id)
                if not auths:
                    print("\nYou have no RD authorizations as beneficiary.")
                else:
                    print("\n" + "-" * 80)
                    print(f"{'Auth ID':<15} {'RD Number':<20} {'Payer ID':<15} {'Status':<15}")
                    print("-" * 80)
                    for auth in auths:
                        print(f"{auth.auth_id:<15} {auth.rd_number:<20} {auth.payer_customer_id:<15} {auth.status:<15}")
                    print("-" * 80)

            elif choice == "2":
                auths = self.bank.rd_authorizations.get_authorizations_by_payer(customer.customer_id)
                if not auths:
                    print("\nYou have no RD authorizations as payer.")
                else:
                    print("\n" + "-" * 80)
                    print(f"{'Auth ID':<15} {'RD Number':<20} {'Beneficiary':<15} {'Status':<15}")
                    print("-" * 80)
                    for auth in auths:
                        print(f"{auth.auth_id:<15} {auth.rd_number:<20} {auth.beneficiary_customer_id:<15} {auth.status:<15}")
                    print("-" * 80)

            elif choice == "3":
                # Create as beneficiary
                my_rds = [rd for rd in self.bank.recurring_deposits.values() if rd.account_number == account.account_number and rd.status == "Active"]
                if not my_rds:
                    print("\n[FAIL] No active RDs found for this account to authorize.")
                    continue
                
                print("\nSelect RD to authorize:")
                for idx, rd in enumerate(my_rds, 1):
                    print(f"{idx}. {rd.rd_number} (Monthly: Rs. {rd.monthly_installment:,.2f})")
                
                try:
                    rd_idx = int(input(f"Select RD (1-{len(my_rds)}): "))
                    selected_rd = my_rds[rd_idx - 1]
                except (ValueError, IndexError):
                    print("Invalid selection.")
                    continue

                payer_id = input("Enter Payer Customer ID: ").strip()
                payer = self.bank.get_customer_by_id(payer_id)
                if not payer:
                    print(f"[FAIL] Customer {payer_id} not found.")
                    continue
                
                payer_accounts = self.bank.get_customer_accounts(payer)
                if not payer_accounts:
                    print(f"[FAIL] Payer {payer_id} has no active accounts.")
                    continue
                
                print("\nSelect Payer Account:")
                for idx, acc in enumerate(payer_accounts, 1):
                    print(f"{idx}. {acc.account_number} ({acc.account_type})")
                
                try:
                    acc_idx = int(input(f"Select Account (1-{len(payer_accounts)}): "))
                    payer_account = payer_accounts[acc_idx - 1]
                except (ValueError, IndexError):
                    print("Invalid selection.")
                    continue

                limit = self.app.read_positive_double("Monthly Payment Limit: Rs. ")
                
                success, msg, auth, otp = self.bank.rd_authorizations.create_authorization(
                    rd_number=selected_rd.rd_number,
                    beneficiary_customer_id=customer.customer_id,
                    beneficiary_account_number=account.account_number,
                    payer_customer_id=payer_id,
                    payer_account_number=payer_account.account_number,
                    monthly_limit=limit
                )
                
                if success:
                    print(msg)
                    print(f"CRITICAL: Share this OTP with the payer for verification: {otp}")
                    self.bank.save()
                else:
                    print(f"[FAIL] {msg}")

            elif choice == "4":
                # Verify as payer
                pending = self.bank.rd_authorizations.get_pending_authorizations_for_payer(customer.customer_id)
                if not pending:
                    print("\nNo pending authorizations found for you.")
                    continue
                
                print("\nPending Authorizations:")
                for idx, auth in enumerate(pending, 1):
                    print(f"{idx}. {auth.auth_id} (RD: {auth.rd_number} for {auth.beneficiary_customer_id})")
                
                try:
                    idx = int(input(f"Select to verify (1-{len(pending)}): "))
                    selected_auth = pending[idx - 1]
                except (ValueError, IndexError):
                    print("Invalid selection.")
                    continue
                
                otp = input("Enter 6-digit Verification OTP: ").strip()
                success, msg = self.bank.rd_authorizations.verify_authorization(selected_auth.auth_id, otp, customer.customer_id)
                
                if success:
                    print(f"\n{msg}")
                    self.bank.save()
                else:
                    print(f"\n{msg}")

            elif choice == "5":
                auth_id = input("Enter Authorization ID to revoke: ").strip()
                reason = input("Reason for revocation: ").strip()
                success, msg = self.bank.rd_authorizations.revoke_authorization(auth_id, reason, customer.customer_id)
                if success:
                    print(f"\n[SUCCESS] {msg}")
                    self.bank.save()
                else:
                    print(f"\n[FAIL] {msg}")

            elif choice == "6":
                break

    def view_rd_statement(self, customer: Customer, account: Account):
        """View RD Statement of Account"""
        my_rds = [rd for rd in self.bank.recurring_deposits.values() if rd.account_number == account.account_number]
        if not my_rds:
            print("\n[INFO] No RDs found for this account.")
            return

        print("\nSelect RD for Statement:")
        for idx, rd in enumerate(my_rds, 1):
            print(f"{idx}. {rd.rd_number} (Rs. {rd.monthly_installment:,.2f})")

        try:
            choice = int(input(f"\nEnter choice (1-{len(my_rds)}): "))
            selected_rd = my_rds[choice - 1]
        except (ValueError, IndexError):
            print("Invalid choice.")
            return

        statement_engine = RDStatement(self.bank)
        statement = statement_engine.get_rd_statement(selected_rd.rd_number)

        if not statement:
            print("[FAIL] Could not generate statement.")
            return

        print("\n" + "=" * 60)
        print("RD STATEMENT OF ACCOUNT")
        print("=" * 60)
        print(f"RD Number:      {statement['rd_number']}")
        print(f"Status:         {statement['status']}")
        print(f"Beneficiary:    {statement['beneficiary_name']}")
        print(f"Payee:          {statement['payee_name']}")
        print(f"Monthly:        Rs. {statement['monthly_installment']:,.2f}")
        print(f"Interest Rate:  {statement['interest_rate']}% p.a.")
        print(f"Paid:           {statement['installments_paid']}/{statement['tenure_months']}")
        print(f"Total Saved:    Rs. {statement['total_deposited']:,.2f}")
        print("-" * 60)
        print(f"{'Date':<15} {'Amount':<15} {'Installment #':<15} {'Method'}")
        print("-" * 60)
        for p in statement['payment_history']:
            p_date = datetime.fromisoformat(p['date']).strftime('%d-%m-%Y')
            print(f"{p_date:<15} Rs. {p['amount']:<13.2f} {p['installment_number']:<15} {p['method']}")
        print("-" * 60)
        input("\nPress Enter to continue...")
