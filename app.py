"""
Flask Web Application for Scala Bank
Professional banking frontend with full feature support
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import json
import os
import csv
import secrets

from backend.Bank import Bank
from backend.BankingApp import BankingApp
from backend.Customer import Customer
from backend.Account import Account
from backend.Card import CreditCard, DebitCard
from backend.loan import Loan
from backend.Transaction import Transaction, TransactionType
from backend.CIBIL import calculate_cibil_score
from backend.AdminControlPanel import AdminControlPanel
from backend.AdminAnalytics import AdminAnalytics
from backend.FixedDeposit import FixedDeposit
from backend.RecurringDeposit import RecurringDeposit
from backend.BankClock import BankClock
from backend.Cheque import ChequeStatus
from backend.ChequeBook import ChequeBookStatus
from backend.FeeManager import fee_manager


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000", "supports_credentials": True}})
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Global bank instance
bank = Bank()


def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'customer_id' not in session:
            if request.is_json or request.headers.get('Accept', '').startswith('application/json') or request.headers.get('Origin'):
                return jsonify({"error": "Authentication required"}), 401
            flash('Please log in first.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session or not session['is_admin']:
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_user():
    """Inject user info into all templates"""
    if 'customer_id' in session:
        customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
        return {'current_user': customer, 'is_admin': session.get('is_admin', False)}
    return {'current_user': None, 'is_admin': False}


@app.route('/')
def index():
    """API health check - React frontend runs on port 3000"""
    return jsonify({"message": "Scala Bank API running. Use React frontend at http://localhost:3000", "status": "ok"})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Customer login"""
    if request.method == 'POST':
        # Handle both JSON (from React) and form data (from HTML forms)
        if request.is_json:
            data = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
        else:
            username = request.form.get('username', request.form.get('customer_id', '')).strip()
            password = request.form.get('password', '').strip()
        
        # Search by username first (from customers.json which uses username field)
        customer = next((c for c in bank.customers if c.username == username), None)
        
        if not customer:
            # Fallback: search by customer_id if username not found
            customer = next((c for c in bank.customers if c.customer_id == username), None)
        
        if customer and customer.password == password:
            session['customer_id'] = customer.customer_id
            session['is_admin'] = False
            session.permanent = True
            
            if request.is_json:
                return jsonify({
                    "success": True, 
                    "message": f"Welcome back, {customer.first_name}!",
                    "customer_id": customer.customer_id,
                    "first_name": customer.first_name,
                    "email": customer.email
                })
            else:
                flash(f'Welcome back, {customer.first_name}!', 'success')
                return redirect(url_for('dashboard'))
        else:
            error_msg = 'Invalid username or password.'
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 401
            else:
                flash(error_msg, 'danger')
    
    return render_template('login.html') if not request.is_json else jsonify({"error": "GET not supported"})


@app.route('/register', methods=['GET', 'POST'])
def register():
    """New customer registration"""
    if request.method == 'POST':
        # Handle both JSON (from React) and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        first_name = data.get('first_name', data.get('firstName', '')).strip()
        last_name = data.get('last_name', data.get('lastName', '')).strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', data.get('phoneNumber', '')).strip()
        age = data.get('age', '25')
        city = data.get('city', '').strip()
        password = data.get('password', '').strip()
        account_type = data.get('account_type', data.get('accountType', 'Pride'))
        
        try:
            age = int(age)
            
            if not first_name or not password:
                error_msg = 'First name and password are required.'
                if request.is_json:
                    return jsonify({"success": False, "error": error_msg}), 400
                flash(error_msg, 'danger')
                return render_template('register.html')
            
            # Generate customer ID
            import random
            cust_id = f"CUST{random.randint(10000000, 99999999)}"
            username = data.get('username', email.split('@')[0] if email else first_name.lower())
            
            customer = Customer(
                customer_id=cust_id,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                dob=data.get('dob', '2000-01-01'),
                gender=data.get('gender', 'Other'),
                phone_number=phone,
                email=email,
                city=city
            )
            
            bank.customers.append(customer)
            bank.save()
            
            if request.is_json:
                return jsonify({
                    "success": True,
                    "message": "Registration successful!",
                    "customer_id": cust_id,
                    "username": username
                })
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            if request.is_json:
                return jsonify({"success": False, "error": str(e)}), 500
            flash(f'Registration error: {str(e)}', 'danger')
    
    if request.is_json:
        return jsonify({"error": "POST required"}), 405
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """Customer dashboard — JSON API"""
    customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
    
    if not customer:
        session.clear()
        return jsonify({"error": "Not logged in"}), 401
    
    accounts = [acc for acc in bank.accounts if acc.customer_id == customer.customer_id]
    loans = [loan for loan in bank.loans if loan.customer_id == customer.customer_id]
    
    # Calculate totals
    total_balance = sum(acc.balance for acc in accounts)
    total_loans = sum(loan.get_remaining_balance() for loan in loans if loan.status == "Active")
    
    return jsonify({
        "customer_id": customer.customer_id,
        "first_name": getattr(customer, 'first_name', ''),
        "total_balance": total_balance,
        "total_loans": total_loans,
        "accounts_count": len(accounts),
        "loans_count": len(loans),
    })


