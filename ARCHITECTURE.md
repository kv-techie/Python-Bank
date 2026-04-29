# 🏗️ System Architecture & Data Flow

Complete architecture overview for Scala Bank full-stack application.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCALA BANK APPLICATION                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────▼───────────┐     ┌────────────▼────────────┐
        │   FRONTEND (React)    │     │  BACKEND (Flask)        │
        │   Port: 3000          │     │  Port: 5000             │
        └───────────┬───────────┘     └────────────┬────────────┘
                    │                              │
        ┌───────────▼───────────┐     ┌────────────▼────────────┐
        │  15 Page Components   │     │  20+ REST Endpoints     │
        │  - Dashboard          │     │  - /login               │
        │  - Accounts           │     │  - /register            │
        │  - Loans              │     │  - /dashboard           │
        │  - Cards              │     │  - /accounts            │
        │  - Transfers          │     │  - /loans               │
        │  - Tax/CIBIL          │     │  - /transfer            │
        │  - Admin              │     │  - /admin               │
        └───────────┬───────────┘     └────────────┬────────────┘
                    │                              │
        ┌───────────▼───────────┐     ┌────────────▼────────────┐
        │  State Management     │     │ Backend Modules         │
        │  - AuthContext        │     │ - Bank.py               │
        │  - BankContext        │     │ - Customer.py           │
        │  - Forms & Validation │     │ - Account.py            │
        │  - Error Handling     │     │ - Loan.py               │
        └───────────┬───────────┘     │ - Card.py               │
                    │                 │ - CIBIL.py              │
                    │                 │ - TaxCalculator.py      │
                    │                 │ - DataStore.py          │
                    │                 └────────────┬────────────┘
                    │                              │
                    └──────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Data Persistence │
                    │  - DataStore.bak  │
                    │  - CSV files      │
                    │  - JSON files     │
                    └───────────────────┘
```

---

## Frontend Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   REACT FRONTEND (src/)                      │
└──────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬────────────────┐
        │                │                │                │
    ┌───▼────┐    ┌─────▼──────┐    ┌────▼─────┐    ┌────▼────┐
    │ App.js │    │ index.js   │    │ Providers│    │ Routes  │
    │Routing │    │ React DOM  │    │Contexts  │    │Protected│
    └────────┘    └────────────┘    └──────────┘    └─────────┘
        │
        ├─── Context Providers ──────────────────────┐
        │                                             │
        │  ┌──────────────────────────────────────┐  │
        │  │  AuthContext.js                      │  │
        │  │  - user: {firstName, customerId}     │  │
        │  │  - isAdmin: boolean                  │  │
        │  │  - login(id, pwd): Promise           │  │
        │  │  - register(data): Promise           │  │
        │  │  - logout(): void                    │  │
        │  └──────────────────────────────────────┘  │
        │                                             │
        │  ┌──────────────────────────────────────┐  │
        │  │  BankContext.js                      │  │
        │  │  - accounts: Array                   │  │
        │  │  - loans: Array                      │  │
        │  │  - cards: Array                      │  │
        │  │  - transferFunds(): Promise          │  │
        │  │  - payLoanEMI(): Promise             │  │
        │  │  - prepayLoan(): Promise             │  │
        │  └──────────────────────────────────────┘  │
        │                                             │
        └─────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    ┌───▼──────┐   ┌─────▼──────┐   ┌────▼──────┐
    │ Components│  │  Pages      │   │   Styles  │
    │           │  │   (15)      │   │   (14)    │
    └────────────┘  └─────────────┘   └───────────┘
    - Navbar.js     - Login.js       - index.css
    - Protected     - Register.js    - App.css
      Route.js      - Dashboard.js   - Navbar.css
                    - Accounts.js    - Auth.css
                    - Loans.js       - Dashboard.css
                    - Cards.js       - Accounts.css
                    - Deposits.js    - Loans.css
                    - CIBIL.js       - Cards.css
                    - Tax.js         - Deposits.css
                    - Transfer.js    - Tax.css
                    - AdminLogin.js  - Transfer.css
                    - AdminDash.js   - Admin.css
```

---

