from datetime import datetime
from typing import Dict, List, Tuple
from .Bank import Bank
from .AdminAnalytics import AdminAnalytics


class AdminControlPanel:
    """Bank Admin Dashboard - Complete visibility into all operations"""
    
    def __init__(self, bank: Bank):
        self.bank = bank
        self.analytics = AdminAnalytics(bank)
        self.last_login = None
        self.session_active = False
        from .DataStore import DataStore
        self.admin_pin = DataStore.load_admin_pin()

    
    def authenticate(self, admin_pin: str) -> bool:
        """Simple admin authentication"""
        if admin_pin == self.admin_pin:
            self.session_active = True
            self.last_login = datetime.now()
            return True
        return False

    
    def display_dashboard(self) -> None:
        """Display complete admin dashboard"""
        if not self.session_active:
            print("[FAIL] Session expired. Please re-authenticate.")
            return
        
        while True:
            print("\n" + "="*80)
            print("[BANK] BANK ADMIN DASHBOARD - CONTROL PANEL".center(80))
            print("="*80)
            print(f"Last Login: {self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else 'N/A'}")
            print("\nSelect Section to View:")
            print("-" * 80)
            print("1. Bank Overview")
            print("2. Revenue Analytics")
            print("3. Loan Portfolio")
            print("4. Credit Card Analysis")
            print("5. Deposit & Investment Portfolio")
            print("6. Transaction Insights")
            print("7. Risk Management Dashboard")
            print("8. Customer Metrics")
            print("9. Change Admin PIN")
            print("0. Back to Main Menu")
            print("-" * 80)
            
            # First-use check
            if self.admin_pin == "1234":
                print("\n" + "!" * 80)
                print("[SECURITY] YOU ARE USING THE DEFAULT ADMIN PIN (1234)".center(80))
                print("[ACTION] YOU MUST CHANGE YOUR PIN BEFORE PROCEEDING".center(80))
                print("!" * 80)
                self._change_admin_pin()
                continue

            choice = input("Enter your choice (0-9): ").strip()

            
            if choice == "1":
                self._section_bank_overview()
            elif choice == "2":
                self._section_revenue_analytics()
            elif choice == "3":
                self._section_loan_portfolio()
            elif choice == "4":
                self._section_credit_analysis()
            elif choice == "5":
                self._section_deposit_portfolio()
            elif choice == "6":
                self._section_transaction_insights()
            elif choice == "7":
                self._section_risk_management()
            elif choice == "8":
                self._section_customer_metrics()
            elif choice == "9":
                self._change_admin_pin()
            elif choice == "0":
                print("\n[OK] Returning to main menu...")
                break

            else:
                print("[FAIL] Invalid choice. Please try again.")
    
    def _change_admin_pin(self) -> None:
        """Change the Admin Dashboard PIN"""
        print("\n" + "-"*40)
        print("🔐 CHANGE ADMIN PIN")
        print("-"*40)
        
        new_pin = input("Enter new 4-6 digit PIN: ").strip()
        if not (new_pin.isdigit() and 4 <= len(new_pin) <= 6):
            print("[FAIL] Invalid PIN format. Must be 4-6 digits.")
            return
            
        confirm_pin = input("Confirm new PIN: ").strip()
        if new_pin != confirm_pin:
            print("[FAIL] PINs do not match.")
            return
            
        # Save PIN
        from .DataStore import DataStore
        DataStore.save_admin_pin(new_pin)
        self.admin_pin = new_pin
        print(f"[SUCCESS] Admin PIN updated successfully.")

    
    def _section_bank_overview(self) -> None:
        """Section 1: Bank Overview"""
        print("\n" + "="*80)
        print("[STATS] SECTION 1: BANK OVERVIEW".center(80))
        print("="*80)
        
        overview = self.analytics.get_bank_overview()
        
        print(f"\nTotal Customers: {overview['total_customers']}")
        print(f"Total Accounts: {overview['total_accounts']}")
        print(f"Total Deposits (All Accounts): ₹{overview['total_deposits']:,.2f}")
        print(f"Total Outstanding Loans: ₹{overview['total_loans']:,.2f}")
        print(f"Net Bank Assets: ₹{overview['net_assets']:,.2f}")
        
        print("\n--- Account Types Distribution ---")
        for acc_type, count in overview['account_type_distribution'].items():
            print(f"  {acc_type}: {count} accounts")
        
        print("\n--- Account Status ---")
        for status, count in overview['account_status'].items():
            print(f"  {status}: {count} accounts")
        
        input("\nPress Enter to continue...")
    
    def _section_revenue_analytics(self) -> None:
        """Section 2: Revenue Analytics"""
        print("\n" + "="*80)
        print("[MONEY] SECTION 2: REVENUE ANALYTICS".center(80))
        print("="*80)
        
        revenue = self.analytics.get_revenue_analytics()
        
        print(f"\n--- Fee & Penalty Revenue ---")
        print(f"  AMB Fees (Annual Maintenance): ₹{revenue['amb_fees']:,.2f}")
        print(f"  SWIFT Transfer Charges: ₹{revenue['swift_charges']:,.2f}")
        print(f"  Loan Prepayment Penalties: ₹{revenue['loan_penalties']:,.2f}")
        print(f"  RD Early Withdrawal Penalties: ₹{revenue['rd_penalties']:,.2f}")
        print(f"  RD Late Payment Penalties: ₹{revenue['rd_late_penalties']:,.2f}")
        
        total_fees = (revenue['amb_fees'] + revenue['swift_charges'] + 
                     revenue['loan_penalties'] + revenue['rd_penalties'] + 
                     revenue['rd_late_penalties'])
        print(f"\n  TOTAL FEE REVENUE: ₹{total_fees:,.2f}")
        
        print(f"\n--- Interest Revenue ---")
        print(f"  Total Interest Earned (Loans): ₹{revenue['loan_interest']:,.2f}")
        print(f"  Total Interest Paid (Deposits): ₹{revenue['deposit_interest']:,.2f}")
        
        print(f"\n--- Net Revenue ---")
        net = revenue['loan_interest'] - revenue['deposit_interest'] + total_fees
        print(f"  Net Interest Margin + Fees: ₹{net:,.2f}")
        
        input("\nPress Enter to continue...")
    
    def _section_loan_portfolio(self) -> None:
        """Section 3: Loan Portfolio"""
        print("\n" + "="*80)
        print("[INFO] SECTION 3: LOAN PORTFOLIO".center(80))
        print("="*80)
        
        loans = self.analytics.get_loan_portfolio()
        
        print(f"\n--- Loan Summary ---")
        print(f"Total Loans: {loans['total_loans']}")
        print(f"Active Loans: {loans['active_loans']}")
        print(f"Closed Loans: {loans['closed_loans']}")
        
        print(f"\n--- Outstanding Balance ---")
        print(f"Total Outstanding: ₹{loans['total_outstanding']:,.2f}")
        
        print(f"\n--- Breakdown by Type ---")
        for loan_type, details in loans['by_type'].items():
            print(f"\n  {loan_type}:")
            print(f"    Count: {details['count']}")
            print(f"    Outstanding: ₹{details['outstanding']:,.2f}")
            print(f"    Avg Amount: ₹{details['avg_amount']:,.2f}")
        
        if loans['overdue_loans'] > 0:
            print(f"\n[WARN]  OVERDUE LOANS: {loans['overdue_loans']}")
        
        if loans['high_default_risk'] > 0:
            print(f"[WARN]  HIGH DEFAULT RISK: {loans['high_default_risk']}")
        
        input("\nPress Enter to continue...")
    
    def _section_credit_analysis(self) -> None:
        """Section 4: Credit Card Analysis"""
        print("\n" + "="*80)
        print("💳 SECTION 4: CREDIT CARD ANALYSIS".center(80))
        print("="*80)
        
        cards = self.analytics.get_credit_card_analysis()
        
        print(f"\n--- Card Statistics ---")
        print(f"Total Credit Cards Issued: {cards['total_cards']}")
        print(f"Active Cards: {cards['active_cards']}")
        print(f"Blocked Cards: {cards['blocked_cards']}")
        
        print(f"\n--- Credit Utilization ---")
        print(f"Total Limit Issued: ₹{cards['total_limit']:,.2f}")
        print(f"Total Balance Outstanding: ₹{cards['total_outstanding']:,.2f}")
        print(f"Avg Utilization Rate: {cards['avg_utilization']:.1f}%")
        
        print(f"\n--- Auto-Pay Policies ---")
        for policy, count in cards['auto_pay_distribution'].items():
            print(f"  {policy}: {count} cards")
        
        print(f"\n--- CIBIL Score Distribution ---")
        for score_range, count in cards['cibil_distribution'].items():
            print(f"  {score_range}: {count} customers")
        
        if cards['high_utilization_count'] > 0:
            print(f"\n[WARN]  HIGH UTILIZATION (>80%): {cards['high_utilization_count']} cards")
        
        if cards['default_count'] > 0:
            print(f"[WARN]  DEFAULTS: {cards['default_count']} cardholder accounts")
        
        input("\nPress Enter to continue...")
    
    def _section_deposit_portfolio(self) -> None:
        """Section 5: Deposit & Investment Portfolio"""
        print("\n" + "="*80)
        print("🏧 SECTION 5: DEPOSIT & INVESTMENT PORTFOLIO".center(80))
        print("="*80)
        
        deposits = self.analytics.get_deposit_portfolio()
        
        print(f"\n--- Fixed Deposits ---")
        print(f"Total FD Accounts: {deposits['fd_count']}")
        print(f"Total FD Amount: ₹{deposits['fd_total']:,.2f}")
        print(f"Avg FD Amount: ₹{deposits['fd_avg']:,.2f}")
        
        print(f"\n--- Recurring Deposits ---")
        print(f"Total RD Accounts: {deposits['rd_count']}")
        print(f"Total RD Total Value: ₹{deposits['rd_total']:,.2f}")
        print(f"Active RD Accounts: {deposits['rd_active']}")
        print(f"Completed RD Accounts: {deposits['rd_completed']}")
        
        print(f"\n--- Upcoming Maturities ---")
        for period, count in deposits['upcoming_maturities'].items():
            print(f"  {period}: {count} deposits")
        
        print(f"\n--- Interest Expense ---")
        print(f"Total FD Interest Paid: ₹{deposits['fd_interest_paid']:,.2f}")
        print(f"Total RD Interest Paid: ₹{deposits['rd_interest_paid']:,.2f}")
        print(f"Combined Interest Expense: ₹{deposits['total_interest_expense']:,.2f}")
        
        input("\nPress Enter to continue...")
    
    def _section_transaction_insights(self) -> None:
        """Section 6: Transaction Insights"""
        print("\n" + "="*80)
        print("[UP] SECTION 6: TRANSACTION INSIGHTS".center(80))
        print("="*80)
        
        transactions = self.analytics.get_transaction_insights()
        
        print(f"\n--- Transaction Volume ---")
        print(f"Total Transactions: {transactions['total_transactions']}")
        print(f"Total Volume (Amount): ₹{transactions['total_volume']:,.2f}")
        
        print(f"\n--- Top Transaction Types ---")
        for idx, (trans_type, count) in enumerate(transactions['top_types'], 1):
            print(f"  {idx}. {trans_type}: {count} transactions")
        
        print(f"\n--- Daily Average ---")
        print(f"Avg Transactions/Day: {transactions['avg_per_day']:.1f}")
        print(f"Avg Amount/Transaction: ₹{transactions['avg_amount']:,.2f}")
        
        print(f"\n--- Credit vs Debit ---")
        print(f"Total Credits: ₹{transactions['total_credits']:,.2f} ({transactions['credit_count']} txns)")
        print(f"Total Debits: ₹{transactions['total_debits']:,.2f} ({transactions['debit_count']} txns)")
        
        input("\nPress Enter to continue...")
    
    def _section_risk_management(self) -> None:
        """Section 7: Risk Management Dashboard"""
        print("\n" + "="*80)
        print("[WARN]  SECTION 7: RISK MANAGEMENT DASHBOARD".center(80))
        print("="*80)
        
        risk = self.analytics.get_risk_management()
        
        print(f"\n--- Account Health ---")
        print(f"Accounts with Low Balance (<Min Required): {risk['low_balance_accounts']}")
        print(f"Accounts in Overdraft: {risk['overdraft_accounts']}")
        print(f"Accounts with Negative Balance: {risk['negative_balance_accounts']}")
        
        print(f"\n--- Loan Health ---")
        print(f"Active Loans: {risk['active_loans']}")
        print(f"Overdue Loans: {risk['overdue_loans']}")
        print(f"Loan Default Risk (High): {risk['high_default_risk']}")
        print(f"Total Overdue Amount: ₹{risk['overdue_amount']:,.2f}")
        
        print(f"\n--- Credit Health ---")
        print(f"High Utilization Cards (>80%): {risk['high_utilization_cards']}")
        print(f"Overdue Credit Card Accounts: {risk['overdue_credit_accounts']}")
        print(f"Total Overdue Credit Amount: ₹{risk['overdue_credit_amount']:,.2f}")
        
        print(f"\n--- Deposit Health ---")
        print(f"Overdue RD Payments: {risk['overdue_rd_payments']}")
        
        risk_score = risk['risk_score']
        if risk_score < 25:
            risk_level = "🟢 LOW RISK"
        elif risk_score < 50:
            risk_level = "🟡 MODERATE RISK"
        elif risk_score < 75:
            risk_level = "🟠 HIGH RISK"
        else:
            risk_level = "🔴 CRITICAL RISK"
        
        print(f"\n--- Overall Risk Score ---")
        print(f"Risk Level: {risk_level} ({risk_score}%)")
        
        input("\nPress Enter to continue...")
    
    def _section_customer_metrics(self) -> None:
        """Section 8: Customer Metrics"""
        print("\n" + "="*80)
        print("👥 SECTION 8: CUSTOMER METRICS".center(80))
        print("="*80)
        
        customers = self.analytics.get_customer_metrics()
        
        print(f"\n--- Customer Base ---")
        print(f"Total Customers: {customers['total_customers']}")
        print(f"Active Customers: {customers['active_customers']}")
        print(f"Inactive Customers: {customers['inactive_customers']}")
        
        print(f"\n--- Customer Demographics ---")
        print(f"Average Age: {customers['avg_age']:.1f} years")
        print(f"Age Range: {customers['age_min']}-{customers['age_max']} years")
        
        print(f"\n--- Top Cities ---")
        for city, count in customers['top_cities'].items():
            print(f"  {city}: {count} customers")
        
        print(f"\n--- Account Ownership per Customer ---")
        print(f"Avg Accounts/Customer: {customers['avg_accounts_per_customer']:.1f}")
        print(f"Avg Loans/Customer: {customers['avg_loans_per_customer']:.1f}")
        print(f"Avg Cards/Customer: {customers['avg_cards_per_customer']:.1f}")
        
        print(f"\n--- Customer Value ---")
        print(f"Total Customer Asset Value: ₹{customers['total_assets']:,.2f}")
        print(f"Avg Asset Value/Customer: ₹{customers['avg_asset_per_customer']:,.2f}")
        
        input("\nPress Enter to continue...")
