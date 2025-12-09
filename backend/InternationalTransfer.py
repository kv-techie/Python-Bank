import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from Account import Account
from Bank import Bank
from BankClock import BankClock
from DataStore import DataStore
from InternationalBankRegistry import InternationalBankRegistry
from Transaction import Transaction


class InternationalTransfer:
    """Handle international money transfers (SWIFT/Wire)"""

    # Exchange rates (INR to other currencies)
    EXCHANGE_RATES = {
        "USD": 83.12,
        "EUR": 90.45,
        "GBP": 105.30,
        "AED": 22.63,
        "SGD": 61.75,
        "AUD": 54.20,
        "CAD": 60.85,
        "JPY": 0.56,
        "CHF": 92.10,
    }

    # SWIFT charges based on amount tiers
    SWIFT_CHARGES = {
        (0, 100000): 500.0,
        (100000, 500000): 750.0,
        (500000, 1000000): 1000.0,
        (1000000, float("inf")): 1500.0,
    }

    PROCESSING_DAYS = 3
    DAILY_LIMIT_INR = 2500000.0  # Rs. 25 lakhs per day

    @staticmethod
    def generate_swift_reference() -> str:
        """Generate unique SWIFT reference number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"SWIFT{timestamp}{random_suffix}"

    @staticmethod
    def validate_swift_code(swift_code: str) -> bool:
        """Validate SWIFT/BIC code format"""
        swift_code = swift_code.replace(" ", "").upper()

        if len(swift_code) not in [8, 11]:
            return False

        if not swift_code[:4].isalpha():
            return False

        if not swift_code[4:6].isalpha():
            return False

        if not swift_code[6:8].isalnum():
            return False

        if len(swift_code) == 11 and not swift_code[8:11].isalnum():
            return False

        return True

    @staticmethod
    def calculate_swift_charges(amount_inr: float) -> float:
        """Calculate SWIFT transfer charges based on amount"""
        for (min_amt, max_amt), charge in InternationalTransfer.SWIFT_CHARGES.items():
            if min_amt <= amount_inr < max_amt:
                return charge
        return 1500.0

    @staticmethod
    def convert_currency(
        amount: float, from_currency: str, to_currency: str
    ) -> Tuple[float, float]:
        """Convert between currencies - Returns (converted_amount, exchange_rate)"""
        if (
            from_currency == "INR"
            and to_currency in InternationalTransfer.EXCHANGE_RATES
        ):
            rate = InternationalTransfer.EXCHANGE_RATES[to_currency]
            converted = amount / rate
            return round(converted, 2), rate

        elif (
            to_currency == "INR"
            and from_currency in InternationalTransfer.EXCHANGE_RATES
        ):
            rate = InternationalTransfer.EXCHANGE_RATES[from_currency]
            converted = amount * rate
            return round(converted, 2), rate

        else:
            if (
                from_currency in InternationalTransfer.EXCHANGE_RATES
                and to_currency in InternationalTransfer.EXCHANGE_RATES
            ):
                inr_amount = (
                    amount * InternationalTransfer.EXCHANGE_RATES[from_currency]
                )
                rate_to = InternationalTransfer.EXCHANGE_RATES[to_currency]
                converted = inr_amount / rate_to
                effective_rate = (
                    InternationalTransfer.EXCHANGE_RATES[from_currency] / rate_to
                )
                return round(converted, 2), effective_rate

        raise ValueError(
            f"Unsupported currency conversion: {from_currency} to {to_currency}"
        )

    @staticmethod
    def initiate_international_transfer(
        account: "Account",
        recipient_name: str,
        recipient_account: str,
        recipient_bank_name: str,
        swift_code: str,
        recipient_country: str,
        amount_to_send: float,
        currency: str,
        purpose: str,
        recipient_address: Optional[str] = None,
        registry: "InternationalBankRegistry" = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """Initiate international wire transfer"""

        # Validate SWIFT code
        if not InternationalTransfer.validate_swift_code(swift_code):
            return False, "Invalid SWIFT/BIC code format", None

        # Check if currency is supported
        if currency not in InternationalTransfer.EXCHANGE_RATES:
            return False, f"Currency {currency} not supported", None

        # Validate with registry if provided
        foreign_account = None
        if registry:
            is_valid, msg, foreign_account = registry.validate_transfer_details(
                recipient_account, swift_code, recipient_name
            )

            if not is_valid:
                return False, f"Recipient validation failed: {msg}", None

        # Convert to INR to check balance
        amount_inr, exchange_rate = InternationalTransfer.convert_currency(
            amount_to_send, currency, "INR"
        )

        # Calculate charges
        swift_charges = InternationalTransfer.calculate_swift_charges(amount_inr)
        total_debit_inr = amount_inr + swift_charges

        # Check daily limit
        today_international_txns = [
            t
            for t in account.transactions
            if t.type == "SWIFT_SENT"
            and datetime.strptime(t.timestamp, "%d-%m-%Y %H:%M:%S").date()
            == BankClock.today()
        ]
        today_total = sum(abs(t.amount) for t in today_international_txns)

        if today_total + total_debit_inr > InternationalTransfer.DAILY_LIMIT_INR:
            remaining = InternationalTransfer.DAILY_LIMIT_INR - today_total
            return (
                False,
                f"Daily international transfer limit exceeded. Remaining: Rs. {remaining:,.2f}",
                None,
            )

        # Check account balance
        min_balance = account._min_operational_balance
        if account.balance - total_debit_inr < min_balance:
            return (
                False,
                f"Insufficient funds. Need Rs. {total_debit_inr:,.2f} + Rs. {min_balance:,.2f} minimum balance",
                None,
            )

        # Generate SWIFT reference
        swift_ref = InternationalTransfer.generate_swift_reference()

        # Expected arrival date
        arrival_date = BankClock.today() + timedelta(
            days=InternationalTransfer.PROCESSING_DAYS
        )

        # Deduct from account
        account.balance -= total_debit_inr

        # Create transaction
        txn = Transaction(
            type="SWIFT_SENT",
            amount=total_debit_inr,
            resulting_balance=account.balance,
            metadata={
                "swift_reference": swift_ref,
                "recipient_name": recipient_name,
                "recipient_account": recipient_account,
                "recipient_bank": recipient_bank_name,
                "swift_code": swift_code,
                "country": recipient_country,
                "amount_foreign": amount_to_send,
                "currency": currency,
                "exchange_rate": exchange_rate,
                "swift_charges": swift_charges,
                "purpose": purpose,
                "expected_arrival": arrival_date.strftime("%Y-%m-%d"),
                "recipient_address": recipient_address or "Not provided",
            },
        )

        account.transactions.append(txn)

        # Log activity
        DataStore.append_activity(
            timestamp=txn.timestamp,
            username=account.username,
            account_number=account.account_number,
            action="SWIFT_SENT",
            amount=total_debit_inr,
            resulting_balance=account.balance,
            txn_id=txn.id,
            metadata=f"swiftRef={swift_ref};currency={currency};foreignAmt={amount_to_send};rate={exchange_rate};charges={swift_charges};country={recipient_country}",
        )

        # Credit foreign account if in registry
        if registry and foreign_account:
            if foreign_account.currency == currency:
                credit_amount = amount_to_send
            else:
                credit_amount, _ = InternationalTransfer.convert_currency(
                    amount_to_send, currency, foreign_account.currency
                )

            foreign_account.receive_transfer(
                amount=credit_amount,
                sender_name=f"{account.first_name} {account.last_name}",
                sender_country="India",
                swift_ref=swift_ref,
            )

        # Check AMB
        account._check_and_apply_amb_fee()

        success_msg = f"""International transfer initiated successfully!
        
