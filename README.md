# 🏦 Scala Bank – Python Banking System v7.0

A comprehensive, feature-rich **banking simulation system** written in Python, mimicking real-world financial operations including credit scoring, loan processing, automated payments, card services, investments, international transfers, and **complete Income Tax Return (ITR) filing system**.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)]()
[![License](https://img.shields.io/badge/License-Private-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![Features](https://img.shields.io/badge/Features-100+-green.svg)]()

---

## 📌 Table of Contents

- [What's New in v7.0](#-whats-new-in-v70)
- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technical Highlights](#-technical-highlights)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Future Enhancements](#-future-enhancements)
- [Quick Start Guide](#-quick-start-guide)
- [Developer](#-developer)
- [License](#-license)

---

## 🎉 What's New in v7.0

### 🆕 Complete Income Tax Return (ITR) Filing System

The biggest update yet! A comprehensive tax management ecosystem that handles end-to-end ITR filing:

- ✅ **Automatic Deduction Detection**: Scans salary, credit card bills, recurring bills, and loan data to detect tax deductions across 5 sections (80C, 80D, 24, 10(13A), 16)
- ✅ **Form 16 Generation**: TDS certificates with employer details and quarterly breakdowns
- ✅ **Form 26AS**: Complete tax credit statement with TDS tracking and refund history
- ✅ **ITR Filing Workflow**: PAN registration → Deduction summary → Tax calculation → Filing → Status tracking
- ✅ **Smart Refund Processing**: Automatic refund calculation with direct credit and transaction logging
- ✅ **Filing History**: Multi-year filing support with void/amend functionality
- ✅ **Status Tracking**: Visual indicators (⏳📝✅💳) for filing status
- ✅ **UTF-8 Report Export**: Comprehensive ITR reports with rupee symbol support

### 🔧 Transaction System Enhancements

- ✅ **Card Network Detection**: Display VISA, MasterCard, RuPay in transaction history
- ✅ **Metadata Parsing**: Parse CSV string metadata for card/merchant info
- ✅ **Tax Refund Transactions**: New SALARY_TAX_REFUND transaction type
- ✅ **Lazy Loading**: On-demand transaction loading for faster startup

### 💼 Loan System Improvements

- ✅ **Loan Type Classification**: HOME, PERSONAL, EDUCATION, VEHICLE, BUSINESS
- ✅ **Tax Benefit Tracking**: Automatic Section 24 deduction for home loans
- ✅ **Interest Tracking**: Track deductible interest for tax purposes

### 🎯 Customer Management

- ✅ **PAN Registration**: Store and validate PAN for tax purposes
- ✅ **Password Recovery**: Secure OTP-based password reset
- ✅ **Enhanced Serialization**: Complete data persistence for all customer attributes

---

## 🎯 Overview

**Scala Bank** simulates enterprise-level banking workflows with:

✔ Multi-account & card support with transaction persistence

✔ CIBIL-based loan & credit card approval with credit monitoring

✔ Recurring bills, salary automation, & EMI logic

✔ Investment products (Fixed Deposits & Recurring Deposits)

✔ **Complete Income Tax Return (ITR) Filing System**

✔ **Tax deduction tracking & Form 16/26AS generation**

✔ **RD Authorization system with OTP verification**

✔ **Comprehensive RD Statement generation and export**

✔ International transfers with currency conversion

✔ Account closure formalities & reward points system

✔ Real-time transaction registry & analytics

✔ **CSV-based transaction persistence with metadata parsing**

✔ Fully integrated **time simulation** engine

📍 **Branch Details**

| Field       | Value       |
| ----------- | ----------- |
| IFSC Code   | SCBA0005621 |
| Branch Name | Jakkasandra |
| Branch Code | 5621        |

## ✨ Key Features

### � Income Tax Return (ITR) Filing System

**Complete Tax Management Ecosystem**

- **Automatic Tax Deduction Detection**:
  - Section 80C: EPF, PPF, ELSS, Life Insurance premiums (up to ₹1.5L)
  - Section 80D: Health insurance premiums (detected from bills & CC)
  - Section 24: Home loan interest deduction (up to ₹2L)
  - Section 10(13A): House Rent Allowance (HRA)
  - Section 16: Standard deduction (₹50,000)

- **ITR Filing Workflow**:
  - PAN registration and validation
  - Real-time gross income calculation (12-month projection)
  - Automatic TDS calculation (30% tax rate)
  - Comprehensive deduction summary from multiple sources
  - Expected refund/tax liability computation
  - Acknowledgment number generation
  - ITR status tracking (Filed, Refund Credited, Tax Paid, Amended)

- **Form Generation**:
  - **Form 16**: TDS certificate with employer details
  - **Form 26AS**: Tax credit statement with TDS tracking
  - **ITR Report**: Comprehensive filing report with UTF-8 support

- **Refund Processing**:
  - Automatic refund calculation
  - Direct credit to bank account
  - Transaction history integration
  - Form 26AS refund entry
  - Status tracking with visual indicators (⏳📝✅💳)

- **ITR Management**:
  - Filing history with complete audit trail
  - Void and amend functionality
  - Duplicate filing prevention
  - Multi-year filing support
  - CSV persistence for refund transactions

- **Tax Deduction Sources**:
  - Salary profile analysis
  - Credit card bill tracking (insurance premiums)
  - Recurring bill analysis (health insurance)
  - Home loan interest tracking
  - HRA calculation from salary components

### �📊 Transaction Management

- **Comprehensive Transaction History** with 20+ filtering options:
  - Quick views (Last 10, 20, 50, All)
  - Deposits & Withdrawals
  - NEFT, RTGS, Inter-Account, SWIFT transfers
  - Cheque transactions (cleared, deposited, bounced)
  - Salary & Tax transactions (including refunds)
  - Debit & Credit card transactions
  - Bill payments & Recurring bills
  - Loan EMI payments
  - Fees & charges

- **Enhanced Transaction Display**:
  - Automatic credit/debit categorization (30+ transaction types)
  - Card network detection (VISA, MasterCard, RuPay)
  - Metadata parsing for CSV-stored transactions
  - Real-time transaction summary with totals
  - Balance verification at each transaction

- **CSV-based Transaction Ledger**:
  - Complete audit trail in `account_activity.csv`
  - On-demand lazy loading for performance
  - Metadata string parsing (cardId, network, merchant, etc.)
  - Persistent transaction records across restarts
  - Support for legacy and modern transaction formats

- **Transaction Types**:
  - **Credits**: DEPOSIT, SALARY, SALARY_TAX_REFUND, NEFT_RECEIVED, RTGS_RECEIVED, LOAN_CREDIT, SWIFT_RECEIVED
  - **Debits**: WITHDRAW, EXPENSE, NEFT_SENT, RTGS_SENT, LOAN_EMI, TAX_DEDUCTED, CREDIT_CARD_PAYMENT, BILL_PAYMENT
  - **Special**: CREDIT_CARD_PURCHASE (tracked separately), RD_AUTH_PAYMENT (authorized deposits)

- **Cheque Persistence**:
  - Cheque books persisted to `data/cheques.json`
  - Cleared cheques retained across sessions
  - Full cheque lifecycle tracking

### 📋 Account Services

- Multi-account support with transaction history per account
- Real-time balance verification
- Transaction filtering by type, date range, or card
- Expense breakdown and categorization
- Account closure with comprehensive formalities

### � Cheque Management

- **Cheque issuance** with automatic cheque book management
- **Post-dated cheque** support (presentable from specified date)
- **Cheque clearing & settlement** with real-time balance verification
- **Cheque bouncing** when insufficient funds
  - Automatic bounce fee deduction (Rs. 500)
  - Clear bounce notification with reason
  - Integration with CIBIL scoring system
- **Cheque book tracking** with status management (used, unused, cancelled)
- **Bounce history** with detailed audit trail

### �💳 Card Services

**Debit Cards**

- VISA/Mastercard/RuPay networks
- Spending limits
- Block/Unblock functionality

**Credit Cards**

- Automatic credit limit evaluation using:
  - CIBIL score
  - Salary profile
  - Employer category
  - Debt-to-Income ratio
- Billing cycles, grace periods, rewards, and interest
- **Luhn algorithm** validation
- **Credit limit enhancement** based on usage patterns
- **Reward points system** with redemption options
- Bill payment with automatic reward points accumulation

### 💰 Loan Management

- EMI calculation (compound interest)
- Automated approval rules (score, income, DTI)
- Transaction-linked repayment history
- **Loan type classification** (HOME, PERSONAL, EDUCATION, VEHICLE, BUSINESS)
- **Tax benefit tracking** for home loans (Section 24 - up to ₹2L interest)
- **Loan closure certificates** with complete audit trail
- Multiple loan types support
- Pre-closure with penalty calculation
- EMI autopay with NACH integration

### 📊 CIBIL Credit Scoring

Weighted scoring model:

- Repayment history (35%)
- Utilization (30%)
- Credit mix, inquiries, account age…
- **Cheque bounce history** (new!)

Score categorization:

- **Excellent:** 750–900
- **Good:** 650–749
- **Average:** 550–649
- **Poor:** 300–549

**Cheque Bounce Impact (Progressive Penalty System)**

- **1st bounce:** -50 points
- **2nd bounce:** -75 additional points (-125 total)
- **3rd+ bounce:** -100 additional points per bounce
- **Credit Restriction:** Automatic at score ≤ 600
  - Customers flagged as credit-restricted
  - Cannot apply for new loans
  - Cannot enhance credit card limits
  - Monitored by admin reports
- **Bounce Tracking:** Customer bounce history with timestamps
- **Admin Reporting:**
  - `get_credit_restricted_customers()` – List of restricted customers
  - `get_customers_with_bounces()` – Top bouncy customers
  - `get_cibil_impact_summary()` – System-wide bounce statistics

### 💵 Salary & Bills Automation

- Automated salary credit (tax applied if > ₹18L/yr)
- Recurring bill engine with NACH mandate support
- Expense categorization (Netflix, utilities, rent…)
- **NACH ID generator** for automated payment authorizations
- Credit card bill payment via recurring bills with reward points

### 💎 Investment Products

**Fixed Deposits (FD)**

- Flexible tenure options (3–120 months)
- Competitive interest rates with senior citizen bonus
- Premature withdrawal with penalty
- Maturity processing with automatic credit
- Current value tracking

**Recurring Deposits (RD)**

- Monthly installment-based savings
- **RD Authorization System** – Allow others to pay your RD installments
  - OTP-based verification (6-digit code, 30-min expiry)
  - Secure multi-party payment setup
  - Real-time status tracking (Active, Pending, Revoked, Suspended)
  - Payment history and audit trail
  - Payer can pay for beneficiary's RD while beneficiary receives maturity amount
- **RD Statement of Accounts**
  - Comprehensive statement generation
  - Payment history tracking
  - Shows payee vs. beneficiary details
  - Export to text file
  - Displays autopay status and financial projections
- NACH authorization for auto-debit
- Interest calculation on maturity
- Penalty handling for missed payments
- Manual and automatic installment payment
- Premature closure with penalty calculation

### 🌍 International Banking

- **Cross-border transfers** with SWIFT/IBAN support
- Real-time currency conversion (10+ currencies)
- Integration with **International Bank Registry**
- Support for multiple foreign currencies
- Compliance with international transfer regulations
- Daily transfer limits with usage tracking
- Purpose-based transfer categorization

### ⏱️ Time Simulation System

- Fast-forward days/weeks/months
- Automatically processes:
  - EMI
  - Bills
  - Salaries
  - Random spending
  - Interest calculations
  - RD installments
  - RD authorized payments
  - FD maturities

### 📈 Financial Analytics

- Expense breakdown by category
- 7/30/90-day trends
- Full transaction history with metadata
- Account closure reports
- Investment portfolio tracking
- Reward points dashboard
- Credit card statement analysis

---

## 🏗️ System Architecture

```
Python-Bank/
├── backend/
│   ├── Account.py
│   ├── AccountClosure.py
│   ├── AddNewIntlAccounts.py
│   ├── Bank.py
│   ├── BankingApp.py
│   ├── BankClock.py
│   ├── Card.py
│   ├── CIBIL.py
│   ├── ClosureFormalities.py
│   ├── CreditEvaluator.py
│   ├── CreditLimitEnhancement.py
│   ├── Customer.py
│   ├── DataStore.py
│   ├── ExpenseSimulator.py
│   ├── FixedDeposit.py
│   ├── Form16.py                        # NEW: TDS certificate generation
│   ├── Form26AS.py                      # NEW: Tax credit statement
│   ├── InternationalBankRegistry.py
│   ├── InternationalTransfer.py
│   ├── ITRFiling.py                     # NEW: Complete ITR system
│   ├── loan.py
│   ├── LoanEvaluator.py
│   ├── MainInterface.py
│   ├── NachIdGenerator.py
│   ├── PasswordRecovery.py
│   ├── RDAuthorization.py
│   ├── RDStatement.py
│   ├── RecurringBill.py
│   ├── RecurringDeposit.py
│   ├── RewardPointsManager.py
│   ├── SalaryProfile.py
│   ├── Serializers.py
│   ├── TaxCalculator.py                 # NEW: Tax computation engine
│   ├── TaxDeductionAnalyzer.py          # NEW: Auto deduction detection
│   ├── TaxExemption.py                  # NEW: Exemption calculations
│   ├── Transaction.py
│   ├── TransactionRegistry.py
│   └── verify_transfer.py
├── data/
│   ├── account_activity.csv             # Primary transaction ledger
│   ├── accounts.csv                     # Basic account data
│   ├── customers.json                   # Customer profiles with PAN
│   ├── loans.json                       # Loan records with type
│   ├── fixed_deposits.json
│   ├── recurring_deposits.json
│   ├── cheques.json
│   ├── rd_authorizations.json
│   └── bank_data.json                   # Complex objects (ITR filings)
└── tests/                                # Comprehensive test suite
```

🗄️ **Data Persistence**

- **CSV-based Activity Ledger** (`account_activity.csv`):
  - Complete audit trail of all account transactions
  - 30+ transaction types (DEPOSIT, SALARY, SALARY_TAX_REFUND, WITHDRAW, NEFT_SENT, etc.)
  - On-demand lazy loading with metadata string parsing
  - Timestamp, amount, and balance verification for each entry
  - Card network and merchant information preservation
  - Support for tax refund transactions with ITR metadata

- **JSON Storage** for object persistence:
  - `bank_data.json` – Complex objects (ITR filings with full history)
  - `accounts.json` – Account objects, balances, and ITR filing records
  - `customers.json` – Customer profiles, KYC, and PAN details
  - `loans.json` – Loan records with type classification and EMI history
  - `fixed_deposits.json` – FD contracts and maturity tracking
  - `recurring_deposits.json` – RD agreements and payment records
  - `cheques.json` – Cheque book and cleared cheque tracking
  - `rd_authorizations.json` – RD authorization records with OTP
  - `transaction_ids.json` – Unique transaction ID registry
  - `activity.log` – Application event log with error traces

---

## 🎯 Technical Highlights

### Architecture Patterns

- **Lazy Loading**: Transactions loaded on-demand for optimal memory usage
- **Atomic Operations**: Temp files + atomic rename for crash-safe persistence
- **Metadata Parsing**: Dual support for dict and CSV string metadata formats
- **Event Sourcing**: Complete audit trail via CSV activity ledger
- **Time Simulation**: Advance clock to trigger recurring events

### Key Algorithms

- **Luhn Algorithm**: Credit card number validation
- **Compound Interest**: Accurate EMI and FD/RD interest calculations
- **CIBIL Scoring**: Multi-factor weighted credit score (300-900)
- **Tax Computation**: Section-wise deduction detection and ITR calculation
- **Currency Conversion**: Real-time forex rates for international transfers

### Data Integrity

- **Transaction Verification**: Balance reconciliation at every step
- **Duplicate Prevention**: Unique transaction IDs with blacklist filtering
- **Cheque Lifecycle**: Full state tracking (issued → cleared/bounced)
- **ITR Filing Control**: Prevent duplicate filings per financial year
- **Error Handling**: Comprehensive exception management with traceback logging

### Performance Optimizations

- **CSV-based Persistence**: Fast read/write without database overhead
- **Lazy Account Loading**: Load accounts without transaction history
- **On-demand Trans Loading**: Fetch transactions only when needed
- **Parallel Operations**: Independent data saves in sequence
- **Memory Efficiency**: Avoid loading entire dataset into memory

---

## 🚀 Installation

### Requirements

- **Python 3.13** or above (tested on 3.13)
- No external dependencies (uses standard library only)

### Setup Steps

```bash
git clone https://github.com/kv-techie/Python-Bank.git
cd Python-Bank/backend
```

Create a virtual environment (optional):

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # macOS/Linux
```

Run the app:

```bash
python MainInterface.py
```

---

## 💻 Usage (Quick Guide)

| Action                       | Path                                                  |
| ---------------------------- | ----------------------------------------------------- |
| Create Account               | Main Menu → Open New Account                          |
| **View Transaction History** | **Account Menu → View Transaction History**           |
| **Filter by Type**           | **History Menu → Deposits/Withdrawals/SWIFT**         |
| Set Salary                   | Manage Salary → Configure Salary                      |
| **Register PAN**             | **Tax Planning → Register/Update PAN**                |
| **View Tax Deductions**      | **Tax Planning → View Deduction Summary**             |
| **Generate Form 16**         | **Tax Planning → Generate Form 16 (TDS Certificate)** |
| **View Form 26AS**           | **Tax Planning → View Form 26AS (Tax Credit)**        |
| **File ITR**                 | **Tax Planning → File Income Tax Return**             |
| **View ITR History**         | **Tax Planning → View ITR Filing History**            |
| **Process Tax Refund**       | **Tax Planning → View ITR History → Process Refund**  |
| Apply Credit Card            | Card Management → Apply                               |
| Make Purchases               | Card Management → Spend                               |
| Open Fixed Deposit           | Investment → Fixed Deposit                            |
| Start Recurring Deposit      | Investment → Recurring Deposit                        |
| **Create RD Authorization**  | **Investment → RD Authorization → Create**            |
| **Verify RD Authorization**  | **Investment → RD Authorization → Verify**            |
| **View RD Statement**        | **Investment → View RD Statement**                    |
| **Export RD Statement**      | **Investment → View RD Statement → Export**           |
| International Transfer       | Transfers → International                             |
| Close Account                | Account Services → Close Account                      |
| Enhance Credit Limit         | Card Management → Request Enhancement                 |
| Redeem Reward Points         | Card Management → Rewards                             |
| Simulate Time                | Fast Forward → Select Days                            |

Each operation prints the results + audit logs.

---

## 📁 Project Structure

| Layer          | Files                                                                              | Responsibilities                                    |
| -------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------- |
| Core Banking   | Account, Bank, Customer, AccountClosure                                            | Accounts, balance, KYC, closures                    |
| Transactions   | Transaction, TransactionRegistry, DataStore                                        | Transaction types, classification, persistence      |
| **Tax System** | **ITRFiling, TaxCalculator, TaxDeductionAnalyzer, TaxExemption, Form16, Form26AS** | **ITR filing, tax computation, deduction tracking** |
| Cards          | Card, CreditEvaluator, CreditLimitEnhancement, RewardPointsManager                 | Debit/Credit card engine & rewards                  |
| Credit/Loans   | CIBIL, LoanEvaluator, loan, ClosureFormalities                                     | Score, approval & closures                          |
| Investments    | FixedDeposit, RecurringDeposit, RDAuthorization, RDStatement                       | FD/RD management, auth & statements                 |
| International  | InternationalTransfer, InternationalBankRegistry, AddNewIntlAccounts               | Cross-border transactions                           |
| Automation     | RecurringBill, SalaryProfile, ExpenseSimulator, NachIdGenerator                    | Auto-pay, spending & NACH                           |
| Infrastructure | BankClock, DataStore, Serializers, PasswordRecovery                                | Time, persistence, auditing & security              |
| UI             | BankingApp, MainInterface                                                          | CLI menus & user interface                          |

> **~10,000+ lines of Python** across modular components with comprehensive tax integration.

---

## 🧪 Testing & Quality Assurance

### Test Suite Coverage

The system includes **50+ comprehensive test cases** covering:

- **Integration Tests**:
  - `test_datastore_integration.py` – Data persistence and loading
  - `test_fd_rd_integration.py` – Fixed and Recurring Deposit workflows
  - `test_rd_integration.py` – RD lifecycle and maturity
  - `test_beneficiary_system.py` – Beneficiary management
  - `test_account_closure_integration.py` – Account closure workflows

- **Feature Tests**:
  - `test_autopay.py` – Automatic payment processing
  - `test_credit_limit_enhancement.py` – Credit limit increases
  - `test_fixed_deposit.py` – FD creation and maturity
  - `test_recurring_deposit.py` – RD installments and tracking
  - `test_international_transfer.py` – Cross-border payments
  - `test_password_recovery.py` – Account security
  - `test_reward_points_manager.py` – Reward point accumulation

- **Tax System Tests**:
  - `test_salary_profile.py` – Salary configuration and TDS
  - Tax deduction detection validation
  - ITR filing workflow verification
  - Form generation accuracy

- **Authorization Tests**:
  - `test_rd_authorization.py` – Authorization creation and verification
  - `test_rd_authorization_otp.py` – OTP validation
  - `test_rd_statement_compatibility.py` – Statement generation

- **Simulation Tests**:
  - `test_rd_autopay_simulation.py` – Autopay scenarios
  - `test_backward_compatibility.py` – Data migration

### Running Tests

```bash
cd tests
python run_all_tests.py          # Run complete test suite
python test_specific_feature.py  # Run individual test
```

### Quality Metrics

- ✅ **100% Critical Path Coverage**: All core banking operations tested
- ✅ **Data Integrity Validation**: Balance reconciliation checks
- ✅ **Transaction Persistence**: CSV/JSON data consistency verified
- ✅ **Error Handling**: Exception cases with proper recovery
- ✅ **Performance Testing**: Startup timing and transaction load tests

---

## 🔮 Future Enhancements

- ✅ ~~Tax document generation (Form 16 & Form 26AS)~~ **IMPLEMENTED**
- ✅ ~~Complete ITR filing system~~ **IMPLEMENTED**
- Web interface (React/Flask)
- MongoDB/PostgreSQL migration for scalability
- REST API with authentication (JWT)
- ATM simulation with card-based operations
- Mutual Funds & SIP with NAV tracking
- Advanced multi-currency wallet system
- PDF export for all statements and reports
- CI/CD pipeline & Docker containerization
- AI-powered fraud detection & anomaly alerts
- Mobile app integration (React Native)
- Biometric authentication (fingerprint/face ID)
- Real-time push notifications
- Blockchain-based transaction verification
- Advanced analytics dashboard with charts
- Customer support chatbot
- Multi-language support (i18n)

---

## � Quick Start Guide

### First Time Setup

1. **Clone and Run**

   ```bash
   git clone https://github.com/kv-techie/Python-Bank.git
   cd Python-Bank/backend
   python MainInterface.py
   ```

2. **Create Your Account**
   - Select "Open New Account"
   - Complete KYC details
   - Set username and password
   - Note your account number

3. **Configure Salary**
   - Go to "Manage Salary" → "Configure Salary"
   - Enter monthly salary (₹350,000 recommended)
   - Choose employer category (FORTUNE_500 for best benefits)

4. **Register PAN for Tax**
   - Go to "Tax Planning" → "Register/Update PAN"
   - Enter your 10-character PAN (e.g., ABCDE1234F)

### Essential First Steps

1. **Get a Credit Card**
   - "Card Management" → "Apply for Credit Card"
   - Approval based on CIBIL score & salary

2. **Setup Recurring Bills**
   - "Recurring Bills" → "Add New Bill"
   - Add insurance, utilities, etc. for auto-deduction tracking

3. **Make Some Transactions**
   - Deposit money using cards
   - Make credit card purchases
   - Pay bills

4. **Fast Forward Time**
   - "Fast Forward" → Choose duration
   - System processes salary, EMIs, bills automatically

5. **File Your ITR**
   - "Tax Planning" → "View Deduction Summary" (see all deductions)
   - "Tax Planning" → "File Income Tax Return"
   - Review and confirm filing
   - "Tax Planning" → "View ITR Filing History" → Process refund

### Sample Workflow

**Goal: File ITR and get ₹120,000 refund**

```
1. Create account → Set salary ₹350,000/month
2. Register PAN → File ITR
3. Fast forward 10 months to accumulate TDS
4. Add home loan (₹62L) for Section 24 deduction
5. Setup health insurance bill for Section 80D
6. File ITR → Expected refund: ₹120,000
7. Process refund → Check transaction history
```

---

## �👨‍💻 Developer

**Kedhar Vinod**
🧑‍🎓 Jain (Deemed-to-be) University, Bengaluru
🔗 GitHub: [@kv-techie](https://github.com/kv-techie)

---

## 📄 License

**Private & Proprietary**
_For educational use only. Not connected to real banks._

---
