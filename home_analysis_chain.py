"""LangChain prompt and structured property-analysis chain."""

import json
import os
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from models import HomeAnalysis


PROMPTS_DIRECTORY = Path(__file__).resolve().parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a UTF-8 prompt stored alongside the application source."""
    prompt_path = PROMPTS_DIRECTORY / filename
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"Unable to load prompt file: {prompt_path}") from exc


def create_prompt() -> ChatPromptTemplate:
    """Create the readable two-message prompt used by the analysis chain."""
    system_prompt = load_prompt("system_prompt.txt")
    human_prompt = load_prompt("human_prompt.txt")
    return ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
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
