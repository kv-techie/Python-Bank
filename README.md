# 🏦 Scala Bank – Python Banking System v5.0

A comprehensive, feature-rich **banking simulation system** written in Python, mimicking real-world financial operations such as credit scoring, loan processing, automated payments, and card services.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()
[![License](https://img.shields.io/badge/License-Private-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Installation](#-installation)
* [Usage](#-usage)
* [Project Structure](#-project-structure)
* [Future Enhancements](#-future-enhancements)
* [Developer](#-developer)
* [License](#-license)

---

## 🎯 Overview

**Scala Bank** simulates enterprise-level banking workflows with:

✔ Multi-account & card support

✔ CIBIL-based loan & credit card approval

✔ Recurring bills, salary automation, & EMI logic

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

### 🏦 Account Management

* 5 account types with different rules & minimum balances:

* Pride (₹2,000), Bespoke (₹2,00,000), Club (₹10,000), Delite (₹5,000), Future (₹0)
* AMB enforcement, cheque tracking
* Minor account protection (daily usage limits)
* Internal & NEFT/RTGS transfers

### 💳 Card Services

**Debit Cards**

* VISA/Mastercard/RuPay networks
* Spending limits
* Block/Unblock

**Credit Cards**

* Automatic credit limit evaluation using:

  * CIBIL score
  * Salary profile
  * Employer category
  * Debt-to-Income ratio
  * Billing cycles, grace periods, rewards, and interest
  * **Luhn algorithm** validation

### 💰 Loan Management

* EMI calculation (compound interest)
* Automated approval rules (score, income, DTI)
* Transaction-linked repayment history
* Loan Closure Certificate

### 📊 CIBIL Credit Scoring

Weighted scoring model:

* Repayment history (35%)
* Utilization (30%)
* Credit mix, inquiries, account age…

Score categorization:

* **Excellent:** 750–900
* **Good:** 650–749
* **Average:** 550–649
* **Poor:** 300–549

### 💵 Salary & Bills Automation

* Automated salary credit (tax applied if > ₹18L/yr)
* Recurring bill engine
* Expense categorization (Netflix, utilities, rent…)

### ⏱️ Time Simulation System

* Fast-forward days/weeks/months
* Automatically processes:

  * EMI
  * Bills
  * Salaries
  * Random spending
  * Interest calculations

### 📈 Financial Analytics

* Expense breakdown by category
* 7/30/90-day trends
* Full transaction history with metadata

---

## 🏗️ System Architecture

```
Python-Bank/
├── backend/
│   ├── Account.py
│   ├── Bank.py
│   ├── BankingApp.py
│   ├── Card.py
│   ├── Customer.py
│   ├── Transaction.py
│   ├── loan.py
│   ├── CIBIL.py
│   ├── CreditEvaluator.py
│   ├── LoanEvaluator.py
│   ├── RecurringBill.py
│   ├── SalaryProfile.py
│   ├── ExpenseSimulator.py
│   ├── BankClock.py
│   ├── DataStore.py
│   ├── TransactionRegistry.py
│   └── MainInterface.py
```

🗄️ **Data Persistence**

* JSON storage:

  * `accounts.json`
  * `customers.json`
  * `loans.json`
  * `activity.log`

---

## 🚀 Installation

### Requirements

* Python 3.8 or above

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

| Action            | Path                             |
| ----------------- | -------------------------------- |
| Create Account    | Main Menu → Open New Account     |
| Set Salary        | Manage Salary → Configure Salary |
| Apply Credit Card | Card Management → Apply          |
| Make Purchases    | Card Management → Spend          |
| Simulate Time     | Fast Forward → Select Days       |

Each operation prints the results + audit logs.

---

## 📁 Project Structure

| Layer          | Files                                          | Responsibilities         |
| -------------- | ---------------------------------------------- | ------------------------ |
| Core Banking   | Account, Bank, Customer                        | Accounts, balance, KYC   |
| Cards          | Card, CreditEvaluator                          | Debit/Credit card engine |
| Credit/Loans   | CIBIL, LoanEvaluator, loan                     | Score & approval         |
| Automation     | RecurringBill, SalaryProfile, ExpenseSimulator | Auto-pay & spending      |
| Infrastructure | BankClock, DataStore, Registry                 | Time & persistence       |
| UI             | BankingApp, MainInterface                      | CLI menus                |

> **~6,000+ lines of Python** across modular components.

---

## 🔮 Future Enhancements

Web interface (React)

MongoDB migration

ATM + cheque book simulation

Investments (FD, MF, SIP)

Multi-currency support

PDF statements

CI/CD & Docker

AI-powered fraud detection



---

## 👨‍💻 Developer

**Kedhar Vinod**
🧑‍🎓 Jain (Deemed-to-be) University, Bengaluru
🔗 GitHub: [@kv-techie](https://github.com/kv-techie)

---

## 📄 License

**Private & Proprietary**
*For educational use only. Not connected to real banks.*

---