## Backend Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   FLASK BACKEND (app.py)                    │
└──────────────────────────────────────────────────────────────┘
                         │
     ┌──────────────────┬┼┬──────────────────┐
     │                  │││                  │
 ┌───▼────┐      ┌─────▼▼──┐      ┌────────▼─────┐
 │ Route  │      │Decorator │      │ Context      │
 │Handler │      │Processing│      │ Processors   │
 └────────┘      └──────────┘      └──────────────┘
     │
     ├─── Public Routes ──────────┐
     │   POST /login              │
     │   POST /register           │
     │   POST /admin-login        │
     │   GET /logout              │
     │                            │
     ├─── Protected Routes ───────┤
     │   Requires: customer_id    │
     │   GET /dashboard           │
     │   GET /accounts            │
     │   GET /account/<id>        │
     │   POST /account/<id>/      │
     │         transfer           │
     │   GET /loans               │
     │   GET /loan/<id>           │
     │   POST /loan/<id>/pay-emi  │
     │   POST /loan/<id>/prepay   │
     │   GET /cards               │
     │   GET /card/<id>           │
     │   POST /card/<id>/pay-bill │
     │   GET /deposits            │
     │   GET /cibil               │
     │   GET /tax                 │
     │                            │
     └─── Admin Routes ───────────┤
         Requires: is_admin       │
         GET /admin               │
         GET /admin/customers     │
         GET /admin/accounts      │
         GET /admin/loans         │
                                  │
         Module Integration       │
         ├── Bank.py             │
         ├── Customer.py         │
         ├── Account.py          │
         ├── Loan.py             │
         ├── Card.py             │
         ├── CIBIL.py            │
         ├── TaxCalculator.py    │
         ├── AdminControl.py     │
         ├── AdminAnalytics.py   │
         └── DataStore.py        │
```

---

## Data Flow: Authentication

```
USER INPUT (Login Page)
    │
    ├─ Customer ID: CUST1001
    ├─ Password: ****
    │
    ▼
VALIDATE (Frontend)
    │
    ├─ Check: Not empty
    ├─ Check: Valid format
    │
    ▼
API CALL (Axios)
    │
    ├─ POST /login
    ├─ Body: {customer_id, password}
    ├─ Headers: Content-Type: form-data
    │
    ▼
BACKEND PROCESS (Flask)
    │
    ├─ Find: Customer in bank.customers
    ├─ Verify: Password matches
    ├─ Set: session['customer_id']
    ├─ Set: session.permanent = True
    │
    ▼
RESPONSE (JSON)
    │
    ├─ Success: {success: true, user: {...}}
    ├─ Error: {success: false, error: "..."}
    │
    ▼
STORE (Frontend)
    │
    ├─ localStorage.setItem('user', {...})
    ├─ setUser() in AuthContext
    ├─ setIsAuthenticated(true)
    │
    ▼
REDIRECT
    │
    ├─ Navigate to /dashboard
    ├─ Show greeting: "Welcome back, John!"
    │
    ▼
RENDER (Dashboard Page)
    │
    ├─ Fetch accounts
    ├─ Fetch loans
    ├─ Calculate totals
    ├─ Display cards
```

---

## Data Flow: Fund Transfer

```
USER INPUT (Transfer Page)
    │
    ├─ From Account: ACC001
    ├─ To Account: ACC002
    ├─ Amount: 5000
    │
    ▼
VALIDATE (Frontend)
    │
    ├─ Check: Accounts selected
    ├─ Check: Amount > 0
    ├─ Check: Amount format valid
    │
    ▼
API CALL (Axios)
    │
    ├─ POST /account/ACC001/transfer
    ├─ Body: {
    │    recipient_account_id: "ACC002",
    │    amount: 5000,
    │    description: "..."
    │  }
    │
    ▼
BACKEND PROCESS (Flask)
    │
    ├─ Validate: Account exists
    ├─ Validate: Recipient exists
    ├─ Validate: Sufficient balance
    ├─ Debit: account.balance -= 5000
    ├─ Credit: recipient.balance += 5000
    ├─ Log: Transaction(FROM, TRANSFER, 5000)
    ├─ Log: Transaction(TO, TRANSFER, 5000)
    ├─ Save: bank.save()
    │
    ▼
RESPONSE (JSON)
    │
    ├─ Success: {success: true, from_balance: ..., to_balance: ...}
    ├─ Error: {success: false, error: "Insufficient balance"}
    │
    ▼
