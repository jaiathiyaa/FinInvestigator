from typing import Any, Dict, List, Set

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_CAUSE_TYPES = {
    "earnings",
    "market_sentiment",
    "capital_allocation",
    "business_growth",
    "analyst_activity",
    "valuation",
    "market_conditions",
    "business_event",
    "other",
}

CAUSE_TYPE_ALIASES = {
    "guidance": "earnings",
    "sales_guidance": "earnings",
    "revenue_guidance": "earnings",
    "forward_guidance": "earnings",
    "financial_guidance": "earnings",
    "analyst_rating": "analyst_activity",
    "analyst_ratings": "analyst_activity",
    "share_buyback": "capital_allocation",
    "buyback": "capital_allocation",
    "repurchase": "capital_allocation",
    "sentiment": "market_sentiment",
}

# These phrases make a causal claim that the evidence may not
# actually establish.
UNSUPPORTED_CAUSAL_PHRASES = {
    "caused",
    "causes",
    "cause the stock",
    "caused the stock",
    "caused shares",
    "caused investors",
    "drove the stock",
    "drove shares",
    "drove investor",
    "drove investors",
    "led to the stock",
    "led the stock",
    "resulted in the stock",
    "resulted in higher",
    "resulted in lower",
    "triggered the rise",
    "triggered the fall",
    "triggered a rally",
    "triggered a selloff",
    "due to",
    "because of",
    "because it",
    "because investors",
    "attributed to",
    "responsible for",
    "directly caused",
    "directly led",
    "guaranteed",
    "ensured",
}

# Future/predictive wording should not appear in causal
# explanations unless the system explicitly supports forecasting.
PREDICTIVE_PHRASES = {
    "will rise",
    "will fall",
    "will increase",
    "will decrease",
    "will grow",
    "will decline",
    "could rise",
    "could fall",
    "could increase",
    "could decrease",
    "may rise",
    "may fall",
    "may increase",
    "may decrease",
    "is expected to rise",
    "is expected to fall",
    "expected to increase",
    "expected to decrease",
    "likely to rise",
    "likely to fall",
    "likely increase",
    "likely decrease",
    "if it fails",
    "if it cannot",
    "if the stock fails",
    "if the company fails",
}


# ============================================================
# STRUCTURED OUTPUT
# ============================================================

class CauseRecord(BaseModel):
    cause_type: str = Field(
        description="One of the allowed cause categories."
    )

    description: str = Field(
        description="A conservative, evidence-grounded explanation."
    )

    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence IDs supporting this cause."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class CauseExtraction(BaseModel):
    causes: List[CauseRecord] = Field(
        default_factory=list
    )


# ============================================================
# MODEL
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

cause_llm = llm.with_structured_output(
    CauseExtraction
)


# ============================================================
# HELPERS
# ============================================================

def _get_evidence_id(
    item: Dict[str, Any],
) -> str | None:

    value = (
        item.get("id")
        or item.get("evidence_id")
    )

    if value is None:
        return None

    return str(value)


def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return " ".join(
        str(value)
        .lower()
        .split()
    )


def _normalize_cause_type(
    cause_type: Any,
) -> str:

    normalized = _normalize_text(
        cause_type
    )

    return CAUSE_TYPE_ALIASES.get(
        normalized,
        normalized,
    )


def _contains_unsupported_causal_language(
    description: str,
) -> bool:

    text = _normalize_text(
        description
    )

    for phrase in UNSUPPORTED_CAUSAL_PHRASES:
        if phrase in text:
            return True

    return False


def _contains_predictive_language(
    description: str,
) -> bool:

    text = _normalize_text(
        description
    )

    for phrase in PREDICTIVE_PHRASES:
        if phrase in text:
            return True

    return False


def _ground_description(
    description: str,
) -> str | None:

    if not description:
        return None

    if _contains_unsupported_causal_language(
        description
    ):
        return None

    if _contains_predictive_language(
        description
    ):
        return None

    return description.strip()


