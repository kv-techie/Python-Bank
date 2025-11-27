class CreditEvaluator:
    """Evaluates and determines credit card limits based on customer profile"""

    @staticmethod
    def calculate_credit_limit(
        cibil_score: float,
        annual_income: float,
        age: int,
        existing_debt: float = 0.0,
        employer_category: str = "pvt",
        has_salary_account: bool = False,
    ) -> float:
        """
        Calculate credit card limit based on CIBIL score, income, and other factors

        Args:
            cibil_score: CIBIL score (300-900)
            annual_income: Annual income in INR
            age: Customer age
            existing_debt: Existing debt obligations (monthly)
            employer_category: "govt", "mnc", or "pvt"
            has_salary_account: Whether customer has salary account with bank

        Returns:
            Approved credit limit in INR
        """
        # Base limit
        base_limit = 10000.0

        # Check minimum eligibility
        if cibil_score < 650:
            return 0.0  # Not eligible

        # Calculate monthly income
        monthly_income = annual_income / 12

        # Base limit calculation: base + 20% of monthly income
        limit = base_limit + (monthly_income * 0.2)

        # CIBIL score adjustment
        if cibil_score < 550:
            limit = base_limit
        elif cibil_score < 650:
            limit *= 0.6
        elif cibil_score < 700:
            limit *= 0.8
        elif cibil_score < 750:
            limit *= 1.0
        elif cibil_score < 800:
            limit *= 1.2
        else:  # 800+
            limit *= 1.5

        # Debt-to-Income (DTI) ratio adjustment
        if monthly_income > 0:
            dti_ratio = existing_debt / monthly_income

            if dti_ratio > 0.5:  # More than 50% DTI
                limit *= 0.5
            elif dti_ratio > 0.4:  # 40-50% DTI
                limit *= 0.75
        else:
            limit = base_limit

        # Employer category adjustment
        emp_cat = employer_category.lower()
        if emp_cat == "govt":
            limit *= 1.3  # Government employees get 30% higher limit
        elif emp_cat == "mnc":
            limit *= 1.25  # MNC employees get 15% higher limit
        # Private sector gets no additional multiplier

        # Salary account bonus
        if has_salary_account:
            limit *= 1.2  # 20% bonus for existing salary account

        # Age-based adjustment
        if age < 25:
            limit *= 0.9  # Young adults get lower limit
        elif age > 60:
            limit *= 0.8  # Senior citizens get slightly lower limit
        # Age 25-60 gets no reduction

        # Apply RBI maximum limit
        RBI_MAX_LIMIT = 500000.0
        limit = min(limit, RBI_MAX_LIMIT)

        # Round to nearest 100
        limit = round(limit / 100) * 100

        # Ensure minimum base limit
        return max(limit, base_limit)

    @staticmethod
    def is_eligible_for_credit_card(
        cibil_score: float, annual_income: float, age: int
    ) -> tuple[bool, str]:
        """
        Check if customer is eligible for credit card

        Args:
            cibil_score: CIBIL score (300-900)
            annual_income: Annual income in INR
            age: Customer age

        Returns:
            (eligible, reason_message)
        """
        if age < 18:
            return False, "Must be 18 years or older"

        if age > 70:
            return False, "Maximum age limit is 70 years"

        if cibil_score < 650:
            return (
                False,
                f"CIBIL score too low ({cibil_score:.0f}). Minimum required: 650",
            )

        if annual_income < 180000:  # Rs. 15,000 per month
            return (
                False,
                f"Annual income too low (Rs. {annual_income:,.0f}). Minimum required: Rs. 1,80,000",
            )

        return True, "Eligible for credit card"

    @staticmethod
    def assign_credit_card_limit_from_customer(customer, bank) -> float:
        """
        Calculate credit card limit using customer and bank objects
        (Alternative method that works with your existing Customer/Bank classes)

        Args:
            customer: Customer object with attributes like salary, cibil_score, etc.
            bank: Bank object to fetch loans and credit cards

        Returns:
            Approved credit limit in INR
        """
        # Get customer details
        salary = getattr(customer, "salary", 30000.0)
        cibil = getattr(customer, "cibil_score", 650.0)
        age = customer.calculate_age() if hasattr(customer, "calculate_age") else 30
        employer_category = getattr(customer, "employer_category", "pvt")
        has_salary_account = getattr(customer, "has_salary_account", False)

        # Calculate existing debt obligations
        existing_debt = 0.0

        # Get existing loans
        if hasattr(bank, "get_loans_for_customer"):
            loans = bank.get_loans_for_customer(customer.customer_id)
            existing_emis = sum(
                loan.calculate_emi()
                for loan in loans
                if getattr(loan, "status", "Active") == "Active"
            )
            existing_debt += existing_emis

        # Get existing credit cards
        if hasattr(bank, "get_credit_cards_for_customer"):
            credit_cards = bank.get_credit_cards_for_customer(customer.customer_id)
            existing_min_due = sum(
                cc.credit_used * 0.05 for cc in credit_cards
            )  # 5% minimum due
            existing_debt += existing_min_due

        # Use the main calculation method
        return CreditEvaluator.calculate_credit_limit(
            cibil_score=cibil,
            annual_income=salary * 12,
            age=age,
            existing_debt=existing_debt,
            employer_category=employer_category,
            has_salary_account=has_salary_account,
        )


