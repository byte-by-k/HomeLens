from langchain_core.prompts import ChatPromptTemplate

from home_analysis_chain import build_prompt_values, create_prompt, load_prompt


def test_external_prompt_files_load() -> None:
    system_prompt = load_prompt("system_prompt.txt")
    human_prompt = load_prompt("human_prompt.txt")
    assert "impartial home-buying research assistant" in system_prompt
    assert "{buyer_profile}" in human_prompt
    assert "{property_information}" in human_prompt
    assert "{known_concerns}" in human_prompt


def test_prompt_creation_has_system_and_human_messages() -> None:
    prompt = create_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    rendered = prompt.invoke(
        {
            "buyer_profile": "buyer",
            "property_information": "property",
            "known_concerns": "concerns",
        }
    ).to_string()
    for heading in [
        "BUYER PROFILE",
        "PROPERTY INFORMATION",
        "KNOWN CONCERNS",
        "ANALYSIS REQUEST",
    ]:
        assert heading in rendered


def test_prompt_values_keep_missing_concerns_explicit() -> None:
    values = build_prompt_values({"maximum_budget": 100}, {"address": "Example"})
    assert values["known_concerns"] == "None supplied by the user."
    assert "maximum_budget" in values["buyer_profile"]
    assert "Example" in values["property_information"]
