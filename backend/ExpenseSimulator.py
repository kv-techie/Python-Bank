import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple

from .Card import CreditCard
from .DataStore import DataStore
from .Transaction import Transaction


@dataclass
class ExpenseTemplate:
    """Template for generating random expenses"""

    category: str
    min_amount: float
    max_amount: float
    daily_probability: float  # 0.0 to 1.0 (chance of occurrence per day)


class ExpenseSimulator:
    """Simulates realistic daily expenses and financial activities"""

    # Predefined expense templates with realistic ranges and probabilities
    EXPENSE_TEMPLATES = [
        ExpenseTemplate("Groceries", 500, 1500, 0.15),  # 15% (2-3 times weekly)
        ExpenseTemplate("Food & Dining", 100, 400, 0.15),  # 15% (occasional eating out)
        ExpenseTemplate("Transportation", 50, 200, 0.6),  # 60% (daily commute)
        ExpenseTemplate("Shopping", 1000, 3000, 0.05),  # 5% (2 times per month)
        ExpenseTemplate("Healthcare", 500, 2000, 0.03),  # 3% (doctor visits, medicines)
        ExpenseTemplate("Entertainment", 200, 1000, 0.1),  # 10% (weekly entertainment)
        ExpenseTemplate("Education", 1000, 5000, 0.02),  # 2% (monthly - tuition/books)
        ExpenseTemplate("Personal Care", 200, 800, 0.05),  # 5% (biweekly - soaps, etc)
        ExpenseTemplate(
            "Utilities", 2000, 4000, 0.05
        ),  # 5% (monthly - electricity, water, etc)
    ]

    # Directory of realistic merchant names by category
    MERCHANT_DIRECTORY = {
        "Groceries": [
            "Big Bazaar",
            "DMart",
            "Reliance Fresh",
            "Spencer's",
            "More",
            "Star Bazaar",
            "Nilgiris",
            "HyperCity",
        ],
        "Food & Dining": [
            "Swiggy",
            "Zomato",
            "McDonald's",
            "Domino's",
            "Starbucks",
            "KFC",
            "Burger King",
            "Subway",
            "Pizza Hut",
            "Cafe Coffee Day",
        ],
        "Shopping": [
            "Amazon",
            "Flipkart",
            "Myntra",
            "Ajio",
            "Nykaa",
            "Meesho",
            "Shoppers Stop",
            "Westside",
        ],
        "Entertainment": [
            "BookMyShow",
            "PVR Cinemas",
            "INOX",
            "Netflix",
            "Amazon Prime",
            "Spotify",
            "Hotstar",
            "YouTube Premium",
        ],
        "Transportation": [
            "Uber",
            "Ola",
            "Rapido",
            "BMTC",
            "Metro",
            "Petrol Pump",
            "Indian Oil",
            "HP Petrol",
        ],
        "Utilities": [
            "BESCOM",
            "BWSSB",
            "Airtel",
            "Jio",
            "Vodafone",
            "ACT Fibernet",
            "Hathway",
        ],
        "Healthcare": [
            "Apollo Pharmacy",
            "MedPlus",
            "Practo",
            "1mg",
            "Fortis Hospital",
            "Manipal Hospital",
            "Clinic",
        ],
        "Education": [
            "Bookstore",
            "Udemy",
            "Coursera",
            "Khan Academy",
            "Byju's",
            "Unacademy",
            "Tuition Center",
        ],
        "Personal Care": [
            "Salon",
            "Lakme Salon",
            "Green Trends",
            "Spa",
            "Parlour",
            "Grooming Lounge",
        ],
        "Utilities": [
            "BESCOM",
            "BWSSB",
            "Gas Agency",
            "Airtel",
            "Jio",
            "Vodafone",
            "Hathway",
            "ACT Fibernet",
        ],
        "Bills": ["BESCOM", "BWSSB", "Gas Agency", "DTH Provider", "Telecom"],
    }

    # Available payment methods (UPI and Credit Card removed as per requirements)
    PAYMENT_METHODS = ["Debit Card", "Net Banking"]

    @staticmethod
    def process_expense(account, template, amount: float) -> bool:
        """
        Process a single expense - routes to credit card if available, otherwise debit

        Args:
            account: The account to charge
            template: The expense template
            amount: The expense amount

        Returns:
            True if expense processed successfully
        """
        merchant = ExpenseSimulator.get_random_merchant(template.category)
        payment_method = ExpenseSimulator.get_random_payment_method()

        # Get active credit cards (not blocked, not expired)
        active_credit_cards = [
            c
            for c in account.cards
            if isinstance(c, CreditCard) and not c.blocked and not c.is_expired()
        ]

        # 70% chance to use credit card if available, 30% use debit
        use_credit = active_credit_cards and random.random() < 0.7

        if use_credit:
            # Use credit card
            card = random.choice(active_credit_cards)

            # Check if card has sufficient credit
            if card.available_credit() >= amount:
                success, message, txn_id = card.make_purchase(
                    amount, merchant, template.category, account
                )

                if success:
                    DataStore.append_activity(
                        timestamp=date.today(),  # Will be overridden by transaction timestamp
                        username=account.username,
                        account_number=account.account_number,
                        action="EXPENSE",
                        amount=amount,
                        resulting_balance=card.available_credit(),
                        txn_id=txn_id,
                        metadata=f"category={template.category};merchant={merchant};method=CreditCard;card={card.network}****{card.card_number[-4:]}",
                    )
                    return True

        # Fall back to debit (from account balance)
        if account.balance - amount >= 300:  # Maintain minimum operational balance
            account.balance -= amount
            txn = Transaction(
                type="EXPENSE",
                amount=amount,
                resulting_balance=account.balance,
                category=template.category,
                merchant=merchant,
                payment_method=payment_method,
            )
            account.transactions.append(txn)

            DataStore.append_activity(
                timestamp=txn.timestamp,
                username=account.username,
                account_number=account.account_number,
                action="EXPENSE",
                amount=amount,
                resulting_balance=account.balance,
                txn_id=txn.id,
                metadata=f"category={template.category};merchant={merchant};method={payment_method}",
            )
            return True

        return False

    @staticmethod
    def get_random_merchant(category: str) -> str:
        """
        Gets a random merchant name for the given category

        Args:
            category: Expense category

        Returns:
            Random merchant name from that category
        """
        merchants = ExpenseSimulator.MERCHANT_DIRECTORY.get(
            category, ["Generic Merchant"]
        )
        return random.choice(merchants)

    @staticmethod
    def get_random_payment_method() -> str:
        """
        Gets a random payment method

        Returns:
            Random payment method (Debit Card, Net Banking, or Cash)
        """
        return random.choice(ExpenseSimulator.PAYMENT_METHODS)

    @staticmethod
    def generate_daily_expenses() -> List[Tuple[ExpenseTemplate, float]]:
        """
        Generates expenses for a single day based on probability

        Returns:
            List of (ExpenseTemplate, amount) tuples for expenses that occur today
        """
        expenses = []
        for template in ExpenseSimulator.EXPENSE_TEMPLATES:
            if random.random() < template.daily_probability:
                amount = round(
                    template.min_amount
                    + random.random() * (template.max_amount - template.min_amount),
                    2,
                )
                expenses.append((template, amount))
        return expenses

    @staticmethod
    def simulate_day(account, bank, simulated_date: date) -> int:
        """
        Simulates a full day of financial activity for an account
        Processes:
        - Salary credit (if it's salary day)
        - Random daily expenses

        Args:
            account: The account to simulate transactions for
            bank: The bank instance for saving
            simulated_date: The date being simulated

        Returns:
            Number of transactions generated
        """
        transaction_count = 0

        # ========== SALARY PROCESSING ==========
        if account.salary_profile:
            profile = account.salary_profile
            if profile.should_credit_today(simulated_date):
                gross_salary = profile.gross_salary
                tax = profile.calculate_tax()
                net_salary = profile.get_net_salary()

                # Credit net salary to account
                account.balance += net_salary
                salary_txn = Transaction(
                    type="SALARY",
                    amount=net_salary,
                    resulting_balance=account.balance,
                    category="Income",
                    merchant="Employer",
                    payment_method="Bank Transfer",
                )
                account.transactions.append(salary_txn)

                DataStore.append_activity(
                    timestamp=salary_txn.timestamp,
                    username=account.username,
                    account_number=account.account_number,
                    action="SALARY",
                    amount=net_salary,
                    resulting_balance=account.balance,
                    txn_id=salary_txn.id,
                    metadata=f"grossSalary={gross_salary};tax={tax};netSalary={net_salary}",
                )

                # Record tax deduction as separate transaction (for tracking)
                if tax > 0:
                    tax_txn = Transaction(
                        type="TAX_DEDUCTED",
                        amount=tax,
                        resulting_balance=account.balance,
                        category="Tax",
                        merchant="Income Tax Department",
                        payment_method="TDS",
                    )
                    account.transactions.append(tax_txn)

                    DataStore.append_activity(
                        timestamp=tax_txn.timestamp,
                        username=account.username,
                        account_number=account.account_number,
                        action="TAX_DEDUCTED",
                        amount=tax,
                        resulting_balance=account.balance,
                        txn_id=tax_txn.id,
                        metadata=f"taxRate=15%;annualIncome={gross_salary * 12}",
                    )

                    print(
                        f"[MONEY] Salary Credited: ₹{net_salary:.2f} (Gross: ₹{gross_salary:.2f}, Tax: ₹{tax:.2f})"
                    )
                else:
                    print(f"[MONEY] Salary Credited: ₹{net_salary:.2f} (No tax deduction)")

                # Update last salary date
                profile.last_salary_date = simulated_date
                transaction_count += 1

        # ========== RANDOM EXPENSE GENERATION ==========
        expenses = ExpenseSimulator.generate_daily_expenses()
        for template, amount in expenses:
            if ExpenseSimulator.process_expense(account, template, amount):
                transaction_count += 1

        return transaction_count

    @staticmethod
    def simulate_multiple_days(
        account, bank, days: int, start_date: date = None
    ) -> int:
        """
        Simulates multiple days of activity

        Args:
            account: The account to simulate
            bank: The bank instance
            days: Number of days to simulate
            start_date: Starting date for simulation (defaults to today)

        Returns:
            Total number of transactions generated
        """
        if start_date is None:
            start_date = date.today()

        total_transactions = 0
        current_date = start_date

        for day in range(1, days + 1):
            current_date = current_date + timedelta(days=1)

            # Process recurring bills
            bills_processed = account.process_recurring_bills(current_date, bank)

            # Generate daily expenses and salary
            daily_txns = ExpenseSimulator.simulate_day(account, bank, current_date)

            total_transactions += bills_processed + daily_txns

        return total_transactions

    @staticmethod
    def get_category_stats(
        category: str,
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Gets expense statistics for a category

        Args:
            category: The expense category

        Returns:
            Tuple of (minAmount, maxAmount, probability, avgAmount) or None if not found
        """
        for template in ExpenseSimulator.EXPENSE_TEMPLATES:
            if template.category == category:
                avg_amount = (template.min_amount + template.max_amount) / 2
                return (
                    template.min_amount,
                    template.max_amount,
                    template.daily_probability,
                    avg_amount,
                )
        return None

    @staticmethod
    def estimate_monthly_expense(category: str) -> Optional[Tuple[float, float, float]]:
        """
        Estimates monthly expense range for a category

        Args:
            category: The expense category

        Returns:
            Tuple of (minMonthly, maxMonthly, avgMonthly) or None if not found
        """
        stats = ExpenseSimulator.get_category_stats(category)
        if stats:
            min_amt, max_amt, prob, avg_amt = stats
            expected_occurrences = 30 * prob
            min_monthly = min_amt * expected_occurrences * 0.5  # Conservative estimate
            max_monthly = max_amt * expected_occurrences * 1.15  # Liberal estimate
            avg_monthly = avg_amt * expected_occurrences
            return (min_monthly, max_monthly, avg_monthly)
        return None

    @staticmethod
    def get_total_monthly_expense_estimate() -> Tuple[float, float, float]:
        """
        Gets total expected monthly expenses across all categories

        Returns:
            Tuple of (totalMin, totalMax, totalAvg)
        """
        total_min = 0.0
        total_max = 0.0
        total_avg = 0.0

        for template in ExpenseSimulator.EXPENSE_TEMPLATES:
            expected_occurrences = 30 * template.daily_probability
            avg = (template.min_amount + template.max_amount) / 2
            min_monthly = template.min_amount * expected_occurrences * 0.5
            max_monthly = template.max_amount * expected_occurrences * 1.5
            avg_monthly = avg * expected_occurrences

            total_min += min_monthly
            total_max += max_monthly
            total_avg += avg_monthly

        return (total_min, total_max, total_avg)

    @staticmethod
    def show_expense_estimates():
        """Display estimated monthly expenses for all categories"""
        print("\n" + "=" * 70)
        print("MONTHLY EXPENSE ESTIMATES")
        print("=" * 70)
        print(
            f"{'Category':<20} {'Min Monthly':>12} {'Max Monthly':>12} {'Avg Monthly':>12}"
        )
        print("-" * 70)

        for template in ExpenseSimulator.EXPENSE_TEMPLATES:
            estimate = ExpenseSimulator.estimate_monthly_expense(template.category)
            if estimate:
                min_m, max_m, avg_m = estimate
                print(
                    f"{template.category:<20} Rs. {min_m:>9,.2f} Rs. {max_m:>9,.2f} Rs. {avg_m:>9,.2f}"
                )

        total_min, total_max, total_avg = (
            ExpenseSimulator.get_total_monthly_expense_estimate()
        )
        print("-" * 70)
        print(
            f"{'TOTAL':<20} Rs. {total_min:>9,.2f} Rs. {total_max:>9,.2f} Rs. {total_avg:>9,.2f}"
        )
        print("=" * 70)
