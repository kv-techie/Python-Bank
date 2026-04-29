# 🚀 Scala Bank - Full Stack Setup Guide

Complete guide for running the Scala Bank application with Python backend (Flask) and React frontend.

## System Requirements

- **Python**: 3.8 or higher
- **Node.js**: 14.0 or higher
- **npm**: 6.0 or higher
- **Git**: For version control
- **Terminal/Command Prompt**: For running commands

## Project Structure

```
Pythonified Bank/
├── backend/                  # Python banking system modules
│   ├── Bank.py
│   ├── Customer.py
│   ├── Account.py
│   ├── Loan.py
│   ├── Card.py
│   ├── CIBIL.py
│   ├── TaxCalculator.py
│   ├── AdminControlPanel.py
│   ├── AdminAnalytics.py
│   └── ...
├── frontend/                 # React web application
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── README.md
├── app.py                    # Flask backend server
├── requirements.txt          # Python dependencies
└── README.md
```

## Setup Instructions

### Step 1: Clone or Prepare the Repository

```bash
# Navigate to the project directory
cd "path/to/Pythonified Bank"
```

### Step 2: Set Up Python Backend

#### 2.1 Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask 2.3.0
- Flask-CORS 4.0.0 (for handling cross-origin requests from React)
- Flask-Login, Flask-SQLAlchemy
- python-dateutil, pytz, requests, Werkzeug, Jinja2, and other utilities

#### 2.3 Verify Flask Installation

```bash
python -c "import flask; print(flask.__version__)"
```

Expected output: `2.3.0`

### Step 3: Set Up React Frontend

#### 3.1 Navigate to Frontend Directory

```bash
cd frontend
```

#### 3.2 Install Node Dependencies

```bash
npm install
```

This will install:
- React 18.2.0
- React Router DOM 6.8.0
- Axios 1.3.0 (for API calls)
- Chart.js and react-chartjs-2 (for charts)
- React Icons
- React Toastify (for notifications)
- date-fns and other utilities

#### 3.3 Create Environment File

```bash
# Copy the example env file
cp .env.example .env

# Edit if needed (optional - defaults are usually fine)
# nano .env  # or use your favorite editor
```

Default `.env` content:
```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENVIRONMENT=development
```

### Step 4: Run the Application

You'll need two terminal windows/tabs open - one for the backend, one for the frontend.

#### Terminal 1: Flask Backend

```bash
# From project root (Pythonified Bank/)
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: off
```

The Flask server will start on **http://localhost:5000**

#### Terminal 2: React Frontend

```bash
# From frontend directory
npm start
```

Expected output:
```
On Your Network: http://192.168.x.x:3000
Compiled successfully!
```

The React app will automatically open in your browser at **http://localhost:3000**

## Login Credentials

### Customer Login
- **Customer ID**: CUST1001 (or any existing customer ID from the system)
- **Password**: (As configured in the system)

### Admin Login
- **URL**: http://localhost:3000/admin-login
- **PIN**: 1234 (default)

## Troubleshooting

### 1. Port Already in Use

If port 5000 or 3000 is already in use:

**Flask (port 5000):**
```bash
# Change port in app.py
app.run(debug=True, port=5001)
```

**React (port 3000):**
```bash
PORT=3001 npm start
```

Update `.env` accordingly:
```
REACT_APP_API_URL=http://localhost:5001
```

### 2. CORS Errors

If you see CORS errors in the browser console, ensure Flask has CORS enabled. Check that `app.py` has:
```python
from flask_cors import CORS
CORS(app)
```

### 3. Module Not Found Errors (Python)

```bash
# Make sure virtual environment is activated
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Then install dependencies again
pip install -r requirements.txt
```

### 4. Node Dependencies Issues

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### 5. Python Version Mismatch

Ensure you're using Python 3.8+:
```bash
python --version
# or
python3 --version
```

### 6. API Not Responding

