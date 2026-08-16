from property_lookup import normalize_property_data


def test_normalize_property_and_listing_data() -> None:
    property_record = {
        "formattedAddress": "123 Main St, Austin, TX 78701",
        "city": "Austin",
        "state": "TX",
        "propertyType": "Single Family",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "squareFootage": 2400,
        "yearBuilt": 1998,
        "hoa": {"fee": 125},
        "propertyTaxes": {
            "2023": {"year": 2023, "total": 9000},
            "2024": {"year": 2024, "total": 9500},
        },
    }
    listing_record = {"price": 725000, "text": "Active four-bedroom listing"}

    result = normalize_property_data(property_record, listing_record)

    assert result["address"] == "123 Main St, Austin, TX 78701"
    assert result["listing_price"] == 725000
    assert result["annual_property_taxes"] == 9500
    assert result["monthly_hoa_fee"] == 125
    assert result["property_type"] == "Single-family home"
    assert result["preferred_location"] == "Austin, TX"


def test_unknown_fields_use_editable_defaults() -> None:
    result = normalize_property_data({"formattedAddress": "Unknown"})
    assert result["listing_price"] == 0
    assert result["annual_property_taxes"] == 0
    assert result["property_type"] == "Other"
