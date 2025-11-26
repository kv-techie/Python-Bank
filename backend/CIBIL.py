# CIBIL.py
from datetime import date, timedelta

def calculate_cibil_score(customer, bank):
    """
    Simulate a realistic CIBIL score based on account/loan/repayment data.
    Takes a customer and the bank object (for loans and accounts).
    Returns an int CIBIL-like score (range: 300–900).
    """
    score = 650  # Start with a baseline

    # --- Repayment history: recent EMIs ---
    today = date.today()
    loans = bank.get_loans_for_customer(customer.customer_id)
    late_payments = 0
    clean_history = True
    total_emis = 0
    missed_this_year = 0
    active_deliquency = 0

    for loan in loans:
        emis_paid = getattr(loan, "emis_paid", 0)
        n = loan.tenure_months
        total_emis += n
        # Assume: If loan is overdue, i.e., expected emis > paid, that is late!
        expected_emis = (today.year - loan.start_date.year) * 12 + (today.month - loan.start_date.month) + 1
        expected_emis = min(expected_emis, loan.tenure_months)
        missed = max(0, expected_emis - emis_paid)
        late_payments += missed
        if missed > 0 and (today.year == loan.start_date.year or missed <= 3):
            missed_this_year += missed
        if missed > 0 and loan.status == "Active":
            active_deliquency += 1
        if missed > 0:
            clean_history = False

    if clean_history:
        score += 100
    else:
        score -= 50 * min(4, late_payments) # up to −200

    if active_deliquency > 0:
        score -= 25 * active_deliquency

    # --- Credit utilization ---
    total_limit = 0
    total_used = 0
    if hasattr(customer, "credit_cards"):  # Suppose you add credit_cards info: [{limit, used},...]
        for cc in customer.credit_cards:
            total_limit += cc.get("limit", 0)
            total_used += cc.get("used", 0)
    utilization = (total_used / total_limit * 100) if total_limit else 0
    if total_limit > 0:
        if utilization < 30:
            score += 50
        elif utilization > 75:
            score -= 50

    # --- Number of credit accounts ---
    n_cards = len(getattr(customer, "credit_cards", []))
    n_loans = len(loans)
    total_accounts = n_cards + n_loans
    if total_accounts > 7:
        score -= 20
    elif 2 <= total_accounts <= 5:
        score += 10

    # --- Recent hard inquiries (simulate by recent loan/card attempts) ---
    hard_inquiries = getattr(customer, "recent_hard_inquiries", [])  # Should be a list of date objects
    n_recent = sum(1 for d in hard_inquiries if d > (today - timedelta(days=365)))
    if n_recent > 3:
        score -= 30

    # --- Credit mix/type ---
    account_types = set()
    for loan in loans:
        account_types.add(getattr(loan, "type", "term_loan"))
    if n_cards > 0:
        account_types.add("credit_card")
    if len(account_types) > 1:
        score += 30

    # --- Oldest account ---
    account_dates = []
    for loan in loans:
        account_dates.append(getattr(loan, "start_date", today))
    for cc in getattr(customer, "credit_cards", []):
        account_dates.append(cc.get("opened", today))
    if account_dates:
        oldest = min(account_dates)
        years = (today - oldest).days // 365
        if years >= 3:
            score += 20

    # Clamp between 300 and 900
    score = max(300, min(900, int(round(score))))
    return score

# Optional: helper to add a hard inquiry to a customer record
def add_credit_inquiry(customer):
    if not hasattr(customer, "recent_hard_inquiries"):
        customer.recent_hard_inquiries = []
    customer.recent_hard_inquiries.append(date.today())