STORE (Frontend)
    │
    ├─ Update: BankContext accounts
    ├─ Show: Toast notification
    ├─ Clear: Form fields
    │
    ▼
DISPLAY
    │
    ├─ Updated balances
    ├─ Confirmation message
    ├─ Recent transactions
```

---

## Data Flow: Loan EMI Payment

```
USER INPUT (Loan Detail Page)
    │
    ├─ Loan ID: LOAN001
    ├─ EMI Amount: 25000 (calculated)
    ├─ Select Account: ACC001
    │
    ▼
VALIDATE (Frontend)
    │
    ├─ Check: Account selected
    ├─ Check: Amount matches EMI
    │
    ▼
API CALL (Axios)
    │
    ├─ POST /loan/LOAN001/pay-emi
    ├─ Body: {
    │    account_id: "ACC001",
    │    amount: 25000
    │  }
    │
    ▼
BACKEND PROCESS (Flask)
    │
    ├─ Validate: Loan exists
    ├─ Validate: Account exists
    ├─ Validate: Sufficient balance
    ├─ Debit: account.balance -= 25000
    ├─ Deduct: loan.outstanding_amount -= 25000
    ├─ Log: Transaction(LOAN_EMI, 25000)
    ├─ Save: bank.save()
    │
    ▼
RESPONSE (JSON)
    │
    ├─ Success: {
    │    success: true,
    │    remaining_outstanding: 1475000
    │  }
    ├─ Error: {success: false, error: "..."}
    │
    ▼
UPDATE (Frontend)
    │
    ├─ Update: Loan outstanding
    ├─ Update: Account balance
    ├─ Show: Toast notification
    │
    ▼
DISPLAY
    │
    ├─ Updated loan status
    ├─ Repayment progress
    ├─ New outstanding amount
```

---

## Component Hierarchy

```
App.js
├── Navbar
│   ├── Logo
│   ├── NavLinks
│   ├── MobileMenu (responsive)
│   └── UserMenu
│
├── Routes
│   ├── Public
│   │   ├── Login
│   │   ├── Register
│   │   └── AdminLogin
│   │
│   ├── Protected (AuthContext check)
│   │   ├── Dashboard
│   │   │   ├── WelcomeSection
│   │   │   ├── SummaryCards
│   │   │   ├── AccountGrid
│   │   │   ├── LoanList
│   │   │   └── QuickActions
│   │   │
│   │   ├── Accounts
│   │   │   └── AccountGrid (card layout)
│   │   │
│   │   ├── AccountDetail
│   │   │   ├── AccountHero
│   │   │   ├── DetailCards
│   │   │   └── TransactionList
│   │   │
│   │   ├── Loans
│   │   │   └── LoanGrid (card layout)
│   │   │
│   │   ├── LoanDetail
│   │   │   ├── LoanHero
│   │   │   ├── SummaryCards
│   │   │   ├── DetailsTable
│   │   │   └── ActionButtons
│   │   │
│   │   ├── Cards
│   │   │   └── CardGrid (visual cards)
│   │   │
│   │   ├── CardDetail
│   │   │   ├── CardVisualization
│   │   │   ├── InfoGrid
│   │   │   └── ActionButtons
│   │   │
│   │   ├── Deposits
│   │   │   ├── FDSection
│   │   │   └── RDSection
│   │   │
│   │   ├── CIBIL
│   │   │   ├── ScoreCircle
│   │   │   ├── Breakdown
│   │   │   └── Tips
│   │   │
│   │   ├── TaxManagement
│   │   │   ├── TaxSummary
│   │   │   ├── DeductionBreakdown
│   │   │   └── ITRStatus
│   │   │
│   │   └── Transfer
│   │       ├── FromAccountSelect
│   │       ├── ToAccountSelect
│   │       ├── AmountInput
│   │       └── SubmitButton
│   │
│   └── AdminProtected (Admin check)
│       ├── AdminLogin
│       └── AdminDashboard
│           ├── MetricCards
│           ├── LoanChart (Bar)
│           └── AccountChart (Pie)
│
└── Providers
    ├── AuthContext.Provider
    └── BankContext.Provider
