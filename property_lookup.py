"""Direct RentCast property lookup used to prefill the Streamlit form."""

from typing import Any

import httpx


RENTCAST_BASE_URL = "https://api.rentcast.io/v1"


class PropertyLookupError(Exception):
    """A safe, user-facing property lookup failure."""


def _latest_property_tax(property_taxes: Any) -> float:
    """Return the newest available annual tax total."""
    if not isinstance(property_taxes, dict) or not property_taxes:
        return 0.0
    records = [record for record in property_taxes.values() if isinstance(record, dict)]
    if not records:
        return 0.0
    latest = max(records, key=lambda record: int(record.get("year", 0) or 0))
    return float(latest.get("total", 0) or 0)


def _property_type_label(value: Any) -> str:
    """Map RentCast labels to the options shown in the form."""
    mapping = {
        "Single Family": "Single-family home",
        "Condo": "Condominium",
        "Townhouse": "Townhouse",
        "Multi-Family": "Multi-family home",
    }
    return mapping.get(str(value or ""), "Other")


def normalize_property_data(
    property_record: dict[str, Any], listing_record: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Convert RentCast records to the app's form fields."""
    listing = listing_record or {}
    source = {**property_record, **{key: value for key, value in listing.items() if value is not None}}
    hoa = source.get("hoa") if isinstance(source.get("hoa"), dict) else {}
    listing_description = listing.get("text") or listing.get("description") or ""

    return {
        "address": source.get("formattedAddress", ""),
        "listing_price": float(listing.get("price", 0) or 0),
        "bedrooms": int(source.get("bedrooms", 0) or 0),
        "bathrooms": float(source.get("bathrooms", 0) or 0),
        "square_footage": int(source.get("squareFootage", 0) or 0),
        "year_built": int(source.get("yearBuilt", 0) or 0),
        "annual_property_taxes": _latest_property_tax(
            property_record.get("propertyTaxes")
        ),
        "monthly_hoa_fee": float(hoa.get("fee", 0) or 0),
        "property_type": _property_type_label(source.get("propertyType")),
        "property_description": str(listing_description),
        "preferred_location": ", ".join(
            part for part in [source.get("city"), source.get("state")] if part
        ),
    }


def _get_records(
    client: httpx.Client, endpoint: str, address: str, api_key: str
) -> list[dict[str, Any]]:
    response = client.get(
        f"{RENTCAST_BASE_URL}/{endpoint}",
        params={"address": address, "limit": 1},
        headers={"Accept": "application/json", "X-Api-Key": api_key},
    )
    if response.status_code in {401, 403}:
        raise PropertyLookupError("RentCast authentication failed. Check RENTCAST_API_KEY.")
    if response.status_code == 429:
        raise PropertyLookupError("RentCast rate limit reached. Please try again later.")
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, list) else []


def lookup_property(address: str, api_key: str) -> dict[str, Any]:
    """Retrieve public property data and any current sale listing by address."""
    if not address.strip():
        raise PropertyLookupError("Enter a full property address before lookup.")
    if not api_key.strip():
        raise PropertyLookupError("RENTCAST_API_KEY is not configured.")

    try:
        with httpx.Client(timeout=20.0) as client:
            properties = _get_records(client, "properties", address, api_key)
            listings = _get_records(client, "listings/sale", address, api_key)
    except PropertyLookupError:
        raise
    except httpx.TimeoutException as exc:
        raise PropertyLookupError("Property lookup timed out. Please try again.") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise PropertyLookupError("Property lookup failed. Please try again.") from exc

    if not properties and not listings:
        raise PropertyLookupError("No matching property was found for that address.")

    return normalize_property_data(
        properties[0] if properties else listings[0],
        listings[0] if listings else None,
    )
