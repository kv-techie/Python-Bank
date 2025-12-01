from typing import TYPE_CHECKING, List

from AccountClosure import AccountClosureService
from Card import CreditCard

if TYPE_CHECKING:
    from Account import Account
    from Bank import Bank
    from Customer import Customer


class ClosureFormalities:
    """Handles user interaction for account and card closure operations"""

    @staticmethod
    def close_card_menu(account: "Account", bank: "Bank"):
        """Handle card closure"""
        if not account.cards:
            print("\n❌ No cards linked to this account.")
            return

        print("\n" + "=" * 60)
        print("CLOSE CARD")
        print("=" * 60)

        # Show all cards
        account.list_cards()

        print("\nSelect a card to close:")
        card_id = input(
            "Enter Card ID or last 4 digits (or 'cancel' to go back): "
        ).strip()

        if card_id.lower() == "cancel":
            return

        # Find the card
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card:
            print("❌ Card not found.")
            return

        # Show card details
        print("\nCard to be closed:")
        print(f"Type: {card.card_type}")
        print(f"Network: {card.network}")
        print(f"Number: **** **** **** {card.card_number[-4:]}")

        if isinstance(card, CreditCard):
            print(f"Credit Limit: Rs. {card.credit_limit:,.2f} INR")
            print(f"Outstanding: Rs. {card.outstanding_balance:,.2f} INR")
            reward_points = getattr(card, "reward_points", 0.0)
            print(f"Reward Points: {reward_points:.0f} (will be forfeited)")

        # Confirmation
        print("\n⚠️  WARNING: This action cannot be undone!")
        confirm = (
            input("\nAre you sure you want to close this card? (yes/no): ")
            .strip()
            .lower()
        )

        if confirm not in ["yes", "y"]:
            print("Card closure cancelled.")
            return

        # Double confirmation for credit cards
        if isinstance(card, CreditCard):
            print("\n⚠️  All reward points will be forfeited.")
            confirm2 = input("Type 'CONFIRM' to proceed: ").strip()
            if confirm2 != "CONFIRM":
                print("Card closure cancelled.")
                return

        # Process closure
        if isinstance(card, CreditCard):
            success, message, cert_path = AccountClosureService.close_credit_card(
                card, account
            )
        else:
            success, message, cert_path = AccountClosureService.close_debit_card(
                card, account
            )

        if success:
            print(f"\n✅ {message}")
            print(f"📄 Closure certificate saved: {cert_path}")
            bank.save()
        else:
            print(f"\n❌ {message}")

    @staticmethod
    def close_account_menu(
        account: "Account",
        customer: "Customer",
        accounts: List["Account"],
        bank: "Bank",
    ) -> bool:
        """
        Handle account closure

        Returns:
            True if account was closed successfully, False otherwise
        """
        print("\n" + "=" * 60)
        print("CLOSE ACCOUNT")
        print("=" * 60)

        # Show account details
        print("\nAccount to be closed:")
        print(f"Account Holder: {account.first_name} {account.last_name}")
        print(f"Account Type: {account.account_type}")
        print(f"Account Number: {account.account_number}")
        print(f"Current Balance: Rs. {account.balance:,.2f} INR")
        print(f"Linked Cards: {len(account.cards)}")
        print(f"Recurring Bills: {len(account.recurring_bills)}")

        # Check for active loans
        active_loans = [
            loan
            for loan in bank.loans
            if loan.customer_id == account.customer_id and not loan.status == "Closed"
        ]

        if active_loans:
            print(f"Active Loans: {len(active_loans)} ⚠️")

        print("\n" + "-" * 60)
        print("CLOSURE CHECKLIST:")
        print("-" * 60)

        # Validation preview
        issues = []

        if account.pending_amb_fees > 0:
            issues.append(
                f"❌ Pending AMB fees: Rs. {account.pending_amb_fees:.2f} INR"
            )
        else:
            print("✅ No pending AMB fees")

        if active_loans:
            issues.append(
                f"❌ {len(active_loans)} active loan(s) - must be closed first"
            )
        else:
            print("✅ No active loans")

        if account.recurring_bills:
            issues.append(
                f"❌ {len(account.recurring_bills)} recurring bill(s) - must be cancelled first"
            )
        else:
            print("✅ No recurring bills")

        # Check credit card balances
        credit_card_issues = []
        for card in account.cards:
            if isinstance(card, CreditCard):
                if card.credit_used > 0 or card.outstanding_balance > 0:
                    credit_card_issues.append(
                        f"❌ Credit card {card.card_number[-4:]} has outstanding balance: Rs. {card.outstanding_balance:.2f} INR"
                    )

        if credit_card_issues:
            issues.extend(credit_card_issues)
        else:
            print("✅ No credit card outstanding balances")

        if account.balance < account._min_operational_balance:
            issues.append(
                f"❌ Account balance (Rs. {account.balance:.2f} INR) below minimum (Rs. {account._min_operational_balance:.2f} INR)"
            )
        else:
            print("✅ Sufficient balance for closure")

        if account.cards:
            print(f"⚠️  {len(account.cards)} card(s) will be terminated")
        else:
            print("✅ No cards to terminate")

        # Show blocking issues
        if issues:
            print("\n" + "-" * 60)
            print("CANNOT CLOSE ACCOUNT - PENDING ACTIONS REQUIRED:")
            print("-" * 60)
            for issue in issues:
                print(f"  {issue}")
            print("-" * 60)
            print("\nPlease resolve the above issues before closing the account.")
            input("\nPress Enter to continue...")
            return False

        # All checks passed - proceed with closure
        print("\n" + "-" * 60)
        print("✅ All requirements met for account closure")
        print("-" * 60)

        print("\n⚠️  WARNING: ACCOUNT CLOSURE IS PERMANENT!")
        print("This action will:")
        print(
            f"  • Close your {account.account_type} account ({account.account_number})"
        )
        print(f"  • Terminate all {len(account.cards)} linked card(s)")
        print(f"  • Disburse final balance of Rs. {account.balance:,.2f} INR")
        print("  • Delete all account data")
        print("\nThis action CANNOT be undone!")

        # First confirmation
        confirm1 = (
            input("\nDo you want to proceed with account closure? (yes/no): ")
            .strip()
            .lower()
        )

        if confirm1 not in ["yes", "y"]:
            print("Account closure cancelled.")
            return False

        # Second confirmation - type account number
        print(
            f"\nTo confirm, please type your account number: {account.account_number}"
        )
        confirm2 = input("Account Number: ").strip()

        if confirm2 != account.account_number:
            print("❌ Account number does not match. Closure cancelled.")
            return False

        # Final confirmation
        confirm3 = input("\nType 'CLOSE ACCOUNT' to finalize: ").strip()

        if confirm3 != "CLOSE ACCOUNT":
            print("Account closure cancelled.")
            return False

        # Process closure
        print("\n🔄 Processing account closure...")
        success, message, cert_path = AccountClosureService.close_account(account, bank)

        if success:
            print("\n" + "=" * 60)
            print("✅ ACCOUNT CLOSED SUCCESSFULLY")
            print("=" * 60)
            print(f"\n{message}")
            print(f"\n📄 Closure certificate: {cert_path}")
            print("\nThank you for banking with us.")
            print("You will be redirected to the main menu.")
            print("=" * 60)

            # Save changes
            bank.save()

            # Wait for user to read
            input("\nPress Enter to continue...")

            return True
        else:
            print(f"\n❌ Account closure failed: {message}")
            return False