```

---

## API Request/Response Flow

```
FRONTEND (React)                    BACKEND (Flask)
    │                                    │
    ├─ axios.post(URL)                  │
    │   {customer_id, password}          │
    │                                    │
    ├──────────────────────────────────▶ │
    │                                    ├─ Receive request
    │                                    ├─ Process data
    │                                    ├─ Database query
    │                                    ├─ Response prep
    │                                    │
    │  ◀──────────────────────────────── ├─ json.dumps()
    │   {success: true, user: {...}}     │
    │                                    │
    ├─ Receive response
    ├─ Parse JSON
    ├─ Update state
    ├─ Handle errors
    │
    ├─ Render UI
    └─ Show toast


Error Handling:
    │
    ├─ 400: Bad Request (validation)
    ├─ 401: Unauthorized (not logged in)
    ├─ 403: Forbidden (not admin)
    ├─ 404: Not Found
    ├─ 500: Server Error
    │
    └─ Display error toast
```

---

## State Management Flow

```
AUTHCONTEXT
    │
    ├─ State:
    │   ├─ user: {firstName, lastName, customerId, email}
    │   ├─ isAdmin: boolean
    │   ├─ isAuthenticated: boolean
    │   └─ loading: boolean
    │
    ├─ Functions:
    │   ├─ login(id, pwd) → {success, user}
    │   ├─ register(data) → {success, customerId}
    │   ├─ adminLogin(pin) → {success}
    │   └─ logout() → clears state & localStorage
    │
    └─ Persistence: localStorage


BANKCONTEXT
    │
    ├─ State:
    │   ├─ accounts: [{id, type, balance, ...}]
    │   ├─ loans: [{id, amount, outstanding, ...}]
    │   ├─ cards: [{id, limit, outstanding, ...}]
    │   ├─ deposits: [{id, amount, rate, ...}]
    │   └─ transactions: [{id, type, amount, ...}]
    │
    ├─ Functions:
    │   ├─ transferFunds(from, to, amount)
    │   ├─ payLoanEMI(loanId, amount)
    │   ├─ prepayLoan(loanId, amount)
    │   ├─ fetchAccountsData()
    │   ├─ fetchLoansData()
    │   └─ fetchCardsData()
    │
    └─ Fetching: Loads from mock data
        (Ready for API integration)


COMPONENT CONSUMPTION
    │
    ├─ useAuth() → {user, login, logout, ...}
    ├─ useBank() → {accounts, loans, transfer, ...}
    │
    └─ Re-renders on state change
```

---

## Database/Persistence Layer

```
RUNTIME STORAGE
    │
    ├─ In-Memory:
    │   ├─ bank.customers (list)
    │   ├─ bank.accounts (list)
    │   ├─ bank.loans (list)
    │   ├─ bank.cards (list)
    │   └─ bank.transactions (list)
    │
    └─ SESSION:
        ├─ session['customer_id']
        ├─ session['is_admin']
        └─ session.permanent

PERSISTENT STORAGE
    │
    ├─ DataStore.bak (binary)
    │   └─ pickle serialized data
    │
    ├─ CSV Files:
    │   ├─ accounts.csv
    │   ├─ account_numbers.txt
    │   ├─ customer_ids.txt
    │   └─ transaction_ids.json
    │
    └─ Save on:
        ├─ bank.save() call
        ├─ Transaction creation
        ├─ Account/Loan updates
        └─ Every operation


READY FOR UPGRADE TO:
    │
    ├─ PostgreSQL
    ├─ MySQL
    ├─ SQLite
    ├─ MongoDB
    └─ Other databases
```

---

## Frontend Build & Deployment

```
DEVELOPMENT                         PRODUCTION
    │                                    │
    ├─ npm start                        │
    │   ├─ Starts dev server            │
    │   ├─ Port 3000                    │
    │   ├─ Hot reload enabled           │
    │   └─ Source maps included         │
    │                                    │
    │                        npm run build
    │                            │
    │                            ├─ Minifies code
    │                            ├─ Tree shakes
    │                            ├─ Optimizes
    │                            ├─ Creates /build
    │                            └─ ~200KB gzip
    │
    └─ Can be deployed to:
        ├─ Netlify
        ├─ Vercel
        ├─ AWS S3 + CloudFront
        ├─ Azure Static Web Apps
        ├─ GitHub Pages
        └─ Any static host
