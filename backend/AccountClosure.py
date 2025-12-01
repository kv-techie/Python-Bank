import os
from typing import TYPE_CHECKING, Optional, Tuple

from BankClock import BankClock
from Card import CreditCard, DebitCard
from DataStore import DataStore

if TYPE_CHECKING:
    from Account import Account


class AccountClosureService:
    """Service for handling account and card closures"""

    @staticmethod
    def close_account(account: "Account", bank) -> Tuple[bool, str, Optional[str]]:
        """
        Close a bank account after validating closure conditions

        Args:
            account: Account to close
            bank: Bank instance (to access loans and remove account)

        Returns:
            (success, message, closure_certificate_path)
        """
        # Validation checks
        validation_result = AccountClosureService._validate_account_closure(
            account, bank
        )
        if not validation_result[0]:
            return False, validation_result[1], None

        # Get final balance
        final_balance = account.balance

        # Close all linked cards
        cards_closed = []
        for card in account.cards:
            if isinstance(card, CreditCard):
                if card.credit_used > 0 or card.outstanding_balance > 0:
                    return (
                        False,
                        f"Cannot close account. Credit card ending in {card.card_number[-4:]} has outstanding balance of Rs. {card.outstanding_balance:.2f} INR",
                        None,
                    )
                cards_closed.append(
                    f"Credit Card {card.network} ending in {card.card_number[-4:]}"
                )
            else:
                cards_closed.append(
                    f"Debit Card {card.network} ending in {card.card_number[-4:]}"
                )

        # Generate closure certificate
        certificate_path = AccountClosureService._generate_closure_certificate(
            account, final_balance, cards_closed
        )

        # Log closure activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="ACCOUNT_CLOSED",
            amount=final_balance,
            resulting_balance=0.0,
            metadata=f"customerId={account.customer_id};cardsTerminated={len(cards_closed)}",
        )

        # Remove from bank's active accounts
        bank.accounts = [
            acc for acc in bank.accounts if acc.account_number != account.account_number
        ]

        return (
            True,
            f"Account closed successfully. Final balance: Rs. {final_balance:.2f} INR. Closure certificate: {certificate_path}",
            certificate_path,
        )

    @staticmethod
    def _validate_account_closure(account: "Account", bank) -> Tuple[bool, str]:
        """Validate if account can be closed"""

        # Check for pending AMB fees
        if account.pending_amb_fees > 0:
            return (
                False,
                f"Cannot close account. Pending AMB fees: Rs. {account.pending_amb_fees:.2f} INR. Please clear dues first.",
            )

        # Check for active loans
        active_loans = [
            loan
            for loan in bank.loans
            if loan.customer_id == account.customer_id and loan.status != "Closed"
        ]
        if active_loans:
            return (
                False,
                f"Cannot close account. {len(active_loans)} active loan(s) found. Please close all loans first.",
            )

        # Check for active recurring bills
        if account.recurring_bills:
            return (
                False,
                f"Cannot close account. {len(account.recurring_bills)} active recurring bill(s). Please cancel them first.",
            )

        # Check credit card outstanding balances
        for card in account.cards:
            if isinstance(card, CreditCard):
                if card.credit_used > 0 or card.outstanding_balance > 0:
                    return (
                        False,
                        f"Cannot close account. Credit card ending in {card.card_number[-4:]} has outstanding balance.",
                    )

        # Minimum balance check
        if account.balance < account._min_operational_balance:
            return (
                False,
                f"Account balance (Rs. {account.balance:.2f} INR) is below minimum operational balance. Deposit required before closure.",
            )

        return True, "Validation passed"

    @staticmethod
    def _generate_closure_certificate(
        account: "Account", final_balance: float, cards_closed: list
    ) -> str:
        """Generate account closure certificate"""
        timestamp = BankClock.get_formatted_datetime()
        closure_date = BankClock.today().strftime("%d-%m-%Y")

        certificate_content = f"""
{"=" * 70}
                    ACCOUNT CLOSURE CERTIFICATE
{"=" * 70}

Closure Date:           {closure_date}
Closure Time:           {timestamp}

ACCOUNT HOLDER DETAILS
----------------------------------------------------------------------
Customer ID:            {account.customer_id}
Name:                   {account.first_name} {account.last_name}
Account Number:         {account.account_number}
Account Type:           {account.account_type}
Date of Birth:          {account.dob}
Gender:                 {account.gender}

BRANCH DETAILS
----------------------------------------------------------------------
Branch Name:            {account.BRANCH_NAME}
IFSC Code:              {account.BRANCH_IFSC}
Branch Code:            {account.ACCOUNT_NUMBER_PREFIX}

CLOSURE SUMMARY
----------------------------------------------------------------------
Final Account Balance:  Rs. {final_balance:.2f} INR
Total Transactions:     {len(account.transactions)}
Pending AMB Fees:       Rs. {account.pending_amb_fees:.2f} INR
Active Recurring Bills: {len(account.recurring_bills)}

CARDS TERMINATED
----------------------------------------------------------------------
"""
        if cards_closed:
            for card in cards_closed:
                certificate_content += f"  - {card}\n"
        else:
            certificate_content += "  None\n"

        certificate_content += f"""
{"=" * 70}

This certificate confirms that the above account has been closed
and all linked cards have been terminated. The final balance of
Rs. {final_balance:.2f} INR will be disbursed as per RBI guidelines.

All recurring payments, loans, and outstanding dues have been cleared.

This is a system-generated certificate and does not require a signature.

{"=" * 70}
Generated on: {timestamp}
System: Python Bank Management System v1.0
{"=" * 70}
"""

        # Save certificate
        os.makedirs("data/closure_certificates", exist_ok=True)
        file_path = f"data/closure_certificates/account_closure_{account.account_number}_{account.customer_id}.txt"

        with open(file_path, "w") as f:
            f.write(certificate_content)

        return file_path

    @staticmethod
    def close_credit_card(
        card: CreditCard, account: "Account"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Close a credit card

        Args:
            card: CreditCard to close
            account: Linked account

        Returns:
            (success, message, closure_document_path)
        """
        # Validation
        if card.credit_used > 0 or card.outstanding_balance > 0:
            return (
                False,
                f"Cannot close credit card. Outstanding balance: Rs. {card.outstanding_balance:.2f} INR. Please clear dues first.",
                None,
            )

        # Check for pending bills
        if card.due_date and BankClock.today() <= card.due_date:
            if card.outstanding_balance > 0:
                return (
                    False,
                    f"Cannot close credit card. Bill due on {card.due_date.strftime('%d-%m-%Y')}. Clear payment first.",
                    None,
                )

        # Generate closure document
        certificate_path = AccountClosureService._generate_card_closure_certificate(
            card, account, "CREDIT"
        )

        # Remove card from account
        account.cards = [c for c in account.cards if c.card_id != card.card_id]

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="CREDIT_CARD_CLOSED",
            amount=None,
            resulting_balance=None,
            metadata=f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network};rewardPoints={card.reward_points:.0f}",
        )

        return (
            True,
            f"Credit card ending in {card.card_number[-4:]} closed successfully. {card.reward_points:.0f} reward points forfeited.",
            certificate_path,
        )

    @staticmethod
    def close_debit_card(
        card: DebitCard, account: "Account"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Close a debit card

        Args:
            card: DebitCard to close
            account: Linked account

        Returns:
            (success, message, closure_document_path)
        """
        # Generate closure document
        certificate_path = AccountClosureService._generate_card_closure_certificate(
            card, account, "DEBIT"
        )

        # Remove card from account
        account.cards = [c for c in account.cards if c.card_id != card.card_id]

        # Log activity
        DataStore.append_activity(
            timestamp=BankClock.get_formatted_datetime(),
            username=account.username,
            account_number=account.account_number,
            action="DEBIT_CARD_CLOSED",
            amount=None,
            resulting_balance=None,
            metadata=f"cardId={card.card_id};cardNumber={card.card_number[-4:]};network={card.network}",
        )

        return (
            True,
            f"Debit card ending in {card.card_number[-4:]} closed successfully.",
            certificate_path,
        )

    @staticmethod
    def _generate_card_closure_certificate(
        card, account: "Account", card_type: str
    ) -> str:
        """Generate card closure certificate"""
        timestamp = BankClock.get_formatted_datetime()
        closure_date = BankClock.today().strftime("%d-%m-%Y")

        certificate_content = f"""
{"=" * 70}
                    {card_type} CARD CLOSURE CERTIFICATE
{"=" * 70}

Closure Date:           {closure_date}
Closure Time:           {timestamp}

CARDHOLDER DETAILS
----------------------------------------------------------------------
Customer ID:            {account.customer_id}
Name:                   {account.first_name} {account.last_name}
Account Number:         {account.account_number}

CARD DETAILS
----------------------------------------------------------------------
Card Type:              {card_type}
Card Network:           {card.network}
Card Number:            **** **** **** {card.card_number[-4:]}
Card ID:                {card.card_id}
Issue Date:             {(card.expiry_date.replace(year=card.expiry_date.year - 4)).strftime("%d-%m-%Y")}
Expiry Date:            {card.expiry_date.strftime("%d-%m-%Y")}
"""

        if card_type == "CREDIT":
            certificate_content += f"""
CREDIT CARD SUMMARY
----------------------------------------------------------------------
Credit Limit:           Rs. {card.credit_limit:,.2f} INR
Credit Used:            Rs. {card.credit_used:.2f} INR
Outstanding Balance:    Rs. {card.outstanding_balance:.2f} INR
Reward Points:          {card.reward_points:.0f} (Forfeited)
"""

        certificate_content += f"""
{"=" * 70}

This certificate confirms that the above {card_type.lower()} card has been
permanently closed and terminated. The card can no longer be used for
any transactions.
"""

        if card_type == "CREDIT":
            certificate_content += """
All outstanding balances have been cleared and reward points forfeited.
"""

        certificate_content += f"""
This is a system-generated certificate and does not require a signature.

{"=" * 70}
Generated on: {timestamp}
System: Python Bank Management System v1.0
{"=" * 70}
"""

        # Save certificate
        os.makedirs("data/card_closures", exist_ok=True)
        file_path = f"data/card_closures/{card_type.lower()}_card_closure_{card.card_number[-4:]}_{account.customer_id}.txt"

        with open(file_path, "w") as f:
            f.write(certificate_content)

        return file_path
