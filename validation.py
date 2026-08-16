"""Deterministic validation for user-entered buyer and property data."""

from datetime import date
from typing import Any


def validate_inputs(buyer: dict[str, Any], property_info: dict[str, Any]) -> list[str]:
    """Return user-friendly validation errors; an empty list means valid input."""
    errors: list[str] = []

    if buyer.get("maximum_budget", 0) <= 0:
        errors.append("Maximum purchase budget must be greater than $0.")
    if not str(buyer.get("preferred_location", "")).strip():
        errors.append("Preferred city or location is required.")
    if buyer.get("minimum_bedrooms", 0) <= 0:
        errors.append("Minimum bedrooms must be greater than 0.")
    if buyer.get("minimum_bathrooms", 0) <= 0:
        errors.append("Minimum bathrooms must be greater than 0.")
    if buyer.get("maximum_commute_minutes", 0) <= 0:
        errors.append("Maximum acceptable commute must be greater than 0 minutes.")
    if buyer.get("maximum_property_age", -1) < 0:
        errors.append("Preferred maximum property age cannot be negative.")

    if not str(property_info.get("address", "")).strip():
        errors.append("Property address is required.")
    if property_info.get("listing_price", 0) <= 0:
        errors.append("Listing price must be greater than $0.")
    if property_info.get("bedrooms", 0) <= 0:
        errors.append("Property bedrooms must be greater than 0.")
    if property_info.get("bathrooms", 0) <= 0:
        errors.append("Property bathrooms must be greater than 0.")
    if property_info.get("square_footage", 0) <= 0:
        errors.append("Square footage must be greater than 0.")

    year_built = property_info.get("year_built", 0)
    if not 1600 <= year_built <= date.today().year:
        errors.append(f"Year built must be between 1600 and {date.today().year}.")
    if property_info.get("annual_property_taxes", -1) < 0:
        errors.append("Annual property taxes cannot be negative.")
    if property_info.get("monthly_hoa_fee", -1) < 0:
        errors.append("Monthly HOA fee cannot be negative.")
    if not 0 <= property_info.get("school_rating", -1) <= 10:
        errors.append("School rating must be between 0 and 10.")
    if property_info.get("estimated_commute_minutes", -1) < 0:
        errors.append("Estimated commute cannot be negative.")
    if not str(property_info.get("property_type", "")).strip():
        errors.append("Property type is required.")

    return errors
