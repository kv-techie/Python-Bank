# 🔌 API Integration Guide

This guide explains how to integrate the React frontend with the Flask backend API.

## Current State

- **Frontend**: React with mock data (hardcoded in contexts)
- **Backend**: Flask with working endpoints and database
- **Status**: Ready for API integration

## Integration Steps

### Step 1: Update AuthContext.js

Replace mock authentication with API calls:

```javascript
// Before (mock):
export const login = async (customerId, password) => {
  const mockUser = mockCustomers.find(c => c.customer_id === customerId);
  if (mockUser && mockUser.password === password) {
    return { success: true, user: mockUser };
  }
  return { success: false, error: 'Invalid credentials' };
};

// After (API):
export const login = async (customerId, password) => {
  try {
    const response = await axios.post(`${API_URL}/login`, {
      customer_id: customerId,
      password: password
    });
    return { success: true, user: response.data.user };
  } catch (error) {
    return { success: false, error: error.response?.data?.error || 'Login failed' };
  }
};
```

### Step 2: Update BankContext.js

Replace mock data fetching with actual API calls:

```javascript
// Before (mock):
const fetchAccountsData = () => {
  setAccounts(mockAccounts);
};

// After (API):
const fetchAccountsData = async () => {
  try {
    const response = await axios.get(`${API_URL}/accounts`);
    setAccounts(response.data.accounts);
  } catch (error) {
    console.error('Failed to fetch accounts:', error);
  }
};
```

### Step 3: Update All API Calls

Replace all mock data operations with actual API endpoints:

#### Transfer Funds
```javascript
const transferFunds = async (fromAccountId, toAccountId, amount, description = '') => {
  try {
    const response = await axios.post(`${API_URL}/account/${fromAccountId}/transfer`, {
      recipient_account_id: toAccountId,
      amount: parseFloat(amount),
      description: description
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.response?.data?.error || 'Transfer failed' };
  }
};
```

#### Pay Loan EMI
```javascript
const payLoanEMI = async (loanId, accountId, amount) => {
  try {
    const response = await axios.post(`${API_URL}/loan/${loanId}/pay-emi`, {
      account_id: accountId,
      amount: parseFloat(amount)
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.response?.data?.error || 'EMI payment failed' };
  }
};
```

## API Endpoints

### Authentication

#### Login
```
POST /login
Headers: Content-Type: application/x-www-form-urlencoded
Body:
  customer_id: string
  password: string
Response: 
  {
    "success": true,
    "message": "Welcome back, John!",
    "user": {
      "customer_id": "CUST1001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com"
    }
  }
```

#### Register
```
POST /register
Headers: Content-Type: application/x-www-form-urlencoded
Body:
  first_name: string
  last_name: string
  email: string
  phone: string
  age: integer
  city: string
  account_type: string (Pride|Club|Bespoke|Delite|Future)
  password: string
Response:
  {
    "success": true,
    "message": "Account created successfully",
    "customer_id": "CUST1002",
    "account_id": "ACC001"
  }
```

#### Admin Login
```
POST /admin-login
Headers: Content-Type: application/x-www-form-urlencoded
Body:
  pin: string (default: 1234)
Response:
  {
    "success": true,
    "message": "Admin access granted"
  }
```

#### Logout
```
GET /logout
Response:
  {
    "success": true,
    "message": "Logged out successfully"
  }
```

### Banking Operations

#### Dashboard
```
GET /dashboard
Headers: Authorization: Bearer {session_token}
Response:
  {
    "accounts": [
      {
        "account_id": "ACC001",
        "account_type": "Savings",
        "balance": 125000.00,
        "status": "Active"
      }
    ],
    "loans": [
      {
        "loan_id": "LOAN001",
        "loan_type": "HOME",
        "amount": 1800000.00,
        "outstanding": 1500000.00,
        "monthly_emi": 25000.00
      }
    ],
    "total_balance": 625000.00,
    "total_outstanding_loans": 1500000.00
  }
```