# Example usage and testing
if __name__ == "__main__":
    print("Credit Limit Calculator Test")
    print("=" * 60)

    # Test Case 1: Young professional with good CIBIL
    limit1 = CreditEvaluator.calculate_credit_limit(
        cibil_score=750,
        annual_income=600000,  # Rs. 50,000/month
        age=28,
        existing_debt=5000,
        employer_category="mnc",
        has_salary_account=True,
    )
    print(f"Case 1 - Young MNC employee: Rs. {limit1:,.2f}")

    # Test Case 2: Government employee with excellent CIBIL
    limit2 = CreditEvaluator.calculate_credit_limit(
        cibil_score=820,
        annual_income=900000,  # Rs. 75,000/month
        age=35,
        existing_debt=8000,
        employer_category="govt",
        has_salary_account=True,
    )
    print(f"Case 2 - Govt employee: Rs. {limit2:,.2f}")

    # Test Case 3: Private sector with average CIBIL
    limit3 = CreditEvaluator.calculate_credit_limit(
        cibil_score=680,
        annual_income=360000,  # Rs. 30,000/month
        age=32,
        existing_debt=3000,
        employer_category="pvt",
        has_salary_account=False,
    )
    print(f"Case 3 - Private sector: Rs. {limit3:,.2f}")

    # Test Case 4: Senior citizen
    limit4 = CreditEvaluator.calculate_credit_limit(
        cibil_score=740,
        annual_income=480000,  # Rs. 40,000/month
        age=62,
        existing_debt=2000,
        employer_category="pvt",
        has_salary_account=True,
    )
    print(f"Case 4 - Senior citizen: Rs. {limit4:,.2f}")

    print("\n" + "=" * 60)
    print("Eligibility Test")
    print("=" * 60)

    # Eligibility tests
    eligible1, msg1 = CreditEvaluator.is_eligible_for_credit_card(750, 600000, 28)
    print(f"Test 1: {msg1} - {eligible1}")

    eligible2, msg2 = CreditEvaluator.is_eligible_for_credit_card(620, 600000, 28)
    print(f"Test 2: {msg2} - {eligible2}")

    eligible3, msg3 = CreditEvaluator.is_eligible_for_credit_card(750, 150000, 28)
    print(f"Test 3: {msg3} - {eligible3}")

    eligible4, msg4 = CreditEvaluator.is_eligible_for_credit_card(750, 600000, 17)
    print(f"Test 4: {msg4} - {eligible4}")