SWIFT Reference: {swift_ref}
Recipient: {recipient_name}
Bank: {recipient_bank_name} ({swift_code})
Country: {recipient_country}

Amount Sent: {amount_to_send:,.2f} {currency}
Exchange Rate: 1 {currency} = Rs. {exchange_rate:,.2f}
Amount in INR: Rs. {amount_inr:,.2f}
SWIFT Charges: Rs. {swift_charges:,.2f}
Total Debited: Rs. {total_debit_inr:,.2f}

Expected Arrival: {arrival_date.strftime("%d-%m-%Y")} ({InternationalTransfer.PROCESSING_DAYS} business days)
Purpose: {purpose}

Transaction ID: {txn.id}
"""

        return True, success_msg, swift_ref

    @staticmethod
    def track_swift_transfer(swift_reference: str, bank: "Bank") -> Optional[dict]:
        """Track a SWIFT transfer by reference number"""
        for account in bank.accounts.values():
            for txn in account.transactions:
                if txn.type == "SWIFT_SENT" and hasattr(txn, "metadata"):
                    if (
                        isinstance(txn.metadata, dict)
                        and txn.metadata.get("swift_reference") == swift_reference
                    ):
                        txn_date = datetime.strptime(
                            txn.timestamp, "%d-%m-%Y %H:%M:%S"
                        ).date()
                        days_elapsed = (BankClock.today() - txn_date).days
                        expected_arrival = datetime.strptime(
                            txn.metadata["expected_arrival"], "%Y-%m-%d"
                        ).date()

                        if BankClock.today() >= expected_arrival:
                            status = "Completed ✅"
                        elif days_elapsed == 0:
                            status = "Processing - Day 1"
                        else:
                            status = f"In Transit - Day {days_elapsed + 1}/{InternationalTransfer.PROCESSING_DAYS}"

                        return {
                            "swift_reference": swift_reference,
                            "status": status,
                            "sender_account": account.account_number,
                            "sender_name": f"{account.first_name} {account.last_name}",
                            "recipient_name": txn.metadata["recipient_name"],
                            "recipient_account": txn.metadata["recipient_account"],
                            "recipient_bank": txn.metadata["recipient_bank"],
                            "swift_code": txn.metadata["swift_code"],
                            "country": txn.metadata["country"],
                            "amount": txn.metadata["amount_foreign"],
                            "currency": txn.metadata["currency"],
                            "exchange_rate": txn.metadata["exchange_rate"],
                            "total_debited_inr": txn.amount,
                            "charges": txn.metadata["swift_charges"],
                            "purpose": txn.metadata["purpose"],
                            "initiated_on": txn.timestamp,
                            "expected_arrival": txn.metadata["expected_arrival"],
                            "transaction_id": txn.id,
                        }

        return None

    @staticmethod
    def get_today_international_limit_used(account: "Account") -> float:
        """Get total international transfers made today"""
        today = BankClock.today()
        total = 0.0

        for txn in account.transactions:
            if txn.type == "SWIFT_SENT":
                try:
                    txn_date = datetime.strptime(
                        txn.timestamp, "%d-%m-%Y %H:%M:%S"
                    ).date()
                    if txn_date == today:
                        total += abs(txn.amount)
                except:
                    pass

        return total
