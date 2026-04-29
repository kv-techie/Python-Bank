import sys
import os
import json
from datetime import date, datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.Bank import Bank
from backend.Customer import Customer
from backend.Account import Account
from backend.BankClock import BankClock, switch_to_virtual_mode
from backend.Transaction import Transaction

def log_test(module, name, success, message=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{module}] {status}: {name} {message}")

def run_comprehensive_tests():
    print("=" * 80)
    print("          SCALA BANK - COMPREHENSIVE MODULE TEST SUITE")
    print("=" * 80)
    
    switch_to_virtual_mode()
    bank = Bank()
    
    # 1. Account Management & Auth
    print("\n[MODULE 1: AUTH & ACCOUNT MANAGEMENT]")
    username = f"testuser_{int(datetime.now().timestamp())}"
    password = "Password123!"
    
    try:
        # Registration
        customer, account = bank.register_customer(
            username=username,
            password=password,
            first_name="Test",
            last_name="User",
            dob="1990-01-01",
            gender="Male",
            phone_number="9876543210",
            email=f"{username}@example.com",
            account_type="Pride"
        )
        # Set Profile for further tests
        customer.salary = 150000
        customer.cibil_score = 820
        customer.job_start_date = "2020-01-01"
        customer.employer_category = "A"
        customer.city = "Bengaluru"
        customer.kyc_completed = True
        
        log_test("AUTH", "Customer Registration", True, f"ID: {customer.customer_id}")
        
        # Authentication
        auth_cust = bank.authenticate(username, password)
        log_test("AUTH", "Authentication", auth_cust is not None and auth_cust.username == username)
        
    except Exception as e:
        log_test("AUTH", "Registration/Auth", False, str(e))

    # 2. Financial Operations
    print("\n[MODULE 2: FINANCIAL OPERATIONS]")
    try:
        # Deposit
        initial_balance = account.balance
        account.deposit(5000, mode="CASH")
        log_test("FINANCE", "Deposit", account.balance == initial_balance + 5000)
        
        # Withdrawal
        account.withdraw(1000, mode="CASH")
        log_test("FINANCE", "Withdrawal", account.balance == initial_balance + 4000)
        
        # Internal Transfer
        recipient_username = "vinked"
        recipient_cust = bank.get_customer(recipient_username)
        if recipient_cust:
            recipient_acc = bank.get_account(recipient_cust.get_account_numbers()[0])
            old_recipient_bal = recipient_acc.balance
            account.transfer(recipient_acc, 500, "INTER_ACCOUNT")
            log_test("FINANCE", "Internal Transfer", recipient_acc.balance == old_recipient_bal + 500)
        else:
            log_test("FINANCE", "Internal Transfer", False, "Recipient vinked not found")
            
    except Exception as e:
        log_test("FINANCE", "Operations", False, str(e))

    # 3. Loans Module
    print("\n[MODULE 3: LOANS]")
    try:
        principal = 50000
        rate = 10.5
        tenure = 12
        approved, loan, reason = bank.evaluate_and_add_loan(
            customer=customer,
            principal=principal,
            interest_rate=rate,
            tenure_months=tenure,
            account=account,
            loan_type="PERSONAL"
        )
        log_test("LOANS", "Loan Application/Approval", approved, reason)
        
        if loan:
            log_test("LOANS", "Loan Disbursal", account.balance >= principal)
            
            # Pay EMI
            old_emis = loan.emis_paid
            bank.pay_emi_for_loan(loan.loan_id, account.account_number)
            log_test("LOANS", "EMI Payment", loan.emis_paid == old_emis + 1)
            
    except Exception as e:
        log_test("LOANS", "Module Error", False, str(e))

    # 4. Cards Module
    print("\n[MODULE 4: CARDS]")
    try:
        # Debit Card
        debit_card = bank.issue_debit_card(customer, account)
        log_test("CARDS", "Debit Card Issuance", debit_card is not None)
        
        # Credit Card
        credit_card = bank.issue_credit_card(customer, account, 100000)
        log_test("CARDS", "Credit Card Issuance", credit_card is not None)
        
        # Set PIN
        credit_card.set_pin("1234")
        success, msg = credit_card.verify_pin("1234")
        log_test("CARDS", "PIN Setting", success, msg)
        
        # Purchase
        success, msg, txn_id = credit_card.make_purchase(500, "Amazon", "Shopping", account)
        log_test("CARDS", "Card Purchase", success, msg)
        
    except Exception as e:
        log_test("CARDS", "Module Error", False, str(e))

    # 5. Deposits (FD/RD)
    print("\n[MODULE 5: DEPOSITS]")
    try:
        # Fixed Deposit
        fd_amount = 10000
        # Signature: create_fixed_deposit(account, principal_amount, tenure_months)
        success, msg, fd = bank.create_fixed_deposit(account, fd_amount, 12)
        log_test("DEPOSITS", "FD Creation", success, msg if not success else f"ID: {fd.fd_number}")
        
        # Recurring Deposit
        rd_amount = 2000
        # Signature: create_recurring_deposit(account, monthly_installment, tenure_months, enable_autopay, autopay_day)
        success, msg, rd = bank.create_recurring_deposit(account, rd_amount, 12, enable_autopay=True, autopay_day=BankClock.today().day)
        log_test("DEPOSITS", "RD Creation", success, msg if not success else f"ID: {rd.rd_number}")
        
    except Exception as e:
        log_test("DEPOSITS", "Module Error", False, str(e))

    # 6. Tax & CIBIL
    print("\n[MODULE 6: TAX & CIBIL]")
    try:
        from backend.TaxCalculator import TaxCalculator
        from backend.CIBIL import calculate_cibil_score
        
        # Tax Calculation
        tax_calc = TaxCalculator(customer, bank)
        summary = tax_calc.get_tax_summary()
        log_test("TAX", "Tax Summary Generation", summary is not None)
        
        # CIBIL
        score = calculate_cibil_score(customer, bank)
        log_test("CIBIL", "Score Calculation", score >= 300, f"Score: {score}")
        
    except Exception as e:
        log_test("TAX/CIBIL", "Module Error", False, str(e))

    print("\n" + "=" * 80)
    print("                TEST SUITE EXECUTION COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    run_comprehensive_tests()
