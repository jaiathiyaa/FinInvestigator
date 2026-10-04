from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Annotated


def merge_trace(
    existing: List[Dict[str, Any]] | None,
    incoming: List[Dict[str, Any]] | None,
) -> List[Dict[str, Any]]:
    """
    Merge trace entries from parallel LangGraph branches.

    Deduplicates exact agent/status combinations while preserving
    execution order as much as possible.
    """

    existing = existing or []
    incoming = incoming or []

    merged = list(existing)

    for item in incoming:
        if not isinstance(item, dict):
            continue

        agent = item.get("agent")
        status = item.get("status")

        duplicate = any(
            isinstance(existing_item, dict)
            and existing_item.get("agent") == agent
            and existing_item.get("status") == status
            for existing_item in merged
        )

        if not duplicate:
            merged.append(item)

    return merged


class InvestigationState(TypedDict, total=False):

    # ============================================================
    # INPUT
    # ============================================================

    query: str
    company: str
    investigation_intent: str
    price_direction: str

    # ============================================================
    # RESEARCH
    # ============================================================

    company_data: Dict[str, Any]
    news_data: Dict[str, Any]
    market_data: Dict[str, Any]

    # ============================================================
    # MOVEMENT
    # ============================================================

    movement_verification: Dict[str, Any]
    movement_mismatch: bool

    # ============================================================
    # ANALYSIS
    # ============================================================

    evidence: List[Dict[str, Any]]
    causes: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]

    # ============================================================
    # FINAL REPORT
    # ============================================================

    final_report: Dict[str, Any]

    # ============================================================
    # TRACE
    # ============================================================

    trace: Annotated[
        List[Dict[str, Any]],
        merge_trace,
    ]

    # ============================================================
    # ERRORS
    # ============================================================

    errors: List[str]

    # ============================================================
    # AUDIT
    # ============================================================

    audit: Dict[str, Any]