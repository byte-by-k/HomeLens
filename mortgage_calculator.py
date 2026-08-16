"""Deterministic mortgage and monthly housing-cost calculations."""

from pydantic import BaseModel, Field


class MortgageEstimate(BaseModel):
    """Itemized educational estimate for financing and ownership costs."""

    purchase_price: float = Field(ge=0)
    down_payment: float = Field(ge=0)
    loan_amount: float = Field(ge=0)
    monthly_principal_and_interest: float = Field(ge=0)
    monthly_property_tax: float = Field(ge=0)
    monthly_homeowners_insurance: float = Field(ge=0)
    monthly_hoa: float = Field(ge=0)
    monthly_pmi: float = Field(ge=0)
    monthly_maintenance: float = Field(ge=0)
    total_estimated_monthly_cost: float = Field(ge=0)
    estimated_closing_costs: float = Field(ge=0)
    estimated_cash_needed: float = Field(ge=0)


def calculate_mortgage(
    purchase_price: float,
    down_payment_percent: float,
    annual_interest_rate: float,
    loan_term_years: int,
    annual_property_taxes: float,
    annual_homeowners_insurance: float,
    monthly_hoa: float,
    annual_pmi_rate: float,
    annual_maintenance_percent: float,
    closing_cost_percent: float,
) -> MortgageEstimate:
    """Calculate an itemized estimate using the standard amortization formula."""
    if purchase_price <= 0:
        raise ValueError("Purchase price must be greater than zero.")
    if not 0 <= down_payment_percent <= 100:
        raise ValueError("Down payment percentage must be between 0 and 100.")
    if annual_interest_rate < 0 or loan_term_years <= 0:
        raise ValueError("Interest rate and loan term must be valid.")

    down_payment = purchase_price * down_payment_percent / 100
    loan_amount = purchase_price - down_payment
    number_of_payments = loan_term_years * 12
    monthly_rate = annual_interest_rate / 100 / 12

    if loan_amount == 0:
        principal_and_interest = 0.0
    elif monthly_rate == 0:
        principal_and_interest = loan_amount / number_of_payments
    else:
        growth = (1 + monthly_rate) ** number_of_payments
        principal_and_interest = loan_amount * monthly_rate * growth / (growth - 1)

    property_tax = max(annual_property_taxes, 0) / 12
    insurance = max(annual_homeowners_insurance, 0) / 12
    hoa = max(monthly_hoa, 0)
    pmi = loan_amount * max(annual_pmi_rate, 0) / 100 / 12 if down_payment_percent < 20 else 0.0
    maintenance = purchase_price * max(annual_maintenance_percent, 0) / 100 / 12
    total_monthly = principal_and_interest + property_tax + insurance + hoa + pmi + maintenance
    closing_costs = purchase_price * max(closing_cost_percent, 0) / 100

    return MortgageEstimate(
        purchase_price=purchase_price,
        down_payment=down_payment,
        loan_amount=loan_amount,
        monthly_principal_and_interest=principal_and_interest,
        monthly_property_tax=property_tax,
        monthly_homeowners_insurance=insurance,
        monthly_hoa=hoa,
        monthly_pmi=pmi,
        monthly_maintenance=maintenance,
        total_estimated_monthly_cost=total_monthly,
        estimated_closing_costs=closing_costs,
        estimated_cash_needed=down_payment + closing_costs,
    )
