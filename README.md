# 🏦 Scala Bank – Python Banking System v6.0

A comprehensive, feature-rich **banking simulation system** written in Python, mimicking real-world financial operations such as credit scoring, loan processing, automated payments, card services, investments, and international transfers.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()
[![License](https://img.shields.io/badge/License-Private-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Future Enhancements](#-future-enhancements)
- [Developer](#-developer)
- [License](#-license)

---

## 🎯 Overview

**Scala Bank** simulates enterprise-level banking workflows with:

✔ Multi-account & card support

✔ CIBIL-based loan & credit card approval

✔ Recurring bills, salary automation, & EMI logic

✔ Investment products (Fixed Deposits & Recurring Deposits)

✔ **RD Authorization system with OTP verification**

✔ **Comprehensive RD Statement generation and export**

✔ International transfers with currency conversion

✔ Account closure formalities & reward points system

✔ Real-time transaction registry & analytics

✔ Fully integrated **time simulation** engine

📍 **Branch Details**

| Field       | Value       |
| ----------- | ----------- |
| IFSC Code   | SCBA0005621 |
| Branch Name | Jakkasandra |
| Branch Code | 5621        |

---

## ✨ Key Features

### 📊 Transaction Management

- **Comprehensive Transaction History** with 20+ filtering options:
  - Quick views (Last 10, 20, 50, All)
  - Deposits & Withdrawals
  - NEFT, RTGS, Inter-Account, SWIFT transfers
  - Cheque transactions (cleared, deposited, bounced)
  - Salary & Tax transactions
  - Debit & Credit card transactions
  - Bill payments & Recurring bills
  - Loan EMI payments
  - Fees & charges
- **Transaction Type Classification**:
  - Automatic credit/debit categorization based on transaction type
  - 30+ transaction types with proper classification
  - Real-time transaction summary with credit/debit totals
- **CSV-based Transaction Ledger**:
  - Audit trail of all account activity
  - On-demand loading from `account_activity.csv`
  - Persistent transaction records across application restarts
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
- **Loan closure certificates** with complete audit trail
- Multiple loan types support

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
│   ├── InternationalBankRegistry.py
│   ├── InternationalTransfer.py
│   ├── loan.py
│   ├── LoanEvaluator.py
│   ├── MainInterface.py
│   ├── NachIdGenerator.py
│   ├── RDAuthorization.py
│   ├── RecurringBill.py
│   ├── RecurringDeposit.py
│   ├── RewardPointsManager.py
│   ├── SalaryProfile.py
│   ├── Serializers.py
│   ├── Transaction.py
│   ├── TransactionRegistry.py
│   └── verify_transfer.py
```

🗄️ **Data Persistence**

- **CSV-based Activity Ledger** (`account_activity.csv`):
  - Complete audit trail of all account transactions
  - 30+ transaction types (DEPOSIT, SALARY, WITHDRAW, NEFT_SENT, etc.)
  - On-demand transaction loading with blacklist filtering
  - Timestamp, amount, and balance verification for each entry

- **JSON Storage** for object persistence:
  - `accounts.json` – Account objects and balances
  - `customers.json` – Customer profiles and KYC
  - `loans.json` – Loan records and EMI history
  - `fixed_deposits.json` – FD contracts and maturity tracking
  - `recurring_deposits.json` – RD agreements and payment records
  - `cheques.json` – Cheque book and cleared cheque tracking
  - `rd_authorizations.json` – RD authorization records
  - `activity.log` – Application event log

---

## 🚀 Installation

### Requirements

- Python 3.8 or above

### Setup Steps

```bash
git clone https://github.com/kv-techie/Python-Bank.git
cd Python-Bank/backend
```

Create a virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # macOS/Linux
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python MainInterface.py
```

---

## 💻 Usage (Quick Guide)

| Action                       | Path                                          |
| ---------------------------- | --------------------------------------------- |
| Create Account               | Main Menu → Open New Account                  |
| **View Transaction History** | **Account Menu → View Transaction History**   |
| **Filter by Type**           | **History Menu → Deposits/Withdrawals/SWIFT** |
| Set Salary                   | Manage Salary → Configure Salary              |
| Apply Credit Card            | Card Management → Apply                       |
| Make Purchases               | Card Management → Spend                       |
| Open Fixed Deposit           | Investment → Fixed Deposit                    |
| Start Recurring Deposit      | Investment → Recurring Deposit                |
| **Create RD Authorization**  | **Investment → RD Authorization → Create**    |
| **Verify RD Authorization**  | **Investment → RD Authorization → Verify**    |
| **View RD Statement**        | **Investment → View RD Statement**            |
| **Export RD Statement**      | **Investment → View RD Statement → Export**   |
| International Transfer       | Transfers → International                     |
| Close Account                | Account Services → Close Account              |
| Enhance Credit Limit         | Card Management → Request Enhancement         |
| Redeem Reward Points         | Card Management → Rewards                     |
| Simulate Time                | Fast Forward → Select Days                    |

Each operation prints the results + audit logs.

---

## 📁 Project Structure

| Layer          | Files                                                                | Responsibilities                               |
| -------------- | -------------------------------------------------------------------- | ---------------------------------------------- |
| Core Banking   | Account, Bank, Customer, AccountClosure                              | Accounts, balance, KYC, closures               |
| Transactions   | Transaction, TransactionRegistry, DataStore                          | Transaction types, classification, persistence |
| Cards          | Card, CreditEvaluator, CreditLimitEnhancement, RewardPointsManager   | Debit/Credit card engine & rewards             |
| Credit/Loans   | CIBIL, LoanEvaluator, loan, ClosureFormalities                       | Score, approval & closures                     |
| Investments    | FixedDeposit, RecurringDeposit, RDAuthorization, **RDStatement**     | FD/RD management, auth & statements            |
| International  | InternationalTransfer, InternationalBankRegistry, AddNewIntlAccounts | Cross-border transactions                      |
| Automation     | RecurringBill, SalaryProfile, ExpenseSimulator, NachIdGenerator      | Auto-pay, spending & NACH                      |
| Infrastructure | BankClock, DataStore, Serializers                                    | Time, persistence & auditing                   |
| UI             | BankingApp, MainInterface                                            | CLI menus & user interface                     |

> **~8,500+ lines of Python** across modular components.

---

## 🔮 Future Enhancements

- Web interface (React)
- MongoDB migration
- ATM simulation
- Mutual Funds & SIP
- Multi-currency support enhancements
- PDF statements
- Tax document generation (Form 16 & Form 26AS)
- CI/CD & Docker
- AI-powered fraud detection
- Mobile app integration
- Biometric authentication

---

## 👨‍💻 Developer

**Kedhar Vinod**
🧑‍🎓 Jain (Deemed-to-be) University, Bengaluru
🔗 GitHub: [@kv-techie](https://github.com/kv-techie)

---

## 📄 License

**Private & Proprietary**
_For educational use only. Not connected to real banks._

---