```

---

## Backend Deployment

```
DEVELOPMENT                         PRODUCTION
    │                                    │
    ├─ python app.py                   │
    │   ├─ Flask dev server            │
    │   ├─ Auto-reload enabled          │
    │   ├─ Debug mode on                │
    │   └─ Port 5000                    │
    │                                    │
    └─ For Production:                  │
        ├─ Use Gunicorn/uWSGI          │
        ├─ Reverse proxy (Nginx)       │
        ├─ Load balancer               │
        ├─ Multiple workers            │
        ├─ Environment variables       │
        ├─ Error logging               │
        ├─ Monitoring                  │
        └─ Database persistence


Can be deployed to:
    ├─ Heroku
    ├─ AWS EC2 / Elastic Beanstalk
    ├─ Azure App Service
    ├─ Google Cloud Run
    ├─ DigitalOcean
    ├─ Kubernetes
    └─ Docker containers
```

---

## Security Architecture

```
AUTHENTICATION LAYER
    │
    ├─ Frontend:
    │   ├─ Form validation
    │   ├─ Password masking
    │   ├─ localStorage for session
    │   └─ Logout clears data
    │
    └─ Backend:
        ├─ Verify credentials
        ├─ Session creation
        ├─ Admin PIN check
        └─ Decorators for protection

AUTHORIZATION LAYER
    │
    ├─ @login_required
    │   └─ Checks: 'customer_id' in session
    │
    └─ @admin_required
        └─ Checks: session['is_admin']

API SECURITY
    │
    ├─ CORS enabled
    ├─ Session-based (cookies)
    ├─ Content validation
    ├─ Error handling (no stack traces)
    └─ Ready for JWT upgrade

FUTURE IMPROVEMENTS
    │
    ├─ JWT tokens
    ├─ HTTPS enforcement
    ├─ Rate limiting
    ├─ Input sanitization
    ├─ CSRF tokens
    └─ Security headers
```

---

## Performance Optimization

```
FRONTEND
    │
    ├─ React:
    │   ├─ Code splitting
    │   ├─ Lazy loading pages
    │   ├─ Memoization
    │   └─ Context optimization
    │
    ├─ CSS:
    │   ├─ CSS variables (no duplication)
    │   ├─ Efficient selectors
    │   ├─ Minimal nesting
    │   └─ No unused styles
    │
    └─ Bundle:
        ├─ ~200KB gzipped
        ├─ Tree shaking enabled
        └─ Minified production build

BACKEND
    │
    ├─ Flask:
    │   ├─ Efficient queries
    │   ├─ Session caching
    │   └─ Error handling
    │
    └─ Database:
        ├─ In-memory (fast)
        ├─ Periodic saves
        └─ Ready for DB upgrade
```

---

## Technology Integration Points

```
FRONTEND ◀────────────────────▶ BACKEND
    │                              │
    ├─ React Router                ├─ Flask routing
    ├─ Context API                 ├─ Session management
    ├─ Axios                       ├─ JSON responses
    ├─ React Toastify              ├─ Error messages
    └─ Chart.js                    └─ Analytics data

    │
    ├─ HTTP/REST API
    │   ├─ Method: POST/GET/PUT/DELETE
    │   ├─ Header: Content-Type: application/json
    │   ├─ Body: JSON payload
    │   └─ Response: JSON with status
    │
    └─ Error Handling
        ├─ Frontend: Toast notifications
        └─ Backend: JSON error responses
```

---

## Scalability Roadmap

```
PHASE 1: Single Instance (Current)
    ├─ Frontend: React SPA
    ├─ Backend: Flask single worker
    └─ Database: In-memory + file persistence

PHASE 2: Multi-Instance Ready
    ├─ Frontend: CDN distribution
    ├─ Backend: Multiple Gunicorn workers
    └─ Database: MySQL/PostgreSQL

PHASE 3: Cloud Native
    ├─ Frontend: CloudFront/Cloudflare
    ├─ Backend: Kubernetes pods
    ├─ Database: RDS/Cloud SQL
    └─ Storage: S3/Cloud Storage

PHASE 4: Enterprise
    ├─ Microservices architecture
    ├─ Message queues (Kafka/RabbitMQ)
    ├─ Distributed cache (Redis)
    ├─ Event streaming
    └─ Advanced monitoring
```

---

**This architecture diagram provides a complete overview of the Scala Bank system, showing component relationships, data flows, and integration points.**

