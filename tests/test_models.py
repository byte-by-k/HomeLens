import pytest
from pydantic import ValidationError

from models import HomeAnalysis


def valid_analysis_data() -> dict:
    return {
        "fit_score": 82,
        "recommendation": "Strong Fit",
        "executive_summary": "The supplied facts show a good overall fit.",
        "matching_features": ["Within budget"],
        "unmet_preferences": [],
        "concerns_and_risks": ["Older HVAC"],
        "missing_information": ["Roof age is unknown"],
        "questions_for_agent": [f"Question {number}?" for number in range(1, 6)],
        "assumptions": [],
        "final_assessment": "Strong fit because most stated needs are met.",
        "disclaimer": "Informational only; not professional advice.",
    }


@pytest.mark.parametrize("score", [-1, 101])
def test_fit_score_must_be_between_zero_and_one_hundred(score: int) -> None:
    data = valid_analysis_data()
    data["fit_score"] = score
    with pytest.raises(ValidationError):
        HomeAnalysis(**data)


@pytest.mark.parametrize("recommendation", ["Strong Fit", "Consider", "Not Recommended"])
def test_permitted_recommendations(recommendation: str) -> None:
    data = valid_analysis_data()
    data["recommendation"] = recommendation
    assert HomeAnalysis(**data).recommendation == recommendation


def test_unknown_recommendation_is_rejected() -> None:
    data = valid_analysis_data()
    data["recommendation"] = "Buy Now"
    with pytest.raises(ValidationError):
        HomeAnalysis(**data)


def test_exactly_five_agent_questions_are_required() -> None:
    data = valid_analysis_data()
    data["questions_for_agent"] = ["Only one?"]
    with pytest.raises(ValidationError):
        HomeAnalysis(**data)


def test_missing_information_is_preserved() -> None:
    analysis = HomeAnalysis(**valid_analysis_data())
    assert "Roof age is unknown" in analysis.missing_information
