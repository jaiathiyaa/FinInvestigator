from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    InvestigationRequest,
    InvestigationResponse,
)
from app.graph.workflow import graph


router = APIRouter(
    prefix="/api",
    tags=["Investigation"],
)


def _build_initial_state(query: str) -> Dict[str, Any]:
    """
    Build the same initial state used by the v8.9 graph test.
    """

    return {
        "query": query,

        "company": "",

        "investigation_intent": "",

        "price_direction": "",

        "company_data": {},

        "news_data": {},

        "market_data": {},

        "movement_verification": {},

        "movement_mismatch": False,

        "evidence": [],

        "causes": [],

        "risks": [],

        "final_report": {},

        "trace": [],

        "errors": [],

        "audit": {},
    }


def _build_response(
    result: Dict[str, Any],
) -> InvestigationResponse:
    """
    Convert LangGraph final state into the public API response.
    """

    errors = result.get("errors", [])

    audit = result.get("audit", {})

    final_report = result.get(
        "final_report",
        {},
    )

    # Prefer the audit result when determining success.
    #
    # The graph may complete successfully even when the
    # investigation itself detects a movement mismatch.
    audit_passed = audit.get("passed")

    if audit_passed is None:
        audit_passed = audit.get("overall")

    if isinstance(audit_passed, str):
        audit_passed = audit_passed.upper() == "PASS"

    if audit_passed is None:
        audit_passed = len(errors) == 0

    success = (
        bool(audit_passed)
        and len(errors) == 0
    )

    return InvestigationResponse(
        success=success,

        query=result.get(
            "query",
            "",
        ),

        company=result.get(
            "company"
        ),

        investigation_intent=result.get(
            "investigation_intent"
        ),

        price_direction=result.get(
            "price_direction"
        ),

        movement_verification=result.get(
            "movement_verification",
            {},
        ),

        movement_mismatch=result.get(
            "movement_mismatch",
            False,
        ),

        company_data=result.get(
            "company_data",
            {},
        ),

        news_data=result.get(
            "news_data",
            {},
        ),

        market_data=result.get(
            "market_data",
            {},
        ),

        evidence=result.get(
            "evidence",
            [],
        ),

        causes=result.get(
            "causes",
            [],
        ),

        risks=result.get(
            "risks",
            [],
        ),

        final_report=final_report,

        audit=audit,

        trace=result.get(
            "trace",
            [],
        ),

        errors=errors,
    )


@router.get("/investigate/health")
async def investigation_health():
    """
    Health check for the investigation API.
    """

    return {
        "status": "ok",
        "service": "investigation",
        "graph": "v8.9",
    }


@router.post(
    "/investigate",
    response_model=InvestigationResponse,
)
async def investigate(
    request: InvestigationRequest,
):
    """
    Execute a complete FinInvestigator investigation.
    """

    initial_state = _build_initial_state(
        request.query.strip()
    )

    try:

        result = await graph.ainvoke(
            initial_state
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Investigation failed.",
                "error": str(exc),
            },
        ) from exc

    return _build_response(result)