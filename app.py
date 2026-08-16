"""Streamlit interface for Home Lens."""

import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from home_analysis_chain import analyze_property
from mortgage_calculator import MortgageEstimate, calculate_mortgage
from models import HomeAnalysis
from property_lookup import PropertyLookupError, lookup_property
from validation import validate_inputs

load_dotenv()

st.set_page_config(page_title="Home Lens", page_icon="🏠", layout="wide")


SAMPLE_VALUES: dict[str, Any] = {
    "maximum_budget": 750_000.0,
    "preferred_location": "South Brunswick, New Jersey",
    "minimum_bedrooms": 4,
    "minimum_bathrooms": 2.5,
    "school_importance": "High",
    "maximum_commute_minutes": 45,
    "maximum_property_age": 30,
    "must_have_features": ["Garage", "Backyard", "Home office"],
    "additional_requirements": "Suitable for a family with children",
    "listing_url": "",
    "address": "Sample Property, South Brunswick, New Jersey",
    "listing_price": 725_000.0,
    "bedrooms": 4,
    "bathrooms": 2.5,
    "square_footage": 2_400,
    "year_built": 1998,
    "annual_property_taxes": 14_000.0,
    "monthly_hoa_fee": 0.0,
    "school_rating": 8.0,
    "estimated_commute_minutes": 40,
    "property_type": "Single-family home",
    "property_description": (
        "Four-bedroom home with an attached garage, backyard, and additional "
        "room that could be used as a home office"
    ),
    "known_concerns": "Older HVAC system and original windows",
    "down_payment_percent": 20.0,
    "annual_interest_rate": 6.5,
    "loan_term_years": 30,
    "annual_homeowners_insurance": 2_000.0,
    "annual_pmi_rate": 0.5,
    "annual_maintenance_percent": 1.0,
    "closing_cost_percent": 3.0,
}


def load_sample() -> None:
    """Populate session state with fictional demonstration values."""
    st.session_state.update(SAMPLE_VALUES)
    st.session_state["sample_loaded"] = True
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("mortgage_estimate", None)


def load_property_from_api() -> None:
    """Look up an address and prefill all fields returned by RentCast."""
    address = str(st.session_state.get("lookup_address", ""))
    api_key = os.getenv("RENTCAST_API_KEY", "")
    try:
        with st.spinner("Looking up public property and listing data..."):
            values = lookup_property(address, api_key)
    except PropertyLookupError as exc:
        st.session_state["lookup_error"] = str(exc)
        st.session_state.pop("lookup_success", None)
        return

    for key, value in values.items():
        # Do not overwrite a useful form value with a field unavailable from the API.
        if value not in ("", 0, 0.0, None):
            st.session_state[key] = value
    st.session_state["lookup_success"] = (
        "Property data loaded. Review all fields—API data may be incomplete or outdated."
    )
    st.session_state.pop("lookup_error", None)
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("mortgage_estimate", None)


