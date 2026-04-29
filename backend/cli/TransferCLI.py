from datetime import datetime
from typing import List, Optional

from ..Customer import Customer
from ..Account import Account
from ..Logger import BankLogger
from ..InternationalTransfer import InternationalTransfer, InternationalBankRegistry
from ..Beneficiary import IFSCValidator
from ..Transaction import Transaction
from ..DataStore import DataStore
import random


class TransferCLI:
    def __init__(self, bank, app):
        self.bank = bank
        self.app = app
        self.transfer_service = app.transfer_service
        self.logger = BankLogger.get_logger("TransferCLI")

    def transfer_funds(self, customer: Customer, account: Account, accounts: List[Account]):
        """Handle fund transfer (Inter-Account, NEFT, RTGS, International)"""
        if len(accounts) > 1:
            print("""
    Choose transfer type:
    1  Inter-Account (Between your own accounts)
    2  NEFT (Up to Rs. 1,99,999.99)
    3  RTGS (From Rs. 2,00,000.00)
    4  International Transfer (SWIFT/Wire)
                """)
            transfer_choice = self.app.read_valid_choice(
                "Enter choice (1-4): ", ["1", "2", "3", "4"]
            )

            if transfer_choice == "1":
                self.inter_account_transfer(account, accounts)
            elif transfer_choice == "2":
                self.external_transfer(customer, account, "NEFT")
            elif transfer_choice == "3":
                self.external_transfer(customer, account, "RTGS")
            elif transfer_choice == "4":
                self.international_transfer(account)  # NEW
        else:
            print("""
    Choose transfer mode:
    1  NEFT (Up to Rs. 1,99,999.99)
    2  RTGS (From Rs. 2,00,000.00)
    3  International Transfer (SWIFT/Wire)
            """)
            transfer_choice = self.app.read_valid_choice(
                "Enter choice (1-3): ", ["1", "2", "3"]
            )

            if transfer_choice == "1":
                self.external_transfer(customer, account, "NEFT")
            elif transfer_choice == "2":
                self.external_transfer(customer, account, "RTGS")
            elif transfer_choice == "3":
                self.international_transfer(account)  # NEW

    def inter_account_transfer(self, account: Account, accounts: List[Account]):
        """Handle inter-account transfer"""
        print("\nYour other accounts:")
        other_accounts = [acc for acc in accounts if acc != account]

        for idx, acc in enumerate(other_accounts, 1):
            print(
                f"{idx}. {acc.account_type} - {acc.account_number} (Balance: Rs. {acc.balance:.2f} INR)"
            )

        choice = self.app.read_valid_choice(
            f"Select recipient account (1-{len(other_accounts)}): ",
            [str(i) for i in range(1, len(other_accounts) + 1)],
        )
        recipient = other_accounts[int(choice) - 1]
        amount = self.app.read_positive_double("Enter amount to transfer: Rs. ")
        account.transfer(recipient, amount, "INTER_ACCOUNT")
        self.bank.save()
        self.logger.info(f"Transferred Rs. {amount:,.2f} from {account.account_number} to {recipient.account_number} (Internal)")

    def external_transfer(self, customer: Customer, account: Account, mode: str):
        """Handle external transfer (NEFT/RTGS)"""
        beneficiaries = customer.beneficiary_manager.list_all()
        
        print("\n" + "=" * 50)
        print(f"EXTERNAL TRANSFER ({mode})")
        print("=" * 50)
        
        if beneficiaries:
            print("\n1. Transfer to Saved Beneficiary")
            print("2. Transfer to New Account")
            choice = input("Enter choice (1-2) [default: 1]: ").strip() or "1"
        else:
            print("\n[INFO] No saved beneficiaries found. Proceeding with manual entry.")
            choice = "2"
            
        if choice == "1":
            print("\n--- Saved Beneficiaries ---")
            recent = customer.beneficiary_manager.get_recent(3)
            frequent = customer.beneficiary_manager.get_frequent(3)
            
            # Print recent/frequent suggestions if available
            if recent:
                print("\nRecently Used:")
                for b in recent:
                    print(f"  - {b.beneficiary_name} ({b.account_number})")
                    
            print("\nAll Beneficiaries:")
            for idx, b in enumerate(beneficiaries, 1):
                print(f"{idx}. {b.beneficiary_name} - {b.account_number} ({b.bank_name})")
                
            idx_choice = input("\nSelect beneficiary number (or 0 to cancel): ").strip()
            if idx_choice.isdigit() and 1 <= int(idx_choice) <= len(beneficiaries):
                b = beneficiaries[int(idx_choice) - 1]
                amount = self.app.read_positive_double(f"Enter amount to transfer to {b.beneficiary_name}: Rs. ")
                success = account.pay_to_beneficiary(b.beneficiary_id, amount, mode, customer.beneficiary_manager)
                if success:
                    self.bank.save()
            return
            
        # Proceed with manual entry (Choice 2)
        while True:
            recipient_acc_num = input("\nEnter recipient's account number: ").strip()
            if not recipient_acc_num:
                print("Account number cannot be empty. Please try again.")
                continue

            recipient = self.bank.find_account_by_number(recipient_acc_num)
            if recipient:
                if recipient.account_number == account.account_number:
                    print("Cannot transfer to your own account. Please enter a different account number.")
                    continue
                print(f"Recipient Name: {recipient.first_name} {recipient.last_name} (Internal Account)")
                amount = self.app.read_positive_double("Enter amount to transfer: Rs. ")
                account.transfer(recipient, amount, mode)
                self.bank.save()
                break
            else:
                if not recipient_acc_num.isdigit() or not (9 <= len(recipient_acc_num) <= 18):
                    print("[ERROR] External account numbers must be numeric and between 9 and 18 digits. Please try again.")
                    continue
                    
                print("\n[EXTERNAL ACCOUNT DETECTED]")
                recipient_name = input("Enter recipient's name: ").strip()
                

                bank_name = ""
                ifsc = ""
                while True:
                    ifsc = input("Enter recipient's IFSC Code (MANDATORY): ").strip().upper()
                    if not ifsc:
                        print("[ERROR] IFSC code is mandatory for external transfers.")
                        continue
                    
                    if not IFSCValidator.validate_format(ifsc):
                        print("Invalid IFSC format. Expected 4 letters, '0', 6 alphanumeric characters.")
                        continue
                        
                    print(f"Validating IFSC Code '{ifsc}' via Razorpay API...")
                    bank_details = IFSCValidator.get_bank_details(ifsc)
                    
                    if bank_details:
                        bank_name = bank_details['bank_name']
                        branch = bank_details.get('branch', '')
                        swift = bank_details.get('swift', '')
                        if swift:
                            print(f"[OK] Bank Found: {bank_name}, {branch} (SWIFT: {swift})")
                        else:
                            print(f"[OK] Bank Found: {bank_name}, {branch}")
                        break

                    else:
                        print("[WARN] Could not validate IFSC via API.")
                        bank_name = input("Enter recipient's bank name manually: ").strip()
                        if not bank_name:
                            print("[ERROR] Bank name is required if IFSC validation fails.")
                            continue
                        break
                
                amount = self.app.read_positive_double("Enter amount to transfer: Rs. ")
                
                # Check minor account limits
                if account.is_minor_account:
                    today_transactions = account.get_today_transactions()
                    if today_transactions + amount > account._minor_daily_transaction_limit:
                        remaining = account._minor_daily_transaction_limit - today_transactions
                        print("Transfer amount exceeds daily transaction limit for minor accounts.")
                        print(f"Remaining limit: Rs. {remaining:.2f} INR")
                        continue
                
                # Check operational balance
                if account.balance - amount < account._min_operational_balance:
                    print(f"Insufficient funds. Must keep at least Rs. {account._min_operational_balance:.2f} INR.")
                    continue
                

                
                account.balance -= amount
                cheque_id = f"CHQ{random.randint(1000000000, 9999999999)}"
                
                txn = Transaction(
                    type=f"{mode}_SENT",
                    amount=amount,
                    resulting_balance=account.balance,
                    cheque_id=cheque_id,
                )
                account.transactions.append(txn)
                
                metadata = f"requestedMode={mode};recipientName={recipient_name};recipientAccount={recipient_acc_num};recipientBank={bank_name}"
                if account.is_minor_account:
                    metadata += ";minorAccount=true"
                    
                DataStore.append_activity(
                    timestamp=txn.timestamp,
                    username=account.username,
                    account_number=account.account_number,
                    action=f"{mode}_SENT_EXTERNAL",
                    amount=amount,
                    resulting_balance=account.balance,
                    txn_id=txn.id,
                    cheque_id=cheque_id,
                    metadata=metadata,
                )
                
                print(f"{mode} payment to {recipient_name} at {bank_name} successful.")
                print(f"Sent: Rs. {amount:.2f} INR | Transaction ID: {txn.id}")
                print(f"Cheque ID: {cheque_id}")
                
                account._check_and_apply_amb_fee()
                self.bank.save()
                
                # Generate receipt for external transfer
                success, path = self.transfer_service.generate_transfer_receipt(
                    account, recipient_name, recipient_acc_num, bank_name, ifsc, amount, mode, txn.id
                )
                if success:
                    print(f"\n[SUCCESS] Transaction receipt generated: {path}")
                    print("The receipt has been saved to the 'receipts' folder.")
                else:
                    print(f"[WARN] Could not generate PDF receipt: {path}")
                break





    def international_transfer(self, account: Account):
        """Handle international wire transfer"""

        print("\n" + "=" * 70)
        print("INTERNATIONAL WIRE TRANSFER (SWIFT)")
        print("=" * 70)

        # Show current limits
        used_today = InternationalTransfer.get_today_international_limit_used(account)
        remaining = InternationalTransfer.DAILY_LIMIT_INR - used_today

        print(
            f"\nDaily International Transfer Limit: Rs. {InternationalTransfer.DAILY_LIMIT_INR:,.2f}"
        )
        print(f"Used Today: Rs. {used_today:,.2f}")
        print(f"Remaining: Rs. {remaining:,.2f}")

        # Option to view sample accounts
        view_samples = (
            input("\nView sample international accounts? (yes/no): ").strip().lower()
        )

        if view_samples in ["yes", "y"]:
            print("\n[INFO] SAMPLE INTERNATIONAL ACCOUNTS")
            print("=" * 120)
            print(f"{'Holder':<30} {'Country':<12} {'Bank':<35} {'Account':<35}")
            print("-" * 120)

            for acc_info in self.bank.international_registry.list_sample_accounts()[
                :10
            ]:
                print(
                    f"{acc_info['holder']:<30} {acc_info['country']:<12} "
                    f"{acc_info['bank']:<35} {acc_info['account']:<35}"
                )

            print("=" * 120)
            print(
                "\n💡 You can transfer to any of these accounts, or enter custom details.\n"
            )

        print("\n" + "-" * 70)
        print("BENEFICIARY DETAILS")
        print("-" * 70)

        recipient_name = input("Recipient Name: ").strip()
        recipient_account = input("Recipient Account/IBAN: ").strip()

        # Check if account exists in registry
        foreign_account = self.bank.international_registry.find_account_by_number(
            recipient_account
        )

        if foreign_account:
            print("\n[OK] Found recipient account:")
            print(f"  Holder: {foreign_account.account_holder}")
            print(f"  Bank: {foreign_account.bank_name}")
            print(f"  Country: {foreign_account.country}")
            print(f"  Currency: {foreign_account.currency}")

            recipient_bank = foreign_account.bank_name
            swift_code = foreign_account.swift_code
            recipient_country = foreign_account.country
            currency = foreign_account.currency
        else:
            print("\n[WARN]  Account not found in registry. Please enter details manually.")
            recipient_bank = input("Recipient Bank Name: ").strip()
            swift_code = input("SWIFT/BIC Code: ").strip().upper()

            print("\nSupported Countries:")
            countries = [
                "USA",
                "UK",
                "UAE",
                "Singapore",
                "Australia",
                "Canada",
                "Germany",
                "France",
                "Japan",
            ]
            for idx, country in enumerate(countries, 1):
                print(f"{idx}. {country}")

            country_choice = input("\nSelect country (1-9) or type name: ").strip()
            if country_choice.isdigit() and 1 <= int(country_choice) <= len(countries):
                recipient_country = countries[int(country_choice) - 1]
            else:
                recipient_country = country_choice

            print("\nSupported Currencies:")
            currencies = list(InternationalTransfer.EXCHANGE_RATES.keys())
            for idx, (curr, rate) in enumerate(
                InternationalTransfer.EXCHANGE_RATES.items(), 1
            ):
                print(f"{idx}. {curr} (1 {curr} = Rs. {rate:,.2f})")

            curr_choice = (
                input(f"\nSelect currency (1-{len(currencies)}) or type code: ")
                .strip()
                .upper()
            )
            if curr_choice.isdigit() and 1 <= int(curr_choice) <= len(currencies):
                currency = currencies[int(curr_choice) - 1]
            elif curr_choice in currencies:
                currency = curr_choice
            else:
                print("Invalid currency")
                return

        recipient_address = input("Recipient Address (optional): ").strip() or None

        print("\n" + "-" * 70)
        print("TRANSFER AMOUNT")
        print("-" * 70)

        try:
            amount_foreign = float(input(f"\nEnter amount in {currency}: "))
            if amount_foreign <= 0:
                print("Amount must be positive")
                return
        except ValueError:
            print("Invalid amount")
            return

        # Show conversion preview
        amount_inr, rate = InternationalTransfer.convert_currency(
            amount_foreign, currency, "INR"
        )
        charges = InternationalTransfer.calculate_swift_charges(amount_inr)
        total = amount_inr + charges

        print("\n" + "-" * 70)
        print("TRANSFER SUMMARY")
        print("-" * 70)
        print(f"Amount to Send: {amount_foreign:,.2f} {currency}")
        print(f"Exchange Rate: 1 {currency} = Rs. {rate:,.2f}")
        print(f"Equivalent INR: Rs. {amount_inr:,.2f}")
        print(f"SWIFT Charges: Rs. {charges:,.2f}")
        print(f"Total Debit: Rs. {total:,.2f}")
        print(
            f"\nExpected Arrival: {InternationalTransfer.PROCESSING_DAYS} business days"
        )
        print("-" * 70)

        # Purpose of remittance
        print("\nPurpose of Remittance:")
        purposes = [
            "Family Maintenance",
            "Education",
            "Medical Treatment",
            "Business Payment",
            "Investment",
            "Gift",
            "Other",
        ]
        for idx, purpose in enumerate(purposes, 1):
            print(f"{idx}. {purpose}")

        purpose_choice = input("\nSelect purpose (1-7): ").strip()
        if purpose_choice.isdigit() and 1 <= int(purpose_choice) <= len(purposes):
            purpose = purposes[int(purpose_choice) - 1]
        else:
            purpose = input("Enter purpose: ").strip()

        # Confirm
        print("\n" + "=" * 70)
        confirm = input("Confirm international transfer? (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("Transfer cancelled")
            return

        # Initiate transfer
        success, message, swift_ref = (
            InternationalTransfer.initiate_international_transfer(
                account=account,
                recipient_name=recipient_name,
                recipient_account=recipient_account,
                recipient_bank_name=recipient_bank,
                swift_code=swift_code,
                recipient_country=recipient_country,
                amount_to_send=amount_foreign,
                currency=currency,
                purpose=purpose,
                recipient_address=recipient_address,
                registry=self.bank.international_registry,
            )
        )

        if success:
            print("\n" + "=" * 70)
            print("[SUCCESS] TRANSFER SUCCESSFUL")
            print("=" * 70)
            print(message)

            if foreign_account:
                # Load transactions if needed
                foreign_account._load_transactions_if_needed()

                print("\n[MONEY] Foreign account credited successfully")
                print(
                    f"   New balance: {foreign_account.balance:,.2f} {foreign_account.currency}"
                )

                # Show last transaction
                if foreign_account.transactions:
                    last_txn = foreign_account.transactions[-1]
                    print("\n📝 Transaction recorded:")
                    print(
                        f"   Amount: +{last_txn['amount']:,.2f} {foreign_account.currency}"
                    )
                    print(f"   From: {last_txn['from']}")
                    print(f"   SWIFT Ref: {last_txn['swift_ref']}")

            self.bank.save()

    def track_swift_transfer_menu(self):
        """Track international SWIFT transfer"""

        swift_ref = input("\nEnter SWIFT Reference Number: ").strip()

        result = InternationalTransfer.track_swift_transfer(swift_ref, self.bank)

        if result:
            print("\n" + "=" * 80)
            print("SWIFT TRANSFER TRACKING")
            print("=" * 80)
            print(f"\nSWIFT Reference: {result['swift_reference']}")
            print(f"Status: {result['status']}")
            print(f"\nSender: {result['sender_name']} ({result['sender_account']})")
            print(f"Recipient: {result['recipient_name']}")
            print(f"Recipient Account: {result['recipient_account']}")
            print(f"Recipient Bank: {result['recipient_bank']}")
            print(f"SWIFT Code: {result['swift_code']}")
            print(f"Country: {result['country']}")
            print(f"\nAmount: {result['amount']:,.2f} {result['currency']}")
            print(
                f"Exchange Rate: 1 {result['currency']} = Rs. {result['exchange_rate']:,.2f}"
            )
            print(f"Total Debited: Rs. {result['total_debited_inr']:,.2f}")
            print(f"SWIFT Charges: Rs. {result['charges']:,.2f}")
            print(f"\nPurpose: {result['purpose']}")
            print(f"Initiated: {result['initiated_on']}")
            print(f"Expected Arrival: {result['expected_arrival']}")
            print(f"Transaction ID: {result['transaction_id']}")
            print("=" * 80)
        else:
            print(f"\n[FAIL] SWIFT transfer with reference '{swift_ref}' not found")

    def view_international_accounts_menu(self):
        """View international accounts registry"""
        while True:
            print("\n" + "=" * 70)
            print("INTERNATIONAL ACCOUNTS REGISTRY")
            print("=" * 70)
            print("1. View Sample Accounts")
            print("2. View Accounts by Country")
            print("3. Search Account by Number")
            print("4. View Registry Statistics")
            print("5. Back to Main Menu")
            print("=" * 70)

            choice = input("\nEnter choice: ").strip()

            if choice == "1":
                self.view_sample_international_accounts()
            elif choice == "2":
                self.view_accounts_by_country()
            elif choice == "3":
                self.search_international_account()
            elif choice == "4":
                self.view_registry_statistics()
            elif choice == "5":
                break

    def view_sample_international_accounts(self):
        """View sample international accounts"""
        accounts = self.bank.international_registry.list_sample_accounts()

        print("\n" + "=" * 130)
        print(
            f"{'Holder':<30} {'Country':<12} {'Bank':<35} {'Account':<35} {'Balance':<18}"
        )
        print("-" * 130)

        for acc in accounts[:20]:
            balance_str = f"{acc['balance']:,.2f} {acc['currency']}"
            print(
                f"{acc['holder']:<30} {acc['country']:<12} "
                f"{acc['bank']:<35} {acc['account']:<35} {balance_str:<18}"
            )

        print("=" * 130)
        print(f"\nShowing 20 of {len(accounts)} total accounts")

    def view_accounts_by_country(self):
        """View accounts filtered by country"""

        countries = list(InternationalBankRegistry.BANKS.keys())

        print("\nSelect country:")
        for idx, country in enumerate(countries, 1):
            print(f"{idx}. {country}")

        choice = input(f"\nEnter choice (1-{len(countries)}): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(countries):
            country = countries[int(choice) - 1]

            matching = self.bank.international_registry.get_accounts_by_country(country)

            print(f"\n📍 {len(matching)} Accounts in {country}:")
            print("=" * 130)
            print(f"{'Holder':<30} {'Bank':<40} {'Account':<35} {'Balance':<18}")
            print("-" * 130)

            for acc in matching[:10]:
                balance_str = f"{acc.balance:,.2f} {acc.currency}"
                print(
                    f"{acc.account_holder:<30} {acc.bank_name:<40} "
                    f"{acc.account_number:<35} {balance_str:<18}"
                )

            print("=" * 130)

    def search_international_account(self):
        """Search for international account"""
        account_num = input("\nEnter account number/IBAN: ").strip()

        account = self.bank.international_registry.find_account_by_number(account_num)

        if account:
            # Load transactions if needed
            account._load_transactions_if_needed()

            print("\n[OK] ACCOUNT FOUND")
            print("=" * 70)
            print(f"Holder: {account.account_holder}")
            print(f"Account: {account.account_number}")
            print(f"Bank: {account.bank_name}")
            print(f"SWIFT: {account.swift_code}")
            print(f"Country: {account.country}")
            print(f"Currency: {account.currency}")
            print(f"Balance: {account.balance:,.2f} {account.currency}")

            if account.transactions:
                print(f"\nTransactions: {len(account.transactions)}")
                print("\nRecent Transactions:")
                for txn in account.transactions[-5:]:
                    print(
                        f"  - {txn['date']}: +{txn['amount']:,.2f} {account.currency} from {txn['from']}"
                    )

            print("=" * 70)
        else:
            print("\n[FAIL] Account not found")

    def manage_beneficiaries_menu(self, customer: Customer):
        """Manage transfer beneficiaries"""
        while True:
            print("\n=== Manage Beneficiaries ===")
            print("1. View Beneficiaries")
            print("2. Add Beneficiary")
            print("3. Remove Beneficiary")
            print("4. Back")

            choice = self.app.read_valid_choice("Enter choice: ", ["1", "2", "3", "4"])

            if choice == "1":
                customer.beneficiary_manager.list_beneficiaries()
            elif choice == "2":
                self.add_beneficiary_flow(customer)
            elif choice == "3":
                self.remove_beneficiary_flow(customer)
            elif choice == "4":
                break

    def add_beneficiary_flow(self, customer: Customer):
        """Flow to add a new beneficiary"""
        print("\n--- Add Beneficiary ---")
        name = input("Beneficiary Name: ").strip()
        acc_num = input("Account Number: ").strip()
        ifsc = input("IFSC Code: ").strip()
        bank_name = input("Bank Name: ").strip()

        if not all([name, acc_num, ifsc, bank_name]):
            print("[FAIL] All fields are required.")
            return

        customer.beneficiary_manager.add_beneficiary(name, acc_num, ifsc, bank_name)
        self.bank.save()
        print(f"[SUCCESS] Beneficiary '{name}' added.")

    def remove_beneficiary_flow(self, customer: Customer):
        """Flow to remove a beneficiary"""
        beneficiaries = customer.beneficiary_manager.beneficiaries
        if not beneficiaries:
            print("[INFO] No beneficiaries to remove.")
            return

        print("\n--- Remove Beneficiary ---")
        for idx, b in enumerate(beneficiaries, 1):
            print(f"{idx}. {b.name} ({b.account_number})")

        choice = self.app.read_valid_choice(
            "Select beneficiary to remove: ", [str(i) for i in range(1, len(beneficiaries) + 1)]
        )
        selected = beneficiaries[int(choice) - 1]
        customer.beneficiary_manager.remove_beneficiary(selected.account_number)
        self.bank.save()
        print(f"[SUCCESS] Beneficiary '{selected.name}' removed.")
