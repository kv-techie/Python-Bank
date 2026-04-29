import os
from datetime import datetime, timedelta
from fpdf import FPDF
from typing import Union

class StatementPDF(FPDF):
    """Base PDF class for bank statements"""
    def __init__(self, title_text, customer_name, account_number):
        super().__init__()
        self.title_text = title_text
        self.customer_name = customer_name
        self.account_number = account_number

    def header(self):
        # Logo placeholder / Bank Name
        self.set_font("helvetica", "B", 24)
        self.set_text_color(0, 51, 102)
        self.cell(0, 15, "SCALA BANK", ln=True, align="L")
        
        # Statement Title
        self.set_font("helvetica", "B", 14)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, self.title_text, ln=True, align="L")
        
        # Divider
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        # Customer Info
        self.set_font("helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(30, 6, "Customer Name:", border=0)
        self.set_font("helvetica", "", 10)
        self.cell(70, 6, self.customer_name, border=0)
        
        self.set_font("helvetica", "B", 10)
        self.cell(35, 6, "Primary Account:", border=0)
        self.set_font("helvetica", "", 10)
        self.cell(0, 6, self.account_number, ln=True, border=0)
        
        self.set_font("helvetica", "B", 10)
        self.cell(30, 6, "Statement Date:", border=0)
        self.set_font("helvetica", "", 10)
        self.cell(0, 6, datetime.now().strftime("%d-%m-%Y %H:%M:%S"), ln=True, border=0)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.cell(0, 10, f"Page {self.page_no()} | Scala Bank - Empowering Your Future | Computer Generated Statement", align="C")

class StatementGenerator:
    """Generates professional PDF Statements of Account (SoA)"""
    
    _RECEIPT_DIR = __import__("backend.config", fromlist=["RECEIPT_DIR"]).RECEIPT_DIR
    
    @staticmethod
    def _ensure_dir():
        if not os.path.exists(StatementGenerator._RECEIPT_DIR):
            os.makedirs(StatementGenerator._RECEIPT_DIR)

    @staticmethod
    def generate_loan_soa(loan, customer):
        """Generate SoA for a Loan"""
        StatementGenerator._ensure_dir()
        filename = f"Loan_SoA_{loan.loan_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("LOAN STATEMENT OF ACCOUNT", f"{customer.first_name} {customer.last_name}", loan.customer_id)
        pdf.add_page()
        
        # 1. Loan Overview
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(230, 240, 250)
        pdf.cell(0, 10, "  LOAN SUMMARY", ln=True, fill=True)
        pdf.ln(2)
        
        details = [
            ("Loan ID", loan.loan_id),
            ("Loan Type", loan.loan_type),
            ("Sanctioned Amount", f"Rs. {loan.principal:,.2f}"),
            ("Interest Rate", f"{loan.interest_rate}% p.a. (Reducing)"),
            ("Tenure", f"{loan.tenure_months} Months"),
            ("Monthly EMI", f"Rs. {loan.calculate_emi():,.2f}"),
            ("Status", loan.status),
            ("Start Date", loan.start_date.strftime("%d-%m-%Y") if loan.start_date else "N/A")
        ]
        
        pdf.set_font("helvetica", "", 10)
        for label, value in details:
            pdf.cell(50, 7, f"{label}:", border=0)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 7, str(value), ln=True, border=0)
            pdf.set_font("helvetica", "", 10)
        
        pdf.ln(5)
        
        # 2. Repayment Progress
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(230, 240, 250)
        pdf.cell(0, 10, "  REPAYMENT PROGRESS", ln=True, fill=True)
        pdf.ln(2)
        
        remaining = loan.get_remaining_balance()
        total_paid = (loan.calculate_emi() * loan.emis_paid)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(50, 7, "EMIs Paid:", border=0)
        pdf.cell(0, 7, f"{loan.emis_paid} of {loan.tenure_months}", ln=True)
        pdf.cell(50, 7, "Principal Outstanding:", border=0)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 7, f"Rs. {remaining:,.2f}", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(50, 7, "Approx. Total Paid:", border=0)
        pdf.cell(0, 7, f"Rs. {total_paid:,.2f}", ln=True)
        
        # Progress Bar
        pdf.ln(2)
        progress_width = 180
        filled_width = (loan.emis_paid / loan.tenure_months) * progress_width
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(10, pdf.get_y(), progress_width, 5)
        pdf.set_fill_color(0, 102, 204)
        pdf.rect(10, pdf.get_y(), filled_width, 5, "F")
        pdf.ln(10)
        
        # 3. Amortization / History Table (Simplified)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(230, 240, 250)
        pdf.cell(0, 10, "  REPAYMENT HISTORY (LAST 12 MONTHS)", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        headers = ["Month", "EMI No", "Status", "Amount"]
        col_widths = [45, 45, 45, 45]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_font("helvetica", "", 10)
        start_month = max(1, loan.emis_paid - 11)
        for i in range(start_month, loan.emis_paid + 1):
            pdf.cell(col_widths[0], 8, f"EMI {i}", border=1, align="C")
            pdf.cell(col_widths[1], 8, str(i), border=1, align="C")
            pdf.cell(col_widths[2], 8, "PAID", border=1, align="C")
            pdf.cell(col_widths[3], 8, f"Rs. {loan.calculate_emi():,.2f}", border=1, align="C")
            pdf.ln()
            
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_loan_closure_pdf(loan, customer, branch_details):
        """Generate official Loan Closure Certificate (NOC)"""
        StatementGenerator._ensure_dir()
        filename = f"Loan_Closure_{loan.loan_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("LOAN CLOSURE CERTIFICATE (NOC)", f"{customer.first_name} {customer.last_name}", loan.customer_id)
        pdf.add_page()
        
        # 1. Branch Details
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, branch_details, align="L")
        pdf.ln(5)
        
        # 2. Main Certification Text
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  TO WHOMSOEVER IT MAY CONCERN", ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 11)
        cert_text = f"This is to certify that the loan account (ID: {loan.loan_id}) maintained by {customer.first_name} {customer.last_name} with Scala Bank has been fully repaid and closed as of {loan.closure_date.strftime('%d-%m-%Y') if hasattr(loan.closure_date, 'strftime') else loan.closure_date}. There are no outstanding dues, principal, interest, or penalties remaining on this loan account."
        pdf.multi_cell(0, 7, cert_text)
        pdf.ln(10)
        
        # 3. Financial Summary Table
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "LOAN SUMMARY AT CLOSURE", ln=True)
        pdf.set_font("helvetica", "", 10)
        
        data = [
            ["Loan Type", loan.loan_type],
            ["Sanctioned Principal", f"Rs. {loan.principal:,.2f}"],
            ["Interest Rate", f"{loan.interest_rate}% p.a."],
            ["Total EMIs Paid", f"{loan.tenure_months} / {loan.tenure_months}"],
            ["Final Balance", "Rs. 0.00 (NIL)"],
            ["Closure Date", loan.closure_date.strftime("%d-%m-%Y") if hasattr(loan.closure_date, 'strftime') else loan.closure_date]
        ]
        
        for row in data:
            pdf.cell(60, 8, row[0], border=1)
            pdf.cell(130, 8, str(row[1]), border=1, ln=True)
            
        pdf.ln(15)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "For SCALA BANK", ln=True)
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(0, 10, "Authorized System Signatory (No physical signature required)", ln=True)
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_account_closure_pdf(account, final_balance, cards_closed, disbursement_info):
        """Generate official Account Closure Certificate"""
        StatementGenerator._ensure_dir()
        filename = f"Account_Closure_{account.account_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("ACCOUNT CLOSURE CERTIFICATE", f"{account.first_name} {account.last_name}", account.account_number)
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(255, 230, 230)
        pdf.cell(0, 10, "  CLOSURE CONFIRMATION", ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 7, f"This document confirms the permanent closure of the {account.account_type} account held with Scala Bank. All associated services, including internet banking, mobile banking, and debit cards, have been deactivated.")
        pdf.ln(5)
        
        # Details
        data = [
            ["Account Number", account.account_number],
            ["Account Type", account.account_type],
            ["Final Disbursement", f"Rs. {final_balance:,.2f}"],
            ["Method", disbursement_info],
            ["Cards Terminated", ", ".join(cards_closed) if cards_closed else "None"],
            ["Closure Date", datetime.now().strftime("%d-%m-%Y")]
        ]
        
        pdf.set_font("helvetica", "", 10)
        for row in data:
            pdf.cell(60, 8, row[0], border=1)
            pdf.multi_cell(130, 8, str(row[1]), border=1)
            
        pdf.ln(20)
        pdf.cell(0, 10, "Thank you for your patronage with Scala Bank.", align="C", ln=True)
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_card_closure_pdf(card, account, card_type):
        """Generate official Card Closure Certificate"""
        StatementGenerator._ensure_dir()
        filename = f"{card_type}_Card_Closure_{card.card_number[-4:]}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF(f"{card_type} CARD CLOSURE ADVICE", f"{account.first_name} {account.last_name}", account.account_number)
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 10, f"  {card_type} CARD DETAILS", ln=True, fill=True)
        pdf.ln(5)
        
        data = [
            ["Card Number", f"**** **** **** {card.card_number[-4:]}"],
            ["Network", card.network],
            ["Card Type", card_type],
            ["Status", "PERMANENTLY CLOSED"],
            ["Closure Date", datetime.now().strftime("%d-%m-%Y")]
        ]
        
        if card_type == "CREDIT":
            data.append(["Outstanding Balance", "Rs. 0.00"])
            data.append(["Reward Points", "FORFEITED"])
            
        pdf.set_font("helvetica", "", 10)
        for row in data:
            pdf.cell(60, 8, row[0], border=1)
            pdf.cell(130, 8, str(row[1]), border=1, ln=True)
            
        pdf.ln(10)
        pdf.set_font("helvetica", "I", 10)
        pdf.multi_cell(0, 7, f"The above mentioned {card_type.lower()} card has been successfully terminated from our records. Please ensure that you destroy the physical card chip to prevent any unauthorized use.")
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_fd_soa(fd, customer):
        """Generate SoA for Fixed Deposit"""
        StatementGenerator._ensure_dir()
        filename = f"FD_SoA_{fd.fd_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("FIXED DEPOSIT ADVICE / SoA", f"{customer.first_name} {customer.last_name}", fd.account_number)
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(230, 250, 240)
        pdf.cell(0, 10, "  DEPOSIT DETAILS", ln=True, fill=True)
        pdf.ln(2)
        
        details = [
            ("FD Number", fd.fd_number),
            ("Principal Amount", f"Rs. {fd.principal_amount:,.2f}"),
            ("Interest Rate", f"{fd.interest_rate}% p.a. (Compounded Quarterly)"),
            ("Tenure", f"{fd.tenure_months} Months"),
            ("Start Date", fd.start_date.strftime("%d-%m-%Y")),
            ("Maturity Date", fd.maturity_date.strftime("%d-%m-%Y")),
            ("Maturity Amount", f"Rs. {fd.maturity_amount:,.2f}"),
            ("Status", fd.status)
        ]
        
        pdf.set_font("helvetica", "", 10)
        for label, value in details:
            pdf.cell(50, 7, f"{label}:", border=0)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 7, str(value), ln=True, border=0)
            pdf.set_font("helvetica", "", 10)
            
        pdf.ln(10)
        
        # Maturity Projection Notice
        pdf.set_fill_color(255, 250, 230)
        pdf.set_font("helvetica", "I", 10)
        msg = f"Your Fixed Deposit is currently {fd.get_status_string()}. Upon maturity on {fd.maturity_date.strftime('%d-%m-%Y')}, the amount of Rs. {fd.maturity_amount:,.2f} will be credited to your linked account {fd.account_number}."
        pdf.multi_cell(0, 8, msg, border=1, fill=True, align="C")
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_rd_soa(rd_statement, customer):
        """Generate SoA for Recurring Deposit using the RDStatement data"""
        StatementGenerator._ensure_dir()
        filename = f"RD_SoA_{rd_statement['rd_number']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("RECURRING DEPOSIT STATEMENT", f"{customer.first_name} {customer.last_name}", rd_statement['rd_number'])
        pdf.add_page()
        
        # Summary
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(250, 240, 230)
        pdf.cell(0, 10, "  RD ACCOUNT SUMMARY", ln=True, fill=True)
        pdf.ln(2)
        
        details = [
            ("RD Number", rd_statement['rd_number']),
            ("Monthly Installment", f"Rs. {rd_statement['monthly_installment']:,.2f}"),
            ("Interest Rate", f"{rd_statement['interest_rate']}% p.a."),
            ("Total Deposited", f"Rs. {rd_statement['total_deposited']:,.2f}"),
            ("Interest Accrued", f"Rs. {rd_statement['interest_earned']:,.2f}"),
            ("Maturity Amount", f"Rs. {rd_statement['maturity_amount']:,.2f}"),
            ("Progress", f"{rd_statement['installments_paid']} / {rd_statement['tenure_months']} installments")
        ]
        
        pdf.set_font("helvetica", "", 10)
        for label, value in details:
            pdf.cell(50, 7, f"{label}:", border=0)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 7, str(value), ln=True, border=0)
            pdf.set_font("helvetica", "", 10)
        
        pdf.ln(10)
        
        # Payment History Table
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(250, 240, 230)
        pdf.cell(0, 10, "  INSTALLMENT PAYMENT HISTORY", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(245, 245, 245)
        headers = ["No", "Date", "Amount", "Mode"]
        col_widths = [20, 50, 50, 60]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_font("helvetica", "", 10)
        for i, payment in enumerate(rd_statement['payment_history'], 1):
            pdf.cell(col_widths[0], 8, str(payment.get('installment_number', i)), border=1, align="C")
            pdf.cell(col_widths[1], 8, payment.get('date', 'N/A'), border=1, align="C")
            pdf.cell(col_widths[2], 8, f"Rs. {payment.get('amount', 0):,.2f}", border=1, align="C")
            pdf.cell(col_widths[3], 8, payment.get('method', 'AUTO-DEBIT'), border=1, align="C")
            pdf.ln()
            
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_itr_report_pdf(customer, filing_record, deductions):
        """Generate official ITR Filing Report PDF"""
        StatementGenerator._ensure_dir()
        filename = f"ITR_Acknowledgement_{customer.pan}_{filing_record.financial_year.replace('-', '_')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("INCOME TAX RETURN FILING ACKNOWLEDGEMENT", f"{customer.first_name} {customer.last_name}", customer.pan)
        pdf.add_page()
        
        # 1. Filing Details
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 255, 240)
        pdf.cell(0, 10, "  FILING INFORMATION", ln=True, fill=True)
        pdf.ln(5)
        
        data = [
            ["Financial Year", filing_record.financial_year],
            ["Filing Date", filing_record.filed_date.strftime("%d-%m-%Y")],
            ["Acknowledgment Number", str(filing_record.ack_number)],
            ["PAN", customer.pan],
            ["Status", "SUBMITTED SUCCESSFULLY"]
        ]
        
        pdf.set_font("helvetica", "", 10)
        for row in data:
            pdf.cell(60, 8, row[0], border=1)
            pdf.cell(130, 8, str(row[1]), border=1, ln=True)
            
        pdf.ln(10)
        
        # 2. Income & Deductions
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  COMPUTATION OF TOTAL INCOME", ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(140, 8, "Gross Annual Salary", border=1)
        pdf.cell(50, 8, f"Rs. {filing_record.gross_income:,.2f}", border=1, ln=True, align="R")
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 8, "Less: Deductions under Chapter VI-A", ln=True)
        pdf.set_font("helvetica", "", 9)
        
        deduction_labels = {
            "16": "Section 16 - Standard Deduction",
            "10(13A)": "Section 10(13A) - HRA/Rent",
            "80C": "Section 80C - Savings/EPF",
            "80D": "Section 80D - Medical Insurance",
            "24": "Section 24 - Home Loan Interest",
        }
        
        for section, amount in sorted(deductions.items()):
            label = deduction_labels.get(section, f"Section {section}")
            pdf.cell(140, 7, f"  {label}", border=1)
            pdf.cell(50, 7, f"Rs. {amount:,.2f}", border=1, ln=True, align="R")
            
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(140, 8, "Total Taxable Income", border=1)
        pdf.cell(50, 8, f"Rs. {filing_record.taxable_income:,.2f}", border=1, ln=True, align="R")
        
        pdf.ln(10)
        
        # 3. Tax Liability
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(255, 240, 240)
        pdf.cell(0, 10, "  TAX LIABILITY & REFUND", ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(140, 8, "Total Tax Liability", border=1)
        pdf.cell(50, 8, f"Rs. {filing_record.tax_liability:,.2f}", border=1, ln=True, align="R")
        
        pdf.cell(140, 8, "TDS Paid during FY", border=1)
        pdf.cell(50, 8, f"Rs. {filing_record.tds_paid:,.2f}", border=1, ln=True, align="R")
        
        if filing_record.refund_amount > 0:
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(0, 100, 0)
            pdf.cell(140, 10, "NET REFUND DUE", border=1)
            pdf.cell(50, 10, f"Rs. {filing_record.refund_amount:,.2f}", border=1, ln=True, align="R")
        else:
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(150, 0, 0)
            pdf.cell(140, 10, "BALANCE TAX PAYABLE", border=1)
            pdf.cell(50, 10, f"Rs. {max(0, filing_record.tax_liability - filing_record.tds_paid):,.2f}", border=1, ln=True, align="R")
            
        pdf.set_text_color(0, 0, 0)
        pdf.ln(20)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, "This is an e-acknowledgement generated by Scala Bank upon successful submission of tax records. This document is valid for audit purposes.", align="C")
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_form16_pdf(form16, hra_exemption=0.0):
        """Generate official Form 16 PDF (Certificate u/s 203)"""
        StatementGenerator._ensure_dir()
        filename = f"Form16_{form16.employee_pan}_{form16.financial_year.replace('-', '_')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("FORM NO. 16 - TDS CERTIFICATE (SALARY)", form16.employee_name, form16.employee_pan)
        pdf.add_page()
        
        # Part A - Deductor Details
        pdf.set_font("helvetica", "B", 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "  PART A - DETAILS OF TAX DEDUCTED AND DEPOSITED", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(95, 7, f"Employer: {form16.employer_name}", border=0)
        pdf.cell(95, 7, f"TAN: {form16.employer_tan}", border=0, ln=True)
        pdf.cell(95, 7, f"PAN: {form16.employer_pan}", border=0)
        pdf.cell(95, 7, f"Assessment Year: {form16.assessment_year}", border=0, ln=True)
        pdf.ln(5)
        
        # TDS Table
        pdf.set_font("helvetica", "B", 9)
        headers = ["Quarter", "Period", "Receipt No", "Amount (Rs.)"]
        widths = [30, 40, 70, 50]
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 8, h, border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_font("helvetica", "", 9)
        for q in form16.quarterly_tds:
            pdf.cell(widths[0], 7, q.quarter, border=1)
            pdf.cell(widths[1], 7, q.quarter_period, border=1)
            pdf.cell(widths[2], 7, q.receipt_numbers[0] if q.receipt_numbers else "-", border=1)
            pdf.cell(widths[3], 7, f"{q.tds_deposited:,.2f}", border=1, ln=True, align="R")
            
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(sum(widths[:3]), 8, "TOTAL TDS DEPOSITED", border=1)
        pdf.cell(widths[3], 8, f"{form16.total_tds_deposited:,.2f}", border=1, ln=True, align="R")
        
        pdf.ln(10)
        
        # Part B - Salary Details
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "  PART B - SALARY COMPUTATION & TAX PAYABLE", ln=True, fill=True)
        pdf.ln(2)
        
        tax_details = form16.calculate_tax_payable(hra_exemption)
        gross_salary = form16.calculate_gross_salary()
        total_16_deductions = form16.standard_deduction + form16.entertainment_allowance + form16.professional_tax
        
        data = [
            ("1. Gross Salary (Total)", f"{gross_salary:,.2f}"),
            ("2. Less: HRA Exemption u/s 10(13A)", f"{hra_exemption:,.2f}"),
            ("3. Balance (1 - 2)", f"{(gross_salary - hra_exemption):,.2f}"),
            ("4. Deductions u/s 16 (Std. Ded, etc.)", f"{total_16_deductions:,.2f}"),
            ("5. Income Chargeable under Salaries", f"{(gross_salary - hra_exemption - total_16_deductions):,.2f}"),
            ("6. Total Deductions under Chapter VI-A", f"{form16.calculate_total_deductions_via():,.2f}"),
            ("7. Total Taxable Income", f"{tax_details['total_income']:,.2f}"),
            ("8. Tax on Total Income", f"{tax_details['tax_on_income']:,.2f}"),
            ("9. Health & Education Cess (4%)", f"{tax_details['cess']:,.2f}"),
            ("10. Net Tax Payable", f"{tax_details['tax_after_relief']:,.2f}"),
            ("11. TDS Already Deducted", f"{form16.total_tds_deposited:,.2f}"),
        ]
        
        pdf.set_font("helvetica", "", 10)
        for label, val in data:
            if "Total Taxable Income" in label or "Net Tax Payable" in label:
                pdf.set_font("helvetica", "B", 10)
            pdf.cell(140, 7, label, border=1)
            pdf.cell(50, 7, f"Rs. {val}", border=1, ln=True, align="R")
            pdf.set_font("helvetica", "", 10)
            
        pdf.ln(10)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, "I certify that a sum of Rs. " + f"{form16.total_tds_deposited:,.2f}" + " has been deducted and deposited to the credit of the Central Government. This is a system-generated certificate.", align="C")
        
        pdf.output(filepath)
        return filepath

    @staticmethod
    def generate_form26as_pdf(form26as, financial_year):
        """Generate official Form 26AS PDF (Tax Credit Statement)"""
        StatementGenerator._ensure_dir()
        filename = f"Form26AS_{form26as.pan}_{financial_year.replace('-', '_')}.pdf"
        filepath = os.path.join(StatementGenerator._RECEIPT_DIR, filename)
        
        pdf = StatementPDF("FORM 26AS - ANNUAL TAX CREDIT STATEMENT", form26as.name, form26as.pan)
        pdf.add_page()
        
        # Summary Header
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 245, 255)
        pdf.cell(0, 10, f"  FINANCIAL YEAR: {financial_year} | PAN: {form26as.pan}", ln=True, fill=True)
        pdf.ln(5)
        
        # Part A - TDS
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "  PART A - DETAILS OF TAX DEDUCTED AT SOURCE", ln=True, border="B")
        pdf.ln(2)
        
        fy_tds = [e for e in form26as.tds_entries if e.financial_year == financial_year]
        if fy_tds:
            pdf.set_font("helvetica", "B", 9)
            headers = ["Deductor", "Section", "Amount Paid", "TDS Deducted"]
            widths = [70, 30, 45, 45]
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 8, h, border=1, align="C", fill=True)
            pdf.ln()
            
            pdf.set_font("helvetica", "", 8)
            for e in fy_tds:
                d_name = e.deductor_name[:35] + ".." if len(e.deductor_name) > 35 else e.deductor_name
                pdf.cell(widths[0], 7, d_name, border=1)
                pdf.cell(widths[1], 7, e.section, border=1, align="C")
                pdf.cell(widths[2], 7, f"{e.amount_paid:,.2f}", border=1, align="R")
                pdf.cell(widths[3], 7, f"{e.tds_deducted:,.2f}", border=1, ln=True, align="R")
        else:
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(0, 10, "No TDS entries found for this year.", ln=True)
            
        pdf.ln(5)
        
        # Part B - Advance Tax
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 10, "  PART B - DETAILS OF TAX PAID (ADVANCE TAX / SELF ASSESSMENT)", ln=True, border="B")
        pdf.ln(2)
        
        fy_advance = [e for e in form26as.advance_tax_entries if e.financial_year == financial_year]
        if fy_advance:
            pdf.set_font("helvetica", "B", 9)
            headers = ["Date", "BSR Code", "Challan No", "Amount"]
            widths = [40, 40, 60, 50]
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 8, h, border=1, align="C", fill=True)
            pdf.ln()
            
            pdf.set_font("helvetica", "", 9)
            for e in fy_advance:
                pdf.cell(widths[0], 7, e.date_of_payment.strftime("%d-%b-%Y"), border=1)
                pdf.cell(widths[1], 7, e.bsr_code, border=1)
                pdf.cell(widths[2], 7, e.challan_number, border=1)
                pdf.cell(widths[3], 7, f"{e.amount:,.2f}", border=1, ln=True, align="R")
        else:
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(0, 10, "No advance tax payments recorded.", ln=True)
            
        pdf.ln(10)
        
        # Net Summary
        pdf.set_font("helvetica", "B", 11)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(140, 10, "TOTAL TAX CREDIT AVAILABLE", border=1, fill=True)
        total_credit = sum(e.tds_deducted for e in fy_tds) + sum(e.amount for e in fy_advance)
        pdf.cell(50, 10, f"Rs. {total_credit:,.2f}", border=1, ln=True, align="R", fill=True)
        
        pdf.ln(20)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, "This is a computer-generated Annual Tax Credit Statement. In case of any discrepancy, please contact the respective deductor/bank.", align="C")
        
        pdf.output(filepath)
        return filepath
