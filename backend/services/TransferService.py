import os
from datetime import datetime
from fpdf import FPDF
from ..Logger import BankLogger

# Centralized config for M3

from ..config import RECEIPT_DIR

class TransferService:
    """Handles business logic for transfers and receipt generation."""
    
    def __init__(self, bank, logger):
        self.bank = bank
        self.logger = logger
        
    def generate_transfer_receipt(self, sender_acc, recipient_name, recipient_acc, bank_name, ifsc, amount, mode, txn_id):
        """Generates a professional PDF receipt for an external fund transfer."""
        os.makedirs(RECEIPT_DIR, exist_ok=True)

        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        dt_display = datetime.now().strftime("%d %B %Y  %H:%M:%S")
        base_filename = f"Receipt_{txn_id}_{timestamp}"
        pdf_filepath  = os.path.join(RECEIPT_DIR, f"{base_filename}.pdf")

        try:
            # Colour palette
            NAVY       = (0, 43, 91)
            GOLD       = (185, 142, 35)
            LIGHT_GREY = (245, 246, 248)
            MID_GREY   = (160, 160, 160)
            GREEN      = (22, 135, 90)
            WHITE      = (255, 255, 255)
            BLACK      = (30, 30, 30)

            BRANCH_NAME  = "Scala Bank - Jakkasandra Branch"
            BRANCH_ADDR  = "14, 4th Cross, Jakkasandra, Koramangala, Bengaluru - 560 034"
            BRANCH_PHONE = "+91 80 4660 1234"
            BRANCH_EMAIL = "care@scalabank.in"
            BRANCH_IFSC  = getattr(sender_acc, "BRANCH_IFSC", "SCBA0005621")
            BRANCH_MICR  = "560005562"
            CIN          = "U65191KA2010PLC123456"

            class ReceiptPDF(FPDF):
                def header(self):
                    self.set_fill_color(*NAVY)
                    self.rect(0, 0, 210, 28, "F")
                    self.set_xy(12, 5)
                    self.set_text_color(*WHITE)
                    self.set_font("helvetica", "B", 22)
                    self.cell(120, 10, "SCALA BANK", ln=False)
                    self.set_font("helvetica", "I", 8)
                    self.set_xy(12, 17)
                    self.cell(186, 6, "Empowering Your Future  |  Regulated by the Reserve Bank of India", align="R", ln=True)
                    
                    self.set_draw_color(*GOLD)
                    self.set_line_width(0.8)
                    self.line(0, 28, 210, 28)
                    
                    self.set_fill_color(*LIGHT_GREY)
                    self.rect(0, 29, 210, 10, "F")
                    self.set_xy(12, 30)
                    self.set_font("helvetica", "", 7.5)
                    self.set_text_color(*MID_GREY)
                    self.cell(0, 7, f"{BRANCH_NAME}  |  {BRANCH_ADDR}  |  Tel: {BRANCH_PHONE}  |  {BRANCH_EMAIL}", ln=True)
                    
                    self.set_xy(12, 43)
                    self.set_text_color(*NAVY)
                    self.set_font("helvetica", "B", 13)
                    self.cell(0, 8, "FUND TRANSFER CONFIRMATION ADVICE", ln=True)
                    self.set_draw_color(*NAVY)
                    self.set_line_width(0.3)
                    self.line(12, self.get_y(), 198, self.get_y())
                    self.ln(4)

                def footer(self):
                    self.set_y(-22)
                    self.set_draw_color(*GOLD)
                    self.set_line_width(0.6)
                    self.line(12, self.get_y(), 198, self.get_y())
                    self.ln(2)
                    self.set_font("helvetica", "", 7)
                    self.set_text_color(*MID_GREY)
                    disclaimer = (
                        "This is a system-generated document and does not require a physical signature. "
                        "Scala Bank is registered under the Companies Act, 2013. "
                        f"CIN: {CIN}.  |  Page {self.page_no()}"
                    )
                    self.multi_cell(0, 4, disclaimer, align="C")

            pdf = ReceiptPDF()
            pdf.set_auto_page_break(auto=True, margin=30)
            pdf.add_page()

            def kv_row(label, value):
                pdf.set_text_color(*MID_GREY)
                pdf.set_font("helvetica", "", 8.5)
                pdf.cell(55, 7, label, border=0)
                pdf.set_text_color(*BLACK)
                pdf.set_font("helvetica", "B", 8.5)
                pdf.cell(0, 7, str(value), border=0, ln=True)

            def section_header(title):
                pdf.set_fill_color(*NAVY)
                pdf.set_text_color(*WHITE)
                pdf.set_font("helvetica", "B", 9)
                pdf.cell(0, 7, f"   {title}", ln=True, fill=True)
                pdf.ln(2)

            section_header("TRANSACTION REFERENCE")
            badge_y = pdf.get_y()
            pdf.set_fill_color(*GREEN)
            pdf.set_text_color(*WHITE)
            pdf.set_font("helvetica", "B", 9)
            pdf.set_xy(153, badge_y - 1)
            pdf.cell(43, 8, "  SUCCESSFUL  ", fill=True, align="C", ln=False)
            pdf.set_xy(12, badge_y)
            pdf.set_text_color(*BLACK)
            kv_row("Transaction ID",  txn_id)
            kv_row("Date & Time",     dt_display)
            kv_row("Transfer Mode",   mode)
            kv_row("UTR / Reference", txn_id[:16].upper())
            kv_row("Channel",         "Internet Banking (Simulated)")
            pdf.ln(4)

            section_header("PARTY DETAILS")
            panel_y = pdf.get_y()
            left_x  = 12
            right_x = 110
            panel_w = 95
            panel_h = 50
            pdf.set_draw_color(*NAVY)
            pdf.set_line_width(0.4)
            pdf.rect(left_x,  panel_y, panel_w, panel_h)
            pdf.rect(right_x, panel_y, panel_w, panel_h)
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.set_font("helvetica", "B", 8)
            pdf.set_xy(left_x, panel_y)
            pdf.cell(panel_w, 8, "  REMITTER (SENDER)", fill=True)
            pdf.set_xy(right_x, panel_y)
            pdf.cell(panel_w, 8, "  BENEFICIARY (RECIPIENT)", fill=True)

            def panel_row(col_x, label, value, row_y):
                pdf.set_xy(col_x + 3, row_y)
                pdf.set_text_color(*MID_GREY)
                pdf.set_font("helvetica", "", 7.5)
                pdf.cell(30, 5.5, label)
                pdf.set_xy(col_x + 33, row_y)
                pdf.set_text_color(*BLACK)
                pdf.set_font("helvetica", "B", 8)
                pdf.cell(panel_w - 36, 5.5, value)

            row_y = panel_y + 10
            sender_name = f"{sender_acc.first_name} {sender_acc.last_name}"
            rows_l = [
                ("Account Holder", sender_name),
                ("Account No.",    sender_acc.account_number),
                ("Account Type",   getattr(sender_acc, "account_type", "Savings")),
                ("Bank",           "SCALA BANK"),
                ("IFSC Code",      BRANCH_IFSC),
                ("Branch",         "Main Branch, Hyderabad"),
            ]
            rows_r = [
                ("Beneficiary",  recipient_name),
                ("Account No.",  recipient_acc),
                ("Account Type", "Savings / Current"),
                ("Bank",         bank_name),
                ("IFSC Code",    ifsc),
                ("Branch",       "As per IFSC"),
            ]
            for (ll, lv), (rl, rv) in zip(rows_l, rows_r):
                panel_row(left_x,  ll, lv, row_y)
                panel_row(right_x, rl, rv, row_y)
                row_y += 6.5

            pdf.set_xy(12, panel_y + panel_h + 4)
            pdf.ln(2)

            section_header("TRANSACTION SUMMARY")
            kv_row("Transfer Amount",  f"Rs. {amount:,.2f}")
            kv_row("Processing Fee",   "Nil  (Scala Bank charges no NEFT/RTGS fees)")
            pdf.ln(1)
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(130, 13, "   TOTAL AMOUNT DEBITED", fill=True, border=0)
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 13, f"Rs. {amount:,.2f}  ", fill=True, align="R", border=0, ln=True)
            pdf.ln(4)

            section_header("AUTHORIZATION")
            pdf.set_font("helvetica", "", 8.5)
            pdf.set_text_color(*BLACK)
            pdf.multi_cell(0, 5.5,
                f"This transaction has been duly authorized and processed by Scala Bank's "
                f"secure banking infrastructure. The funds will be credited to the "
                f"beneficiary account within the standard {mode} settlement window as "
                f"prescribed by the Reserve Bank of India.")
            pdf.ln(6)

            sig_y = pdf.get_y()
            pdf.set_draw_color(*MID_GREY)
            pdf.set_line_width(0.3)
            pdf.line(12, sig_y, 80, sig_y)
            pdf.set_xy(12, sig_y + 1)
            pdf.set_font("helvetica", "I", 7.5)
            pdf.set_text_color(*MID_GREY)
            pdf.cell(70, 5, "Authorized Digital Signatory")
            pdf.line(130, sig_y, 198, sig_y)
            pdf.set_xy(130, sig_y + 1)
            pdf.cell(68, 5, "Branch Manager / Scala Bank", align="R")

            pdf.output(pdf_filepath)
            return True, pdf_filepath
        except Exception as e:
            self.logger.error(f"Could not generate PDF receipt: {e}")
            return False, str(e)