def render_bullets(items: list[str], empty_message: str = "None identified.") -> None:
    """Render readable bullets without displaying an empty section."""
    if not items:
        st.write(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def display_results(result: HomeAnalysis) -> None:
    """Display a validated model response for a nontechnical buyer."""
    st.divider()
    st.header("Property Fit Analysis")

    recommendation_renderers = {
        "Strong Fit": st.success,
        "Consider": st.warning,
        "Not Recommended": st.error,
    }
    recommendation_renderers[result.recommendation](
        f"Recommendation: {result.recommendation}"
    )

    score_column, summary_column = st.columns([1, 3])
    with score_column:
        st.metric("Fit Score", f"{result.fit_score}/100")
        st.progress(result.fit_score / 100)
    with summary_column:
        st.subheader("Executive Summary")
        st.write(result.executive_summary)

    fits_column, unmet_column = st.columns(2)
    with fits_column:
        with st.container(border=True):
            st.subheader("Why This Property Fits")
            render_bullets(result.matching_features)
    with unmet_column:
        with st.container(border=True):
            st.subheader("Unmet Buyer Preferences")
            render_bullets(result.unmet_preferences)

    with st.expander("Concerns and Risks", expanded=True):
        render_bullets(result.concerns_and_risks)
    with st.expander("Missing Information", expanded=True):
        render_bullets(result.missing_information)
    with st.expander("Questions for the Listing Agent", expanded=True):
        render_bullets(result.questions_for_agent)
    with st.expander("Assumptions"):
        render_bullets(result.assumptions, "No assumptions were used.")

    st.subheader("Final Assessment")
    st.write(result.final_assessment)
    st.info(result.disclaimer)


def display_mortgage_estimate(estimate: MortgageEstimate) -> None:
    """Display financing costs separately from the AI recommendation."""
    st.divider()
    st.header("Estimated Mortgage and Monthly Ownership Cost")
    st.metric("Estimated Total Monthly Cost", f"${estimate.total_estimated_monthly_cost:,.0f}")

    first_row = st.columns(4)
    first_row[0].metric("Principal & Interest", f"${estimate.monthly_principal_and_interest:,.0f}")
    first_row[1].metric("Property Tax", f"${estimate.monthly_property_tax:,.0f}")
    first_row[2].metric("Home Insurance", f"${estimate.monthly_homeowners_insurance:,.0f}")
    first_row[3].metric("HOA", f"${estimate.monthly_hoa:,.0f}")

    second_row = st.columns(4)
    second_row[0].metric("PMI", f"${estimate.monthly_pmi:,.0f}")
    second_row[1].metric("Maintenance Reserve", f"${estimate.monthly_maintenance:,.0f}")
    second_row[2].metric("Loan Amount", f"${estimate.loan_amount:,.0f}")
    second_row[3].metric("Down Payment", f"${estimate.down_payment:,.0f}")

    with st.expander("Upfront cash estimate", expanded=True):
        st.write(f"Estimated closing costs: **${estimate.estimated_closing_costs:,.0f}**")
        st.write(f"Down payment plus closing costs: **${estimate.estimated_cash_needed:,.0f}**")
    st.info(
        "Educational estimate only—not a loan quote. Actual rates, insurance, PMI, "
        "taxes, closing costs, and lender fees vary. Utilities are not included."
    )


def main() -> None:
    """Render the form, validate it, and run analysis on demand."""
    financing_defaults = {
        "down_payment_percent": 20.0,
        "annual_interest_rate": 6.5,
        "loan_term_years": 30,
        "annual_homeowners_insurance": 2_000.0,
        "annual_pmi_rate": 0.5,
        "annual_maintenance_percent": 1.0,
        "closing_cost_percent": 3.0,
    }
    for key, value in financing_defaults.items():
        st.session_state.setdefault(key, value)

    st.title("Home Lens")
    st.subheader(
        "Understand whether a house truly fits your family—not just your search filters."
    )
    st.write(
        "Enter your home-buying preferences and property information to receive "
        "an AI-generated fit analysis."
    )
    st.info(
        "API-enhanced version: Search by a full US address to prefill available "
        "property details, then review them before analysis."
    )

    st.header("Property Lookup")
    lookup_column, button_column = st.columns([4, 1])
    with lookup_column:
        st.text_input(
            "Full US property address",
            key="lookup_address",
            placeholder="5500 Grand Lake Dr, San Antonio, TX 78244",
        )
    with button_column:
        st.write("")
        st.write("")
        st.button("Look Up Property", type="primary", on_click=load_property_from_api)
    st.caption(
        "Lookup uses RentCast public-record and sale-listing data. One lookup uses "
        "two API requests. School rating, commute, and concerns still require review."
    )
    if st.session_state.get("lookup_error"):
        st.error(st.session_state["lookup_error"])
        if "configured" in st.session_state["lookup_error"]:
            st.code("RENTCAST_API_KEY=your_api_key", language="text")
    if st.session_state.get("lookup_success"):
        st.success(st.session_state["lookup_success"])

    if st.button("Load Sample Property", help="Loads fictional demonstration data"):
        load_sample()
    if st.session_state.get("sample_loaded"):
        st.caption("Fictional sample data loaded—not a real or currently available property.")

    with st.form("property_analysis_form"):
        st.header("1. Buyer Preferences")
        left, right = st.columns(2)
        with left:
            maximum_budget = st.number_input(
                "Maximum purchase budget ($)", min_value=0.0, step=10_000.0,
                key="maximum_budget"
            )
            preferred_location = st.text_input(
                "Preferred city or location", key="preferred_location"
            )
            minimum_bedrooms = st.number_input(
                "Minimum bedrooms", min_value=0, step=1, key="minimum_bedrooms"
            )
            minimum_bathrooms = st.number_input(
                "Minimum bathrooms", min_value=0.0, step=0.5, key="minimum_bathrooms"
            )
        with right:
            school_importance = st.selectbox(
                "School importance", ["Low", "Medium", "High"], key="school_importance"
            )
            maximum_commute_minutes = st.number_input(
                "Maximum acceptable commute (minutes)", min_value=0, step=5,
                key="maximum_commute_minutes"
            )
            maximum_property_age = st.number_input(
                "Preferred maximum property age (years)", min_value=0, step=1,
                key="maximum_property_age"
            )
            must_have_features = st.multiselect(
                "Must-have features",
                ["Garage", "Backyard", "Home office", "Basement", "First-floor bedroom", "Updated kitchen"],
                key="must_have_features",
            )
        additional_requirements = st.text_area(
            "Additional family requirements", key="additional_requirements"
        )

        st.header("2. Property Information")
        listing_url = st.text_input(
            "Zillow or listing URL (optional—reference only)", key="listing_url",
            help="The application stores this as text and never opens or verifies the URL."
        )
        address = st.text_input("Property address", key="address")
        property_left, property_right = st.columns(2)
        with property_left:
            listing_price = st.number_input(
                "Listing price ($)", min_value=0.0, step=10_000.0, key="listing_price"
            )
            bedrooms = st.number_input("Bedrooms", min_value=0, step=1, key="bedrooms")
            bathrooms = st.number_input(
                "Bathrooms", min_value=0.0, step=0.5, key="bathrooms"
            )
            square_footage = st.number_input(
                "Square footage", min_value=0, step=100, key="square_footage"
            )
            year_built = st.number_input(
                "Year built", min_value=1600, step=1, key="year_built"
            )
            annual_property_taxes = st.number_input(
                "Annual property taxes ($)", min_value=0.0, step=500.0,
                key="annual_property_taxes"
            )
        with property_right:
            monthly_hoa_fee = st.number_input(
                "Monthly HOA fee ($)", min_value=0.0, step=25.0, key="monthly_hoa_fee"
            )
            school_rating = st.number_input(
                "School rating (0–10)", min_value=0.0, max_value=10.0, step=0.5,
                key="school_rating"
            )
            estimated_commute_minutes = st.number_input(
                "Estimated commute (minutes)", min_value=0, step=5,
                key="estimated_commute_minutes"
            )
            property_type = st.selectbox(
                "Property type",
                ["Single-family home", "Townhouse", "Condominium", "Multi-family home", "Other"],
                key="property_type",
            )
        property_description = st.text_area(
            "Property description", key="property_description"
        )
        known_concerns = st.text_area("Known concerns", key="known_concerns")

        st.header("3. Mortgage and Cost Assumptions")
        finance_left, finance_right = st.columns(2)
        with finance_left:
            down_payment_percent = st.number_input(
                "Down payment (%)", min_value=0.0, max_value=100.0, step=1.0,
                key="down_payment_percent"
            )
            annual_interest_rate = st.number_input(
                "Annual mortgage interest rate (%)", min_value=0.0, max_value=30.0,
                step=0.125, key="annual_interest_rate"
            )
            loan_term_years = st.selectbox(
                "Loan term (years)", [15, 20, 30], key="loan_term_years"
            )
            annual_homeowners_insurance = st.number_input(
                "Estimated annual homeowners insurance ($)", min_value=0.0,
                step=100.0, key="annual_homeowners_insurance"
            )
        with finance_right:
            annual_pmi_rate = st.number_input(
                "Estimated annual PMI rate (%)", min_value=0.0, max_value=5.0,
                step=0.1, key="annual_pmi_rate",
                help="Applied only when the down payment is below 20%."
            )
            annual_maintenance_percent = st.number_input(
                "Annual maintenance reserve (% of price)", min_value=0.0,
                max_value=10.0, step=0.25, key="annual_maintenance_percent"
            )
            closing_cost_percent = st.number_input(
                "Estimated closing costs (% of price)", min_value=0.0,
                max_value=10.0, step=0.25, key="closing_cost_percent"
            )

        submitted = st.form_submit_button("Analyze Property", type="primary")

    if submitted:
        buyer = {
            "maximum_budget": maximum_budget,
            "preferred_location": preferred_location,
            "minimum_bedrooms": minimum_bedrooms,
            "minimum_bathrooms": minimum_bathrooms,
            "school_importance": school_importance,
            "maximum_commute_minutes": maximum_commute_minutes,
            "maximum_property_age": maximum_property_age,
            "must_have_features": must_have_features,
            "additional_requirements": additional_requirements,
        }
        property_info = {
            "listing_url_reference_only": listing_url,
            "address": address,
            "listing_price": listing_price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "square_footage": square_footage,
            "year_built": year_built,
            "annual_property_taxes": annual_property_taxes,
            "monthly_hoa_fee": monthly_hoa_fee,
            "school_rating": school_rating,
            "estimated_commute_minutes": estimated_commute_minutes,
            "property_type": property_type,
            "property_description": property_description,
            "known_concerns": known_concerns,
        }
        errors = validate_inputs(buyer, property_info)
        if errors:
            st.error("Please correct the following before analysis:")
            render_bullets(errors)
        else:
            st.session_state["mortgage_estimate"] = calculate_mortgage(
                purchase_price=listing_price,
                down_payment_percent=down_payment_percent,
                annual_interest_rate=annual_interest_rate,
                loan_term_years=loan_term_years,
                annual_property_taxes=annual_property_taxes,
                annual_homeowners_insurance=annual_homeowners_insurance,
                monthly_hoa=monthly_hoa_fee,
                annual_pmi_rate=annual_pmi_rate,
                annual_maintenance_percent=annual_maintenance_percent,
                closing_cost_percent=closing_cost_percent,
            )

        if not errors and not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key is missing.")
            st.code("OPENAI_API_KEY=your_api_key\nOPENAI_MODEL=gpt-4.1-mini", language="text")
            st.write("Create a local `.env` file using `.env.example`, then restart Streamlit.")
        elif not errors:
            try:
                with st.spinner("Investigating how this property fits your needs..."):
                    st.session_state["analysis_result"] = analyze_property(
                        buyer, property_info
                    )
            except AuthenticationError:
                st.error("OpenAI authentication failed. Check OPENAI_API_KEY and try again.")
            except RateLimitError:
                st.error("The OpenAI rate limit was reached. Wait briefly and try again.")
            except (APITimeoutError, APIConnectionError):
                st.error("The AI service could not be reached in time. Please try again.")
            except (ValidationError, TypeError):
                st.error("The AI response did not match the required structure. Please try again.")
            except Exception:
                st.error("Analysis could not be completed. Check the model setting and try again.")

    mortgage_estimate = st.session_state.get("mortgage_estimate")
    if isinstance(mortgage_estimate, MortgageEstimate):
        display_mortgage_estimate(mortgage_estimate)

    result = st.session_state.get("analysis_result")
    if isinstance(result, HomeAnalysis):
        display_results(result)


if __name__ == "__main__":
    main()
