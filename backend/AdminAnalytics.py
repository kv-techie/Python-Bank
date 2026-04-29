from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from .Bank import Bank
from .Transaction import TransactionType
from .FeeManager import fee_manager


class AdminAnalytics:
    """Data aggregation and analytics engine for admin dashboard"""
    
    def __init__(self, bank: Bank):
        self.bank = bank
    
    def get_bank_overview(self) -> Dict:
        """Get overall bank statistics"""
        total_deposits = sum(acc.balance for acc in self.bank.accounts)
        total_loans = sum(loan.get_remaining_balance() for loan in self.bank.loans if loan.status == "Active")
        
        # Account type distribution
        account_type_distribution = {}
        for account in self.bank.accounts:
            acc_type = account.account_type
            account_type_distribution[acc_type] = account_type_distribution.get(acc_type, 0) + 1
        
        # Account status
        account_status = {}
        for account in self.bank.accounts:
            status = "Locked" if getattr(account, 'locked', False) else "Active"
            account_status[status] = account_status.get(status, 0) + 1
        
        return {
            'total_customers': len(self.bank.customers),
            'total_accounts': len(self.bank.accounts),
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'net_assets': total_deposits - total_loans,
            'account_type_distribution': account_type_distribution,
            'account_status': account_status
        }
    
    def get_revenue_analytics(self) -> Dict:
        """Analyze all fee and interest revenue"""
        # Calculate AMB fees (Using dynamic fee from manager)
        amb_fee_unit = fee_manager.get_fee('amb_fee', 300.0)
        min_bal_threshold = fee_manager.get_fee('min_balance_threshold', 10000.0)
        
        amb_fees = 0
        for account in self.bank.accounts:
            if account.balance < min_bal_threshold:
                amb_fees += amb_fee_unit
        
        # SWIFT charges (Using dynamic charges from manager)
        swift_base = fee_manager.get_fee('swift_base_charge', 500.0)
        swift_step = fee_manager.get_fee('swift_step_charge', 1000.0)
        
        swift_charges = 0
        for account in self.bank.accounts:
            for txn in account.transactions:
                if hasattr(txn, 'type') and txn.type == TransactionType.INTERNATIONAL_TRANSFER:
                    if hasattr(txn, 'amount'):
                        if txn.amount < 50000:
                            swift_charges += swift_base
                        elif txn.amount < 100000:
                            swift_charges += swift_base + swift_step
                        elif txn.amount < 500000:
                            swift_charges += swift_base + (swift_step * 2)
                        else:
                            swift_charges += swift_base + (swift_step * 5)
        
        # Loan prepayment penalties
        loan_penalties = 0
        for loan in self.bank.loans:
            if hasattr(loan, 'prepayment_penalty_charged'):
                loan_penalties += loan.prepayment_penalty_charged
        
        # RD penalties
        rd_penalties = 0
        rd_late_penalties = 0
        if hasattr(self.bank, 'recurring_deposits'):
            for rd in self.bank.recurring_deposits.values():
                if hasattr(rd, 'early_withdrawal_penalty'):
                    rd_penalties += getattr(rd, 'early_withdrawal_penalty', 0.0)
                if hasattr(rd, 'late_payment_penalties'):
                    rd_late_penalties += getattr(rd, 'late_payment_penalties', 0.0)

        # Cheque Bounce Revenue (NEW SECTION)
        bounce_fee_unit = fee_manager.get_fee("cheque_bounce_fee", 500.0)
        cheque_bounce_revenue = 0
        for account in self.bank.accounts:
            for txn in account.transactions:
                if getattr(txn, 'type', '') == "CHEQUE_BOUNCE":
                    cheque_bounce_revenue += bounce_fee_unit

        # Interest revenue/expense
        loan_interest = 0
        deposit_interest = 0
        
        for loan in self.bank.loans:
            if hasattr(loan, 'interest_paid'):
                loan_interest += loan.interest_paid
        
        if hasattr(self.bank, 'fixed_deposits'):
            for fd in self.bank.fixed_deposits.values():
                if hasattr(fd, 'interest_earned'):
                    deposit_interest += getattr(fd, 'interest_earned', 0.0)
        if hasattr(self.bank, 'recurring_deposits'):
            for rd in self.bank.recurring_deposits.values():
                if hasattr(rd, 'interest_earned'):
                    deposit_interest += getattr(rd, 'interest_earned', 0.0)
        
        return {
            'amb_fees': amb_fees,
            'swift_charges': swift_charges,
            'loan_penalties': loan_penalties,
            'rd_penalties': rd_penalties,
            'rd_late_penalties': rd_late_penalties,
            'cheque_bounce_revenue': cheque_bounce_revenue,
            'loan_interest': loan_interest,
            'deposit_interest': deposit_interest
        }
    
    def get_loan_portfolio(self) -> Dict:
        """Analyze loan portfolio"""
        total_outstanding = 0
        active_count = 0
        closed_count = 0
        overdue_count = 0
        high_default_risk = 0
        
        by_type = {}
        
        for loan in self.bank.loans:
            if loan.status == "Active":
                active_count += 1
                total_outstanding += loan.get_remaining_balance()
                
                # Check for overdue
                if hasattr(loan, 'next_emi_date') and loan.next_emi_date < datetime.now().date():
                    overdue_count += 1
                
                # Simple default risk: outstanding > 75% of original amount
                if loan.get_remaining_balance() > (loan.principal * 0.75):
                    high_default_risk += 1
            else:
                closed_count += 1
            
            # Breakdown by type
            loan_type = loan.loan_type
            if loan_type not in by_type:
                by_type[loan_type] = {'count': 0, 'outstanding': 0.0, 'total_amount': 0.0}
            
            by_type[loan_type]['count'] += 1
            if loan.status == "Active":
                by_type[loan_type]['outstanding'] += loan.get_remaining_balance()
            by_type[loan_type]['total_amount'] += loan.principal
        
        # Calculate averages
        for loan_type in by_type:
            if by_type[loan_type]['count'] > 0:
                by_type[loan_type]['avg_amount'] = by_type[loan_type]['total_amount'] / by_type[loan_type]['count']
            else:
                by_type[loan_type]['avg_amount'] = 0.0
        
        return {
            'total_loans': len(self.bank.loans),
            'active_loans': active_count,
            'closed_loans': closed_count,
            'total_outstanding': total_outstanding,
            'overdue_loans': overdue_count,
            'high_default_risk': high_default_risk,
            'by_type': by_type
        }
    
    def get_credit_card_analysis(self) -> Dict:
        """Analyze credit card portfolio"""
        total_cards = 0
        active_cards = 0
        blocked_cards = 0
        total_limit = 0.0
        total_outstanding = 0.0
        high_utilization_count = 0
        default_count = 0
        
        auto_pay_distribution = {'NONE': 0, 'MINIMUM': 0, 'FULL': 0}
        cibil_distribution = {'Poor': 0, 'Fair': 0, 'Good': 0, 'Excellent': 0}
        
        for account in self.bank.accounts:
            if hasattr(account, 'cards'):
                for card in account.cards:
                    if getattr(card, 'card_type', '') != "CREDIT":
                        continue
                    total_cards += 1
                    
                    if not getattr(card, 'blocked', False) and not card.is_expired():
                        active_cards += 1
                        total_limit += getattr(card, 'credit_limit', 0.0)
                        total_outstanding += getattr(card, 'outstanding_balance', 0.0)
                        
                        # Check utilization
                        c_limit = getattr(card, 'credit_limit', 0.0)
                        utilization = (getattr(card, 'outstanding_balance', 0.0) / c_limit * 100) if c_limit > 0 else 0
                        if utilization > 80:
                            high_utilization_count += 1
                        
                        # Auto-pay policy
                        if hasattr(card, 'auto_pay_policy'):
                            auto_pay_distribution[card.auto_pay_policy] = auto_pay_distribution.get(card.auto_pay_policy, 0) + 1
                    
                    else:
                        blocked_cards += 1
        
        # CIBIL distribution from customers
        for customer in self.bank.customers:
            if hasattr(customer, 'cibil_score'):
                cibil = customer.cibil_score
                if cibil is not None:
                    if cibil < 550:
                        cibil_distribution['Poor'] += 1
                    elif cibil < 650:
                        cibil_distribution['Fair'] += 1
                    elif cibil < 750:
                        cibil_distribution['Good'] += 1
                    else:
                        cibil_distribution['Excellent'] += 1
        
        # Check for defaults
        for account in self.bank.accounts:
            if hasattr(account, 'cards'):
                for card in account.cards:
                    if getattr(card, 'card_type', '') != "CREDIT":
                        continue
                    if hasattr(card, 'default_status') and card.default_status:
                        default_count += 1
        
        avg_utilization = 0.0
        if total_cards > 0:
            avg_utilization = (total_outstanding / total_limit * 100) if total_limit > 0 else 0.0
        
        return {
            'total_cards': total_cards,
            'active_cards': active_cards,
            'blocked_cards': blocked_cards,
            'total_limit': total_limit,
            'total_outstanding': total_outstanding,
            'avg_utilization': avg_utilization,
            'high_utilization_count': high_utilization_count,
            'default_count': default_count,
            'auto_pay_distribution': auto_pay_distribution,
            'cibil_distribution': cibil_distribution
        }
    
    def get_deposit_portfolio(self) -> Dict:
        """Analyze FD and RD portfolio"""
        fd_count = 0
        fd_total = 0.0
        rd_count = 0
        rd_total = 0.0
        rd_active = 0
        rd_completed = 0
        fd_interest_paid = 0.0
        rd_interest_paid = 0.0
        
        upcoming_maturities = {'This Month': 0, 'Next Month': 0, '<3 Months': 0, '>3 Months': 0}
        
        today = datetime.now().date()
        
        if hasattr(self.bank, 'fixed_deposits'):
            for fd in self.bank.fixed_deposits.values():
                fd_count += 1
                fd_total += getattr(fd, 'principal_amount', 0.0)
                
                if hasattr(fd, 'interest_earned'):
                    fd_interest_paid += getattr(fd, 'interest_earned', 0.0)
                
                # Check maturity
                if hasattr(fd, 'maturity_date') and getattr(fd, 'maturity_date'):
                    mat_date = fd.maturity_date.date() if isinstance(fd.maturity_date, datetime) else fd.maturity_date
                    if isinstance(mat_date, str):
                        try:
                            from datetime import date
                            mat_date = date.fromisoformat(mat_date[:10])
                        except Exception as e:
                            continue
                    if not isinstance(mat_date, str):
                        days_to_maturity = (mat_date - today).days
                        if 0 <= days_to_maturity <= 30:
                            upcoming_maturities['This Month'] += 1
                        elif 30 < days_to_maturity <= 60:
                            upcoming_maturities['Next Month'] += 1
                        elif 60 < days_to_maturity <= 90:
                            upcoming_maturities['<3 Months'] += 1
                        else:
                            upcoming_maturities['>3 Months'] += 1
        
        if hasattr(self.bank, 'recurring_deposits'):
            for rd in self.bank.recurring_deposits.values():
                rd_count += 1
                if hasattr(rd, 'monthly_amount'):
                    rd_total += getattr(rd, 'monthly_amount', 0.0)
                
                if hasattr(rd, 'status'):
                    if rd.status == "Active":
                        rd_active += 1
                    else:
                        rd_completed += 1
                
                if hasattr(rd, 'interest_earned'):
                    rd_interest_paid += getattr(rd, 'interest_earned', 0.0)
                
                # Check maturity
                if hasattr(rd, 'maturity_date') and getattr(rd, 'maturity_date'):
                    mat_date = rd.maturity_date.date() if isinstance(rd.maturity_date, datetime) else rd.maturity_date
                    if isinstance(mat_date, str):
                        try:
                            from datetime import date
                            mat_date = date.fromisoformat(mat_date[:10])
                        except Exception as e:
                            continue
                    if not isinstance(mat_date, str):
                        days_to_maturity = (mat_date - today).days
                        if 0 <= days_to_maturity <= 30:
                            upcoming_maturities['This Month'] += 1
                        elif days_to_maturity > 0:
                            upcoming_maturities['Next Month'] += 1
        
        fd_avg = fd_total / fd_count if fd_count > 0 else 0.0
        
        return {
            'fd_count': fd_count,
            'fd_total': fd_total,
            'fd_avg': fd_avg,
            'fd_interest_paid': fd_interest_paid,
            'rd_count': rd_count,
            'rd_total': rd_total,
            'rd_active': rd_active,
            'rd_completed': rd_completed,
            'rd_interest_paid': rd_interest_paid,
            'total_interest_expense': fd_interest_paid + rd_interest_paid,
            'upcoming_maturities': upcoming_maturities
        }
    
    def get_transaction_insights(self) -> Dict:
        """Analyze transaction patterns"""
        total_transactions = 0
        total_volume = 0.0
        total_credits = 0.0
        total_debits = 0.0
        credit_count = 0
        debit_count = 0
        
        transaction_types = {}
        
        for account in self.bank.accounts:
            for txn in account.transactions:
                total_transactions += 1
                
                if hasattr(txn, 'amount'):
                    total_volume += txn.amount
                
                # Track by type
                txn_type = str(txn.type) if hasattr(txn, 'type') else "Unknown"
                transaction_types[txn_type] = transaction_types.get(txn_type, 0) + 1
                
                # Credit vs Debit
                if hasattr(txn, 'is_credit') and txn.is_credit():
                    total_credits += getattr(txn, 'amount', 0.0)
                    credit_count += 1
                elif hasattr(txn, 'is_debit') and txn.is_debit():
                    total_debits += getattr(txn, 'amount', 0.0)
                    debit_count += 1
        
        # Top transaction types
        top_types = sorted(transaction_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate averages
        avg_per_day = total_transactions / 365 if total_transactions > 0 else 0.0
        avg_amount = total_volume / total_transactions if total_transactions > 0 else 0.0
        
        return {
            'total_transactions': total_transactions,
            'total_volume': total_volume,
            'total_credits': total_credits,
            'total_debits': total_debits,
            'credit_count': credit_count,
            'debit_count': debit_count,
            'top_types': top_types,
            'avg_per_day': avg_per_day,
            'avg_amount': avg_amount
        }
    
    def get_risk_management(self) -> Dict:
        """Analyze risk metrics"""
        low_balance_accounts = 0
        overdraft_accounts = 0
        negative_balance_accounts = 0
        overdue_loans = 0
        high_default_risk = 0
        overdue_amount = 0.0
        overdue_credit_accounts = 0
        overdue_credit_amount = 0.0
        high_utilization_cards = 0
        overdue_rd_payments = 0
        
        active_loans = 0
        
        # Check accounts
        for account in self.bank.accounts:
            min_bal = account.get_amb_requirement()
            
            if account.balance < min_bal and account.balance >= 0:
                low_balance_accounts += 1
            elif account.balance < 0:
                negative_balance_accounts += 1
                overdraft_accounts += 1
        
        # Check loans
        for loan in self.bank.loans:
            if loan.status == "Active":
                active_loans += 1
                
                # Check overdue
                if hasattr(loan, 'next_emi_date') and loan.next_emi_date < datetime.now().date():
                    overdue_loans += 1
                    overdue_amount += loan.get_remaining_balance()
                
                # Check default risk
                if loan.get_remaining_balance() > (loan.principal * 0.75):
                    high_default_risk += 1
        
        # Check credit cards
        for account in self.bank.accounts:
            if hasattr(account, 'cards'):
                for card in account.cards:
                    if getattr(card, 'card_type', '') != "CREDIT":
                        continue
                    if getattr(card, 'outstanding_balance', 0.0) > 0:
                        c_limit = getattr(card, 'credit_limit', 0.0)
                        utilization = (card.outstanding_balance / c_limit * 100) if c_limit > 0 else 0
                        if utilization > 80:
                            high_utilization_cards += 1
                        
                        # Check if overdue
                        if hasattr(card, 'due_date') and getattr(card, 'due_date') and card.due_date < datetime.now().date():
                            overdue_credit_accounts += 1
                            overdue_credit_amount += card.outstanding_balance
        
        # Check RD overdue payments
        if hasattr(self.bank, 'recurring_deposits'):
            for rd in self.bank.recurring_deposits.values():
                if hasattr(rd, 'next_payment_date') and getattr(rd, 'next_payment_date') and rd.next_payment_date < datetime.now().date():
                    overdue_rd_payments += 1
        
        # Calculate risk score (0-100)
        risk_factors = (
            low_balance_accounts * 2 +
            overdraft_accounts * 10 +
            negative_balance_accounts * 15 +
            overdue_loans * 20 +
            high_default_risk * 15 +
            overdue_credit_accounts * 10 +
            overdue_rd_payments * 5
        )
        
        risk_score = min(100, risk_factors // max(1, len(self.bank.accounts)))
        
        return {
            'low_balance_accounts': low_balance_accounts,
            'overdraft_accounts': overdraft_accounts,
            'negative_balance_accounts': negative_balance_accounts,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'high_default_risk': high_default_risk,
            'overdue_amount': overdue_amount,
            'overdue_credit_accounts': overdue_credit_accounts,
            'overdue_credit_amount': overdue_credit_amount,
            'high_utilization_cards': high_utilization_cards,
            'overdue_rd_payments': overdue_rd_payments,
            'risk_score': risk_score
        }
    
    def get_customer_metrics(self) -> Dict:
        """Analyze customer base"""
        total_customers = len(self.bank.customers)
        active_customers = 0
        inactive_customers = 0
        
        ages = []
        cities = {}
        total_assets = 0.0
        total_accounts = 0
        total_loans = 0
        total_cards = 0
        
        for customer in self.bank.customers:
            from datetime import date
            if hasattr(customer, 'dob') and customer.dob:
                try:
                    dob_date = date.fromisoformat(customer.dob)
                    today = date.today()
                    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                    ages.append(age)
                except ValueError:
                    pass
            
            # City distribution
            if hasattr(customer, 'city') and customer.city:
                cities[customer.city] = cities.get(customer.city, 0) + 1
            
            # Account ownership
            customer_accounts = [acc for acc in self.bank.accounts if getattr(acc, 'customer_id', '') == customer.customer_id]
            customer_loans = [loan for loan in self.bank.loans if getattr(loan, 'customer_id', '') == customer.customer_id]
            customer_cards = []
            for account in customer_accounts:
                if hasattr(account, 'cards'):
                    customer_cards.extend([c for c in account.cards if getattr(c, 'card_type', '') == 'CREDIT'])
            
            total_accounts += len(customer_accounts)
            total_loans += len(customer_loans)
            total_cards += len(customer_cards)
            
            # Asset value
            for account in customer_accounts:
                total_assets += account.balance
            
            # Active/Inactive based on recent transactions
            has_recent_txn = False
            if customer_accounts:
                for account in customer_accounts:
                    if account.transactions:
                        last_txn_date = account.transactions[-1].timestamp.date()
                        if (datetime.now().date() - last_txn_date).days < 30:
                            has_recent_txn = True
                            break
            
            if has_recent_txn or customer_accounts:
                active_customers += 1
            else:
                inactive_customers += 1
        
        # Top cities
        top_cities = dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5])
        
        avg_age = sum(ages) / len(ages) if ages else 0.0
        age_min = min(ages) if ages else 0
        age_max = max(ages) if ages else 0
        avg_accounts = total_accounts / total_customers if total_customers > 0 else 0.0
        avg_loans = total_loans / total_customers if total_customers > 0 else 0.0
        avg_cards = total_cards / total_customers if total_customers > 0 else 0.0
        avg_assets = total_assets / total_customers if total_customers > 0 else 0.0
        
        return {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'inactive_customers': inactive_customers,
            'avg_age': avg_age,
            'age_min': age_min,
            'age_max': age_max,
            'top_cities': top_cities,
            'avg_accounts_per_customer': avg_accounts,
            'avg_loans_per_customer': avg_loans,
            'avg_cards_per_customer': avg_cards,
            'total_assets': total_assets,
            'avg_asset_per_customer': avg_assets
        }