def _build_evidence_index(
    evidence: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:

    index: Dict[str, Dict[str, Any]] = {}

    for item in evidence:

        evidence_id = _get_evidence_id(
            item
        )

        if evidence_id:
            index[evidence_id] = item

    return index


def _claim_text(
    evidence: Dict[str, Any],
) -> str:

    return str(
        evidence.get("claim")
        or evidence.get("text")
        or ""
    ).strip()


# ============================================================
# VALIDATION
# ============================================================

def _validate_causes(
    causes: List[CauseRecord],
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    evidence_index = _build_evidence_index(
        evidence
    )

    validated: List[Dict[str, Any]] = []

    for cause in causes:

        cause_type = _normalize_cause_type(
            cause.cause_type
        )

        if cause_type not in ALLOWED_CAUSE_TYPES:
            cause_type = "other"

        description = _ground_description(
            cause.description
        )

        if description is None:
            print(
                "[Cause Validation] "
                "Rejected unsupported description: "
                f"{cause.description}"
            )
            continue

        valid_evidence_ids: List[str] = []

        for evidence_id in cause.evidence_ids:

            evidence_id = str(
                evidence_id
            )

            if evidence_id in evidence_index:
                valid_evidence_ids.append(
                    evidence_id
                )

        if not valid_evidence_ids:
            print(
                "[Cause Validation] "
                "Rejected cause with no valid evidence: "
                f"{cause_type}"
            )
            continue

        confidence = max(
            0.0,
            min(
                1.0,
                float(
                    cause.confidence
                ),
            ),
        )

        validated.append(
            {
                "cause_type": cause_type,
                "description": description,
                "evidence_ids": valid_evidence_ids,
                "confidence": confidence,
            }
        )

    return validated


# ============================================================
# DEDUPLICATION
# ============================================================

def _cause_similarity_key(
    cause: Dict[str, Any],
) -> str:

    return str(
        cause.get("cause_type", "")
    )


def _merge_cause_records(
    existing: Dict[str, Any],
    incoming: Dict[str, Any],
) -> Dict[str, Any]:

    evidence_ids = list(
        dict.fromkeys(
            existing.get(
                "evidence_ids",
                [],
            )
            + incoming.get(
                "evidence_ids",
                [],
            )
        )
    )

    # Keep the stronger confidence.
    confidence = max(
        float(
            existing.get(
                "confidence",
                0.0,
            )
        ),
        float(
            incoming.get(
                "confidence",
                0.0,
            )
        ),
    )

    existing_description = (
        existing.get(
            "description",
            ""
        )
    )

    incoming_description = (
        incoming.get(
            "description",
            ""
        )
    )

    if (
        incoming_description
        and incoming_description
        != existing_description
        and len(incoming_description)
        > len(existing_description)
    ):
        description = incoming_description
    else:
        description = existing_description

    return {
        "cause_type": existing.get(
            "cause_type"
        ),
        "description": description,
        "evidence_ids": evidence_ids,
        "confidence": confidence,
    }


def _deduplicate_causes(
    causes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    merged: Dict[
        str,
        Dict[str, Any]
    ] = {}

    for cause in causes:

        key = _cause_similarity_key(
            cause
        )

        if key not in merged:
            merged[key] = cause
        else:
            merged[key] = _merge_cause_records(
                merged[key],
                cause,
            )

    return list(
        merged.values()
    )


# ============================================================
# PROMPT
# ============================================================

def _build_prompt(
    query: str,
    company: str,
    price_direction: str,
    evidence: List[Dict[str, Any]],
) -> str:

    evidence_lines: List[str] = []

    for item in evidence:

        evidence_id = _get_evidence_id(
            item
        )

        if not evidence_id:
            continue

        claim = _claim_text(
            item
        )

        if not claim:
            continue

        evidence_lines.append(
            f"{evidence_id}: {claim}"
        )

    evidence_text = "\n".join(
        evidence_lines
    )

    return f"""
You are the Cause Analysis Agent in a financial investigation system.

Company:
{company}

Investigation query:
{query}

Observed price direction:
{price_direction}

Your task is to identify evidence-grounded factors associated with the
observed stock movement.

IMPORTANT:

1. Do NOT claim that an event definitely caused the stock movement unless
   the evidence explicitly establishes causality.

2. Prefer conservative language:
   - associated with
   - coincided with
   - occurred alongside
   - was reported alongside
   - identified in the evidence

3. Do NOT use:
   - caused
   - drove
   - due to
   - because of
   - resulted in
   - triggered
   - attributed to
   - responsible for

4. Do NOT make predictions.

5. Every cause MUST reference at least one evidence ID.

6. Group related evidence under the same cause category.

7. Avoid duplicate causes of the same type.

8. If multiple evidence records describe the same factor, return one
   cause with multiple evidence IDs.

Allowed cause types:
- earnings
- market_sentiment
- capital_allocation
- business_growth
- analyst_activity
- valuation
- market_conditions
- business_event
- other

Evidence:

{evidence_text}
"""


# ============================================================
# MAIN AGENT
# ============================================================

async def cause_analyzer(
    state: Dict[str, Any],
) -> Dict[str, Any]:

    if state.get("movement_mismatch", False):
        print("[Cause Agent] Movement mismatch detected.")
        print("[Cause Agent] Skipping causal analysis because the requested price movement is not supported by the market data.")

        trace = list(state.get("trace", []))
        trace.append({
            "agent": "cause_analyzer",
            "status": "completed",
            "mode": "movement_mismatch",
            "reason": "requested_movement_not_supported",
        })

        return {
            "causes": [],
            "trace": trace,
        }
    query = state.get(
        "query",
        ""
    )

    company = state.get(
        "company",
        ""
    )

    intent = state.get(
        "investigation_intent",
        "general_investigation",
    )

    price_direction = state.get(
        "price_direction",
        "unknown",
    )

    evidence = state.get(
        "evidence",
        [],
    )

    trace = list(
        state.get(
            "trace",
            [],
        )
    )

    print(
        f"[Cause Agent] Investigation intent: "
        f"{intent}"
    )

    # --------------------------------------------------------
    # General investigation
    # --------------------------------------------------------

    if intent != "cause_analysis":

        print(
            "[Cause Agent] Skipping causal analysis "
            "because cause analysis was not requested."
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "skipped",
                "reason": "cause_analysis_not_requested",
                "intent": intent,
            }
        )

        return {
            "causes": [],
            "trace": trace,
        }

    # --------------------------------------------------------
    # No evidence
    # --------------------------------------------------------

    if not evidence:

        print(
            "[Cause Agent] No evidence available."
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "failed",
                "reason": "no_evidence",
            }
        )

        return {
            "causes": [],
            "trace": trace,
        }

    print(
        "[Cause Agent] Starting cause analysis"
    )

    prompt = _build_prompt(
        query=query,
        company=company,
        price_direction=price_direction,
        evidence=evidence,
    )

    try:

        result = await cause_llm.ainvoke(
            prompt
        )

        raw_causes = (
            result.causes
            if result
            else []
        )

        validated = _validate_causes(
            raw_causes,
            evidence,
        )

        deduplicated = _deduplicate_causes(
            validated
        )

        print(
            f"[Cause Agent] Validated "
            f"{len(deduplicated)} causes"
        )

        for cause in deduplicated:

            print(
                f"  - "
                f"{cause['cause_type']} "
                f"({len(cause['evidence_ids'])} evidence, "
                f"confidence={cause['confidence']})"
            )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "completed",
                "intent": intent,
                "raw_cause_count": len(
                    raw_causes
                ),
                "validated_cause_count": len(
                    validated
                ),
                "deduplicated_cause_count": len(
                    deduplicated
                ),
            }
        )

        return {
            "causes": deduplicated,
            "trace": trace,
        }

    except Exception as exc:

        print(
            "[Cause Agent] Error: "
            f"{type(exc).__name__}: {exc}"
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "failed",
                "error": str(exc),
            }
        )

        return {
            "causes": [],
            "trace": trace,
            "errors": [
                *state.get(
                    "errors",
                    [],
                ),
                (
                    "cause_analyzer: "
                    f"{type(exc).__name__}: {exc}"
                ),
            ],
        }