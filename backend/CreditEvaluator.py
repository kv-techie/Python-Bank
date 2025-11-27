def assign_credit_card_limit(customer, bank) -> float:
    base_limit = 10000

    salary = customer.salary if customer.salary else 30000
    cibil = customer.cibil_score if customer.cibil_score else 650
    loans = bank.get_loans_for_customer(customer.customer_id)
    credit_cards = bank.get_credit_cards_for_customer(customer.customer_id)

    existing_emis = sum(
        loan.calculate_emi() for loan in loans if loan.status == "Active"
    )
    existing_min_due = sum(
        cc.credit_used * 0.05 for cc in credit_cards
    )  # Assuming 5% min due

    dti = (existing_emis + existing_min_due) / salary if salary > 0 else 1.0

    limit = base_limit + salary * 0.2

    if cibil < 550:
        limit = base_limit
    elif cibil < 650:
        limit *= 0.6
    elif cibil < 700:
        limit *= 0.8
    else:
        limit *= 1.0

    if dti > 0.5:
        limit *= 0.5
    elif dti > 0.4:
        limit *= 0.75

    emp_cat = (
        customer.employer_category.lower() if customer.employer_category else "pvt"
    )
    if emp_cat == "govt":
        limit *= 1.3
    elif emp_cat == "mnc":
        limit *= 1.15

    if getattr(customer, "has_salary_account", False):
        limit *= 1.2

    age = customer.calculate_age()
    if age < 25:
        limit *= 0.7
    elif age > 60:
        limit *= 0.8

    RBI_MAX_LIMIT = 500000
    limit = min(limit, RBI_MAX_LIMIT)

    # Round to nearest 100
    limit = round(limit / 100) * 100

    return max(limit, base_limit)
