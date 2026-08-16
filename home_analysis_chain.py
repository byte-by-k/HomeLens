"""LangChain prompt and structured property-analysis chain."""

import json
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from models import HomeAnalysis


SYSTEM_PROMPT = """You are an impartial home-buying research assistant.

Compare one property against the buyer preferences supplied by the user. Use only
the supplied information. Never invent, retrieve, or assume missing property facts.
Clearly separate user-provided facts, missing information, and assumptions. Explain
why the property does or does not fit the buyer.

Consider price, bedrooms, bathrooms, property age, taxes, HOA fees, schools,
commute, size, maintenance concerns, and must-have features. Treat a listing URL
as reference text only; do not open it or claim to have verified it.

Do not make conclusions based on protected characteristics or infer neighborhood
demographics. Do not guarantee investment returns, future property value, school
quality, safety, or outcomes. Return exactly five useful questions for the listing
agent. Put every unknown fact that could materially affect the decision in
missing_information. Assumptions must never be presented as facts.

The final assessment must explain the recommendation. The disclaimer must state
that the analysis is informational and is not financial, legal, appraisal,
inspection, mortgage, or real-estate advice."""

HUMAN_PROMPT = """BUYER PROFILE
{buyer_profile}

PROPERTY INFORMATION
{property_information}

KNOWN CONCERNS
{known_concerns}

ANALYSIS REQUEST
Evaluate how well this property fits this buyer. Provide an explainable score and
recommendation, explicitly identify unmet preferences, risks, missing information,
and assumptions, and give exactly five questions for the listing agent."""


def create_prompt() -> ChatPromptTemplate:
    """Create the readable two-message prompt used by the analysis chain."""
    return ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
    )


def create_analysis_chain(
    api_key: str | None = None,
    model_name: str | None = None,
) -> Runnable:
    """Create an LCEL chain that returns a validated HomeAnalysis object."""
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    resolved_model = model_name or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
    llm = ChatOpenAI(
        api_key=resolved_key,
        model=resolved_model,
        temperature=0.1,
        timeout=45,
        max_retries=2,
    )
    structured_llm = llm.with_structured_output(HomeAnalysis)
    return create_prompt() | structured_llm


def build_prompt_values(
    buyer: dict[str, Any], property_info: dict[str, Any]
) -> dict[str, str]:
    """Serialize form data into clearly labeled prompt variables."""
    property_without_concerns = {
        key: value for key, value in property_info.items() if key != "known_concerns"
    }
    concerns = str(property_info.get("known_concerns", "")).strip()
    return {
        "buyer_profile": json.dumps(buyer, indent=2, ensure_ascii=False),
        "property_information": json.dumps(
            property_without_concerns, indent=2, ensure_ascii=False
        ),
        "known_concerns": concerns or "None supplied by the user.",
    }


def analyze_property(
    buyer: dict[str, Any],
    property_info: dict[str, Any],
    api_key: str | None = None,
    model_name: str | None = None,
) -> HomeAnalysis:
    """Invoke the analysis chain with the user-entered data."""
    chain = create_analysis_chain(api_key=api_key, model_name=model_name)
    result = chain.invoke(build_prompt_values(buyer, property_info))
    if not isinstance(result, HomeAnalysis):
        raise TypeError("The model did not return a valid HomeAnalysis response.")
    return result
