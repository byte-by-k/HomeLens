from datetime import date

from validation import validate_inputs


def valid_inputs() -> tuple[dict, dict]:
    buyer = {
        "maximum_budget": 750_000,
        "preferred_location": "South Brunswick, New Jersey",
        "minimum_bedrooms": 4,
        "minimum_bathrooms": 2.5,
        "maximum_commute_minutes": 45,
        "maximum_property_age": 30,
    }
    property_info = {
        "address": "Sample Property",
        "listing_price": 725_000,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "square_footage": 2_400,
        "year_built": 1998,
        "annual_property_taxes": 14_000,
        "monthly_hoa_fee": 0,
        "school_rating": 8,
        "estimated_commute_minutes": 40,
        "property_type": "Single-family home",
    }
    return buyer, property_info


def test_valid_input_has_no_errors() -> None:
    buyer, property_info = valid_inputs()
    assert validate_inputs(buyer, property_info) == []


def test_required_address_is_validated() -> None:
    buyer, property_info = valid_inputs()
    property_info["address"] = " "
    assert "Property address is required." in validate_inputs(buyer, property_info)


def test_invalid_budget_and_listing_price_are_validated() -> None:
    buyer, property_info = valid_inputs()
    buyer["maximum_budget"] = 0
    property_info["listing_price"] = -1
    errors = validate_inputs(buyer, property_info)
    assert any("budget" in error.lower() for error in errors)
    assert any("listing price" in error.lower() for error in errors)


def test_invalid_bedroom_and_bathroom_values_are_validated() -> None:
    buyer, property_info = valid_inputs()
    property_info["bedrooms"] = 0
    property_info["bathrooms"] = -1
    errors = validate_inputs(buyer, property_info)
    assert any("property bedrooms" in error.lower() for error in errors)
    assert any("property bathrooms" in error.lower() for error in errors)


def test_future_year_is_invalid() -> None:
    buyer, property_info = valid_inputs()
    property_info["year_built"] = date.today().year + 1
    assert any("year built" in error.lower() for error in validate_inputs(buyer, property_info))
