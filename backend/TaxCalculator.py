"""
Tax Calculator with Deduction Support
Calculates taxable income and tax liability with deductions applied
"""

from typing import Dict, Tuple


class TaxCalculator:
    """Calculates tax liability with deductions"""

    def __init__(self, customer, bank):
        self.customer = customer
        self.bank = bank
        self.salary = getattr(customer, "salary", 0)
        self.annual_salary = self.salary * 12
        
        # Convert List[TaxExemption] or Dict to Dict[section, amount]
        self.deductions = {}
        # Try tax_deductions first (legacy), then tax_exemptions (new)
        exemptions = getattr(customer, "tax_deductions", getattr(customer, "tax_exemptions", []))
        
        if isinstance(exemptions, list):
            for ex in exemptions:
                if hasattr(ex, "section") and hasattr(ex, "eligible_amount"):
                    self.deductions[ex.section] = self.deductions.get(ex.section, 0) + ex.eligible_amount
                elif isinstance(ex, dict) and "section" in ex:
                    self.deductions[ex["section"]] = self.deductions.get(ex["section"], 0) + ex.get("eligibleAmount", 0)
        elif isinstance(exemptions, dict):
            self.deductions = exemptions

    def get_tax_summary(self) -> dict:
        """Get a summary of tax for the customer"""
        taxable_income, tax_payable, tax_rate = self.calculate_tax_with_deductions(
            self.annual_salary, self.deductions
        )
        return {
            "gross_annual": self.annual_salary,
            "taxable_income": taxable_income,
            "tax_payable": tax_payable,
            "tax_rate": tax_rate,
            "deductions": self.deductions
        }

    # Your existing tax brackets (as per your system)
    TAX_SLABS = [
        (1800000, 0.0),  # Up to ₹18,00,000: 0%
        (2200000, 0.15),  # ₹18,00,001-₹22,00,000: 15%
        (2600000, 0.20),  # ₹22,00,001-₹26,00,000: 20%
        (3000000, 0.25),  # ₹26,00,001-₹30,00,000: 25%
        (float("inf"), 0.30),  # Above ₹30,00,000: 30%
    ]

    @staticmethod
    def calculate_tax_with_deductions(
        gross_annual_salary: float, deductions: Dict[str, float]
    ) -> Tuple[float, float, float]:
        """
        Calculate tax with deductions applied

        Args:
            gross_annual_salary: Annual gross salary
            deductions: Dictionary of section -> eligible_amount

        Returns:
            (taxable_income, tax_payable, tax_rate_percentage)
        """
        # Calculate total deductions
        total_deductions = sum(deductions.values())

        # Taxable income = Gross - Deductions
        taxable_income = max(0, gross_annual_salary - total_deductions)

        # Apply tax bracket
        tax_rate = TaxCalculator._get_tax_rate(taxable_income)
        tax_payable = round(taxable_income * tax_rate, 2)

        return taxable_income, tax_payable, tax_rate

    @staticmethod
    def calculate_tax_without_deductions(
        gross_annual_salary: float,
    ) -> Tuple[float, float]:
        """
        Calculate tax without deductions (old method)
        This is what your current system does

        Args:
            gross_annual_salary: Annual gross salary

        Returns:
            (tax_payable, tax_rate_percentage)
        """
        tax_rate = TaxCalculator._get_tax_rate(gross_annual_salary)
        tax_payable = round(gross_annual_salary * tax_rate, 2)

        return tax_payable, tax_rate

    @staticmethod
    def _get_tax_rate(annual_income: float) -> float:
        """
        Determine tax rate based on income slab

        Args:
            annual_income: Annual income in rupees

        Returns:
            Tax rate as decimal (0.0 to 0.30)
        """
        for limit, rate in TaxCalculator.TAX_SLABS:
            if annual_income <= limit:
                return rate

        return 0.30  # Default to highest rate

    @staticmethod
    def calculate_monthly_tax_with_deductions(
        monthly_salary: float, annual_deductions: Dict[str, float]
    ) -> Tuple[float, float, float]:
        """
        Calculate monthly tax with deductions

        Args:
            monthly_salary: Monthly gross salary
            annual_deductions: Annual deductions dictionary

        Returns:
            (monthly_taxable, monthly_tax, monthly_tax_rate)
        """
        gross_annual = monthly_salary * 12
        taxable_income, annual_tax, tax_rate = (
            TaxCalculator.calculate_tax_with_deductions(gross_annual, annual_deductions)
        )

        monthly_taxable = taxable_income / 12
        monthly_tax = annual_tax / 12

        return monthly_taxable, monthly_tax, tax_rate

    @staticmethod
    def generate_tax_report(
        customer_name: str,
        gross_annual_salary: float,
        monthly_salary: float,
        deductions: Dict[str, float],
        salary_days: int = 30,
    ) -> str:
        """
        Generate formatted tax computation report

        Args:
            customer_name: Employee name
            gross_annual_salary: Annual gross salary
            monthly_salary: Monthly gross salary
            deductions: Dictionary of deductions
            salary_days: Number of salary credit days

        Returns:
            Formatted report string
        """
        # Calculate tax with deductions
        taxable_income, tax_with_deductions, tax_rate = (
            TaxCalculator.calculate_tax_with_deductions(gross_annual_salary, deductions)
        )

        # Calculate tax without deductions for comparison
        tax_without_deductions, _ = TaxCalculator.calculate_tax_without_deductions(
            gross_annual_salary
        )

        # Calculate monthly figures
        monthly_tax_with_deductions = tax_with_deductions / 12
        monthly_net_with_deductions = monthly_salary - monthly_tax_with_deductions

        monthly_tax_without_deductions = tax_without_deductions / 12
        monthly_net_without_deductions = monthly_salary - monthly_tax_without_deductions

        # Tax savings
        annual_tax_saved = tax_without_deductions - tax_with_deductions
        monthly_tax_saved = annual_tax_saved / 12
        savings_percentage = (
            (annual_tax_saved / tax_without_deductions * 100)
            if tax_without_deductions > 0
            else 0
        )

        # Build report
        report = f"""
╔════════════════════════════════════════════════════════════╗
║                    TAX COMPUTATION REPORT                  ║
║                    Financial Year 2025-26                  ║
╚════════════════════════════════════════════════════════════╝

EMPLOYEE: {customer_name}
═════════════════════════════════════════════════════════════

GROSS INCOME:
   Monthly Salary: ₹{monthly_salary:,.2f}
   Annual Salary:  ₹{gross_annual_salary:,.2f}

DEDUCTIONS:
"""

        section_names = {
            "16": "Standard Deduction (Section 16)",
            "10(13A)": "HRA - House Rent Allowance",
            "80C": "Section 80C (EPF, Life Insurance, etc.)",
            "80D": "Section 80D (Medical Insurance)",
            "24": "Section 24 (Home Loan Interest)",
        }

        total_deductions = 0.0
        for section, amount in deductions.items():
            if amount > 0:
                name = section_names.get(section, section)
                report += f"   [OK] {name}: ₹{amount:,.2f}\n"
                total_deductions += amount

        report += f"""
   ─────────────────────────────
   TOTAL DEDUCTIONS: ₹{total_deductions:,.2f}

TAXABLE INCOME:
   Annual: ₹{gross_annual_salary:,.2f} - ₹{total_deductions:,.2f} = ₹{taxable_income:,.2f}
   Monthly: ₹{taxable_income / 12:,.2f}

TAX CALCULATION:
   Taxable Income: ₹{taxable_income:,.2f}
   Tax Rate: {tax_rate * 100:.0f}%
   Annual Tax: ₹{tax_with_deductions:,.2f}
   Monthly Tax: ₹{monthly_tax_with_deductions:,.2f}

NET SALARY:
   Annual: ₹{gross_annual_salary - tax_with_deductions:,.2f}
   Monthly: ₹{monthly_net_with_deductions:,.2f}

═════════════════════════════════════════════════════════════

TAX BENEFIT SUMMARY:
   Annual Tax Without Deductions: ₹{tax_without_deductions:,.2f}
   Annual Tax With Deductions:    ₹{tax_with_deductions:,.2f}
   ─────────────────────────────
   [MONEY] TAX SAVED ANNUALLY: ₹{annual_tax_saved:,.2f} ({savings_percentage:.1f}%)
   [MONEY] TAX SAVED MONTHLY:  ₹{monthly_tax_saved:,.2f}

═════════════════════════════════════════════════════════════

COMPARISON:
                          Without Deductions    With Deductions    Savings
Annual Gross            ₹{gross_annual_salary:>16,.2f}   ₹{gross_annual_salary:>16,.2f}        -
Annual Deductions       ₹{0:>16,.2f}   ₹{total_deductions:>16,.2f}   ₹{total_deductions:>14,.2f}
Annual Taxable          ₹{gross_annual_salary:>16,.2f}   ₹{taxable_income:>16,.2f}   ₹{gross_annual_salary - taxable_income:>14,.2f}
Annual Tax              ₹{tax_without_deductions:>16,.2f}   ₹{tax_with_deductions:>16,.2f}   ₹{annual_tax_saved:>14,.2f}
Annual Net              ₹{gross_annual_salary - tax_without_deductions:>16,.2f}   ₹{gross_annual_salary - tax_with_deductions:>16,.2f}   ₹{annual_tax_saved:>14,.2f}

Monthly Net             ₹{monthly_net_without_deductions:>16,.2f}   ₹{monthly_net_with_deductions:>16,.2f}   ₹{monthly_tax_saved:>14,.2f}

═════════════════════════════════════════════════════════════
"""
        return report

    @staticmethod
    def compare_regimes(
        gross_annual_salary: float, deductions_old_regime: Dict[str, float]
    ) -> Tuple[str, Dict]:
        """
        Compare Old Regime (with deductions) vs New Regime (no deductions)

        Args:
            gross_annual_salary: Annual gross salary
            deductions_old_regime: Deductions for old regime

        Returns:
            (recommendation, details_dict)
        """
        # Old regime with deductions
        old_regime_taxable, old_regime_tax, old_regime_rate = (
            TaxCalculator.calculate_tax_with_deductions(
                gross_annual_salary, deductions_old_regime
            )
        )

        # New regime (no deductions, no exemptions)
        new_regime_tax, new_regime_rate = (
            TaxCalculator.calculate_tax_without_deductions(gross_annual_salary)
        )

        # Annual net income
        old_regime_net = gross_annual_salary - old_regime_tax
        new_regime_net = gross_annual_salary - new_regime_tax

        # Difference
        tax_difference = abs(old_regime_tax - new_regime_tax)
        better_regime = (
            "OLD REGIME" if old_regime_tax < new_regime_tax else "NEW REGIME"
        )

        # Details dictionary
        details = {
            "old_regime": {
                "gross": gross_annual_salary,
                "total_deductions": sum(deductions_old_regime.values()),
                "taxable": old_regime_taxable,
                "tax": old_regime_tax,
                "tax_rate": old_regime_rate,
                "net": old_regime_net,
                "monthly_tax": old_regime_tax / 12,
                "monthly_net": old_regime_net / 12,
            },
            "new_regime": {
                "gross": gross_annual_salary,
                "taxable": gross_annual_salary,
                "tax": new_regime_tax,
                "tax_rate": new_regime_rate,
                "net": new_regime_net,
                "monthly_tax": new_regime_tax / 12,
                "monthly_net": new_regime_net / 12,
            },
            "tax_savings": tax_difference,
        }

        return better_regime, details
