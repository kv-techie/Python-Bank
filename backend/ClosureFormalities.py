from typing import TYPE_CHECKING, List

from AccountClosure import AccountClosureService
from BankClock import BankClock
from Beneficiary import Beneficiary
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
    def _add_new_beneficiary_for_closure(
        account: "Account", bank: "Bank", disbursement_details: dict
    ) -> dict:
        """Helper to add a new beneficiary during account closure"""
        print("\nAdd New Beneficiary:")
        print("-" * 40)

        beneficiary_name = input("Beneficiary Name: ").strip()
        if not beneficiary_name:
            print("❌ Name cannot be empty.")
            return disbursement_details

        account_number = input("Beneficiary Account Number: ").strip()
        if not account_number:
            print("❌ Account number cannot be empty.")
            return disbursement_details

        ifsc_code = input("IFSC Code: ").strip()
        if not ifsc_code:
            print("❌ IFSC code cannot be empty.")
            return disbursement_details

        bank_name = input("Bank Name: ").strip()
        if not bank_name:
            print("❌ Bank name cannot be empty.")
            return disbursement_details

        account_type = input(
            "Account Type (Savings/Current) [default: Savings]: "
        ).strip()
        if not account_type:
            account_type = "Savings"

        # Create new beneficiary
        beneficiary = Beneficiary(
            beneficiary_name=beneficiary_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            account_type=account_type,
        )

        # Add to account
        account.add_beneficiary(beneficiary)

        disbursement_details["beneficiary"] = beneficiary
        disbursement_details["method"] = "bank_transfer"

        print(f"✅ Beneficiary added: {beneficiary_name}")

        return disbursement_details

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

        # Disbursement method selection
        print("\n" + "-" * 60)
        print("DISBURSEMENT METHOD")
        print("-" * 60)
        print(f"Final Balance to Disburse: Rs. {account.balance:,.2f} INR")
        print("\nSelect disbursement method:")
        print("1️⃣  Issue Cheque")
        print("2️⃣  Bank Transfer")

        disbursement_method = input("\nEnter your choice (1 or 2): ").strip()

        disbursement_details = {
            "method": None,
            "beneficiary": None,
            "cheque_number": None,
        }

        if disbursement_method == "1":
            disbursement_details["method"] = "cheque"
            # Cheque number will be auto-assigned from cheque book manager
            print("\n✅ Cheque Method Selected")
            print(f"Amount: Rs. {account.balance:,.2f} INR")
            print(f"Payable to: {account.first_name} {account.last_name}")
            print("Cheque will be issued from your cheque book immediately.")

        elif disbursement_method == "2":
            print("\n" + "-" * 60)
            print("BANK TRANSFER DETAILS")
            print("-" * 60)

            # Check for existing beneficiaries
            if account.beneficiaries:
                print("\nYour existing beneficiaries:")
                for idx, ben in enumerate(account.beneficiaries, 1):
                    print(
                        f"{idx}. {ben.beneficiary_name} - {ben.account_number[-4:]} ({ben.bank_name})"
                    )

                print(f"{len(account.beneficiaries) + 1}. Add new beneficiary")
                ben_choice = input("\nSelect beneficiary (enter number): ").strip()

                try:
                    ben_idx = int(ben_choice) - 1
                    if 0 <= ben_idx < len(account.beneficiaries):
                        disbursement_details["beneficiary"] = account.beneficiaries[
                            ben_idx
                        ]
                        disbursement_details["method"] = "bank_transfer"
                    elif ben_idx == len(account.beneficiaries):
                        disbursement_details = (
                            ClosureFormalities._add_new_beneficiary_for_closure(
                                account, bank, disbursement_details
                            )
                        )
                    else:
                        print("❌ Invalid selection.")
                        return False
                except ValueError:
                    print("❌ Invalid input.")
                    return False
            else:
                # No existing beneficiaries - add new one
                disbursement_details = (
                    ClosureFormalities._add_new_beneficiary_for_closure(
                        account, bank, disbursement_details
                    )
                )

            if disbursement_details["beneficiary"] is None:
                print("❌ No beneficiary selected. Closure cancelled.")
                return False

            # Validate account
            beneficiary = disbursement_details["beneficiary"]
            print("\n✅ Bank Transfer Method Selected")
            print(f"Beneficiary: {beneficiary.beneficiary_name}")
            print(f"Account: {beneficiary.account_number}")
            print(f"IFSC: {beneficiary.ifsc_code}")
            print(f"Bank: {beneficiary.bank_name}")
            print(f"Amount: Rs. {account.balance:,.2f} INR")

            # Check if account starts with 5621 (internal account)
            if beneficiary.account_number.startswith("5621"):
                print("\n🔍 Validating internal account...")
                recipient_account = bank.find_account_by_number(
                    beneficiary.account_number
                )

                if recipient_account:
                    print(
                        f"✅ Account found: {recipient_account.first_name} {recipient_account.last_name}"
                    )
                    print(f"   Account Type: {recipient_account.account_type}")
                    print(
                        f"   Current Balance: Rs. {recipient_account.balance:,.2f} INR"
                    )
                    print(
                        f"   Updated Balance: Rs. {recipient_account.balance + account.balance:,.2f} INR"
                    )
                    disbursement_details["validated_internal"] = True
                else:
                    print(
                        f"⚠️  WARNING: Cannot find internal account {beneficiary.account_number}"
                    )
                    confirm_transfer = (
                        input("Proceed anyway? (yes/no): ").strip().lower()
                    )
                    if confirm_transfer not in ["yes", "y"]:
                        print("Closure cancelled.")
                        return False
                    disbursement_details["validated_internal"] = False
            else:
                print("\n✅ External bank account - will be transferred via NEFT")

        else:
            print("❌ Invalid selection.")
            return False

        # Final confirmation
        confirm3 = input("\nType 'CLOSE ACCOUNT' to finalize: ").strip()

        if confirm3 != "CLOSE ACCOUNT":
            print("Account closure cancelled.")
            return False

        # Process closure
        print("\n🔄 Processing account closure...")
        success, message, cert_path = AccountClosureService.close_account(
            account, bank, disbursement_details
        )

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
