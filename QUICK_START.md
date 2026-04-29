# ⚡ Quick Start Reference

Fast reference guide for developers to get the Scala Bank application up and running.

## One-Command Setup

### Windows
```bash
setup.bat
```

### macOS/Linux
```bash
chmod +x setup.sh
./setup.sh
```

---

## Manual Setup (5 minutes)

### Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
# ➡️ Server runs on http://localhost:5000
```

### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env (optional)
cp .env.example .env

# Run
npm start
# ➡️ Browser opens http://localhost:3000
```

---

## Running the Application

### Terminal 1 (Backend)
```bash
source venv/bin/activate  # or: venv\Scripts\activate on Windows
python app.py
```

### Terminal 2 (Frontend)
```bash
cd frontend
npm start
```

**Result**: Application opens at http://localhost:3000

---

## Default Credentials

### Customer Login
- **ID**: CUST1001 (or first existing customer)
- **Password**: (depends on system setup)

### Admin Dashboard
- **URL**: http://localhost:3000/admin-login
- **PIN**: 1234

---

## Essential Files

| File | Purpose |
|------|---------|
| `app.py` | Flask backend server |
| `requirements.txt` | Python dependencies |
| `frontend/package.json` | React dependencies |
| `SETUP_GUIDE.md` | Detailed setup instructions |
| `API_INTEGRATION_GUIDE.md` | API documentation |
| `PROJECT_STATUS.md` | Current status and progress |

---

## Common Tasks

### Install Dependencies
```bash
# Python
pip install -r requirements.txt

# JavaScript
cd frontend && npm install
```

### Run Backend Only
```bash
python app.py
# Visit http://localhost:5000/login
```

### Run Frontend Only
```bash
cd frontend && npm start
# Requires backend running on port 5000
```

### Build for Production
```bash
cd frontend
npm run build
# Creates /build folder with optimized files
```

### Check Versions
```bash
python --version     # Should be 3.8+
node --version      # Should be 14+
npm --version       # Should be 6+
```

### Troubleshoot Port 3000 Already in Use
```bash
PORT=3001 npm start  # Use different port
# Update REACT_APP_API_URL in .env if backend on different port
```

### Troubleshoot Port 5000 Already in Use
```bash
# Edit app.py, change:
# app.run(debug=True)
# to:
# app.run(debug=True, port=5001)
```

---

## Project Structure

```
📁 Scala Bank/
├── 📄 app.py                    # Flask backend
├── 📄 requirements.txt          # Python packages
├── 📁 backend/                  # Python modules
│   ├── Bank.py
│   ├── Customer.py
│   ├── Account.py
│   ├── Loan.py
│   ├── Card.py
│   ├── CIBIL.py
│   └── ... (more modules)
│
├── 📁 frontend/                 # React app
│   ├── 📄 package.json
│   ├── 📄 .env.example
│   ├── 📁 public/
│   │   └── index.html           # HTML entry point
│   └── 📁 src/
│       ├── App.js               # Main component
│       ├── index.js             # React render
│       ├── 📁 pages/            # Page components (15)
│       ├── 📁 components/       # UI components (2)
│       ├── 📁 context/          # State management (2)
│       └── 📁 styles/           # CSS files (14)
│
├── 📄 SETUP_GUIDE.md            # How to setup
├── 📄 API_INTEGRATION_GUIDE.md   # API reference
└── 📄 PROJECT_STATUS.md         # Current status
```

---

## Key Endpoints

### Authentication
- `POST /login` - Customer login
- `POST /register` - New customer signup
- `POST /admin-login` - Admin access
- `GET /logout` - Sign out

### Banking
- `GET /dashboard` - Home page data
- `GET /accounts` - All accounts
- `GET /loans` - All loans
- `GET /cards` - All cards
- `GET /deposits` - FD/RD data
- `GET /cibil` - Credit score
- `GET /tax` - Tax information

### Transfers
- `POST /account/<id>/transfer` - Send money

### Loans
- `POST /loan/<id>/pay-emi` - Pay EMI
- `POST /loan/<id>/prepay` - Prepay loan

### Admin
- `GET /admin` - Dashboard

---

## Testing Features

### Login Page
1. Go to http://localhost:3000
2. Enter Customer ID: CUST1001
3. Enter Password
4. Click Login

### Dashboard
1. View summary cards with balances
2. See recent accounts and loans
3. Click "Quick Actions"

### Transfers
1. Go to Transfer page
2. Select from/to accounts
3. Enter amount
4. Confirm

### Admin Dashboard
1. Go to http://localhost:3000/admin-login
2. Enter PIN: 1234
3. View charts and analytics

---

## Performance Tips

### Speed Up Installation
```bash
# Use npm ci instead of npm install (for exact versions)
cd frontend && npm ci
```

### Clear Cache
```bash
npm cache clean --force
rm -rf node_modules
npm install
```

### Faster React Build
```bash
cd frontend
npm run build -- --mode=production
```

---

## Documentation Links

- **Setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **API**: See [API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)
- **Status**: See [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Frontend**: See [frontend/README.md](frontend/README.md)
- **Main Project**: See [README.md](README.md)

---

## Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web app |
| Backend | http://localhost:5000 | API server |
| Login | http://localhost:3000 | Customer login |
| Admin | http://localhost:3000/admin-login | Admin dashboard |

---

## Environment Variables

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENVIRONMENT=development
```

---

## Git Commands

### Initial Setup
```bash
git init
git add .
git commit -m "Initial commit"
```

### Daily Workflow
```bash
git status           # See changes
git add .            # Stage all
git commit -m "..."  # Commit
git push             # Upload
```

---

## Debugging

### Browser Console
```javascript
// Check if frontend loaded
console.log(window.location.hostname)

// Check API calls
// Network tab in DevTools (F12)
```

### Backend Console
```python
# Check if Flask started
print("Server running...")

# Add print statements for debugging
```

### Check Services Running
```bash
# Frontend running
curl http://localhost:3000

# Backend running
curl http://localhost:5000/login
```

---

## File Locations

### Backend Files
- Main server: `app.py`
- Dependencies: `requirements.txt`
- Modules: `backend/` directory

### Frontend Files
- Entry point: `frontend/public/index.html`
- Main component: `frontend/src/App.js`
- Pages: `frontend/src/pages/`
- Styles: `frontend/src/styles/`

---

## Quick Fixes

### React Not Reloading
```bash
# Kill npm and restart
# Ctrl+C in frontend terminal
npm start
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :3000

# macOS/Linux
lsof -i :3000

# Kill the process and try again
```

### Flask 404 Errors
- Ensure backend is running on port 5000
- Check request URL in browser Network tab
- Verify API endpoint in `app.py`

### CORS Errors
- Ensure Flask has CORS enabled
- Check that frontend `.env` has correct API URL
- Restart both backend and frontend

---

## Next Steps

1. ✅ Setup application (see above)
2. 📖 Read SETUP_GUIDE.md
3. 🔌 Integrate frontend with backend (see API_INTEGRATION_GUIDE.md)
4. 🧪 Test all features
5. 🚀 Deploy to production

---

## Need Help?

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed steps
2. Review [API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md) for API details
3. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for current status
4. Review error messages in browser console (F12)
5. Check Flask server output for backend errors

---

**Last Updated**: January 2025  
**Version**: 1.0.0