#### Get Accounts
```
GET /accounts
Response:
  {
    "accounts": [
      {
        "account_id": "ACC001",
        "account_type": "Savings",
        "balance": 125000.00,
        "status": "Active",
        "created_date": "2023-01-15"
      }
    ]
  }
```

#### Get Account Details
```
GET /account/{account_id}
Response:
  {
    "account_id": "ACC001",
    "account_type": "Savings",
    "balance": 125000.00,
    "status": "Active",
    "transactions": [
      {
        "transaction_id": "TXN001",
        "type": "TRANSFER",
        "amount": 5000.00,
        "direction": "Debit",
        "description": "Transfer to ACC002",
        "timestamp": "2025-01-15 14:30:00"
      }
    ]
  }
```

#### Transfer Funds
```
POST /account/{account_id}/transfer
Body:
  recipient_account_id: string
  amount: float
  description: string (optional)
Response:
  {
    "success": true,
    "message": "Transfer successful",
    "from_balance": 120000.00,
    "to_balance": 510000.00
  }
```

#### Get Loans
```
GET /loans
Response:
  {
    "loans": [
      {
        "loan_id": "LOAN001",
        "loan_type": "HOME",
        "amount": 1800000.00,
        "outstanding": 1500000.00,
        "monthly_emi": 25000.00,
        "remaining_months": 60,
        "status": "Active"
      }
    ]
  }
```

#### Get Loan Details
```
GET /loan/{loan_id}
Response:
  {
    "loan_id": "LOAN001",
    "loan_type": "HOME",
    "amount": 1800000.00,
    "outstanding": 1500000.00,
    "monthly_emi": 25000.00,
    "interest_rate": 8.5,
    "tenure_months": 120,
    "remaining_months": 60,
    "status": "Active"
  }
```

#### Pay EMI
```
POST /loan/{loan_id}/pay-emi
Body:
  account_id: string
  amount: float
Response:
  {
    "success": true,
    "message": "EMI paid successfully",
    "remaining_outstanding": 1475000.00
  }
```

#### Prepay Loan
```
POST /loan/{loan_id}/prepay
Body:
  account_id: string
  amount: float
Response:
  {
    "success": true,
    "message": "Loan prepaid successfully",
    "penalty": 5000.00,
    "total_amount": 105000.00
  }
```

#### Get Cards
```
GET /cards
Response:
  {
    "cards": [
      {
        "card_id": "CARD001",
        "card_type": "Credit",
        "masked_number": "****1234",
        "limit": 500000.00,
        "outstanding": 150000.00,
        "status": "Active"
      }
    ]
  }
```

#### Pay Card Bill
```
POST /card/{card_id}/pay-bill
Body:
  account_id: string
  amount: float
Response:
  {
    "success": true,
    "message": "Bill paid successfully",
    "remaining_outstanding": 130000.00
  }
```

#### Get Deposits
```
GET /deposits
Response:
  {
    "fixed_deposits": [
      {
        "fd_id": "FD001",
        "amount": 500000.00,
        "rate": 6.5,
        "maturity_date": "2025-12-31",
        "status": "Active"
      }
    ],
    "recurring_deposits": [
      {
        "rd_id": "RD001",
        "monthly_amount": 10000.00,
        "rate": 5.5,
        "months": 60,
        "status": "Active"
      }
    ]
  }
```

#### Get CIBIL Score
```
GET /cibil
Response:
  {
    "score": 785,
    "rating": "Excellent",
    "breakdown": {
      "payment_history": {
        "score": 35,
        "percentage": 35,
        "rating": "Excellent"
      },
      "credit_utilization": {
        "score": 30,
        "percentage": 30,
        "rating": "Good"
      },
      "credit_mix": {
        "score": 15,
        "percentage": 15,
        "rating": "Good"
      },
      "credit_inquiries": {
        "score": 10,
        "percentage": 10,
        "rating": "Excellent"
      },
      "default_history": {
        "score": 10,
        "percentage": 10,
        "rating": "Excellent"
      }
    }
  }
```

