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
                beneficiary_name = f"{acc.first_name} {acc.last_name}"
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
                        payee_name = f"{acc.first_name} {acc.last_name}"
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

    def export_statement(self, rd_number: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Export RD statement as professional PDF
        
        Args:
            rd_number: RD number to export
            filename: Ignored
            
        Returns:
            Path to created file or None if failed
        """
        statement = self.get_rd_statement(rd_number)
        if not statement:
            return None

        try:
            from .StatementGenerator import StatementGenerator
            
            # Find the account associated with this RD to get the customer
            account = None
            if rd_number in self.bank.recurring_deposits:
                acc_num = self.bank.recurring_deposits[rd_number].account_number
                for acc in self.bank.accounts:
                    if acc.account_number == acc_num:
                        account = acc
                        break
            
            if not account:
                return None
                
            customer = self.bank.get_customer_by_id(account.customer_id)
            filepath = StatementGenerator.generate_rd_soa(statement, customer)
            print(f"[OK] Official RD Statement (PDF) generated: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[FAIL] Error generating RD Statement PDF: {e}")
            return None
