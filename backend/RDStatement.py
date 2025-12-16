"""
RD Statement of Accounts Module
Generates detailed statements for Recurring Deposits
"""

from datetime import datetime
from typing import Dict, List, Optional


class RDStatement:
    """Generate comprehensive RD payment statements"""

    def __init__(self, bank):
        self.bank = bank

    def get_rd_statement(self, rd_number: str) -> Optional[Dict]:
        """
        Get complete statement details for an RD

        Returns:
            Dictionary with RD statement details or None if not found
        """
        # Find the RD
        if (
            not hasattr(self.bank, "recurring_deposits")
            or rd_number not in self.bank.recurring_deposits
        ):
            return None

        rd = self.bank.recurring_deposits[rd_number]

        # Find the RD holder (beneficiary) account
        beneficiary_account = None
        beneficiary_name = "Unknown"
        for acc in self.bank.accounts:
            if acc.account_number == rd.account_number:
                beneficiary_account = acc
                beneficiary_name = f"{acc.first_name} {acc.last_name}"  # ✅ FIXED
                break

        # Find who is paying for the RD (payee)
        payee_name = beneficiary_name  # Default: beneficiary pays themselves
        is_authorized = False

        if hasattr(self.bank, "rd_authorizations"):
            active_auth = self.bank.rd_authorizations.get_active_authorization(
                rd_number
            )
            if active_auth:
                is_authorized = True
                # Find payer account details
                for acc in self.bank.accounts:
                    if acc.account_number == active_auth.payer_account_number:
                        payee_name = f"{acc.first_name} {acc.last_name}"  # ✅ FIXED
                        break

        # Create statement
        statement = {
            "rd_number": rd.rd_number,
            "rd_creation_date": rd.creation_date
            if hasattr(rd, "creation_date")
            else rd.start_date.strftime("%d-%m-%Y"),
            "monthly_installment": rd.monthly_installment,
            "interest_rate": rd.interest_rate,
            "payee_name": payee_name,
            "beneficiary_name": beneficiary_name,
            "is_authorized": is_authorized,
            "tenure_months": rd.tenure_months,
            "installments_paid": rd.installments_paid,
            "status": rd.status,
            "total_deposited": rd.total_deposited,
            "interest_earned": getattr(rd, "interest_earned", 0),
            "maturity_amount": rd.calculate_maturity_amount()
            if hasattr(rd, "calculate_maturity_amount")
            else 0,
            "autopay_enabled": rd.autopay_enabled,
            "autopay_day": rd.autopay_day if rd.autopay_enabled else None,
            "payment_history": rd.payment_history
            if hasattr(rd, "payment_history")
            else [],
            "last_payment_date": rd.last_payment_date.strftime("%d-%m-%Y")
            if hasattr(rd, "last_payment_date") and rd.last_payment_date
            else None,
        }

        return statement

    def get_all_rd_statements(self, account_number: str) -> List[Dict]:
        """Get statements for all RDs in a specific account"""
        statements = []

        if not hasattr(self.bank, "recurring_deposits"):
            return statements

        for rd in self.bank.recurring_deposits.values():
            if rd.account_number == account_number:
                statement = self.get_rd_statement(rd.rd_number)
                if statement:
                    statements.append(statement)

        return statements

    def print_rd_statement(self, rd_statement: Dict) -> None:
        """Pretty print RD statement to console"""

        print("\n" + "=" * 100)
        print("RECURRING DEPOSIT - STATEMENT OF ACCOUNTS")
        print("=" * 100)

        print(f"\n{'RD DETAILS':^100}")
        print("-" * 100)
        print(f"RD Number              : {rd_statement['rd_number']}")
        print(f"Creation Date          : {rd_statement['rd_creation_date']}")
        print(f"Status                 : {rd_statement['status']}")
        print(
            f"Tenure                 : {rd_statement['installments_paid']}/{rd_statement['tenure_months']} months"
        )

        print(f"\n{'FINANCIAL DETAILS':^100}")
        print("-" * 100)
        print(
            f"Monthly Installment    : Rs. {rd_statement['monthly_installment']:>15,.2f}"
        )
        print(
            f"Interest Rate          : {rd_statement['interest_rate']:>15.2f}% per annum"
        )
        print(f"Total Deposited        : Rs. {rd_statement['total_deposited']:>15,.2f}")
        print(f"Interest Earned        : Rs. {rd_statement['interest_earned']:>15,.2f}")
        print(f"Maturity Amount        : Rs. {rd_statement['maturity_amount']:>15,.2f}")

        print(f"\n{'HOLDER DETAILS':^100}")
        print("-" * 100)
        print(f"RD Beneficiary         : {rd_statement['beneficiary_name']}")
        print(f"Payee (Who Pays)       : {rd_statement['payee_name']}")

        if rd_statement["is_authorized"]:
            print("Payment Type           : Authorized Payment")
        else:
            print("Payment Type           : Direct Payment")

        print(f"\n{'AUTOPAY DETAILS':^100}")
        print("-" * 100)
        print(
            f"Autopay Enabled        : {'Yes ✓' if rd_statement['autopay_enabled'] else 'No ✗'}"
        )
        if rd_statement["autopay_enabled"] and rd_statement["autopay_day"]:
            print(
                f"Autopay Day            : {rd_statement['autopay_day']} of each month"
            )
        if rd_statement["last_payment_date"]:
            print(f"Last Payment Date      : {rd_statement['last_payment_date']}")

        print(f"\n{'PAYMENT HISTORY':^100}")
        print("-" * 100)

        if not rd_statement["payment_history"]:
            print("No payments recorded yet")
        else:
            print(
                f"{'#':<4} {'Date':<15} {'Installment':<15} {'Amount':<15} {'Method':<20}"
            )
            print("-" * 100)

            for idx, payment in enumerate(rd_statement["payment_history"], 1):
                payment_date = payment.get("date", "N/A")
                installment_no = payment.get("installment_number", idx)
                amount = payment.get("amount", 0)
                method = payment.get("method", "Manual")

                print(
                    f"{idx:<4} {payment_date:<15} {installment_no:<15} Rs. {amount:>12,.2f}  {method:<20}"
                )

        print("\n" + "=" * 100)

    def export_rd_statement_to_text(
        self, rd_number: str, filename: str = None
    ) -> Optional[str]:
        """
        Export RD statement to text file

        Args:
            rd_number: RD number to export
            filename: Optional custom filename (default: RD_[rd_number]_statement.txt)

        Returns:
            Path to created file or None if failed
        """
        statement = self.get_rd_statement(rd_number)
        if not statement:
            return None

        if not filename:
            filename = f"RD_{rd_number}_statement.txt"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("=" * 100 + "\n")
                f.write("RECURRING DEPOSIT - STATEMENT OF ACCOUNTS\n")
                f.write("=" * 100 + "\n")

                f.write("\nRD DETAILS\n")
                f.write("-" * 100 + "\n")
                f.write(f"RD Number              : {statement['rd_number']}\n")
                f.write(f"Creation Date          : {statement['rd_creation_date']}\n")
                f.write(f"Status                 : {statement['status']}\n")
                f.write(
                    f"Tenure                 : {statement['installments_paid']}/{statement['tenure_months']} months\n"
                )

                f.write("\nFINANCIAL DETAILS\n")
                f.write("-" * 100 + "\n")
                f.write(
                    f"Monthly Installment    : Rs. {statement['monthly_installment']:>15,.2f}\n"
                )
                f.write(
                    f"Interest Rate          : {statement['interest_rate']:>15.2f}% per annum\n"
                )
                f.write(
                    f"Total Deposited        : Rs. {statement['total_deposited']:>15,.2f}\n"
                )
                f.write(
                    f"Interest Earned        : Rs. {statement['interest_earned']:>15,.2f}\n"
                )
                f.write(
                    f"Maturity Amount        : Rs. {statement['maturity_amount']:>15,.2f}\n"
                )

                f.write("\nHOLDER DETAILS\n")
                f.write("-" * 100 + "\n")
                f.write(f"RD Beneficiary         : {statement['beneficiary_name']}\n")
                f.write(f"Payee (Who Pays)       : {statement['payee_name']}\n")
                f.write(
                    f"Payment Type           : {'Authorized Payment' if statement['is_authorized'] else 'Direct Payment'}\n"
                )

                f.write("\nAUTOPAY DETAILS\n")
                f.write("-" * 100 + "\n")
                f.write(
                    f"Autopay Enabled        : {'Yes' if statement['autopay_enabled'] else 'No'}\n"
                )
                if statement["autopay_enabled"] and statement["autopay_day"]:
                    f.write(
                        f"Autopay Day            : {statement['autopay_day']} of each month\n"
                    )
                if statement["last_payment_date"]:
                    f.write(
                        f"Last Payment Date      : {statement['last_payment_date']}\n"
                    )

                f.write("\nPAYMENT HISTORY\n")
                f.write("-" * 100 + "\n")

                if not statement["payment_history"]:
                    f.write("No payments recorded yet\n")
                else:
                    f.write(
                        f"{'#':<4} {'Date':<15} {'Installment':<15} {'Amount':<15} {'Method':<20}\n"
                    )
                    f.write("-" * 100 + "\n")

                    for idx, payment in enumerate(statement["payment_history"], 1):
                        payment_date = payment.get("date", "N/A")
                        installment_no = payment.get("installment_number", idx)
                        amount = payment.get("amount", 0)
                        method = payment.get("method", "Manual")

                        f.write(
                            f"{idx:<4} {payment_date:<15} {installment_no:<15} Rs. {amount:>12,.2f}  {method:<20}\n"
                        )

                f.write("\n" + "=" * 100 + "\n")
                f.write(
                    f"Statement Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
                )

            return filename

        except Exception as e:
            print(f"❌ Error exporting statement: {e}")
            return None
