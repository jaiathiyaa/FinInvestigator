from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural-language financial investigation query.",
    )


class InvestigationResponse(BaseModel):
    success: bool

    query: str

    company: Optional[str] = None

    investigation_intent: Optional[str] = None

    price_direction: Optional[str] = None

    movement_verification: Dict[str, Any] = Field(
        default_factory=dict
    )

    movement_mismatch: bool = False

    company_data: Dict[str, Any] = Field(
        default_factory=dict
    )

    news_data: Dict[str, Any] = Field(
        default_factory=dict
    )

    market_data: Dict[str, Any] = Field(
        default_factory=dict
    )

    evidence: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    causes: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    risks: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    final_report: Dict[str, Any] = Field(
        default_factory=dict
    )

    audit: Dict[str, Any] = Field(
        default_factory=dict
    )

    trace: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    errors: List[str] = Field(
        default_factory=list
    )