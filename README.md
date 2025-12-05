# 🏦 Scala Bank – Enterprise Banking Simulation System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Educational-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Active%20Development-success.svg)]()
[![Code Size](https://img.shields.io/badge/Code-350K+-orange.svg)]()

A production-grade **banking simulation system** built in Python, replicating real-world financial operations including credit scoring, loan processing, card management, automated payments, reward systems, and time-accelerated financial simulations.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Module Documentation](#-module-documentation)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Data Persistence](#-data-persistence)
- [Technical Specifications](#-technical-specifications)
- [Future Enhancements](#-future-enhancements)
- [Developer](#-developer)
- [License](#-license)

---

## 🎯 Overview

**Scala Bank** is a comprehensive banking simulation that demonstrates enterprise-level software architecture with 23+ interconnected modules and over 350KB of Python code. The system provides:

✅ Complete banking lifecycle management (account opening to closure)

✅ Multi-layered credit evaluation system (CIBIL-based)

✅ Sophisticated card services (debit & credit with rewards)

✅ Automated financial workflows (salary, bills, EMI)

✅ Time simulation engine for financial scenario modeling

✅ Comprehensive transaction tracking and analytics

### 🏢 Bank Details

| Parameter     | Value                    |
|---------------|-------------------------|
| Bank Name     | Scala Bank              |
| IFSC Code     | SCBA0005621             |
| Branch Name   | Jakkasandra             |
| Branch Code   | 5621                    |
| Supported Currency | INR (₹)            |

---

## ✨ Key Features

### 🏦 Account Management System

**5 Account Types with Differentiated Features:**

| Account Type | Minimum Balance | Interest Rate | Key Features |
|-------------|----------------|---------------|-------------|
| **Pride** | ₹2,000 | Standard | Entry-level savings |
| **Bespoke** | ₹2,00,000 | Premium | High-value customers |
| **Club** | ₹10,000 | Enhanced | Mid-tier benefits |
| **Delite** | ₹5,000 | Standard | Balanced offering |
| **Future** | ₹0 | Basic | Minor/Student accounts |

**Core Account Features:**
- Average Monthly Balance (AMB) enforcement with penalties
- Cheque book management and tracking
- Minor account protection (daily transaction limits)
- Internal transfers (instant)
- NEFT/RTGS/IMPS support
- Account freezing and dormancy handling
- Comprehensive account closure process

### 💳 Card Services

#### Debit Cards
- **Networks:** VISA, Mastercard, RuPay
- **Features:**
  - Daily spending limits
  - Card blocking/unblocking
  - ATM withdrawal tracking
  - Transaction categorization
  - Linked account validation

#### Credit Cards
- **Intelligent Credit Limit Calculation:**
  - CIBIL score-based evaluation
  - Salary and employer category analysis
  - Debt-to-Income (DTI) ratio assessment
  - Credit history consideration
  - Automated limit enhancement

- **Credit Card Operations:**
  - Billing cycle management
  - Grace period handling
  - Interest calculation (compound)
  - Minimum payment enforcement
  - Reward points system
  - Card upgrade/downgrade
  - Luhn algorithm validation

### 💰 Loan Management

**Loan Types Supported:**
- Personal Loans
- Home Loans
- Vehicle Loans
- Education Loans

**Loan Features:**
- Automated approval based on:
  - CIBIL score (minimum 650)
  - Monthly income requirements
  - Debt-to-Income ratio (<40%)
  - Employment stability
- EMI calculation using compound interest
- Prepayment and foreclosure options
- Late payment penalties
- Automated NACH (National Automated Clearing House) setup
- Loan closure certificate generation

### 📊 CIBIL Credit Scoring System

**Weighted Scoring Model:**
- **Payment History** (35%): On-time payments, defaults
- **Credit Utilization** (30%): Credit used vs. available
- **Credit Mix** (15%): Diversity of credit types
- **Credit Inquiries** (10%): Hard inquiries impact
- **Account Age** (10%): Length of credit history

**Score Classification:**
- **Excellent** (750-900): Best rates, instant approvals
- **Good** (650-749): Standard approvals, good rates
- **Average** (550-649): Limited approvals, higher rates
- **Poor** (300-549): Rejections, remediation required

### 💼 Salary & Recurring Payments

**Salary Profile Management:**
- Automated monthly salary credits
- Tax deduction (TDS) for income >₹18L/year
- Employer category tracking (MNC, PSU, Government, Startup)
- Salary slip generation
- Bonus and increment handling

**Recurring Bill Automation:**
- Multiple billing frequencies (daily, weekly, monthly)
- Category-based expense tracking:
  - Utilities (electricity, water, gas)
  - Subscriptions (Netflix, Spotify, Prime)
  - Insurance premiums
  - Rent and maintenance
  - Telecom bills
- Auto-debit with insufficient balance handling
- NACH mandate management

### 🎁 Reward Points System

**Earning Mechanism:**
- Base reward rate: 1 point per ₹100 spent
- Category multipliers:
  - Dining: 3x points
  - Travel: 2x points
  - Online shopping: 2x points
  - Fuel: 1.5x points

**Redemption Options:**
- Statement credit
- Gift vouchers
- Airline miles
- Cashback
- Points expiry tracking

### ⏱️ Time Simulation Engine (BankClock)

**Capabilities:**
- Fast-forward time (days/weeks/months)
- Automated daily/monthly processing:
  - EMI deductions
  - Bill payments
  - Salary credits
  - Interest calculations
  - Credit card billing cycles
- Random expense generation
- Financial scenario modeling
- Date-based transaction validation

### 📈 Financial Analytics

**Analytics Features:**
- Expense categorization and breakdown
- Trend analysis (7/30/90 days)
- Spending patterns identification
- Budget vs. actual comparison
- Credit utilization tracking
- Investment portfolio summary
- Comprehensive transaction history

### 🔐 Security & Compliance

- Customer KYC (Know Your Customer) validation
- PAN card verification
- Aadhaar linking
- Transaction limits enforcement
- Fraud detection patterns
- Account activity monitoring
- Audit trail maintenance

---

## 🏗️ System Architecture

### Project Structure

```
Python-Bank/
├── backend/
│   ├── Core Banking Modules
│   │   ├── Account.py              (53KB) - Account lifecycle & operations
│   │   ├── Bank.py                 (17KB) - Central bank controller
│   │   ├── Customer.py             (11KB) - Customer profile management
│   │   ├── Transaction.py          (8KB)  - Transaction processing
│   │   └── AccountClosure.py       (13KB) - Account closure workflows
│   │
│   ├── Card Management
│   │   ├── Card.py                 (35KB) - Debit/Credit card engine
│   │   ├── CreditEvaluator.py      (8KB)  - Credit limit calculation
│   │   ├── CreditLimitEnhancement.py (9KB) - Limit upgrade logic
│   │   └── RewardPointsManager.py  (11KB) - Rewards & redemption
│   │
│   ├── Credit & Loan Systems
│   │   ├── CIBIL.py                (4KB)  - Credit score calculation
│   │   ├── loan.py                 (3KB)  - Loan data model
│   │   ├── LoanEvaluator.py        (4KB)  - Loan approval engine
│   │   └── ClosureFormalities.py   (9KB)  - Loan closure process
│   │
│   ├── Automation & Scheduling
│   │   ├── RecurringBill.py        (15KB) - Bill payment automation
│   │   ├── SalaryProfile.py        (13KB) - Salary processing
│   │   ├── ExpenseSimulator.py     (14KB) - Spending simulation
│   │   ├── BankClock.py            (5KB)  - Time management
│   │   └── NachIdGenerator.py      (1KB)  - NACH mandate IDs
│   │
│   ├── Data Layer
│   │   ├── DataStore.py            (16KB) - JSON persistence
│   │   ├── TransactionRegistry.py  (7KB)  - Transaction logging
│   │   └── Serializers.py          (3KB)  - Object serialization
│   │
│   └── Application Layer
│       ├── MainInterface.py        (1KB)  - Entry point
│       └── BankingApp.py           (104KB) - CLI interface & workflows
│
├── Data Files (Auto-generated)
│   ├── accounts.json
│   ├── customers.json
│   ├── loans.json
│   ├── cards.json
│   ├── activity.log
│   └── loan_closure_*.txt
│
├── .gitignore
└── README.md
```

### Architecture Layers

| Layer | Components | Responsibility |
|-------|-----------|---------------|
| **Presentation** | MainInterface, BankingApp | User interaction, menu systems |
| **Business Logic** | Account, Card, Loan, CIBIL | Core banking operations |
| **Automation** | BankClock, RecurringBill, ExpenseSimulator | Scheduled tasks |
| **Data Access** | DataStore, TransactionRegistry | Persistence, logging |
| **Utilities** | Serializers, NachIdGenerator | Helper functions |

---

## 📚 Module Documentation

### Core Banking Modules

#### `Account.py` (53,980 bytes)
The largest module handling complete account lifecycle:
- Account creation and validation
- Balance management and interest calculation
- Transfer processing (internal, NEFT, RTGS, IMPS)
- Cheque management
- AMB enforcement
- Account statements
- Dormancy and freezing logic

#### `Bank.py` (17,177 bytes)
Central bank orchestrator:
- Customer registration
- Account opening workflows
- Branch management
- IFSC routing
- Inter-account operations

#### `Customer.py` (10,929 bytes)
Customer profile management:
- KYC details
- Contact information
- Linked accounts tracking
- Customer verification
- Profile updates

#### `Transaction.py` (7,821 bytes)
Transaction processing engine:
- Transaction creation and validation
- Status tracking
- Reversal handling
- Metadata management

#### `AccountClosure.py` (12,693 bytes)
Account closure workflows:
- Pre-closure validations
- Outstanding balance settlement
- Linked services disconnection
- Closure certificate generation

### Card Management Modules

#### `Card.py` (35,149 bytes)
Comprehensive card operations:
- Debit card issuance and management
- Credit card lifecycle
- Transaction authorization
- Card blocking/unblocking
- PIN management
- Network-specific rules (VISA/Mastercard/RuPay)

#### `CreditEvaluator.py` (8,628 bytes)
Intelligent credit assessment:
- Multi-factor credit evaluation
- Dynamic limit calculation
- Risk scoring
- Employer category weighting

#### `CreditLimitEnhancement.py` (9,377 bytes)
Credit limit upgrades:
- Eligibility checking
- Usage pattern analysis
- Automatic enhancement triggers
- Manual enhancement processing

#### `RewardPointsManager.py` (11,307 bytes)
Reward program management:
- Points accrual calculation
- Category-based multipliers
- Redemption processing
- Points expiry handling

### Credit & Loan Modules

#### `CIBIL.py` (3,588 bytes)
Credit scoring implementation:
- Multi-factor score calculation
- Payment history tracking
- Credit utilization analysis
- Score impact predictions

#### `LoanEvaluator.py` (4,304 bytes)
Loan approval engine:
- Eligibility assessment
- Income verification
- DTI ratio calculation
- Approval/rejection logic

#### `ClosureFormalities.py` (8,628 bytes)
Loan closure processing:
- Outstanding calculation
- Prepayment processing
- NOC (No Objection Certificate) generation
- CIBIL reporting

### Automation Modules

#### `RecurringBill.py` (14,920 bytes)
Bill payment automation:
- Bill scheduling
- Auto-debit processing
- Failed payment handling
- Notification triggers

#### `SalaryProfile.py` (12,603 bytes)
Salary automation:
- Salary configuration
- Automated credit on payday
- Tax calculation and deduction
- Salary slip generation

#### `ExpenseSimulator.py` (13,688 bytes)
Realistic spending simulation:
- Category-based random expenses
- Spending pattern modeling
- Transaction generation
- Budget adherence simulation

#### `BankClock.py` (5,352 bytes)
Time management system:
- Current date tracking
- Fast-forward functionality
- Scheduled task triggering
- Date-based validations

### Data Layer Modules

#### `DataStore.py` (15,883 bytes)
Persistence layer:
- JSON file operations
- Object serialization/deserialization
- Data integrity checks
- Backup and recovery

#### `TransactionRegistry.py` (6,768 bytes)
Transaction logging:
- Comprehensive audit trail
- Query and filter capabilities
- Analytics support
- Export functionality

#### `Serializers.py` (3,300 bytes)
Object serialization:
- Custom JSON encoders
- Date/datetime handling
- Complex object serialization

### Application Layer

#### `BankingApp.py` (103,832 bytes)
Largest application module - comprehensive CLI interface:
- Multi-level menu system
- 50+ banking operations
- Input validation
- Error handling
- User guidance

#### `MainInterface.py` (577 bytes)
Application entry point:
- Application initialization
- Exception handling
- Graceful shutdown

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 50MB free disk space

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/kv-techie/Python-Bank.git
   cd Python-Bank/backend
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   If `requirements.txt` doesn't exist, the system uses Python standard library only.

4. **Run the Application**
   ```bash
   python MainInterface.py
   ```

### First Run

On first launch, the system will:
- Create necessary data directories
- Initialize JSON data files
- Set up the BankClock (starts at current date)
- Display the main menu

---

## 💻 Usage Guide

### Quick Start Workflow

1. **Create Customer Profile**
   - Navigate to: Main Menu → Customer Management → Register New Customer
   - Provide: Name, DOB, PAN, Aadhaar, Contact Details

2. **Open Bank Account**
   - Main Menu → Account Services → Open New Account
   - Select account type (Pride, Bespoke, Club, Delite, Future)
   - Initial deposit (must meet minimum balance)

3. **Configure Salary Profile**
   - Main Menu → Salary Management → Set Salary Profile
   - Input: Monthly salary, employer type, payday
   - System auto-credits salary monthly

4. **Apply for Debit Card**
   - Main Menu → Card Services → Apply for Debit Card
   - Select network (VISA/Mastercard/RuPay)
   - Card issued instantly

5. **Apply for Credit Card**
   - Main Menu → Card Services → Apply for Credit Card
   - System evaluates CIBIL score, salary, DTI
   - Approval/rejection with reasons

6. **Set Up Recurring Bills**
   - Main Menu → Bill Management → Add Recurring Bill
   - Configure: Payee, amount, frequency, category
   - Auto-debit on due dates

7. **Fast Forward Time**
   - Main Menu → Time Simulation → Fast Forward
   - Select days/weeks/months
   - Observe automated transactions (salary, bills, EMI)

### Common Operations

| Operation | Menu Path | Description |
|-----------|-----------|-------------|
| Check Balance | Account Services → View Balance | Current balance and available funds |
| Transfer Money | Account Services → Transfer Funds | Internal/NEFT/RTGS transfers |
| View Transactions | Account Services → Transaction History | Filtered transaction list |
| Apply for Loan | Loan Services → Apply for Loan | Loan application and processing |
| Pay Credit Card | Card Services → Pay Credit Bill | Credit card bill payment |
| Check CIBIL | Credit Services → View CIBIL Score | Credit score and factors |
| Generate Statement | Account Services → Account Statement | Period-wise statement |
| Close Account | Account Services → Close Account | Account closure workflow |

### CLI Navigation Tips

- Use numeric inputs to select menu options
- Type `0` or `back` to return to previous menu
- Type `exit` or `quit` to close application
- All monetary inputs accept decimal values
- Dates follow DD/MM/YYYY format

---

## 💾 Data Persistence

### JSON Data Files

| File | Contents | Update Frequency |
|------|----------|------------------|
| `accounts.json` | All bank accounts | Every transaction |
| `customers.json` | Customer profiles | Profile updates |
| `loans.json` | Loan records | EMI payments, closures |
| `cards.json` | Card details | Card operations |
| `bills.json` | Recurring bills | Bill execution |
| `salaries.json` | Salary profiles | Salary credits |
| `cibil.json` | Credit scores | Score recalculation |

### Logging

- **activity.log**: Timestamped audit trail of all operations
- **error.log**: Exception and error tracking
- **transaction.log**: Detailed transaction records

### Backup Recommendations

```bash
# Manual backup
cp -r backend/data/ backup_$(date +%Y%m%d)/

# Restore from backup
cp -r backup_20250101/data/ backend/
```

---

## 🔧 Technical Specifications

### System Requirements

- **RAM**: 256MB minimum, 512MB recommended
- **Storage**: 50MB for application, 100MB for data growth
- **Python Version**: 3.8 - 3.12
- **Operating System**: Windows, macOS, Linux

### Performance Metrics

- **Account Operations**: <50ms response time
- **Transaction Processing**: <100ms
- **CIBIL Calculation**: <200ms
- **Time Simulation**: 1 month simulation in <5 seconds
- **Data Persistence**: Auto-save after every operation

### Code Statistics

- **Total Lines of Code**: ~15,000+
- **Total File Size**: ~350KB
- **Number of Modules**: 23
- **Number of Classes**: 40+
- **Number of Functions**: 200+

### Design Patterns Used

- **Singleton**: Bank, BankClock, DataStore
- **Factory**: Account creation, Card issuance
- **Strategy**: Transaction processing, Evaluation algorithms
- **Observer**: Event notifications, Logging
- **Repository**: DataStore abstraction

### Key Algorithms

1. **CIBIL Score Calculation**
   - Weighted multi-factor model
   - Real-time score updates

2. **EMI Calculation**
   - Compound interest formula
   - Prepayment adjustment

3. **Credit Limit Evaluation**
   - Income-based calculation
   - Risk-adjusted limits

4. **Luhn Algorithm**
   - Card number validation
   - Checksum verification

---

## 🔮 Future Enhancements

### Short-term (Next 3-6 months)

- [ ] Web-based interface (Flask/Django)
- [ ] RESTful API development
- [ ] MySQL/PostgreSQL migration
- [ ] Comprehensive test suite
- [ ] Docker containerization

### Medium-term (6-12 months)

- [ ] Mobile app (React Native)
- [ ] Real-time notifications
- [ ] PDF statement generation
- [ ] Email integration
- [ ] Cheque book physical simulation
- [ ] ATM transaction simulation

### Long-term (1-2 years)

- [ ] Multi-currency support
- [ ] Investment products (FD, MF, SIP, Bonds)
- [ ] Insurance integration
- [ ] Forex operations
- [ ] AI-powered fraud detection
- [ ] Blockchain integration for audit
- [ ] GraphQL API
- [ ] Microservices architecture

### Advanced Features

- Real-time stock trading integration
- Cryptocurrency wallet
- P2P lending platform
- Merchant payment gateway
- QR code payments (UPI simulation)
- International wire transfers (SWIFT)

---

## 🧪 Testing

### Manual Testing Scenarios

1. **Account Lifecycle**
   - Open account → Deposit → Withdraw → Transfer → Close

2. **Credit Card Journey**
   - Apply → Spend → Bill generation → Payment → Rewards

3. **Loan Processing**
   - Apply → Approval → EMI deduction → Prepayment → Closure

4. **Time Simulation**
   - Fast forward 1 year → Verify automated transactions

5. **Credit Score Impact**
   - Track CIBIL changes with different behaviors

### Test Data

Sample customer profiles included for testing various scenarios:
- High-income earner (excellent credit)
- Mid-income earner (good credit)
- Low-income earner (average credit)
- Defaulter profile (poor credit)

---

## 📊 Sample Outputs

### Account Statement Example
```
═══════════════════════════════════════════════════════
                 SCALA BANK - ACCOUNT STATEMENT
═══════════════════════════════════════════════════════
Account Number  : ACC123456789
Account Type    : Pride Savings
Customer Name   : Kedhar Vinod
Period          : 01/11/2025 - 30/11/2025
───────────────────────────────────────────────────────
Opening Balance : ₹50,000.00
Total Credits   : ₹1,25,000.00
Total Debits    : ₹78,450.00
Closing Balance : ₹96,550.00
═══════════════════════════════════════════════════════
```

### CIBIL Score Report
```
╔══════════════════════════════════════════════════════╗
║             CIBIL CREDIT SCORE REPORT                ║
╠══════════════════════════════════════════════════════╣
║ Credit Score         : 782 (EXCELLENT)               ║
║ Last Updated         : 05/12/2025                    ║
║                                                      ║
║ Score Factors:                                       ║
║ ✓ Payment History    : 35% (Excellent)              ║
║ ✓ Credit Utilization : 30% (Good - 28% used)        ║
║ ✓ Credit Mix         : 15% (Diverse)                ║
║ ✓ Credit Inquiries   : 10% (Low)                    ║
║ ✓ Account Age        : 10% (5 years 3 months)       ║
╚══════════════════════════════════════════════════════╝
```

---

## 🤝 Contributing

This is an educational project. Contributions are welcome!

### How to Contribute

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Add docstrings to all functions/classes
- Include type hints where possible
- Write meaningful commit messages

---

## 👨‍💻 Developer

**Kedhar Vinod**

- 🎓 Student at Jain (Deemed-to-be) University, Bengaluru
- 🔗 GitHub: [@kv-techie](https://github.com/kv-techie)
- 📍 Location: Bengaluru, India
- 💼 Interests: Banking Systems, Financial Technology, Python Development

### Project Stats

- **Started**: September 2024
- **Lines of Code**: 15,000+
- **Development Time**: 400+ hours
- **Version**: 5.0
- **Public Repos**: 4

---

## 📄 License

**Educational Use License**

This project is developed for educational purposes only. 

- ✅ Free to use for learning and academic projects
- ✅ Can be modified and extended for personal use
- ✅ Can be shared with proper attribution
- ❌ Not for commercial use
- ❌ Not affiliated with any real banking institution
- ❌ Does not handle real money or financial transactions

### Disclaimer

⚠️ **Important**: This is a simulation system for educational purposes only. It does not:
- Connect to real banking networks
- Process actual financial transactions
- Store sensitive personal/financial data securely
- Comply with banking regulations (PCI-DSS, etc.)
- Provide financial advice

Do not use this system for actual banking operations.

---

## 🙏 Acknowledgments

- Inspired by real-world banking systems
- Python community for excellent documentation
- Open-source projects that provided architectural insights
- Jain University for academic support

---

## 📞 Support

### Getting Help

- 📖 Check this README for detailed documentation
- 🐛 Report bugs via GitHub Issues
- 💡 Request features via GitHub Issues
- 📧 Contact developer through GitHub profile

### Known Issues

- Time simulation with large time jumps may slow performance
- Large transaction histories can increase load times
- JSON file corruption if application crashes during write operations

### Troubleshooting

**Issue**: Application won't start
- Solution: Ensure Python 3.8+ is installed, check for corrupted JSON files

**Issue**: Data not persisting
- Solution: Check file permissions in backend/data/ directory

**Issue**: CIBIL score not updating
- Solution: Ensure sufficient transaction history exists

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

## 📝 Changelog

### Version 5.0 (Current)
- Added comprehensive account closure workflows
- Implemented credit limit enhancement system
- Added reward points management
- Enhanced time simulation capabilities
- Improved CIBIL scoring algorithm

### Version 4.0
- Added recurring bill automation
- Implemented salary profile management
- Enhanced card services

### Version 3.0
- Added loan management system
- Implemented CIBIL scoring
- Added transaction registry

### Version 2.0
- Added card services (debit & credit)
- Implemented basic CIBIL

### Version 1.0
- Initial release with basic banking operations

---

<div align="center">

**Built with ❤️ by Kedhar Vinod**

*Simulating the future of banking, one transaction at a time*

</div>