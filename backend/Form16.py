"""
Form 16 - Certificate under section 203 of the Income-tax Act, 1961
for Tax Deducted at Source from Salary

Part A: Details of tax deducted and deposited
Part B: Details of salary paid and tax deducted
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass
class SalaryComponent:
    """Individual salary component"""

    description: str
    amount: float


@dataclass
class Deduction:
    """Tax deduction under various sections"""

    section: str
    description: str
    amount: float


@dataclass
class QuarterlyTDS:
    """TDS details for a quarter"""

    quarter: str  # Q1, Q2, Q3, Q4
    quarter_period: str  # "Apr-Jun", "Jul-Sep", etc.
    receipt_numbers: List[str]  # Challan numbers
    tds_deposited: float
    deposit_dates: List[date]


class Form16:
    """
    Form 16 - Certificate under section 203 of the Income-tax Act, 1961
    for Tax Deducted at Source from Salary

    Part A: Details of tax deducted and deposited
    Part B: Details of salary paid and tax deducted
    """

    # Tax regime rates for FY 2024-25 onwards (New Regime)
    NEW_REGIME_SLABS = [
        (300000, 0.0),  # Up to 3L - Nil
        (700000, 0.05),  # 3L-7L - 5%
        (1000000, 0.10),  # 7L-10L - 10%
        (1200000, 0.15),  # 10L-12L - 15%
        (1500000, 0.20),  # 12L-15L - 20%
        (float("inf"), 0.30),  # Above 15L - 30%
    ]

    def __init__(
        self,
        employee_name: str,
        employee_pan: str,
        designation: str,
        employer_name: str,
        employer_tan: str,
        employer_pan: str,
        employer_address: str,
        financial_year: str,
        assessment_year: str,
    ):
        self.employee_name = employee_name
        self.employee_pan = employee_pan
        self.designation = designation
        self.employer_name = employer_name
        self.employer_tan = employer_tan
        self.employer_pan = employer_pan
        self.employer_address = employer_address
        self.financial_year = financial_year
        self.assessment_year = assessment_year

        # Salary components
        self.basic_salary = 0.0
        self.dearness_allowance = 0.0
        self.hra_received = 0.0
        self.other_allowances = 0.0
        self.perquisites = 0.0
        self.profits_in_lieu = 0.0

        # Deductions
        self.standard_deduction = 50000.0  # Fixed for FY 2024-25
        self.entertainment_allowance = 0.0
        self.professional_tax = 0.0

        # Chapter VI-A deductions
        self.deductions_80c = 0.0  # LIC, PPF, ELSS, etc.
        self.deductions_80ccd1b = 0.0  # NPS
        self.deductions_80d = 0.0  # Health insurance
        self.deductions_80e = 0.0  # Education loan interest
        self.deductions_80g = 0.0  # Donations
        self.other_deductions = 0.0

        # Tax details
        self.quarterly_tds: List[QuarterlyTDS] = []
        self.total_tds_deposited = 0.0

        # Other income
        self.other_income = 0.0

        # Relief under section 89
        self.relief_89 = 0.0

    def set_salary_components(
        self,
        basic: float,
        da: float = 0.0,
        hra: float = 0.0,
        other_allowances: float = 0.0,
        perquisites: float = 0.0,
        profits_in_lieu: float = 0.0,
    ):
        """Set salary components"""
        self.basic_salary = basic
        self.dearness_allowance = da
        self.hra_received = hra
        self.other_allowances = other_allowances
        self.perquisites = perquisites
        self.profits_in_lieu = profits_in_lieu

    def set_chapter_via_deductions(
        self,
        deduction_80c: float = 0.0,
        deduction_80ccd1b: float = 0.0,
        deduction_80d: float = 0.0,
        deduction_80e: float = 0.0,
        deduction_80g: float = 0.0,
        other: float = 0.0,
    ):
        """Set Chapter VI-A deductions"""
        self.deductions_80c = min(deduction_80c, 150000.0)  # Max 1.5L
        self.deductions_80ccd1b = min(deduction_80ccd1b, 50000.0)  # Max 50K
        self.deductions_80d = deduction_80d
        self.deductions_80e = deduction_80e
        self.deductions_80g = deduction_80g
        self.other_deductions = other

    def add_quarterly_tds(self, quarter_data: QuarterlyTDS):
        """Add quarterly TDS details"""
        self.quarterly_tds.append(quarter_data)
        self.total_tds_deposited += quarter_data.tds_deposited

    def calculate_gross_salary(self) -> float:
        """Calculate gross salary (before deductions)"""
        return (
            self.basic_salary
            + self.dearness_allowance
            + self.hra_received
            + self.other_allowances
            + self.perquisites
            + self.profits_in_lieu
        )

    def calculate_hra_exemption(
        self, rent_paid: float, metro_city: bool = False
    ) -> float:
        """
        Calculate HRA exemption (least of three):
        1. Actual HRA received
        2. Rent paid minus 10% of salary
        3. 50% of salary (metro) or 40% (non-metro)
        """
        basic_da = self.basic_salary + self.dearness_allowance

        option1 = self.hra_received
        option2 = max(0, rent_paid - (0.10 * basic_da))
        option3 = (0.50 if metro_city else 0.40) * basic_da

        return min(option1, option2, option3)

    def calculate_gross_total_income(self, hra_exemption: float = 0.0) -> float:
        """Calculate Gross Total Income"""
        gross_salary = self.calculate_gross_salary()
        less_exemptions = hra_exemption
        income_chargeable_salary = gross_salary - less_exemptions

        # Less: Deductions under section 16
        less_standard_deduction = self.standard_deduction
        less_entertainment = self.entertainment_allowance
        less_professional_tax = self.professional_tax

        total_deductions_16 = (
            less_standard_deduction + less_entertainment + less_professional_tax
        )

        income_from_salary = max(0, income_chargeable_salary - total_deductions_16)

        # Add other income
        gross_total_income = income_from_salary + self.other_income

        return gross_total_income

    def calculate_total_deductions_via(self) -> float:
        """Calculate total deductions under Chapter VI-A"""
        return (
            self.deductions_80c
            + self.deductions_80ccd1b
            + self.deductions_80d
            + self.deductions_80e
            + self.deductions_80g
            + self.other_deductions
        )

    def calculate_total_income(self, hra_exemption: float = 0.0) -> float:
        """Calculate Total Income (after all deductions)"""
        gti = self.calculate_gross_total_income(hra_exemption)
        deductions = self.calculate_total_deductions_via()
        return max(0, gti - deductions)

    def calculate_tax_on_income(self, total_income: float) -> float:
        """Calculate tax based on new regime slabs"""
        tax = 0.0
        previous_limit = 0

        for limit, rate in self.NEW_REGIME_SLABS:
            if total_income <= previous_limit:
                break

            taxable_in_slab = min(total_income, limit) - previous_limit
            tax += taxable_in_slab * rate
            previous_limit = limit

        return tax

    def calculate_tax_payable(self, hra_exemption: float = 0.0) -> Dict[str, float]:
        """Calculate complete tax liability"""
        total_income = self.calculate_total_income(hra_exemption)
        tax_on_income = self.calculate_tax_on_income(total_income)

        # Add surcharge if applicable
        surcharge = 0.0
        if total_income > 5000000:  # Above 50L
            surcharge = tax_on_income * 0.10
        elif total_income > 10000000:  # Above 1Cr
            surcharge = tax_on_income * 0.15

        # Add Health & Education Cess (4%)
        cess = (tax_on_income + surcharge) * 0.04

        total_tax = tax_on_income + surcharge + cess

        # Less: Relief under section 89
        tax_after_relief = max(0, total_tax - self.relief_89)

        # Net tax payable
        net_tax_payable = tax_after_relief

        # Less: TDS already deducted
        tax_balance = net_tax_payable - self.total_tds_deposited

        return {
            "total_income": total_income,
            "tax_on_income": tax_on_income,
            "surcharge": surcharge,
            "cess": cess,
            "total_tax": total_tax,
            "relief_89": self.relief_89,
            "tax_after_relief": tax_after_relief,
            "tds_deducted": self.total_tds_deposited,
            "tax_balance": tax_balance,  # Positive = tax due, Negative = refund
        }

    def generate_form16(
        self, hra_exemption: float = 0.0, rent_paid: float = 0.0
    ) -> str:
        """Generate complete Form 16 certificate"""

        tax_details = self.calculate_tax_payable(hra_exemption)

        output = []

        # PART A - Certificate details
        output.append("=" * 100)
        output.append("FORM NO. 16")
        output.append("[See rule 31(1)(a)]")
        output.append("=" * 100)
        output.append("")
        output.append("Certificate under section 203 of the Income-tax Act, 1961")
        output.append("for tax deducted at source on salary")
        output.append("")
        output.append("=" * 100)
        output.append("PART A")
        output.append(
            "(Certificate under section 203 of the Income-tax Act, 1961 for tax deducted at source)"
        )
        output.append("=" * 100)
        output.append("")

        # 1. Name and address of Employer
        output.append("1. Name and address of the Employer")
        output.append(f"   {self.employer_name}")
        output.append(f"   {self.employer_address}")
        output.append("")

        # 2. TAN and PAN of Deductor
        output.append(f"2. TAN of the Deductor: {self.employer_tan}")
        output.append(f"   PAN of the Deductor: {self.employer_pan}")
        output.append("")

        # 3. PAN of Employee
        output.append(f"3. PAN of the Employee: {self.employee_pan}")
        output.append("")

        # 4. Employee details
        output.append(f"4. Name of the Employee: {self.employee_name}")
        output.append(f"   Designation: {self.designation}")
        output.append("")

        # 5. Period
        output.append("5. Period:")
        output.append(f"   Financial Year: {self.financial_year}")
        output.append(f"   Assessment Year: {self.assessment_year}")
        output.append("")

        # 6. Summary of tax deducted at source
        output.append("6. Summary of Tax Deducted at Source")
        output.append("")
        output.append(
            f"{'Quarter':<15} {'Period':<20} {'Receipt Numbers':<25} {'Amount (₹)':<15} {'Deposit Date':<15}"
        )
        output.append("-" * 100)

        for q in self.quarterly_tds:
            receipt_str = ", ".join(q.receipt_numbers[:2])
            if len(q.receipt_numbers) > 2:
                receipt_str += "..."

            date_str = (
                q.deposit_dates[0].strftime("%d-%b-%Y") if q.deposit_dates else "-"
            )

            output.append(
                f"{q.quarter:<15} "
                f"{q.quarter_period:<20} "
                f"{receipt_str:<25} "
                f"{q.tds_deposited:>13,.2f} "
                f"{date_str:<15}"
            )

        output.append("-" * 100)
        output.append(f"{'Total':<35} {'':<25} {self.total_tds_deposited:>13,.2f}")
        output.append("")

        # Verification
        output.append("Verification")
        output.append(
            f"I, {self.employer_name}, do hereby certify that the information given above is true,"
        )
        output.append(
            "complete and correct and is based on the books of account, documents, TDS statements,"
        )
        output.append("and other available records.")
        output.append("")
        output.append("Place: Bengaluru")
        output.append(f"Date: {datetime.now().strftime('%d-%b-%Y')}")
        output.append("")
        output.append("Full Name: [Authorized Signatory]")
        output.append("Designation: [HR Manager]")
        output.append("")
        output.append("=" * 100)

        # PART B - Salary and tax details
        output.append("")
        output.append("=" * 100)
        output.append("PART B")
        output.append("(Details of Salary Paid and any other income and tax deducted)")
        output.append("=" * 100)
        output.append("")

        output.append("1. Gross Salary")
        output.append(
            f"   (a) Salary as per provisions contained in sec.17(1)    ₹{self.basic_salary:>15,.2f}"
        )
        output.append(
            f"   (b) Value of perquisites u/s 17(2)                      ₹{self.perquisites:>15,.2f}"
        )
        output.append(
            f"   (c) Profits in lieu of salary u/s 17(3)                 ₹{self.profits_in_lieu:>15,.2f}"
        )
        output.append(
            f"   (d) Total                                               ₹{self.calculate_gross_salary():>15,.2f}"
        )
        output.append("")

        output.append("2. Less: Allowances to the extent exempt u/s 10")
        output.append(
            f"   House Rent Allowance u/s 10(13A)                       ₹{hra_exemption:>15,.2f}"
        )
        output.append(
            f"   Total                                                   ₹{hra_exemption:>15,.2f}"
        )
        output.append("")

        income_chargeable = self.calculate_gross_salary() - hra_exemption
        output.append(
            f"3. Balance (1 - 2)                                         ₹{income_chargeable:>15,.2f}"
        )
        output.append("")

        output.append("4. Deductions under section 16")
        output.append(
            f"   (a) Standard deduction u/s 16(ia)                       ₹{self.standard_deduction:>15,.2f}"
        )
        output.append(
            f"   (b) Entertainment allowance u/s 16(ii)                  ₹{self.entertainment_allowance:>15,.2f}"
        )
        output.append(
            f"   (c) Tax on employment u/s 16(iii)                       ₹{self.professional_tax:>15,.2f}"
        )

        total_16_deductions = (
            self.standard_deduction
            + self.entertainment_allowance
            + self.professional_tax
        )
        output.append(
            f"   Total                                                   ₹{total_16_deductions:>15,.2f}"
        )
        output.append("")

        income_from_salary = max(0, income_chargeable - total_16_deductions)
        output.append(
            f"5. Income chargeable under 'Salaries' (3 - 4)              ₹{income_from_salary:>15,.2f}"
        )
        output.append("")

        output.append("6. Add: Any other income reported by the employee")
        output.append(
            f"   Other income                                            ₹{self.other_income:>15,.2f}"
        )
        output.append("")

        gti = income_from_salary + self.other_income
        output.append(
            f"7. Gross total income (5 + 6)                              ₹{gti:>15,.2f}"
        )
        output.append("")

        output.append("8. Deductions under Chapter VI-A")
        output.append(
            f"   (a) Section 80C                                         ₹{self.deductions_80c:>15,.2f}"
        )
        output.append(
            f"   (b) Section 80CCD(1B) - NPS                             ₹{self.deductions_80ccd1b:>15,.2f}"
        )
        output.append(
            f"   (c) Section 80D - Health Insurance                      ₹{self.deductions_80d:>15,.2f}"
        )
        output.append(
            f"   (d) Section 80E - Education Loan Interest               ₹{self.deductions_80e:>15,.2f}"
        )
        output.append(
            f"   (e) Section 80G - Donations                             ₹{self.deductions_80g:>15,.2f}"
        )
        output.append(
            f"   (f) Other deductions (if any)                           ₹{self.other_deductions:>15,.2f}"
        )

        total_via = self.calculate_total_deductions_via()
        output.append(
            f"   Total                                                   ₹{total_via:>15,.2f}"
        )
        output.append("")

        output.append(
            f"9. Total income (7 - 8)                                    ₹{tax_details['total_income']:>15,.2f}"
        )
        output.append("")

        output.append(
            f"10. Tax on total income                                    ₹{tax_details['tax_on_income']:>15,.2f}"
        )
        output.append("")

        if tax_details["surcharge"] > 0:
            output.append(
                f"11. Surcharge                                              ₹{tax_details['surcharge']:>15,.2f}"
            )
            output.append("")

        output.append(
            f"12. Health and Education Cess @ 4%                         ₹{tax_details['cess']:>15,.2f}"
        )
        output.append("")

        output.append(
            f"13. Total tax payable (10 + 11 + 12)                       ₹{tax_details['total_tax']:>15,.2f}"
        )
        output.append("")

        if self.relief_89 > 0:
            output.append(
                f"14. Relief under section 89                                ₹{self.relief_89:>15,.2f}"
            )
            output.append("")

        output.append(
            f"15. Net tax payable                                        ₹{tax_details['tax_after_relief']:>15,.2f}"
        )
        output.append("")

        output.append(
            f"16. Tax deducted at source (from Part A)                   ₹{self.total_tds_deposited:>15,.2f}"
        )
        output.append("")

        if tax_details["tax_balance"] > 0:
            output.append(
                f"17. Tax payable / (Refundable)                             ₹{tax_details['tax_balance']:>15,.2f} (Payable)"
            )
        else:
            output.append(
                f"17. Tax payable / (Refundable)                             ₹{abs(tax_details['tax_balance']):>15,.2f} (Refundable)"
            )

        output.append("")
        output.append("=" * 100)

        # Verification Part B
        output.append("")
        output.append("Verification")
        output.append(
            f"I, {self.employer_name}, do hereby certify that the information given above is true,"
        )
        output.append(
            "complete and correct and is based on the books of account, documents and other"
        )
        output.append("available records.")
        output.append("")
        output.append("Place: Bengaluru")
        output.append(f"Date: {datetime.now().strftime('%d-%b-%Y')}")
        output.append("")
        output.append("Signature of the person responsible for deduction of tax")
        output.append("Full Name: [Authorized Signatory]")
        output.append("Designation: [HR Manager]")
        output.append("")
        output.append("=" * 100)
        output.append("")
        output.append(
            "Note: This is a system-generated Form 16 and does not require physical signature."
        )
        output.append(f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}")

        return "\n".join(output)

    def export_to_file(
        self, filename: Optional[str] = None, hra_exemption: float = 0.0
    ):
        """Export Form 16 to text file"""
        if filename is None:
            filename = f"Form16_{self.employee_pan}_{self.financial_year.replace('-', '_')}.txt"

        form16_content = self.generate_form16(hra_exemption)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(form16_content)

        print(f"✓ Form 16 exported to: {filename}")
        return filename

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "employeeName": self.employee_name,
            "employeePan": self.employee_pan,
            "designation": self.designation,
            "employerName": self.employer_name,
            "employerTan": self.employer_tan,
            "employerPan": self.employer_pan,
            "employerAddress": self.employer_address,
            "financialYear": self.financial_year,
            "assessmentYear": self.assessment_year,
            "basicSalary": self.basic_salary,
            "dearnessAllowance": self.dearness_allowance,
            "hraReceived": self.hra_received,
            "otherAllowances": self.other_allowances,
            "perquisites": self.perquisites,
            "profitsInLieu": self.profits_in_lieu,
            "standardDeduction": self.standard_deduction,
            "entertainmentAllowance": self.entertainment_allowance,
            "professionalTax": self.professional_tax,
            "deductions80C": self.deductions_80c,
            "deductions80CCD1B": self.deductions_80ccd1b,
            "deductions80D": self.deductions_80d,
            "deductions80E": self.deductions_80e,
            "deductions80G": self.deductions_80g,
            "otherDeductions": self.other_deductions,
            "quarterlyTds": [
                {
                    "quarter": q.quarter,
                    "quarterPeriod": q.quarter_period,
                    "receiptNumbers": q.receipt_numbers,
                    "tdsDeposited": q.tds_deposited,
                    "depositDates": [d.isoformat() for d in q.deposit_dates],
                }
                for q in self.quarterly_tds
            ],
            "totalTdsDeposited": self.total_tds_deposited,
            "otherIncome": self.other_income,
            "relief89": self.relief_89,
        }

    @staticmethod
    def from_dict(data: dict) -> "Form16":
        """Deserialize from dictionary"""
        form = Form16(
            employee_name=data["employeeName"],
            employee_pan=data["employeePan"],
            designation=data["designation"],
            employer_name=data["employerName"],
            employer_tan=data["employerTan"],
            employer_pan=data["employerPan"],
            employer_address=data["employerAddress"],
            financial_year=data["financialYear"],
            assessment_year=data["assessmentYear"],
        )

        form.set_salary_components(
            basic=data["basicSalary"],
            da=data["dearnessAllowance"],
            hra=data["hraReceived"],
            other_allowances=data["otherAllowances"],
            perquisites=data["perquisites"],
            profits_in_lieu=data["profitsInLieu"],
        )

        form.standard_deduction = data["standardDeduction"]
        form.entertainment_allowance = data["entertainmentAllowance"]
        form.professional_tax = data["professionalTax"]

        form.set_chapter_via_deductions(
            deduction_80c=data["deductions80C"],
            deduction_80ccd1b=data["deductions80CCD1B"],
            deduction_80d=data["deductions80D"],
            deduction_80e=data["deductions80E"],
            deduction_80g=data["deductions80G"],
            other=data["otherDeductions"],
        )

        for q_data in data.get("quarterlyTds", []):
            quarter_tds = QuarterlyTDS(
                quarter=q_data["quarter"],
                quarter_period=q_data["quarterPeriod"],
                receipt_numbers=q_data["receiptNumbers"],
                tds_deposited=q_data["tdsDeposited"],
                deposit_dates=[date.fromisoformat(d) for d in q_data["depositDates"]],
            )
            form.add_quarterly_tds(quarter_tds)

        form.other_income = data["otherIncome"]
        form.relief_89 = data["relief89"]

        return form
