"""Structured response models for the home analysis."""

from typing import Literal

from pydantic import BaseModel, Field


class HomeAnalysis(BaseModel):
    """A validated, explainable property-fit recommendation."""

    fit_score: int = Field(
        ge=0,
        le=100,
        description="Overall property fit score from 0 to 100",
    )
    recommendation: Literal["Strong Fit", "Consider", "Not Recommended"]
    executive_summary: str = Field(min_length=1)
    matching_features: list[str]
    unmet_preferences: list[str]
    concerns_and_risks: list[str]
    missing_information: list[str]
    questions_for_agent: list[str] = Field(
        min_length=5,
        max_length=5,
        description="Exactly five useful questions for the listing agent",
    )
    assumptions: list[str]
    final_assessment: str = Field(
        min_length=1,
        description="Explanation supporting the selected recommendation",
    )
    disclaimer: str = Field(min_length=1)