#### Get Tax Information
```
GET /tax
Response:
  {
    "gross_income": 1200000.00,
    "deductions": {
      "section_80c": {
        "limit": 150000.00,
        "claimed": 100000.00,
        "remaining": 50000.00
      },
      "section_80d": {
        "limit": 50000.00,
        "claimed": 50000.00,
        "remaining": 0.00
      },
      "section_24": {
        "limit": 200000.00,
        "claimed": 180000.00,
        "remaining": 20000.00
      },
      "section_10_13a": {
        "limit": 300000.00,
        "claimed": 200000.00,
        "remaining": 100000.00
      }
    },
    "total_deductions": 530000.00,
    "taxable_income": 670000.00,
    "itr_status": {
      "last_filed": "2024-06-15",
      "status": "Completed",
      "refund_amount": 15000.00
    }
  }
```

### Admin Operations

#### Admin Dashboard
```
GET /admin
Headers: Is-Admin: true
Response:
  {
    "total_customers": 1250,
    "total_accounts": 2100,
    "total_deposits": 25000000.00,
    "total_loans": 18000000.00,
    "fee_revenue": 850000.00,
    "risk_score": 35,
    "loan_portfolio": {
      "HOME": 6000000.00,
      "VEHICLE": 5000000.00,
      "PERSONAL": 3000000.00,
      "EDUCATION": 2500000.00,
      "BUSINESS": 1500000.00
    },
    "account_distribution": {
      "Pride": 450,
      "Club": 600,
      "Bespoke": 200,
      "Delite": 400,
      "Future": 50
    }
  }
```

## Error Handling

All endpoints return error responses in this format:

```javascript
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (missing required fields, invalid data)
- `401` - Unauthorized (not logged in)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Server error

## CORS Configuration

The Flask app needs CORS enabled to allow requests from the React frontend:

```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

## Session Management

The application uses Flask sessions. After login, the session is automatically maintained in cookies. No explicit token management is needed for basic auth flow.

For JWT-based authentication (more secure), implement:

```javascript
// After login, store token
localStorage.setItem('token', response.data.token);

// Include in all API requests
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

## Testing API Integration

### Using Postman

1. Import the API endpoints listed above
2. Set base URL to `http://localhost:5000`
3. Test each endpoint manually
4. Verify request/response formats

### Using cURL

```bash
# Test login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "customer_id=CUST1001&password=password123"

# Test dashboard
curl -X GET http://localhost:5000/dashboard

# Test transfer
curl -X POST http://localhost:5000/account/ACC001/transfer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "recipient_account_id=ACC002&amount=5000"
```

## Best Practices

1. **Error Handling**: Always catch errors and display user-friendly messages
2. **Loading States**: Show loading spinners during API calls
3. **Validation**: Validate data on frontend before sending to backend
4. **Timeouts**: Set reasonable request timeouts (15-30 seconds)
5. **Retry Logic**: Implement automatic retries for failed requests
6. **Caching**: Cache data appropriately to reduce API calls
7. **Rate Limiting**: Implement client-side rate limiting

## Frontend Context Updates Example

```javascript
// AuthContext.js
const login = async (customerId, password) => {
  setLoading(true);
  try {
    const response = await axios.post(`${API_URL}/login`, {
      customer_id: customerId,
      password: password
    });
    
    setUser(response.data.user);
    setIsAuthenticated(true);
    
    // Store in localStorage for persistence
    localStorage.setItem('user', JSON.stringify(response.data.user));
    
    return { success: true };
  } catch (error) {
    const errorMsg = error.response?.data?.error || 'Login failed';
    return { success: false, error: errorMsg };
  } finally {
    setLoading(false);
  }
};
```

## Monitoring API Performance

Add timing logs to monitor API performance:

```javascript
const startTime = Date.now();
const response = await axios.get(`${API_URL}/accounts`);
const duration = Date.now() - startTime;
console.log(`Fetched accounts in ${duration}ms`);
```

---

**Next Steps**:
1. Implement axios configuration in contexts
2. Replace mock data with API calls
3. Test all endpoints systematically
4. Handle errors gracefully
5. Optimize performance
6. Deploy to production

