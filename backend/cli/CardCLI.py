from datetime import datetime
from typing import Tuple, Optional

from ..Card import Card, CreditCard, DebitCard
from ..Customer import Customer
from ..Account import Account
from ..Logger import BankLogger
from ..RecurringBill import PaymentMethod, RecurringBill, RecurringBillFactory
from ..Transaction import Transaction
from ..CreditLimitEnhancement import CreditLimitEnhancement
from ..RewardPointsManager import RewardPointsManager
from ..BankClock import BankClock



class CardCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.card_service = app.card_service
        self.logger = BankLogger.get_logger("CardCLI")

    def card_management_menu(self, account: Account):
        """Card management submenu"""
        while True:
            print("\n" + "=" * 50)
            print("CARD MANAGEMENT")
            print("=" * 50)
            print("1. View All Cards")
            print("2. Apply for Debit Card")
            print("3. Apply for Credit Card")
            print("4. View Card Details")  # NEW OPTION
            print("5. Make Card Purchase")
            print("6. Pay Credit Card Bill")
            print("7. View Credit Card Statement")
            print("8. Block Card")
            print("9. Unblock Card")
            print("10.Credit Limit Enhancement Request")
            print("11. Manage Auto-Pay Settings")
            print("12. Set/Change Card PIN")
            print("13. Back to Main Menu")
            print("=" * 50)

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                account.list_cards()

            elif choice == "2":
                self.apply_debit_card(account)

            elif choice == "3":
                self.apply_credit_card(account)

            elif choice == "4":
                self.view_card_details(account)  # NEW METHOD

            elif choice == "5":
                self.make_card_purchase(account)

            elif choice == "6":
                self.pay_credit_card(account)

            elif choice == "7":
                self.view_credit_statement(account)

            elif choice == "8":
                self.block_card(account)

            elif choice == "9":
                self.unblock_card(account)

            elif choice == "10":
                self.request_credit_limit_enhancement(account)

            elif choice == "11":
                self.manage_card_auto_pay(account)

            elif choice == "12":
                self.set_card_pin(account)

            elif choice == "13":
                break

            else:
                print("Invalid choice")


    # ========== CARD MANAGEMENT OPERATIONS ==========


    def request_credit_limit_enhancement(self, account: Account):
        """Request credit limit enhancement for a credit card"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards found")
            return

        print("\n" + "=" * 70)
        print("CREDIT LIMIT ENHANCEMENT REQUEST [UP]")
        print("=" * 70)

        # Show all credit cards
        for idx, card in enumerate(credit_cards, 1):
            print(f"\n{idx}. {card.network} **** **** **** {card.card_number[-4:]}")
            print(f"   Current Limit: Rs. {card.credit_limit:,.2f}")
            print(f"   Used: Rs. {card.credit_used:,.2f}")
            print(f"   Available: Rs. {card.available_credit():,.2f}")
            print(f"   Utilization: {card.credit_utilization():.1f}%")

        if len(credit_cards) == 1:
            selected_card = credit_cards[0]
        else:
            choice = input(f"\nSelect card (1-{len(credit_cards)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(credit_cards):
                    selected_card = credit_cards[idx]
                else:
                    print("[FAIL] Invalid choice")
                    return
            except ValueError:
                print("[FAIL] Invalid input")
                return

        # Get customer object
        customer = self.bank.get_customer_by_id(account.customer_id)
        if not customer:
            print("[FAIL] Error: Customer not found")
            return

        print(f"\n{'=' * 70}")
        print(f"Checking eligibility for {selected_card.network} card...")
        print(f"{'=' * 70}")

        # Check eligibility
        eligible, reason, details = CreditLimitEnhancement.check_eligibility(
            selected_card, customer, self.bank, account
        )

        # Display eligibility details
        print("\n[STATS] ELIGIBILITY CRITERIA:")
        print(f"{'=' * 70}")

        if "card_age_months" in details:
            status = "[SUCCESS]" if details["card_age_months"] >= 6 else "[FAIL]"
            print(
                f"{status} Card Age: {details['card_age_months']} months (Required: 6+)"
            )

        if "cibil_score" in details:
            status = "[SUCCESS]" if details["cibil_score"] >= 700 else "[FAIL]"
            print(
                f"{status} CIBIL Score: {details['cibil_score']:.0f} (Required: 700+)"
            )

        if "utilization" in details:
            util = details["utilization"]
            status = "[SUCCESS]" if 30 <= util <= 90 else "[FAIL]"
            print(f"{status} Credit Utilization: {util:.1f}% (Required: 30-90%)")

        if "total_payments" in details:
            status = "[SUCCESS]" if details["total_payments"] >= 3 else "[FAIL]"
            print(
                f"{status} Payment History: {details['total_payments']} payments (Required: 3+)"
            )

        if "on_time_ratio" in details:
            ratio = details["on_time_ratio"] * 100
            status = "[SUCCESS]" if details["on_time_ratio"] >= 0.95 else "[FAIL]"
            print(f"{status} On-Time Payments: {ratio:.0f}% (Required: 95%+)")

        if "defaulted_loans" in details:
            status = "[SUCCESS]" if details["defaulted_loans"] == 0 else "[FAIL]"
            print(
                f"{status} Defaulted Loans: {details['defaulted_loans']} (Required: 0)"
            )

        print(f"{'=' * 70}")

        if not eligible:
            print(f"\n[FAIL] INELIGIBLE: {reason}")
            print("\n💡 Tips to become eligible:")
            print("   • Maintain good payment history (pay bills on time)")
            print("   • Use your credit card regularly (30-75% utilization)")
            print("   • Keep your CIBIL score above 700")
            print("   • Wait for 6 months between enhancement requests")
            return

        print(f"\n[SUCCESS] ELIGIBLE: {reason}")

        # Calculate and show potential new limit
        annual_income = 0
        if account.salary_profile:
            annual_income = account.salary_profile.gross_salary * 12
        else:
            annual_income = 300000

        potential_new_limit = CreditLimitEnhancement.calculate_new_limit(
            current_limit=selected_card.credit_limit,
            cibil_score=details["cibil_score"],
            utilization=details["utilization"],
            income=annual_income,
        )

        increase = potential_new_limit - selected_card.credit_limit
        increase_pct = (increase / selected_card.credit_limit) * 100

        print("\n[MONEY] POTENTIAL ENHANCEMENT:")
        print(f"{'=' * 70}")
        print(f"Current Limit:     Rs. {selected_card.credit_limit:>15,.2f}")
        print(f"Proposed New Limit: Rs. {potential_new_limit:>15,.2f}")
        print(f"Increase Amount:    Rs. {increase:>15,.2f} ({increase_pct:.1f}%)")
        print(f"{'=' * 70}")

        # Confirm request
        confirm = (
            input("\nProceed with enhancement request? (yes/no): ").strip().lower()
        )

        if confirm not in ["yes", "y"]:
            print("[FAIL] Request cancelled")
            return

        # Process enhancement
        approved, message, new_limit = CreditLimitEnhancement.request_enhancement(
            selected_card, customer, self.bank, account
        )

        print(f"\n{'=' * 70}")
        if approved:
            print("🎉 CREDIT LIMIT ENHANCED!")
            print(f"{'=' * 70}")
            print(message)
            print(
                f"\n💳 Your new available credit: Rs. {selected_card.available_credit():,.2f}"
            )
            self.bank.save()
        else:
            print("[FAIL] ENHANCEMENT DENIED")
            print(f"{'=' * 70}")
            print(message)

        print(f"{'=' * 70}")

    def apply_debit_card(self, account: Account):
        """Apply for a new debit card"""
        print("\n--- Apply for Debit Card ---")

        # Show existing debit cards (if any)
        existing_debit = [c for c in account.cards if isinstance(c, DebitCard)]
        if existing_debit:
            print(
                f"\nYou currently have {len(existing_debit)} debit card(s) linked to this account:"
            )
            for idx, card in enumerate(existing_debit, 1):
                status = (
                    "Blocked"
                    if card.blocked
                    else ("Expired" if card.is_expired() else "Active")
                )
                print(
                    f"  {idx}. {card.network} **** {card.card_number[-4:]} ({status})"
                )
            print()

        confirm = input("Apply for a new debit card? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Application cancelled")
            return

        # Ask user to select card network
        print("\nSelect Card Network:")
        print("1. VISA")
        print("2. Mastercard")
        print("3. RuPay (Indian domestic)")

        network_choice = self.app.read_valid_choice("Enter choice (1-3): ", ["1", "2", "3"])
        network_map = {"1": "VISA", "2": "MASTERCARD", "3": "RUPAY"}
        network = network_map[network_choice]

        debit_card = DebitCard(account.customer_id, account.account_number, network)
        account.add_card(debit_card)
        self.bank.save()
        print(f"\n[OK] {network} Debit card issued successfully!")
        print(
            f"Total debit cards: {len([c for c in account.cards if isinstance(c, DebitCard)])}"
        )

    def apply_credit_card(self, account: Account):
        """Apply for a new credit card"""
        from datetime import datetime

        print("\n--- Apply for Credit Card ---")

        # Show existing credit cards (if any)
        existing_credit = [c for c in account.cards if isinstance(c, CreditCard)]
        if existing_credit:
            print(
                f"\nYou currently have {len(existing_credit)} credit card(s) linked to this account:"
            )
            for idx, card in enumerate(existing_credit, 1):
                status = (
                    "Blocked"
                    if card.blocked
                    else ("Expired" if card.is_expired() else "Active")
                )
                print(
                    f"  {idx}. {card.network} **** {card.card_number[-4:]} - Limit: Rs. {card.credit_limit:,.0f} ({status})"
                )
            print()

        # Check eligibility via CardService
        customer = self.bank.get_customer_by_id(account.customer_id)
        if not customer:
            print("✗ Error: Customer information not found")
            return

        eligible, reason, cibil_score, annual_income, credit_limit = self.card_service.check_credit_card_eligibility(customer, account)

        if not eligible:
            print(f"✗ {reason}")
            return

        print(f"[OK] {reason}")
        print(f"CIBIL Score: {cibil_score:.0f}")
        print(f"Annual Income: Rs. {annual_income:,.2f} INR")
        print(f"\nApproved Credit Limit: Rs. {credit_limit:,.2f} INR")

        confirm = (
            input("\nProceed with credit card application? (yes/no): ").strip().lower()
        )
        if confirm not in ["yes", "y"]:
            print("Application cancelled")
            return

        # Ask user to select card network
        print("\nSelect Card Network:")
        print("1. VISA")
        print("2. Mastercard")
        print("3. RuPay (Indian domestic)")

        network_choice = self.app.read_valid_choice("Enter choice (1-3): ", ["1", "2", "3"])
        network_map = {"1": "VISA", "2": "MASTERCARD", "3": "RUPAY"}
        network = network_map[network_choice]

        # Get billing day preference
        while True:
            billing_day = input("\nPreferred billing day (1-28): ").strip()
            try:
                billing_day = int(billing_day)
                if 1 <= billing_day <= 28:
                    break
                else:
                    print("Billing day must be between 1 and 28")
            except ValueError:
                print("Invalid input")

        # Issue card via service
        self.card_service.issue_credit_card(account, credit_limit, billing_day, network, "NONE")
        print(f"\n[OK] {network} Credit card issued successfully!")
        print(f"Billing Day: {billing_day} of each month")
        print(
            f"Total credit cards: {len([c for c in account.cards if isinstance(c, CreditCard)])}"
        )

        # Ask about auto-pay policy
        print("\n" + "=" * 60)
        print("AUTO-PAY POLICY CONFIGURATION")
        print("=" * 60)
        print("Set how your credit card bill should be paid automatically:")
        print("1. NONE - Manual payment only (default)")
        print("2. MINIMUM - Auto-pay minimum due amount")
        print("3. FULL - Auto-pay full outstanding balance")
        print("=" * 60)

        policy_choice = self.app.read_valid_choice(
            "Select auto-pay policy (1-3): ", ["1", "2", "3"]
        )
        policy_map = {"1": "NONE", "2": "MINIMUM", "3": "FULL"}
        auto_pay_policy = policy_map[policy_choice]
        self.card_service.update_auto_pay_policy(account.cards[-1], auto_pay_policy)

        if auto_pay_policy == "NONE":
            print("\n[OK] Auto-pay disabled. You'll pay manually each month.")
        elif auto_pay_policy == "MINIMUM":
            print(
                "\n[OK] Auto-pay enabled: Minimum due will be paid automatically from your account."
            )
        else:
            print(
                "\n[OK] Auto-pay enabled: Full outstanding balance will be paid automatically from your account."
            )

    def make_card_purchase(self, account: Account):
        """Make a purchase using a card"""
        if not account.cards:
            print("No cards available")
            return

        print("\n--- Make Card Purchase ---")
        account.list_cards()

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card:
            print("Card not found")
            return

        try:
            amount = float(input("Enter amount: ").strip())
            merchant = input("Merchant name: ").strip()
            category = (
                input(
                    "Category (Shopping/Dining/Travel/Entertainment/Bills/Other): "
                ).strip()
                or "Shopping"
            )

            account.make_card_purchase(card.card_id, amount, merchant, category)
            self.bank.save()

        except ValueError:
            print("Invalid amount")

    def pay_credit_card(self, account: Account):
        """Pay credit card bill with option to use reward points"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("No credit cards available")
            return

        print("\n--- Pay Credit Card Bill ---")

        for card in credit_cards:
            print(f"\nCard: **** **** **** {card.card_number[-4:]}")
            print(f"Outstanding: Rs. {card.credit_used:,.2f} INR")
            print(
                f"💎 Reward Points: {card.reward_points:.0f} (Value: Rs. {RewardPointsManager.calculate_points_value(card.reward_points):.2f})"
            )
            if card.outstanding_balance > 0:
                print(f"Bill Amount: Rs. {card.outstanding_balance:,.2f} INR")
                print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card or not isinstance(card, CreditCard):
            print("Credit card not found")
            return

        outstanding = card.credit_used if card.credit_used > 0 else 0

        if outstanding == 0:
            print("\n[SUCCESS] No outstanding balance!")
            return

        print(f"\n{'=' * 70}")
        print("PAYMENT OPTIONS")
        print(f"{'=' * 70}")
        print(f"Account Balance: Rs. {account.balance:,.2f} INR")
        print(f"Outstanding: Rs. {outstanding:,.2f} INR")
        print(
            f"💎 Reward Points: {card.reward_points:.0f} (Rs. {RewardPointsManager.calculate_points_value(card.reward_points):.2f})"
        )
        print(f"{'=' * 70}")

        # Check if rewards can be used
        can_use_rewards = (
            card.reward_points >= RewardPointsManager.MIN_REDEMPTION_POINTS
        )

        # Ask about reward points
        reward_points_to_use = 0
        if can_use_rewards:
            use_rewards = (
                input("\nUse reward points for payment? (yes/no): ").strip().lower()
            )

            if use_rewards in ["yes", "y"]:
                redemption_options = RewardPointsManager.get_redemption_options(
                    card, outstanding
                )

                print("\n💎 REWARD POINTS REDEMPTION")
                print(f"{'=' * 70}")
                print(f"Available: {redemption_options['available_points']:.0f} points")
                print(
                    f"Max Redeemable: {redemption_options['max_redeemable_points']:.0f} points (Rs. {redemption_options['max_redeemable_value']:.2f})"
                )
                print(f"Rate: 1 point = Rs. {RewardPointsManager.REDEMPTION_RATE}")

                # Show preset options if available
                if "presets" in redemption_options and redemption_options["presets"]:
                    print("\n🎯 QUICK OPTIONS:")
                    for idx, preset in enumerate(redemption_options["presets"], 1):
                        print(
                            f"  {idx}. {preset['label']}: {preset['points']:.0f} points → Rs. {preset['value']:.2f}"
                        )
                    print(f"  {len(redemption_options['presets']) + 1}. Custom amount")
                    print("  0. Skip (pay cash only)")

                    choice = input("\nSelect: ").strip()

                    try:
                        choice_num = int(choice)
                        if choice_num == 0:
                            reward_points_to_use = 0
                        elif 1 <= choice_num <= len(redemption_options["presets"]):
                            reward_points_to_use = redemption_options["presets"][
                                choice_num - 1
                            ]["points"]
                        elif choice_num == len(redemption_options["presets"]) + 1:
                            reward_points_to_use = float(
                                input(
                                    f"Enter points ({RewardPointsManager.MIN_REDEMPTION_POINTS}-{redemption_options['max_redeemable_points']:.0f}): "
                                )
                            )
                        else:
                            print("[FAIL] Invalid option")
                            return
                    except ValueError:
                        print("[FAIL] Invalid input")
                        return
                else:
                    try:
                        reward_points_to_use = float(
                            input(
                                f"Enter points to redeem (100-{redemption_options['max_redeemable_points']:.0f}): "
                            )
                        )
                    except ValueError:
                        print("[FAIL] Invalid input")
                        return

        # Calculate amounts
        reward_value = 0
        remaining_balance = outstanding

        if reward_points_to_use > 0:
            # Validate redemption
            can_redeem, reason = RewardPointsManager.can_redeem(
                card, reward_points_to_use
            )
            if not can_redeem:
                print(f"\n[FAIL] {reason}")
                return

            reward_value = RewardPointsManager.calculate_points_value(
                reward_points_to_use
            )
            remaining_balance = outstanding - reward_value

            print(
                f"\n💎 Redeeming: {reward_points_to_use:.0f} points → Rs. {reward_value:.2f}"
            )
            print(f"[MONEY] Remaining to pay: Rs. {remaining_balance:.2f}")

        # Get cash amount
        cash_amount = 0
        if remaining_balance > 0:
            print(f"\nAccount Balance: Rs. {account.balance:,.2f} INR")

            try:
                cash_input = input(
                    f"Enter cash amount to pay (0-{remaining_balance:.2f}): Rs. "
                ).strip()
                cash_amount = float(cash_input) if cash_input else 0

                if cash_amount < 0 or cash_amount > remaining_balance:
                    print("[FAIL] Invalid amount")
                    return
            except ValueError:
                print("[FAIL] Invalid amount")
                return

        # Validate total payment
        total_payment = cash_amount + reward_value
        if total_payment == 0:
            print("[FAIL] No payment amount entered")
            return

        # Process payment
        print(f"\n{'=' * 70}")
        print("PROCESSING PAYMENT...")
        print(f"{'=' * 70}")

        try:
            # Use the combined payment method
            success, message, txn_id = card.pay_bill_with_rewards(
                cash_amount, reward_points_to_use, account
            )

            if success:
                print("\n[SUCCESS] PAYMENT SUCCESSFUL!")
                print(f"{'=' * 70}")

                # Show breakdown
                if cash_amount > 0:
                    print(f"💵 Cash:           Rs. {cash_amount:>12,.2f}")
                if reward_value > 0:
                    print(
                        f"💎 Rewards:        Rs. {reward_value:>12,.2f} ({reward_points_to_use:.0f} pts)"
                    )
                print(f"{'─' * 70}")
                print(f"[STATS] Total:          Rs. {total_payment:>12,.2f}")
                print(f"{'=' * 70}")
                print(f"💳 New Balance:    Rs. {card.credit_used:>12,.2f}")
                print(f"💎 Remaining Pts:  {card.reward_points:>15,.0f}")
                print(f"{'=' * 70}")

                self.bank.save()
            else:
                print(f"\n[FAIL] Payment failed: {message}")

        except Exception as e:
            print(f"\n[FAIL] Error: {e}")

    def view_credit_statement(self, account: Account):
        """View credit card statement"""
        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("No credit cards available")
            return

        if len(credit_cards) == 1:
            account.show_credit_card_statement(credit_cards[0].card_id)
        else:
            print("\n--- Select Credit Card ---")
            for i, card in enumerate(credit_cards, 1):
                print(f"{i}. **** **** **** {card.card_number[-4:]}")

            try:
                choice = int(input("Enter choice: ").strip())
                if 1 <= choice <= len(credit_cards):
                    account.show_credit_card_statement(credit_cards[choice - 1].card_id)
                else:
                    print("Invalid choice")
            except ValueError:
                print("Invalid input")

    def block_card(self, account: Account):
        """Block a card"""
        if not account.cards:
            print("No cards available")
            return

        account.list_cards()
        card_id = input("\nEnter Card ID to block: ").strip()
        account.block_card(card_id)
        self.bank.save()

    def unblock_card(self, account: Account):
        """Unblock a card"""
        if not account.cards:
            print("No cards available")
            return

        account.list_cards()
        card_id = input("\nEnter Card ID to unblock: ").strip()
        account.unblock_card(card_id)
        self.bank.save()

    def set_card_pin(self, account: Account):
        """Set or change the PIN for a card"""
        if not account.cards:
            print("\n[FAIL] No cards found for this account.")
            return

        print("\n" + "=" * 50)
        print("SET/CHANGE CARD PIN")
        print("=" * 50)
        
        # List all cards
        account.list_cards()
        
        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)
        
        if not card:
            print("[FAIL] Card not found.")
            return
            
        print(f"\nSetting PIN for: {card.network} **** **** **** {card.card_number[-4:]}")
        
        new_pin = input("Enter new 4-digit PIN: ").strip()
        if not new_pin.isdigit() or len(new_pin) != 4:
            print("[FAIL] Invalid PIN. Must be exactly 4 digits.")
            return
            
        confirm_pin = input("Confirm new 4-digit PIN: ").strip()
        if new_pin != confirm_pin:
            print("[FAIL] PINs do not match.")
            return
            
        if card.set_pin(new_pin):
            print(f"\n[SUCCESS] PIN set successfully for card ending in {card.card_number[-4:]}!")
            self.bank.save()
        else:
            print("[FAIL] Failed to set PIN.")


    # ========== RECURRING BILLS / CARD BILLS ==========


    def add_credit_card_bill(self, account: Account):
        """Special handling for credit card bills"""
        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards linked to this account.")
            print("Add a credit card first from Card Management menu.")
            input("\nPress Enter to continue...")
            return

        print("\n" + "=" * 60)
        print("CREDIT CARD BILL SETUP")
        print("=" * 60)
        print("0. Manual Entry (Custom Amount)")

        for idx, card in enumerate(credit_cards, 1):
            current_bill = card.current_balance

            print(
                f"{idx}. {card.network} ****{card.card_number[-4:]} "
                f"(Current Balance: Rs. {current_bill:,.2f})"
            )

        card_choice = input(f"\nSelect option (0-{len(credit_cards)}): ").strip()

        if card_choice == "0":
            # Manual entry
            bill_name = input("Bill name: ") or "Credit Card Bill (Manual)"
            amount = float(input("Enter bill amount: Rs. "))
            linked_card_id = None
            is_dynamic = False

        elif card_choice.isdigit() and 1 <= int(card_choice) <= len(credit_cards):
            selected_card = credit_cards[int(card_choice) - 1]

            bill_name = f"{selected_card.network} Credit Card"
            amount = selected_card.current_balance
            linked_card_id = selected_card.card_id
            is_dynamic = True

            print(
                f"\n[SUCCESS] Linked to {selected_card.network} ****{selected_card.card_number[-4:]}"
            )
            print("💡 Bill amount will auto-update from card statement")

        else:
            print("[FAIL] Invalid choice")
            input("\nPress Enter...")
            return

        category = "Finance"
        frequency = "MONTHLY"
        day_of_month = int(input("Due day of month (1-28): "))

        # Credit card bills are ALWAYS paid from bank account
        payment_method = PaymentMethod.BANK_ACCOUNT
        payment_card_id = None

        print("\n💡 Credit card bills are automatically paid from your bank account.")

        auto_debit_choice = input("\nEnable auto-pay? (y/n): ").strip().lower()
        auto_debit = auto_debit_choice == "y"

        # Create bill
        bill = RecurringBill(
            name=bill_name,
            category=category,
            base_amount=amount,
            frequency=frequency,
            day_of_month=day_of_month,
            auto_debit=auto_debit,
            linked_card_id=linked_card_id,
            is_dynamic=is_dynamic,
            payment_method=payment_method,
            payment_card_id=payment_card_id,
        )

        account.add_recurring_bill(bill)
        self.bank.save()

        print("\n" + "=" * 60)
        print("[SUCCESS] CREDIT CARD BILL ADDED")
        print("=" * 60)
        print(f"Bill: {bill.name}")
        print(f"Amount: Rs. {bill.base_amount:,.2f}")
        print(f"Due Day: {bill.day_of_month}")
        print(f"Auto-pay: {'[SUCCESS] Enabled' if bill.auto_debit else '[FAIL] Disabled'}")
        if is_dynamic:
            print("[STATS] Amount will auto-update from card")
        print("=" * 60)

        input("\nPress Enter to continue...")

    def view_card_details(self, account: Account):
        """View detailed information about a specific card"""
        if not account.cards:
            print("No cards available")
            return

        print("\n--- View Card Details ---")
        account.list_cards()

        card_id = input("\nEnter Card ID or last 4 digits: ").strip()
        card = account.get_card_by_id(card_id) or account.get_card_by_number(card_id)

        if not card:
            print("Card not found")
            return

        print("\n" + "=" * 60)
        print("CARD DETAILS")
        print("=" * 60)
        print(f"Card Type: {card.card_type}")
        print(f"Card Network: {card.network}")
        print(f"Card Number: **** **** **** {card.card_number[-4:]}")
        print(
            f"Full Card Number: {card.card_number}"
        )  # Show full number (in real banking, never show this!)
        print(f"CVV: {card.cvv}")  # Show CVV (in real banking, never show this!)
        print(f"Card ID: {card.card_id}")
        print(f"Expiry Date: {card.expiry_date.strftime('%m/%Y')}")
        print(
            f"Status: {'Blocked' if card.blocked else ('Expired' if card.is_expired() else 'Active')}"
        )
        print(f"Daily Limit: Rs. {card.daily_limit:,.2f} INR")

        if isinstance(card, CreditCard):
            print("\nCredit Card Specific Details:")
            print(f"Credit Limit: Rs. {card.credit_limit:,.2f} INR")
            print(f"Credit Used: Rs. {card.credit_used:,.2f} INR")
            print(f"Available Credit: Rs. {card.available_credit():,.2f} INR")
            print(f"Credit Utilization: {card.credit_utilization():.1f}%")
            print(f"Billing Day: {card.billing_day} of each month")
            print(f"Interest Rate: {card.interest_rate * 100:.1f}% per annum")
            reward_points = getattr(card, "reward_points", 0.0)
            print(f"Reward Points: {reward_points:.0f}")

            if card.outstanding_balance > 0:
                print("\nBilling Information:")
                print(f"Outstanding Balance: Rs. {card.outstanding_balance:,.2f} INR")
                print(f"Minimum Due: Rs. {card.minimum_due:,.2f} INR")
                if card.due_date:

                    days_remaining = (card.due_date - BankClock.today()).days
                    print(
                        f"Due Date: {card.due_date.strftime('%d-%m-%Y')} ({days_remaining} days)"
                    )

        print("=" * 60)

        # Card validation
        is_valid = Card.validate_card_number(card.card_number)
        detected_network = Card.get_card_network(card.card_number)
        print(
            f"\n[OK] Card Number Validation: {'Valid' if is_valid else 'Invalid'} (Luhn Check)"
        )
        print(f"[OK] Detected Network from Number: {detected_network}")
        print("=" * 60)

    def manage_card_auto_pay(self, account: Account):
        """Manage auto-pay settings for credit cards"""

        credit_cards = [c for c in account.cards if isinstance(c, CreditCard)]

        if not credit_cards:
            print("\n[FAIL] No credit cards available")
            return

        print("\n" + "=" * 60)
        print("CREDIT CARD AUTO-PAY MANAGEMENT")
        print("=" * 60)
        print("\nYour Credit Cards:")

        for idx, card in enumerate(credit_cards, 1):
            policy = getattr(card, "auto_pay_policy", "NONE")
            policy_display = {
                "NONE": "[FAIL] Manual Payment",
                "MINIMUM": "[INFO] Auto-pay Minimum Due",
                "FULL": "[SUCCESS] Auto-pay Full Balance",
            }
            print(f"{idx}. **** **** **** {card.card_number[-4:]} ({card.network})")
            print(f"   Current: {policy_display.get(policy, 'Unknown')}")

        if len(credit_cards) == 1:
            selected_card = credit_cards[0]
        else:
            choice = input(
                f"\nSelect card to configure (1-{len(credit_cards)}): "
            ).strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(credit_cards):
                    selected_card = credit_cards[idx]
                else:
                    print("Invalid selection")
                    return
            except ValueError:
                print("Invalid input")
                return

        print("\n" + "=" * 60)
        print("AUTO-PAY POLICY OPTIONS")
        print("=" * 60)
        print("1. NONE - Manual payment only")
        print("   └─ You'll pay manually each month")
        print("2. MINIMUM - Auto-pay minimum due")
        print(
            "   └─ Minimum due automatically paid from your account when bill is generated"
        )
        print("3. FULL - Auto-pay full balance")
        print("   └─ Complete outstanding balance automatically paid from your account")
        print("=" * 60)

        policy_choice = self.app.read_valid_choice("Select policy (1-3): ", ["1", "2", "3"])
        policy_map = {"1": "NONE", "2": "MINIMUM", "3": "FULL"}
        new_policy = policy_map[policy_choice]

        old_policy = getattr(selected_card, "auto_pay_policy", "NONE")
        if old_policy == new_policy:
            print(f"\n[WARN]  Policy is already set to {new_policy}")
            return

        selected_card.auto_pay_policy = new_policy
        self.bank.save()

        print("\n" + "=" * 60)
        policy_display = {
            "NONE": "[FAIL] Manual Payment",
            "MINIMUM": "[INFO] Auto-pay Minimum Due",
            "FULL": "[SUCCESS] Auto-pay Full Balance",
        }

        print("[SUCCESS] AUTO-PAY POLICY UPDATED")
        print(
            f"Card: **** **** **** {selected_card.card_number[-4:]} ({selected_card.network})"
        )
        print(f"New Policy: {policy_display[new_policy]}")
        print("=" * 60)

        if new_policy == "NONE":
            print("\nℹ️  You'll need to pay your credit card bill manually each month.")
        elif new_policy == "MINIMUM":
            print("\nℹ️  Minimum due will be automatically deducted from your account")
            print("   when your monthly bill is generated (on billing day).")
            print("   Make sure you have sufficient balance in your account.")
        else:  # FULL
            print(
                "\nℹ️  Your complete outstanding balance will be automatically deducted"
            )
            print("   from your account when the bill is generated.")
            print("   This helps avoid interest charges and late payment fees.")
        print("=" * 60)

    def view_debit_card_transactions(self, account: Account):
        """View transactions by specific debit card"""

        # Load transactions if needed
        account._load_transactions_if_needed()

        debit_cards = [c for c in account.cards if isinstance(c, DebitCard)]

        if not debit_cards:
            print("\n[FAIL] No debit cards found")
            return

        print("\n--- Select Debit Card ---")
        print("0. All Debit Cards")
        for idx, card in enumerate(debit_cards, 1):
            print(f"{idx}. {card.network} **** **** **** {card.card_number[-4:]}")

        choice_input = input("\nEnter choice: ").strip()

        # Get limit preference
        limit = self._get_transaction_limit()

        if choice_input == "0":
            # Show all debit card transactions
            account.show_transactions(limit=limit, transaction_type_filter="DEBIT_CARD")
        else:
            # Find specific card
            selected_card = None
            if choice_input.isdigit() and 1 <= int(choice_input) <= len(debit_cards):
                selected_card = debit_cards[int(choice_input) - 1]
            else:
                for card in debit_cards:
                    if card.card_number[-4:] == choice_input:
                        selected_card = card
                        break

            if not selected_card:
                print("[FAIL] Card not found")
                return

            print(
                f"\n💳 Transactions for debit card ending in {selected_card.card_number[-4:]}:"
            )
            account.show_transactions(
                limit=limit, card_filter=selected_card.card_number[-4:]
            )

    def view_credit_card_transactions(self, account: Account):
        """View credit card payment transactions"""
        # Load transactions if needed
        account._load_transactions_if_needed()

        limit = self._get_transaction_limit()
        print("\n💳 Credit Card Payments:")
        account.show_transactions(
            limit=limit, transaction_type_filter="CREDIT_CARD_PAYMENT"
        )

    def manage_recurring_bills(self, account: Account):
        """Manage recurring bills"""
        managing = True
        while managing:
            print("\n=== Recurring Bills Management ===")
            print("1. View Recurring Bills")
            print("2. Add Recurring Bill")
            print("3. Remove Recurring Bill")
            print("4. View Rewards Dashboard 💎")
            print("5. Back to Main Menu")

            choice = self.app.read_valid_choice("Enter choice: ", ["1", "2", "3", "4", "5"])

            if choice == "1":
                self.view_recurring_bills(account)
            elif choice == "2":
                self.add_recurring_bill(account)
            elif choice == "3":
                self.remove_recurring_bill(account)
            elif choice == "4":
                self.show_rewards_dashboard(account)
            elif choice == "5":
                managing = False

    def view_recurring_bills(self, account: Account):
        """View recurring bills with payment methods and rewards"""
        if not account.recurring_bills:
            print("\n[INFO] No recurring bills found.")
            input("\nPress Enter to continue...")
            return

        # Update dynamic bills
        updated = account.update_dynamic_bills()
        if updated:
            print("\n💳 Dynamic Bills Updated:")
            for u in updated:
                print(f"   {u['bill_name']}: Rs. {u['old_amount']:,.2f} → Rs. {u['new_amount']:,.2f}")

        # Summary calculations
        total_monthly_rewards = 0
        total_annual_rewards = 0
        bills_on_card = []

        for bill in account.recurring_bills:
            if bill.payment_method == PaymentMethod.CREDIT_CARD and bill.payment_card_id:
                card = account.get_card_by_id(bill.payment_card_id)
                if card and isinstance(card, CreditCard):
                    rewards = bill.base_amount * card.reward_rate
                    if bill.frequency == "MONTHLY":
                        total_monthly_rewards += rewards
                        total_annual_rewards += rewards * 12
                        bills_on_card.append((bill.name, rewards, card.network))
                    elif bill.frequency == "QUARTERLY":
                        total_annual_rewards += rewards * 4
                    elif bill.frequency == "YEARLY":
                        total_annual_rewards += rewards

        print("\n" + "=" * 130)
        print(f"{'RECURRING BILLS':^130}")
        print("=" * 130)
        print(f"\n{'Name':<35} {'Amount':<15} {'Freq':<10} {'Due Day':<10} {'Payment Method':<40} {'Rewards'}")
        print("-" * 130)

        for bill in account.recurring_bills:
            payment_desc = bill.get_payment_description(account)
            rewards_str = ""
            if bill.payment_method == PaymentMethod.CREDIT_CARD and bill.payment_card_id:
                card = account.get_card_by_id(bill.payment_card_id)
                if card:
                    rewards = int(bill.base_amount * card.reward_rate)
                    rewards_str = f"💎 {rewards} pts"

            auto_marker = " 🤖" if bill.auto_debit else ""
            dynamic_marker = " [STATS]" if bill.is_dynamic else ""

            print(f"{bill.name:<35} Rs. {bill.base_amount:<12,.2f} {bill.frequency:<10} "
                  f"{bill.day_of_month:<10} {payment_desc:<40} {rewards_str}{auto_marker}{dynamic_marker}")

        print("=" * 130)
        input("\nPress Enter to continue...")

    def show_rewards_dashboard(self, account: Account):
        """Show rewards earned from credit card purchases"""
        account._load_transactions_if_needed()
        print("\n" + "=" * 80)
        print(f"{'💎 REWARDS DASHBOARD':^80}")
        print("=" * 80)

        total_points = 0
        for txn in account.transactions:
            if txn.type in ["CREDIT_CARD_PURCHASE", "CREDIT_CARD_BILL_PAYMENT"]:
                total_points += self.get_reward_points(txn.metadata)

        print(f"\nLifetime Rewards Earned: {total_points} points")
        print(f"Approximate Value: Rs. {total_points:,.2f}")
        print("=" * 80)
        input("\nPress Enter to continue...")

    def add_recurring_bill(self, account: Account):
        """Add a recurring bill"""
        print("\n=== Add Recurring Bill ===")
        common_bills = RecurringBillFactory.get_common_bills()
        for idx, (name, cat, min_amt, max_amt, freq) in enumerate(common_bills, 1):
            print(f"{idx}. {name} ({cat}) - Rs. {min_amt:.2f}-Rs. {max_amt:.2f} [{freq}]")
        print(f"{len(common_bills) + 1}. Custom Bill")

        template_choice = self.app.read_valid_choice("Select: ", [str(i) for i in range(1, len(common_bills) + 2)])
        
        if int(template_choice) <= len(common_bills):
            name, cat, min_amt, max_amt, freq = common_bills[int(template_choice) - 1]
            amount = float(input(f"Enter amount (Rs. {min_amt:.2f}-Rs. {max_amt:.2f}): "))
            frequency = freq
        else:
            name = input("Name: ").strip()
            cat = "Custom"
            amount = self.app.read_positive_double("Amount (Rs.): ")
            frequency = "MONTHLY"

        day = int(input("Due day (1-28): "))
        
        # Payment method
        print("\n1. Bank Account\n2. Credit Card")
        pay_choice = input("Select: ").strip()
        method = PaymentMethod.BANK_ACCOUNT
        card_id = None
        
        if pay_choice == "2":
            cards = [c for c in account.cards if isinstance(c, CreditCard)]
            if cards:
                for idx, c in enumerate(cards, 1):
                    print(f"{idx}. {c.network} ****{c.card_number[-4:]}")
                c_choice = input("Select card: ").strip()
                if c_choice.isdigit() and 1 <= int(c_choice) <= len(cards):
                    method = PaymentMethod.CREDIT_CARD
                    card_id = cards[int(c_choice) - 1].card_id

        bill = RecurringBillFactory.create_custom_bill(name, cat, amount, frequency, day, True, method, card_id)
        account.add_recurring_bill(bill)
        self.bank.save()
        print("[SUCCESS] Bill added.")

    def remove_recurring_bill(self, account: Account):
        """Remove a recurring bill"""
        if not account.recurring_bills:
            print("[INFO] No bills found.")
            return
        for idx, b in enumerate(account.recurring_bills, 1):
            print(f"{idx}. {b.name} (Rs. {b.base_amount:,.2f})")
        choice = input("Select to remove: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(account.recurring_bills):
            bill = account.recurring_bills.pop(int(choice) - 1)
            self.bank.save()
            print(f"[SUCCESS] {bill.name} removed.")

    def get_reward_points(self, metadata):
        """Extract reward points from metadata"""
        parsed = self._parse_metadata(metadata)
        try:
            return int(parsed.get("reward_points_earned", 0) or parsed.get("rewardPoints", 0) or 0)
        except (ValueError, TypeError):
            return 0

    def _parse_metadata(self, metadata) -> dict:
        """Parse metadata into dict"""
        if not metadata: return {}
        if isinstance(metadata, dict): return metadata
        if isinstance(metadata, str):
            try:
                import json
                return json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                # Handle semicolon-separated
                res = {}
                for pair in metadata.split(";"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        res[k.strip()] = v.strip()
                return res
        return {}