1. Check Flask is running (http://localhost:5000 should show a page)
2. Check browser console for CORS errors
3. Verify `.env` file has correct API URL
4. Check network tab in browser developer tools for failed requests

## Development Workflow

### Making Changes to Backend

1. Edit files in `/backend/` or `app.py`
2. Flask will auto-reload with debug mode enabled
3. Refresh browser to see changes take effect

### Making Changes to Frontend

1. Edit files in `/frontend/src/`
2. React will auto-reload the app
3. Changes appear instantly in browser

### Testing Features

1. **Test Authentication**: Use login/register pages
2. **Test Transactions**: Use transfers, EMI payments
3. **Test Admin**: Access admin dashboard (PIN: 1234)
4. **Test Data**: Check browser console for API responses

## File Customization

### Change Admin PIN

Edit `app.py`:
```python
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin authentication"""
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        
        if pin == 'YOUR_NEW_PIN':  # Change this
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
```

### Change API Port

1. In `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change port here
```

2. In `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:5001
```

### Change Frontend Port

```bash
PORT=3001 npm start
```

## Database/Data Persistence

Currently, the application uses in-memory data storage. To persist data:

1. **For Testing**: Use the existing `DataStore.py` mechanism
2. **For Production**: Implement SQLAlchemy database integration
   - Update `app.py` to use Flask-SQLAlchemy
   - Create database models
   - Run migrations

## API Endpoints

### Authentication
- `POST /login` - Customer login
- `POST /register` - New customer registration
- `POST /admin-login` - Admin authentication
- `GET /logout` - Logout

### Banking Operations
- `GET /dashboard` - Customer dashboard data
- `GET /accounts` - List customer accounts
- `GET /account/<id>` - Account details
- `POST /account/<id>/transfer` - Transfer funds
- `GET /loans` - List customer loans
- `GET /loan/<id>` - Loan details
- `POST /loan/<id>/pay-emi` - Pay loan EMI
- `POST /loan/<id>/prepay` - Prepay loan
- `GET /cards` - List customer cards
- `GET /card/<id>` - Card details
- `POST /card/<id>/pay-bill` - Pay card bill
- `GET /deposits` - List deposits
- `GET /cibil` - CIBIL score
- `GET /tax` - Tax information

### Admin Operations
- `GET /admin` - Admin dashboard
- `GET /admin/customers` - List all customers
- `GET /admin/accounts` - List all accounts
- `GET /admin/loans` - List all loans

## Performance Tips

1. **Clear Cache**: `npm cache clean --force`
2. **Rebuild Frontend**: `npm run build`
3. **Check Network**: Use browser DevTools Network tab
4. **Monitor Console**: Watch for errors and warnings
5. **Use Redux DevTools**: For state management debugging

## Security Considerations

### Development Only
- Default admin PIN is 1234 (change before production)
- Session secrets are hardcoded (use environment variables)
- CORS is open to all origins (restrict in production)

### Production Recommendations
1. Use environment variables for secrets
2. Implement proper authentication (OAuth2, JWT)
3. Enable HTTPS
4. Restrict CORS to specific domains
5. Use production database (PostgreSQL, MySQL)
6. Implement rate limiting
7. Add request validation
8. Use CSRF tokens
9. Implement proper error handling

## Deployment

### To Heroku (Example)

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Deploy backend
git push heroku main

# Build and deploy frontend
cd frontend
npm run build
# Then follow Heroku frontend deployment guide
```

### To AWS/Azure/GCP

See platform-specific deployment guides.

## Building for Production

### Backend
```bash
# No special build needed, just ensure security configs
```

### Frontend
```bash
cd frontend
npm run build
```

This creates a `/build` directory with optimized production files.

## Logs and Debugging

### Flask Logs
Check terminal where Flask is running - all requests logged with:
- Request method and path
- Status code
- Response time

### React Logs
Check browser console (F12) for:
- Component errors
- API call failures
- State management issues

### Network Debugging
Use browser DevTools Network tab to:
- Monitor API calls
- Check request/response payloads
- Analyze performance

## Getting Help

### Common Issues
1. Review the Troubleshooting section above
2. Check Flask and React terminals for error messages
3. Open browser Developer Console (F12) for JavaScript errors
4. Check that both servers are running on correct ports

### Development
- For Python issues: Check `app.py` and backend modules
- For React issues: Check component files in `/frontend/src/`
- For styling issues: Check CSS files in `/frontend/src/styles/`

## Next Steps

1. **Customize Data**: Modify backend to use your own customer/account data
2. **Add Features**: Extend React components or Flask endpoints
3. **Connect Database**: Integrate SQLAlchemy for persistent storage
4. **Deploy**: Choose a hosting platform and deploy
5. **Monitor**: Set up logging and monitoring in production

## Version Information

- **Backend**: Flask 2.3.0
- **Frontend**: React 18.2.0 with React Router 6.8.0
- **Python**: 3.8+
- **Node**: 14.0+

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [React Router Documentation](https://reactrouter.com/)
- [Axios Documentation](https://axios-http.com/)

## Support

For issues, questions, or feature requests, contact the development team.

---

**Last Updated**: January 2025
**Setup Version**: 1.0.0