@app.route('/accounts')
@login_required
def accounts():
    """Get all accounts for logged-in customer (API endpoint)"""
    try:
        customer_id = session.get('customer_id')
        customer = next((c for c in bank.customers if c.customer_id == customer_id), None)
        
        if not customer:
            return jsonify([])
        
        accounts_list = []
        for acc in bank.accounts:
            if acc.customer_id == customer.customer_id:
                accounts_list.append({
                    "id": getattr(acc, 'account_number', getattr(acc, 'account_id', 'N/A')),
                    "type": getattr(acc, 'account_type', 'Savings'),
                    "accountNumber": getattr(acc, 'account_number', 'N/A'),
                    "balance": getattr(acc, 'balance', 0),
                    "status": "Active",
                    "createdDate": getattr(acc, 'creation_date', '').isoformat() if hasattr(getattr(acc, 'creation_date', None), 'isoformat') else ""
                })
        
        return jsonify(accounts_list)
    except Exception as e:
        print(f"Error in /accounts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])


@app.route('/account/<account_id>')
@login_required
def view_account(account_id):
    """View account details — JSON API"""
    account = next((acc for acc in bank.accounts if acc.account_number == account_id), None)
    
    if not account or account.customer_id != session['customer_id']:
        return jsonify({"error": "Account not found or access denied"}), 404
    
    # Get recent transactions
    recent_txns = account.transactions[-20:] if hasattr(account, 'transactions') else []
    
    txns_list = []
    for t in recent_txns:
        txns_list.append({
            "id": getattr(t, 'transaction_id', ''),
            "type": str(getattr(t, 'transaction_type', '')),
            "amount": getattr(t, 'amount', 0),
            "direction": getattr(t, 'direction', ''),
            "date": getattr(t, 'timestamp', '').isoformat() if hasattr(getattr(t, 'timestamp', None), 'isoformat') else str(getattr(t, 'timestamp', '')),
            "description": getattr(t, 'description', '')
        })
    
    return jsonify({
        "id": account.account_number,
        "accountNumber": account.account_number,
        "type": getattr(account, 'account_type', 'Savings'),
        "balance": getattr(account, 'balance', 0),
        "status": "Active",
        "transactions": txns_list
    })


@app.route('/account/<account_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer(account_id):
    """Transfer money between accounts — JSON API"""
    try:
        account = next((acc for acc in bank.accounts if acc.account_number == account_id), None)
        
        if not account or account.customer_id != session['customer_id']:
            return jsonify({"success": False, "error": "Account not found or access denied"}), 404
        
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
            
            recipient_account_id = data.get('recipient_account_id', '').strip()
            amount = float(data.get('amount', 0))
            
            recipient = next((acc for acc in bank.accounts if acc.account_number == recipient_account_id), None)
            
            if not recipient:
                return jsonify({"success": False, "error": "Recipient account not found"}), 404
            elif amount <= 0:
                return jsonify({"success": False, "error": "Invalid amount"}), 400
            elif account.balance < amount:
                return jsonify({"success": False, "error": "Insufficient balance"}), 400
            else:
                account.balance -= amount
                recipient.balance += amount
                
                txn_debit = Transaction(account.account_number, TransactionType.TRANSFER, amount, 'Debit')
                txn_credit = Transaction(recipient.account_number, TransactionType.TRANSFER, amount, 'Credit')
                
                account.transactions.append(txn_debit)
                recipient.transactions.append(txn_credit)
                
                bank.save()
                
                return jsonify({
                    "success": True,
                    "message": f"₹{amount:,.2f} transferred successfully"
                })
        
        return jsonify({"success": True, "account_id": account_id})
    except Exception as e:
        print(f"Error in transfer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/loans')
@login_required
def loans():
    """Get all loans for logged-in customer (API endpoint)"""
    try:
        customer_id = session.get('customer_id')
        customer = next((c for c in bank.customers if c.customer_id == customer_id), None)
        
        if not customer:
            return jsonify([])
        
        loans_list = []
        for loan in getattr(bank, 'loans', []):
            if getattr(loan, 'customer_id', None) == customer.customer_id:
                # Use Loan class methods to compute actual values
                outstanding = loan.get_remaining_balance() if hasattr(loan, 'get_remaining_balance') else getattr(loan, 'outstanding_amount', 0)
                emi = loan.calculate_emi() if hasattr(loan, 'calculate_emi') else getattr(loan, 'emi_amount', 0)
                months_remaining = max(0, getattr(loan, 'tenure_months', 0) - getattr(loan, 'emis_paid', 0))
                loans_list.append({
                    "id": getattr(loan, 'loan_id', 'N/A'),
                    "type": getattr(loan, 'loan_type', 'Personal'),
                    "amount": getattr(loan, 'principal', 0),
                    "principal": getattr(loan, 'principal', 0),
                    "outstanding": outstanding,
                    "emi": emi,
                    "months_remaining": months_remaining,
                    "rateOfInterest": getattr(loan, 'interest_rate', 0),
                    "status": getattr(loan, 'status', 'Active')
                })
        
        return jsonify(loans_list)
    except Exception as e:
        print(f"Error in /loans: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])


@app.route('/loan/<loan_id>')
@login_required
def view_loan(loan_id):
    """View loan details"""
    loan = next((l for l in bank.loans if l.loan_id == loan_id), None)
    
    if not loan or loan.customer_id != session['customer_id']:
        flash('Loan not found.', 'danger')
        return redirect(url_for('loans'))
    
    # Get closure details if available
    closure_details = loan.get_closure_details() if hasattr(loan, 'get_closure_details') else None
    
    return render_template('loan_detail.html', 
                         loan=loan,
                         closure_details=closure_details)


@app.route('/loan/<loan_id>/pay-emi', methods=['POST'])
@login_required
def pay_emi(loan_id):
    """Pay EMI for a loan — JSON API"""
    try:
        loan = next((l for l in bank.loans if l.loan_id == loan_id), None)
        
        if not loan or loan.customer_id != session['customer_id']:
            return jsonify({"success": False, "error": "Loan not found"}), 404
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        account_id = data.get('account_id', '').strip()
        account = next((acc for acc in bank.accounts if acc.account_number == account_id), None)
        
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404
        
        emi_amount = loan.calculate_emi() if hasattr(loan, 'calculate_emi') else 0
        
        if account.balance < emi_amount:
            return jsonify({"success": False, "error": f"Insufficient balance. EMI: ₹{emi_amount:,.2f}"}), 400
        
        account.balance -= emi_amount
        loan.emis_paid += 1
        
        txn = Transaction(account.account_number, TransactionType.LOAN_EMI, emi_amount, 'Debit')
        account.transactions.append(txn)
        
        bank.save()
        
        return jsonify({
            "success": True,
            "message": f"EMI paid successfully! ₹{emi_amount:,.2f}",
            "emi_amount": emi_amount,
            "remaining_balance": loan.get_remaining_balance()
        })
    except Exception as e:
        print(f"Error in /loan/{loan_id}/pay-emi: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/loan/<loan_id>/prepay', methods=['GET', 'POST'])
@login_required
def prepay_loan(loan_id):
    """Prepay loan early with penalty — JSON API"""
    try:
        loan = next((l for l in bank.loans if l.loan_id == loan_id), None)
        
        if not loan or loan.customer_id != session['customer_id']:
            return jsonify({"success": False, "error": "Loan not found"}), 404
        
        closure_details = loan.get_closure_details()
        
        if request.method == 'GET':
            return jsonify({
                "success": True,
                "closure_details": closure_details
            })
        
        # POST — process prepayment
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        account_id = data.get('account_id', '').strip()
        account = next((acc for acc in bank.accounts if acc.account_number == account_id), None)
        
        if not account:
            return jsonify({"success": False, "error": "Account not found"}), 404
        
        total_payment = closure_details['total_payment']
        
        if account.balance < total_payment:
            return jsonify({"success": False, "error": f"Insufficient balance. Required: ₹{total_payment:,.2f}"}), 400
        
        account.balance -= total_payment
        
        txn_principal = Transaction(account.account_number, TransactionType.LOAN_PREPAYMENT, 
                                  closure_details['remaining_balance'], 'Debit')
        account.transactions.append(txn_principal)
        
        if closure_details['penalty_amount'] > 0:
            txn_penalty = Transaction(account.account_number, TransactionType.LOAN_PREPAYMENT_PENALTY,
                                    closure_details['penalty_amount'], 'Debit')
            account.transactions.append(txn_penalty)
            loan.prepayment_penalty_charged = closure_details['penalty_amount']
        
        loan.status = "Closed"
        loan.emis_paid = loan.tenure_months
        
        bank.save()
        
        return jsonify({
            "success": True,
            "message": f"Loan prepaid successfully! Total: ₹{total_payment:,.2f}",
            "total_payment": total_payment
        })
    except Exception as e:
        print(f"Error in /loan/{loan_id}/prepay: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/cards')
@login_required
def cards():
    """Get all cards for logged-in customer (API endpoint)"""
    try:
        customer_id = session.get('customer_id')
        customer = next((c for c in bank.customers if c.customer_id == customer_id), None)
        
        if not customer:
            return jsonify([])
        
        all_cards = []
        for account in getattr(bank, 'accounts', []):
            if getattr(account, 'customer_id', None) == customer.customer_id:
                # Account.cards is a List[Card] — each card has card_type ("CREDIT" or "DEBIT")
                for card in getattr(account, 'cards', []):
                    try:
                        card_type_raw = getattr(card, 'card_type', 'DEBIT').upper()
                        is_credit = card_type_raw == 'CREDIT'
                        card_data = {
                            "cardId": getattr(card, 'card_id', ''),
                            "cardNumber": str(getattr(card, 'card_number', 'XXXX'))[-4:],
                            "cardType": "Credit" if is_credit else "Debit",
                            "status": "Blocked" if getattr(card, 'blocked', False) else "Active",
                            "network": getattr(card, 'network', 'Visa'),
                            "expiryDate": str(getattr(card, 'expiry_date', '')),
                            "isPinSet": getattr(card, 'is_pin_set', False),
                        }
                        if is_credit:
                            card_data["limit"] = getattr(card, 'credit_limit', 0)
                            card_data["outstanding"] = getattr(card, 'outstanding_balance', getattr(card, 'credit_used', 0))
                            card_data["balance"] = getattr(card, 'outstanding_balance', 0)
                            card_data["availableLimit"] = getattr(card, 'credit_limit', 0) - getattr(card, 'credit_used', 0)
                        else:
                            card_data["limit"] = getattr(card, 'daily_limit', 0)
                            card_data["balance"] = getattr(account, 'balance', 0)
                        all_cards.append(card_data)
                    except Exception as card_err:
                        print(f"Error processing card: {card_err}")
        
        return jsonify(all_cards)
    except Exception as e:
        print(f"Error in /cards: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])


@app.route('/card/<card_id>')
@login_required
def view_card(card_id):
    """View card details"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            if hasattr(account, 'credit_cards'):
                card = next((c for c in account.credit_cards if c.card_id == card_id), None)
                if card:
                    return render_template('card_detail.html', card=card, account=account)
            if hasattr(account, 'debit_cards'):
                card = next((c for c in account.debit_cards if c.card_id == card_id), None)
                if card:
                    return render_template('card_detail.html', card=card, account=account)
    
    flash('Card not found.', 'danger')
    return redirect(url_for('cards'))


@app.route('/api/card/<card_id>/status')
@login_required
def card_pin_status(card_id):
    """Check if card PIN is set and other status details"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            # Search both cards list directly and via property if exists
            cards = getattr(account, 'cards', [])
            card = next((c for c in cards if c.card_id == card_id), None)
            
            if card:
                return jsonify({
                    "success": True,
                    "isPinSet": getattr(card, 'is_pin_set', False),
                    "blocked": getattr(card, 'blocked', False),
                    "remainingAttempts": 3 - getattr(card, 'failed_pin_attempts', 0)
                })
    
    return jsonify({"success": False, "error": "Card not found"}), 404

@app.route('/api/card/<card_id>/pin', methods=['POST'])
@login_required
def set_card_pin(card_id):
    """Set or change card PIN"""
    data = request.get_json()
    new_pin = data.get('pin')
    
    if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
        return jsonify({"success": False, "error": "PIN must be 4 digits"}), 400
        
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            cards = getattr(account, 'cards', [])
            card = next((c for c in cards if c.card_id == card_id), None)
            
            if card:
                if hasattr(card, 'set_pin'):
                    card.set_pin(new_pin)
                    bank.save()
                    return jsonify({"success": True, "message": "PIN updated successfully"})
                else:
                    return jsonify({"success": False, "error": "Card model doesn't support PIN operations"}), 500
                    
    return jsonify({"success": False, "error": "Card not found"}), 404

@app.route('/api/card/<card_id>/verify-pin', methods=['POST'])
@login_required
def verify_card_pin(card_id):
    """Verify card PIN before a sensitive action"""
    data = request.get_json()
    entered_pin = data.get('pin')
    
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            cards = getattr(account, 'cards', [])
            card = next((c for c in cards if c.card_id == card_id), None)
            
            if card:
                if hasattr(card, 'verify_pin'):
                    success, message = card.verify_pin(entered_pin)
                    bank.save() # Save failed attempts/blocking
                    return jsonify({"success": success, "message": message})
                else:
                    return jsonify({"success": False, "error": "Card model doesn't support PIN verification"}), 500
                    
    return jsonify({"success": False, "error": "Card not found"}), 404


@app.route('/api/accounts/<account_number>/withdraw', methods=['POST'])
@login_required
def atm_withdraw(account_number):
    """Simulate ATM withdrawal with card and PIN"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    card_id = data.get('card_id')
    pin = data.get('pin')
    
    account = next((acc for acc in bank.accounts if acc.account_number == account_number), None)
    if not account or account.customer_id != session['customer_id']:
        return jsonify({"success": False, "error": "Account not found"}), 404
        
    card = next((c for c in account.cards if c.card_id == card_id), None)
    if not card:
        return jsonify({"success": False, "error": "Card not linked to this account"}), 404
        
    # Account.withdraw(amount, card, pin) handles the PIN verification and balance checks
    try:
        # Capture print statements if needed, or check for return values
        # Since I modified Account.py to return early on failure, I'll need to check balance or status
        old_balance = account.balance
        account.withdraw(amount, card, pin)
        
        if account.balance < old_balance:
            bank.save()
            return jsonify({
                "success": True, 
                "message": f"Successfully withdrawn ₹{amount:,.2f}",
                "new_balance": account.balance
            })
        else:
            return jsonify({"success": False, "error": "Withdrawal failed. Check PIN or balance."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/accounts/<account_number>/deposit', methods=['POST'])
@login_required
def atm_deposit(account_number):
    """Simulate Cash Deposit with card and PIN"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    card_id = data.get('card_id')
    pin = data.get('pin')
    
    account = next((acc for acc in bank.accounts if acc.account_number == account_number), None)
    if not account or account.customer_id != session['customer_id']:
        return jsonify({"success": False, "error": "Account not found"}), 404
        
    card = next((c for c in account.cards if c.card_id == card_id), None)
    if not card:
        return jsonify({"success": False, "error": "Card not linked to this account"}), 404
        
    try:
        old_balance = account.balance
        account.deposit(amount, card, pin)
        
        if account.balance > old_balance:
            bank.save()
            return jsonify({
                "success": True, 
                "message": f"Successfully deposited ₹{amount:,.2f}",
                "new_balance": account.balance
            })
        else:
            return jsonify({"success": False, "error": "Deposit failed. Check PIN."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/card/<card_id>/pay-bill', methods=['POST'])
@login_required
def pay_card_bill(card_id):
    """Pay credit card bill"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            if hasattr(account, 'credit_cards'):
                card = next((c for c in account.credit_cards if c.card_id == card_id), None)
                if card:
                    amount = float(request.form.get('amount', 0))
                    
                    if amount <= 0:
                        flash('Invalid amount.', 'danger')
                    elif account.balance < amount:
                        flash('Insufficient balance.', 'danger')
                    elif amount > card.outstanding_balance:
                        flash('Amount exceeds outstanding balance.', 'danger')
                    else:
                        try:
                            account.balance -= amount
                            card.outstanding_balance -= amount
                            
                            txn = Transaction(account.account_id, TransactionType.CREDIT_CARD_PAYMENT, amount, 'Debit')
                            account.transactions.append(txn)
                            
                            bank.save()
                            
                            flash(f'Payment successful! ₹{amount:,.2f}', 'success')
                        
                        except Exception as e:
                            flash(f'Payment error: {str(e)}', 'danger')
                    
                    return redirect(url_for('view_card', card_id=card_id))
    
    flash('Card not found.', 'danger')
    return redirect(url_for('cards'))


@app.route('/deposits')
@login_required
def deposits():
    """Get all deposits (FD and RD) for logged-in customer (API endpoint)"""
    try:
        customer_id = session.get('customer_id')
        customer = next((c for c in bank.customers if c.customer_id == customer_id), None)
        
        if not customer:
            return jsonify({"fixedDeposits": [], "recurringDeposits": []})
        
        # Get customer's account numbers
        customer_accounts = set()
        for acc in bank.accounts:
            if getattr(acc, 'customer_id', None) == customer.customer_id:
                customer_accounts.add(acc.account_number)
        
        fd_list = []
        rd_list = []
        
        # bank.fixed_deposits is a dict keyed by fd_number
        for fd_id, fd in getattr(bank, 'fixed_deposits', {}).items():
            if getattr(fd, 'account_number', '') in customer_accounts:
                try:
                    mat_date = getattr(fd, 'maturity_date', None)
                    if hasattr(mat_date, 'strftime'):
                        mat_date = mat_date.strftime('%Y-%m-%d')
                    else:
                        mat_date = str(mat_date) if mat_date else ''
                    
                    fd_list.append({
                        "depositId": getattr(fd, 'fd_number', fd_id),
                        "amount": getattr(fd, 'principal_amount', 0),
                        "rate": getattr(fd, 'interest_rate', 0),
                        "tenureMonths": getattr(fd, 'tenure_months', 0),
                        "maturityDate": mat_date,
                        "maturityAmount": getattr(fd, 'maturity_amount', 0),
                        "status": getattr(fd, 'status', 'Active'),
                        "startDate": getattr(fd, 'start_date', '').strftime('%Y-%m-%d') if hasattr(getattr(fd, 'start_date', None), 'strftime') else ''
                    })
                except Exception as fd_err:
                    print(f"Error processing FD {fd_id}: {fd_err}")
        
        # bank.recurring_deposits is a dict keyed by rd_number
        for rd_id, rd in getattr(bank, 'recurring_deposits', {}).items():
            if getattr(rd, 'account_number', '') in customer_accounts:
                try:
                    mat_date = getattr(rd, 'maturity_date', None)
                    if hasattr(mat_date, 'strftime'):
                        mat_date = mat_date.strftime('%Y-%m-%d')
                    else:
                        mat_date = str(mat_date) if mat_date else ''
                    
                    rd_list.append({
                        "depositId": getattr(rd, 'rd_number', rd_id),
                        "monthlyInstallment": getattr(rd, 'monthly_installment', 0),
                        "rate": getattr(rd, 'interest_rate', 0),
                        "tenureMonths": getattr(rd, 'tenure_months', 0),
                        "installmentsPaid": getattr(rd, 'installments_paid', 0),
                        "totalDeposited": getattr(rd, 'total_deposited', 0),
                        "maturityDate": mat_date,
                        "status": getattr(rd, 'status', 'Active'),
                        "autopayEnabled": getattr(rd, 'autopay_enabled', False),
                        "startDate": getattr(rd, 'start_date', '').strftime('%Y-%m-%d') if hasattr(getattr(rd, 'start_date', None), 'strftime') else ''
                    })
                except Exception as rd_err:
                    print(f"Error processing RD {rd_id}: {rd_err}")
        
        return jsonify({"fixedDeposits": fd_list, "recurringDeposits": rd_list})
    except Exception as e:
        print(f"Error in /deposits: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"fixedDeposits": [], "recurringDeposits": []})


@app.route('/cibil')
@login_required
def cibil_score():
    """View CIBIL score and report — JSON API"""
    try:
        customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
        
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        
        # Calculate CIBIL score
        score = calculate_cibil_score(customer, bank)
        customer.cibil_score = score
        
        # Determine rating
        if score >= 750:
            rating = 'Excellent'
            color = 'success'
        elif score >= 650:
            rating = 'Good'
            color = 'info'
        elif score >= 550:
            rating = 'Average'
            color = 'warning'
        else:
            rating = 'Poor'
            color = 'danger'
        
        return jsonify({
            "score": score,
            "rating": rating,
            "color": color,
            "maxScore": 900
        })
    except Exception as e:
        print(f"Error in /cibil: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"score": 0, "rating": "Unknown", "color": "danger", "maxScore": 900})


@app.route('/tax')
@login_required
def tax_management():
    """Tax management and ITR filing — JSON API"""
    try:
        customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
        
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        
        accounts = [acc for acc in bank.accounts if acc.customer_id == customer.customer_id]
        
        # Find salary profile from customer's accounts
        salary_profile = None
        gross_income = 0
        customer_accs = [acc for acc in bank.accounts if acc.customer_id == customer.customer_id]
        for acc in customer_accs:
            if getattr(acc, 'salary_profile', None):
                salary_profile = acc.salary_profile
                gross_income = getattr(salary_profile, 'gross_salary', 0) * 12
                break
        
        # If no salary profile, try customer salary attribute
        if gross_income == 0:
            gross_income = getattr(customer, 'salary', 0) * 12 if getattr(customer, 'salary', None) else 0
        
        deductions = {}
        try:
            from backend.TaxDeductionAnalyzer import TaxDeductionAnalyzer
            deductions = TaxDeductionAnalyzer.get_all_deductions(
                customer, salary_profile, is_metro=False, bank=bank
            )
        except Exception as e:
            print(f"TaxDeductionAnalyzer error: {e}")
            import traceback
            traceback.print_exc()
        
        # Build deductions with limits for frontend
        SECTION_LIMITS = {
            '16': 50000,
            '10(13A)': 300000,
            '80C': 150000,
            '80D': 50000,
            '24': 200000,
        }
        SECTION_NAMES = {
            '16': 'Standard Deduction',
            '10(13A)': 'HRA',
            '80C': '80C',
            '80D': '80D',
            '24': '24 (Home Loan Interest)',
        }
        
        deductions_detail = {}
        for section, amount in deductions.items():
            deductions_detail[SECTION_NAMES.get(section, section)] = {
                'limit': SECTION_LIMITS.get(section, amount),
                'claimed': amount
            }
        
        total_deductions = sum(deductions.values())
        
        return jsonify({
            "grossIncome": gross_income,
            "totalDeductions": total_deductions,
            "taxableIncome": max(0, gross_income - total_deductions),
            "deductions": deductions_detail,
            "taxRegime": getattr(customer, 'tax_regime', 'OLD_REGIME'),
            "pan": getattr(customer, 'pan', None)
        })
    except Exception as e:
        print(f"Error in /tax: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"grossIncome": 0, "deductions": {}, "taxRegime": "OLD_REGIME"})



# ========== CARD MANAGEMENT ENDPOINTS ==========

@app.route('/api/card/apply', methods=['POST'])
@login_required
def apply_card():
    """Apply for a new debit or credit card"""
    data = request.get_json()
    card_type = data.get('card_type', 'DEBIT').upper()  # DEBIT or CREDIT
    network = data.get('network', 'VISA').upper()
    account_number = data.get('account_number')
    billing_day = int(data.get('billing_day', 1))
    auto_pay_policy = data.get('auto_pay_policy', 'NONE').upper()

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    try:
        if card_type == 'DEBIT':
            from backend.Card import DebitCard
            from datetime import datetime, timedelta
            expiry = datetime.now() + timedelta(days=365 * 4)
            card = DebitCard(
                card_number=f"4{''.join([str(__import__('random').randint(0,9)) for _ in range(15)])}",
                expiry_date=expiry,
                cvv=str(__import__('random').randint(100, 999)),
                card_id=f"DC{account_number[-6:]}{__import__('random').randint(1000,9999)}",
                network=network
            )
            card.is_pin_set = False
            account.cards.append(card)
            bank.save()
            return jsonify({"success": True, "message": f"{network} Debit Card issued successfully!", "card_id": card.card_id})

        elif card_type == 'CREDIT':
            from backend.Card import CreditCard
            from backend.CreditEvaluator import CreditEvaluator
            from backend.CIBIL import calculate_cibil_score

            customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
            if not customer:
                return jsonify({"success": False, "error": "Customer not found"}), 404

            if not account.salary_profile:
                return jsonify({"success": False, "error": "Credit card requires a salary profile. Please set up salary first."}), 400

            dob = datetime.strptime(account.dob, "%Y-%m-%d")
            age = (datetime.now() - dob).days // 365
            cibil_score = calculate_cibil_score(customer, bank)
            annual_income = account.salary_profile.gross_salary * 12

            eligible, reason = CreditEvaluator.is_eligible_for_credit_card(cibil_score, annual_income, age)
            if not eligible:
                return jsonify({"success": False, "error": f"Not eligible: {reason}"}), 400

            credit_limit = CreditEvaluator.calculate_credit_limit(
                cibil_score=cibil_score, annual_income=annual_income, age=age,
                existing_debt=0.0,
                employer_category=getattr(customer, 'employer_category', 'pvt'),
                has_salary_account=True
            )

            from datetime import datetime, timedelta
            expiry = datetime.now() + timedelta(days=365 * 4)
            card = CreditCard(
                card_number=f"5{''.join([str(__import__('random').randint(0,9)) for _ in range(15)])}",
                expiry_date=expiry,
                cvv=str(__import__('random').randint(100, 999)),
                card_id=f"CC{account_number[-6:]}{__import__('random').randint(1000,9999)}",
                network=network,
                credit_limit=credit_limit,
                billing_day=billing_day
            )
            card.auto_pay_policy = auto_pay_policy
            card.is_pin_set = False
            account.cards.append(card)
            bank.save()
            return jsonify({
                "success": True,
                "message": f"{network} Credit Card issued! Limit: ₹{credit_limit:,.0f}",
                "card_id": card.card_id,
                "credit_limit": credit_limit,
                "cibil_score": cibil_score
            })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/card/<card_id>/block', methods=['POST'])
@login_required
def block_card_api(card_id):
    """Block a card"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            card = next((c for c in account.cards if c.card_id == card_id), None)
            if card:
                card.blocked = True
                bank.save()
                return jsonify({"success": True, "message": "Card blocked successfully"})
    return jsonify({"success": False, "error": "Card not found"}), 404


@app.route('/api/card/<card_id>/unblock', methods=['POST'])
@login_required
def unblock_card_api(card_id):
    """Unblock a card"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            card = next((c for c in account.cards if c.card_id == card_id), None)
            if card:
                card.blocked = False
                card.failed_pin_attempts = 0
                bank.save()
                return jsonify({"success": True, "message": "Card unblocked successfully"})
    return jsonify({"success": False, "error": "Card not found"}), 404


@app.route('/api/card/<card_id>/pay-bill', methods=['POST'])
@login_required
def pay_card_bill_api(card_id):
    """Pay credit card bill via JSON API"""
    data = request.get_json()
    amount = float(data.get('amount', 0))

    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            card = next((c for c in account.cards if c.card_id == card_id), None)
            if card:
                from backend.Card import CreditCard
                if not isinstance(card, CreditCard):
                    return jsonify({"success": False, "error": "Not a credit card"}), 400
                outstanding = getattr(card, 'credit_used', 0)
                if amount <= 0:
                    return jsonify({"success": False, "error": "Invalid amount"}), 400
                if account.balance < amount:
                    return jsonify({"success": False, "error": "Insufficient balance"}), 400
                if amount > outstanding:
                    return jsonify({"success": False, "error": f"Amount exceeds outstanding ₹{outstanding:,.2f}"}), 400
                try:
                    success, message, txn_id = card.pay_bill_with_rewards(amount, 0, account)
                    if success:
                        bank.save()
                        return jsonify({"success": True, "message": message, "new_outstanding": card.credit_used})
                    return jsonify({"success": False, "error": message}), 400
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "Card not found"}), 404


@app.route('/api/card/<card_id>/statement')
@login_required
def card_statement(card_id):
    """Get credit card statement"""
    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            card = next((c for c in account.cards if c.card_id == card_id), None)
            if card:
                from backend.Card import CreditCard
                transactions = []
                if hasattr(card, 'transactions'):
                    for txn in card.transactions[-30:]:  # last 30 txns
                        transactions.append({
                            "date": str(getattr(txn, 'date', '') or getattr(txn, 'timestamp', '')),
                            "description": str(getattr(txn, 'description', '') or getattr(txn, 'merchant', '')),
                            "amount": getattr(txn, 'amount', 0),
                            "type": str(getattr(txn, 'type', 'PURCHASE'))
                        })
                return jsonify({
                    "card_id": card_id,
                    "outstanding": getattr(card, 'credit_used', 0),
                    "credit_limit": getattr(card, 'credit_limit', 0),
                    "available": getattr(card, 'credit_limit', 0) - getattr(card, 'credit_used', 0),
                    "reward_points": getattr(card, 'reward_points', 0),
                    "billing_day": getattr(card, 'billing_day', 1),
                    "transactions": transactions
                })
    return jsonify({"success": False, "error": "Card not found"}), 404


@app.route('/api/card/<card_id>/purchase', methods=['POST'])
@login_required
def card_purchase(card_id):
    """Make a purchase with a card (PIN-verified)"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    merchant = data.get('merchant', 'Unknown Merchant')
    category = data.get('category', 'Shopping')

    for account in bank.accounts:
        if account.customer_id == session['customer_id']:
            card = next((c for c in account.cards if c.card_id == card_id), None)
            if card:
                try:
                    account.make_card_purchase(card_id, amount, merchant, category)
                    bank.save()
                    return jsonify({"success": True, "message": f"Purchase of ₹{amount:,.2f} at {merchant} successful!"})
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)}), 400
    return jsonify({"success": False, "error": "Card not found"}), 404


# ========== FD/RD ENDPOINTS ==========

@app.route('/api/deposits/fd/create', methods=['POST'])
@login_required
def create_fd():
    """Create a new Fixed Deposit"""
    data = request.get_json()
    account_number = data.get('account_number')
    amount = float(data.get('amount', 0))
    tenure = int(data.get('tenure_months', 12))

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    try:
        success, message, fd = bank.create_fixed_deposit(account, amount, tenure)
        if success:
            bank.save()
            return jsonify({
                "success": True,
                "message": message,
                "fd_id": getattr(fd, 'fd_number', ''),
                "maturity_amount": getattr(fd, 'maturity_amount', 0),
                "rate": getattr(fd, 'interest_rate', 0)
            })
        return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/deposits/rd/create', methods=['POST'])
@login_required
def create_rd():
    """Create a new Recurring Deposit"""
    data = request.get_json()
    account_number = data.get('account_number')
    monthly = float(data.get('monthly_installment', 0))
    tenure = int(data.get('tenure_months', 12))
    autopay = bool(data.get('enable_autopay', False))
    autopay_day = int(data.get('autopay_day', 1))

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    try:
        success, message, rd = bank.create_recurring_deposit(account, monthly, tenure, autopay, autopay_day)
        if success:
            bank.save()
            return jsonify({
                "success": True,
                "message": message,
                "rd_id": getattr(rd, 'rd_number', ''),
                "maturity_amount": getattr(rd, 'maturity_amount', 0) if hasattr(rd, 'maturity_amount') else 0
            })
        return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/deposits/rd/<rd_id>/pay', methods=['POST'])
@login_required
def pay_rd_installment_api(rd_id):
    """Manually pay an RD installment"""
    data = request.get_json()
    account_number = data.get('account_number')

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    rd = bank.recurring_deposits.get(rd_id)
    if not rd:
        return jsonify({"success": False, "error": "RD not found"}), 404

    try:
        success, message = bank.pay_rd_installment(rd_id, account)
        if success:
            bank.save()
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/deposits/fd/<fd_id>/close', methods=['POST'])
@login_required
def close_fd_api(fd_id):
    """Close an FD prematurely"""
    data = request.get_json()
    account_number = data.get('account_number')

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    fd = bank.fixed_deposits.get(fd_id)
    if not fd:
        return jsonify({"success": False, "error": "FD not found"}), 404

    try:
        success, message, amount = bank.close_fixed_deposit(fd_id, account, premature=True)
        if success:
            bank.save()
            return jsonify({"success": True, "message": message, "amount_credited": amount})
        return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/deposits/rd/<rd_id>/close', methods=['POST'])
@login_required
def close_rd_api(rd_id):
    """Close an RD prematurely"""
    data = request.get_json()
    account_number = data.get('account_number')

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    rd = bank.recurring_deposits.get(rd_id)
    if not rd:
        return jsonify({"success": False, "error": "RD not found"}), 404

    try:
        success, message, amount = bank.close_recurring_deposit(rd_id, account, premature=True)
        if success:
            bank.save()
            return jsonify({"success": True, "message": message, "amount_credited": amount})
        return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/deposits/rates')
def deposit_rates():
    """Get FD/RD interest rates"""
    return jsonify({
        "fd_rates": FixedDeposit.INTEREST_RATES,
        "rd_rates": RecurringDeposit.INTEREST_RATES,
        "fd_min": FixedDeposit.MIN_AMOUNT,
        "fd_max": FixedDeposit.MAX_AMOUNT,
        "rd_min": RecurringDeposit.MIN_MONTHLY_AMOUNT,
        "rd_max": RecurringDeposit.MAX_MONTHLY_AMOUNT,
        "senior_bonus_fd": FixedDeposit.SENIOR_CITIZEN_BONUS,
        "senior_bonus_rd": RecurringDeposit.SENIOR_CITIZEN_BONUS
    })


# ========== LOAN APPLICATION ENDPOINT ==========

@app.route('/api/loans/apply', methods=['POST'])
@login_required
def apply_loan():
    """Apply for a new loan"""
    data = request.get_json()
    account_number = data.get('account_number')
    loan_type = data.get('loan_type', 'PERSONAL').upper()
    principal = float(data.get('principal', 0))
    interest_rate = float(data.get('interest_rate', 10))
    tenure_months = int(data.get('tenure_months', 12))

    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
    if not customer:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    try:
        from backend.CIBIL import calculate_cibil_score, add_credit_inquiry
        add_credit_inquiry(customer)
        customer.cibil_score = calculate_cibil_score(customer, bank)

        approved, loan, msg = bank.evaluate_and_add_loan(
            customer, principal, interest_rate, tenure_months, account, loan_type
        )
        if approved:
            bank.save()
            emi = loan.calculate_emi()
            return jsonify({
                "success": True,
                "message": f"Loan approved! ₹{principal:,.2f} credited to your account.",
                "loan_id": loan.loan_id,
                "emi": emi,
                "interest_rate": loan.interest_rate,
                "cibil_score": customer.cibil_score
            })
        return jsonify({"success": False, "error": msg}), 400
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ========== ACCOUNT MANAGEMENT ENDPOINTS ==========

@app.route('/api/accounts/create', methods=['POST'])
@login_required
def create_account():
    """Create an additional account for the customer"""
    data = request.get_json()
    account_type = data.get('account_type', 'Savings')

    customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)
    if not customer:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    try:
        account = bank.create_additional_account(customer, account_type)
        bank.save()
        return jsonify({
            "success": True,
            "message": f"{account_type} account created successfully!",
            "account_number": account.account_number
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/accounts/<account_number>/close', methods=['POST'])
@login_required
def close_account_api(account_number):
    """Close an account"""
    account = next((acc for acc in bank.accounts
                    if acc.account_number == account_number
                    and acc.customer_id == session['customer_id']), None)
    if not account:
        return jsonify({"success": False, "error": "Account not found"}), 404

    customer = next((c for c in bank.customers if c.customer_id == session['customer_id']), None)

    try:
        if account.balance > 0:
            return jsonify({"success": False, "error": f"Please withdraw remaining balance of ₹{account.balance:,.2f} before closing."}), 400

        # Check for active loans
        loans = bank.get_loans_for_customer(customer.customer_id)
        active_loans = [l for l in loans if l.status == 'Active']
        if active_loans:
            return jsonify({"success": False, "error": "Cannot close account with active loans."}), 400

        account.status = 'Closed'
        bank.save()
        return jsonify({"success": True, "message": "Account closed successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/transactions/search')
@login_required
def search_transactions():
    """Search transactions by ID across all customer accounts"""
    txn_id = request.args.get('id', '').strip()
    if not txn_id:
        return jsonify({"found": False, "error": "No transaction ID provided"}), 400

    customer_id = session['customer_id']
    for account in bank.accounts:
        if account.customer_id != customer_id:
            continue
        for txn in getattr(account, 'transactions', []):
            if str(getattr(txn, 'id', '') or getattr(txn, 'transaction_id', '')).lower() == txn_id.lower():
                return jsonify({
                    "found": True,
                    "transaction": {
                        "id": str(getattr(txn, 'id', '') or getattr(txn, 'transaction_id', '')),
                        "account": account.account_number,
                        "type": str(getattr(txn, 'type', '')).replace('TransactionType.', ''),
                        "amount": getattr(txn, 'amount', 0),
                        "direction": getattr(txn, 'direction', ''),
                        "date": str(getattr(txn, 'date', '') or getattr(txn, 'timestamp', '')),
                        "description": str(getattr(txn, 'description', ''))
                    }
                })
    return jsonify({"found": False, "error": "Transaction not found"})


# ========== CHEQUE SYSTEM ENDPOINTS ==========

@app.route('/api/accounts/<account_number>/cheques')
@login_required
def get_cheques(account_number):
    """Get cheque books and cheques for an account"""
    customer_id = session.get('customer_id')
    account = next((acc for acc in bank.accounts if acc.account_number == account_number), None)
    
    if not account or account.customer_id != customer_id:
        return jsonify({"error": "Account not found or access denied"}), 404
        
    manager = account.cheque_book_manager
    books = [book.to_dict() for book in manager.get_all_cheque_books()]
    
    return jsonify({
        "account_number": account_number,
        "cheque_books": books
    })

@app.route('/api/accounts/<account_number>/cheque-book', methods=['POST'])
@login_required
def request_cheque_book(account_number):
    """Issue a new cheque book for an account"""
    customer_id = session.get('customer_id')
    account = next((acc for acc in bank.accounts if acc.account_number == account_number), None)
    
    if not account or account.customer_id != customer_id:
        return jsonify({"error": "Account not found or access denied"}), 404
        
    new_book = account.cheque_book_manager.create_and_issue_cheque_book()
    bank.save()
    
    return jsonify({
        "success": True,
        "message": "New cheque book of 50 leaves issued successfully!",
        "cheque_book_id": new_book.cheque_book_id
    })

@app.route('/api/accounts/<account_number>/issue-cheque', methods=['POST'])
@login_required
def issue_cheque(account_number):
    """Update a blank cheque with payee details (writing the cheque)"""
    customer_id = session.get('customer_id')
    account = next((acc for acc in bank.accounts if acc.account_number == account_number), None)
    
    if not account or account.customer_id != customer_id:
        return jsonify({"error": "Account not found or access denied"}), 404
        
    data = request.get_json()
    cheque_number = data.get('cheque_number')
    amount = float(data.get('amount', 0))
    payee_name = data.get('payee_name')
    date_presentable = data.get('date_presentable', datetime.now().strftime("%Y-%m-%d"))
    
    cheque = account.cheque_book_manager.get_cheque_by_number(cheque_number)
    if not cheque:
        return jsonify({"error": "Cheque number not found in your issued books"}), 404
        
    if cheque.status != ChequeStatus.ISSUED:
        return jsonify({"error": f"Cheque is no longer available. Status: {cheque.status.value}"}), 400
        
    # Standard check: amount must be positive
    if amount <= 0:
        return jsonify({"error": "Cheque amount must be greater than zero"}), 400

    # Fill metadata and amount
    cheque.amount = amount
    cheque.payee_name = payee_name
    cheque.date_presentable = date_presentable
    
    bank.save()
    
    return jsonify({
        "success": True,
        "message": f"Cheque {cheque_number} successfully issued to {payee_name}."
    })

@app.route('/api/cheque/deposit', methods=['POST'])
@login_required
def deposit_cheque():
    """Deposit a cheque into an account (Simulation of Clearing)"""
    customer_id = session.get('customer_id')
    data = request.get_json()
    
    cheque_number = data.get('cheque_number')
    micr = data.get('micr')
    deposit_to_acc_num = data.get('account_number')
    
    # 1. Verify depositing account ownership
    deposit_account = next((acc for acc in bank.accounts if acc.account_number == deposit_to_acc_num), None)
    if not deposit_account or deposit_account.customer_id != customer_id:
        return jsonify({"error": "Target deposit account not found or access denied"}), 404
        
    # 2. Find the issuing account by searching all accounts' cheque managers
    issuing_account = None
    cheque = None
    
    for acc in bank.accounts:
        c = acc.cheque_book_manager.get_cheque_by_number(cheque_number)
        if c and c.micr_code == micr:
            issuing_account = acc
            cheque = c
            break
            
    if not cheque:
        return jsonify({"error": "Cheque details/MICR combination not found in system"}), 404
        
    # 3. Check cheque status and readiness
    if cheque.status != ChequeStatus.ISSUED:
        return jsonify({"error": f"Cheque cannot be cleared. Status: {cheque.status.value}"}), 400
        
    if cheque.amount <= 0:
        return jsonify({"error": "This is a blank cheque. The issuer must fill it before deposit."}), 400
        
    if not cheque.is_presentable():
        return jsonify({"error": f"Cheque cannot be presented until {cheque.date_presentable}"}), 400

    # 4. Process Funds
    if issuing_account.balance < cheque.amount:
        # BOUNCE LOGIC
        bounce_fee = fee_manager.get_fee("cheque_bounce_fee", 500.0)
        cheque.mark_bounced("Insufficient Funds", bounce_fee)
        issuing_account.balance -= bounce_fee
        
        # Log to activity (DataStore is handled by account's to_dict during bank.save)
        # But we also add standard transactions
        from backend.Transaction import Transaction as Txn
        bounce_txn = Txn(type="CHEQUE_BOUNCE", amount=-bounce_fee, resulting_balance=issuing_account.balance, cheque_id=cheque.cheque_id)
        issuing_account.transactions.append(bounce_txn)
        
        bank.save()
        return jsonify({
            "success": False, 
            "error": "CHEQUE BOUNCED: Insufficient funds in issuing account. ₹500 bounce fee charged to issuer."
        }), 400

    # 5. CLEARANCE SUCCESS
    issuing_account.balance -= cheque.amount
    deposit_account.balance += cheque.amount
    cheque.mark_cleared()
    
    from backend.Transaction import Transaction as Txn
    
    # Issuer Debit
    issuer_txn = Txn(
        type="CHEQUE_CLEARED", 
        amount=-cheque.amount, 
        resulting_balance=issuing_account.balance, 
        cheque_id=cheque.cheque_id,
        merchant=cheque.payee_name
    )
    issuing_account.transactions.append(issuer_txn)
    
    # Depositor Credit
    depositor_txn = Txn(
        type="CHEQUE_DEPOSITED", 
        amount=cheque.amount, 
        resulting_balance=deposit_account.balance, 
        cheque_id=cheque.cheque_id,
        merchant=f"From {issuing_account.account_number}"
    )
    deposit_account.transactions.append(depositor_txn)
    
    bank.save()
    
    return jsonify({
        "success": True,
        "message": f"Cheque {cheque_number} cleared! ₹{cheque.amount:,.2f} has been credited to your account."
    })


@app.route('/api/admin/stats')
@admin_required
def get_admin_stats():
    """Get live bank-wide analytics for the admin dashboard"""
    analytics = AdminAnalytics(bank)
    
    overview = analytics.get_bank_overview()
    revenue = analytics.get_revenue_analytics()
    loans = analytics.get_loan_portfolio()
    cards = analytics.get_credit_card_analysis()
    deposits = analytics.get_deposit_portfolio()
    risk = analytics.get_risk_management()
    
    # Calculate Total Fee Revenue from the breakdown
    total_fees = (
        revenue['amb_fees'] + 
        revenue['swift_charges'] + 
        revenue['loan_penalties'] + 
        revenue['rd_penalties'] + 
        revenue['rd_late_penalties'] +
        revenue.get('cheque_bounce_revenue', 0)
    )
    
    return jsonify({
        "summary": {
            "totalCustomers": overview['total_customers'],
            "totalAccounts": overview['total_accounts'],
            "totalDeposits": overview['total_deposits'],
            "totalLoans": overview['total_loans'],
            "totalFees": total_fees,
            "riskScore": risk['risk_score']
        },
        "revenue": revenue,
        "loans": loans,
        "cards": cards,
        "deposits": deposits,
        "risk": risk
    })

@app.route('/api/admin/fees', methods=['GET', 'POST'])
@admin_required
def manage_fees():
    """Get or update bank-wide fee configuration"""
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            fee_manager.update_fee(key, value)
        return jsonify({"success": True, "message": "Fees updated successfully", "fees": fee_manager.fees})
    
    return jsonify(fee_manager.fees)

@app.route('/api/admin/audit-log')
@admin_required
def get_audit_log():
    """Fetch the system audit log from account_activity.csv"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    search = request.args.get('search', '').lower()
    
    activity_file = "backend/data/account_activity.csv"
    if not os.path.exists(activity_file):
        return jsonify([])
        
    audit_data = []
    import csv
    with open(activity_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Reverse to get latest logs first
        all_rows = list(reader)[::-1]
        
        if search:
            all_rows = [r for r in all_rows if search in str(r).lower()]
            
        # Pagination
        paginated = all_rows[offset:offset+limit]
        audit_data = paginated
        
    return jsonify({
        "logs": audit_data,
        "total": len(all_rows)
    })


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        # Handle both JSON (from React) and form data (from HTML forms)
        if request.is_json:
            data = request.get_json()
            pin = data.get('pin', '').strip()
        else:
            pin = request.form.get('pin', '').strip()
        
        if pin == '1234':  # Default admin PIN
            session['is_admin'] = True
            session['customer_id'] = 'ADMIN'
            session.permanent = True
            
            if request.is_json:
                return jsonify({"success": True, "message": "Admin access granted!"})
            else:
                flash('Admin access granted!', 'success')
                return redirect(url_for('admin_dashboard'))
        else:
            error_msg = 'Invalid PIN.'
            if request.is_json:
                return jsonify({"success": False, "error": error_msg}), 401
            else:
                flash(error_msg, 'danger')
    
    return render_template('admin_login.html')


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard - comprehensive analytics"""
    analytics = AdminAnalytics(bank)
    
    overview = analytics.get_bank_overview()
    revenue = analytics.get_revenue_analytics()
    loans_data = analytics.get_loan_portfolio()
    cards_data = analytics.get_credit_card_analysis()
    deposits_data = analytics.get_deposit_portfolio()
    transactions = analytics.get_transaction_insights()
    risk = analytics.get_risk_management()
    customers = analytics.get_customer_metrics()
    
    return render_template('admin_dashboard.html',
                         overview=overview,
                         revenue=revenue,
                         loans=loans_data,
                         cards=cards_data,
                         deposits=deposits_data,
                         transactions=transactions,
                         risk=risk,
                         customers=customers)


@app.route('/admin/customers')
@admin_required
def admin_customers():
    """View all customers"""
    return render_template('admin_customers.html', customers=bank.customers)


@app.route('/admin/accounts')
@admin_required
def admin_accounts():
    """View all accounts"""
    return render_template('admin_accounts.html', accounts=bank.accounts)


@app.route('/admin/loans')
@admin_required
def admin_loans():
    """View all loans"""
    return render_template('admin_loans.html', loans=bank.loans)


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500


# ========== SIMULATION CLOCK ENDPOINTS ==========

@app.route('/api/simulation/clock', methods=['GET'])
@login_required
def get_clock_status():
    """Get current clock status (BankClock)"""
    try:
        from backend.BankClock import BankClock
        return jsonify({
            "currentTime": BankClock.get_formatted_datetime(),
            "currentDate": BankClock.get_formatted_date(),
            "mode": BankClock.get_mode(),
            "compact": BankClock.get_compact_display()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/simulation/advance', methods=['POST'])
@login_required
def advance_clock():
    """Advance the clock (Virtual mode only)"""
    data = request.get_json()
    days = int(data.get('days', 0))
    months = int(data.get('months', 0))
    
    try:
        from backend.BankClock import BankClock
        if BankClock.get_mode() == "REAL":
            return jsonify({"success": False, "error": "Switch to VIRTUAL mode to advance time."}), 400
        
        total_days = days + (months * 30)
        if total_days <= 0:
            return jsonify({"success": False, "error": "Advancement must be positive."}), 400
            
        BankClock.advance_days(total_days)
        
        # Simulation Logic: Check for recurring events
        # In a real app, this would trigger background workers
        # For this sim, we'll manually trigger some checks
        for account in bank.accounts:
            # Trigger RD payments, EMI, interest checks if applicable
            # (In the CLI, these are often checked on login or menu access)
            pass
            
        bank.save()
        return jsonify({
            "success": True, 
            "message": f"Clock advanced by {total_days} days.",
            "currentTime": BankClock.get_formatted_datetime()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/simulation/mode', methods=['POST'])
@login_required
def toggle_clock_mode():
    """Switch between REAL and VIRTUAL mode"""
    data = request.get_json()
    mode = data.get('mode', 'VIRTUAL').upper()
    
    try:
        from backend.BankClock import BankClock
        if mode == "REAL":
            BankClock.switch_to_real_mode()
        else:
            BankClock.switch_to_virtual_mode()
            
        return jsonify({
            "success": True, 
            "mode": BankClock.get_mode(),
            "currentTime": BankClock.get_formatted_datetime()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== ADVANCED TAX ENDPOINTS ==========

@app.route('/api/tax/compare', methods=['GET'])
@login_required
def compare_tax_regimes():
    """Compare savings between OLD and NEW tax regimes"""
    try:
        customer_id = session.get('customer_id')
        account = next((acc for acc in bank.accounts if acc.customer_id == customer_id), None)
        if not account or not account.salary_profile:
            return jsonify({"error": "No salary profile found."}), 400

        from backend.TaxCalculator import TaxCalculator
        gross_salary = account.salary_profile.gross_salary * 12
        
        # Mocking deductions since they are tied to sections like 80C etc.
        # In a real implementation we'd sum up the actual claimed items
        deductions_total = 0
        if hasattr(account, 'tax_exemptions'):
            deductions_total = sum(d.claimed_amount for d in account.tax_exemptions.values() if d.status == "Approved")

        old_tax = TaxCalculator.calculate_annual_tax(gross_salary, deductions_total, "OLD_REGIME")
        new_tax = TaxCalculator.calculate_annual_tax(gross_salary, 0, "NEW_REGIME")

        return jsonify({
            "grossIncome": gross_salary,
            "deductions": deductions_total,
            "oldRegime": {
                "tax": old_tax,
                "takeHome": gross_salary - old_tax
            },
            "newRegime": {
                "tax": new_tax,
                "takeHome": gross_salary - new_tax
            },
            "recommendation": "OLD_REGIME" if old_tax < new_tax else "NEW_REGIME"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tax/file-itr', methods=['POST'])
@login_required
def file_itr_simulation():
    """Simulate ITR filing"""
    try:
        # Simple simulation
        data = request.get_json()
        year = data.get('year', '2023-24')
        
        # Log this as a special entry in 'tax history' if it existed
        return jsonify({
            "success": True,
            "message": f"ITR for {year} filed successfully!",
            "ackNumber": f"ITR{__import__('random').randint(1000000, 9999999)}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/loans/<loan_id>/nach', methods=['GET', 'POST'])
@login_required
def manage_loan_nach(loan_id):
    """Manage NACH auto-debit mandate for a loan"""
    try:
        customer_id = session.get('customer_id')
        account = next((acc for acc in bank.accounts if acc.customer_id == customer_id), None)
        if not account:
            return jsonify({"error": "Account not found."}), 404
            
        loan = next((l for l in account.loans if l.loan_id == loan_id), None)
        if not loan:
            return jsonify({"error": "Loan not found."}), 404
            
        if request.method == 'POST':
            data = request.get_json()
            enabled = data.get('enabled', False)
            
            # Simple simulation: add an attribute to the loan object
            # In the real backend, this would affect recurrent billing logic
            loan.nach_enabled = enabled
            bank.save()
            
            return jsonify({
                "success": True,
                "enabled": enabled,
                "message": f"NACH mandate {'enabled' if enabled else 'disabled'} successfully."
            })
        
        return jsonify({
            "loanId": loan_id,
            "nachEnabled": getattr(loan, 'nach_enabled', False),
            "mandateId": f"NACH{loan_id[-6:]}",
            "lastDeduction": getattr(loan, 'last_nach_date', 'None'),
            "status": "Active" if getattr(loan, 'nach_enabled', False) else "Inactive"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= ADMINISTRATIVE APIs =================

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    """Get overall bank stats for admin dashboard"""
    analytics = AdminAnalytics(bank)
    
    # 1. Summary Metrics
    revenue = analytics.get_revenue_analytics()
    risk = analytics.get_risk_management()
    overview = analytics.get_bank_overview()
    loans_data = analytics.get_loan_portfolio()
    
    total_fees = (revenue['amb_fees'] + revenue['swift_charges'] + 
                 revenue['loan_penalties'] + revenue['rd_penalties'] + 
                 revenue['rd_late_penalties'] + revenue['cheque_bounce_revenue'])
    
    summary = {
        "totalFees": total_fees,
        "riskScore": risk['risk_score'],
        "totalDeposits": overview['total_deposits'],
        "totalLoans": overview['total_loans'],
        "totalAccounts": overview['total_accounts'],
        "totalCustomers": overview['total_customers']
    }
    
    # 2. Loan Portfolio
    loans_resp = {
        "active_loans": loans_data['active_loans'],
        "by_type": loans_data['by_type']
    }
    
    # 3. Deposit Composition
    deposits_data = analytics.get_deposit_portfolio()
    deposits_resp = {
        "fd_total": deposits_data['fd_total'],
        "rd_total": deposits_data['rd_total']
    }
    
    return jsonify({
        "summary": summary,
        "loans": loans_resp,
        "deposits": deposits_resp
    })

@app.route('/api/admin/fees', methods=['GET', 'POST'])
def admin_fees():
    """Get or update bank fee configuration"""
    if request.method == 'POST':
        data = request.get_json()
        for key, value in data.items():
            fee_manager.update_fee(key, value)
        return jsonify({"success": True, "message": "Fees updated successfully"})
    
    return jsonify(fee_manager.fees)

@app.route('/api/admin/audit-log')
def admin_audit_log():
    """Get system audit log with search and pagination"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    search = request.args.get('search', '').lower()
    
    activity_file = "backend/data/account_activity.csv"
    if not os.path.exists(activity_file):
        return jsonify({"logs": [], "total": 0})
    
    logs = []
    try:
        with open(activity_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Search filter
                if search:
                    row_str = " ".join(row.values()).lower()
                    if search not in row_str:
                        continue
                logs.append(row)
        
        # Newest first
        logs.reverse()
        
        total = len(logs)
        paginated_logs = logs[offset : offset + limit]
        
        return jsonify({
            "logs": paginated_logs,
            "total": total
        })
    except Exception as e:
        return jsonify({"error": str(e), "logs": [], "total": 0}), 500

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true', host='127.0.0.1', port=5000)
