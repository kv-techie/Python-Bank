import re
from typing import Dict, Any

class TaxService:
    """
    Handles tax-related business logic, PAN validation, and ITR PDF generation.
    Decouples core tax logic from the CLI UI in BankingApp.
    """
    
    def __init__(self, bank, logger):
        self.bank = bank
        self.logger = logger
        
    def add_tax_exemption(self, customer, deduction):
        """Core logic to add a tax deduction to a customer profile with logging"""
        customer.tax_deductions.append(deduction)
        self.bank.save()
        self.logger.info(f"Customer {customer.customer_id} declared tax deduction: {deduction.section} for ₹{deduction.amount:,.2f}")
        return True

    def validate_pan(self, pan: str) -> bool:
        """Validate PAN format"""
        pattern = r"^[A-Z]{2}[A-Z]{1}[P-Z]{1}[A-Z]{1}[0-9]{7}[A-Z]{1}[0-9]{1}[Z]{1}[0-9]{1}$"
        if re.match(pattern, pan):
            return True
        # Also allow simple format: any 10 chars
        return len(pan) == 10 and pan.isalnum()
        
    def save_itr_report_to_file(self, customer, filing_record, deductions: Dict):
        """Save ITR report as a professional PDF"""
        try:
            # Absolute import since we'll standardize on relative imports later (M5)
            # but for now we are inside backend/services/
            from ..StatementGenerator import StatementGenerator
            filepath = StatementGenerator.generate_itr_report_pdf(customer, filing_record, deductions)
            return True, filepath
        except Exception as e:
            self.logger.error(f"Error generating tax report: {e}")
            return False, str(e)
