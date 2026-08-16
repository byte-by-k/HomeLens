import pytest

from mortgage_calculator import calculate_mortgage


def test_itemized_mortgage_estimate() -> None:
    estimate = calculate_mortgage(500_000, 20, 6, 30, 12_000, 2_400, 100, 0.5, 1, 3)
    assert estimate.loan_amount == 400_000
    assert estimate.monthly_property_tax == 1_000
    assert estimate.monthly_homeowners_insurance == 200
    assert estimate.monthly_pmi == 0
    assert estimate.estimated_closing_costs == 15_000
    assert estimate.estimated_cash_needed == 115_000
    assert estimate.total_estimated_monthly_cost > 3_000


def test_pmi_is_included_below_twenty_percent_down() -> None:
    estimate = calculate_mortgage(500_000, 10, 6, 30, 0, 0, 0, 0.5, 0, 0)
    assert estimate.monthly_pmi == pytest.approx(187.5)


def test_zero_interest_uses_simple_principal_division() -> None:
    estimate = calculate_mortgage(120_000, 0, 0, 30, 0, 0, 0, 0, 0, 0)
    assert estimate.monthly_principal_and_interest == pytest.approx(333.3333, rel=1e-4)


def test_invalid_purchase_price_is_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_mortgage(0, 20, 6, 30, 0, 0, 0, 0, 0, 0)
