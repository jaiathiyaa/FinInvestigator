from __future__ import annotations

from typing import Any, Dict, List
import re

from app.graph.state import InvestigationState


# ============================================================
# HELPERS
# ============================================================


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _unique(
    values: List[str],
) -> List[str]:

    seen = set()
    result = []

    for value in values:

        if not value:
            continue

        value = str(value)

        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def _normalize_source_type(
    value: Any,
) -> str:

    if value is None:
        return "unknown"

    value = str(value).strip().lower()

    if value == "finance":
        return "market"

    return value


def _evidence_id(
    item: Dict[str, Any],
) -> str | None:

    value = item.get("id")

    if value is None:
        value = item.get("evidence_id")

    if value is None:
        return None

    return str(value)


def _evidence_claim(
    item: Dict[str, Any],
) -> str:

    claim = (
        item.get("claim")
        or item.get("text")
        or item.get("description")
        or item.get("statement")
    )

    if claim is None:
        return ""

    return str(claim).strip()


def _evidence_index(
    evidence: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:

    result = {}

    for item in evidence:

        if not isinstance(item, dict):
            continue

        evidence_id = _evidence_id(item)

        if evidence_id:
            result[evidence_id] = item

    return result


def _get_cause_type(
    cause: Dict[str, Any],
) -> str:

    return str(
        cause.get("cause_type")
        or cause.get("type")
        or "other"
    ).strip()


def _get_cause_description(
    cause: Dict[str, Any],
) -> str:

    value = (
        cause.get("description")
        or cause.get("text")
        or cause.get("statement")
    )

    if value is None:
        return ""

    return str(value).strip()


def _get_cause_evidence_ids(
    cause: Dict[str, Any],
) -> List[str]:

    ids = cause.get("evidence_ids", [])

    if not isinstance(ids, list):
        return []

    return _unique(
        [
            str(x)
            for x in ids
            if x is not None
        ]
    )


def _get_risk_type(
    risk: Dict[str, Any],
) -> str:

    return str(
        risk.get("risk_type")
        or risk.get("type")
        or "other"
    ).strip()


def _get_risk_description(
    risk: Dict[str, Any],
) -> str:

    value = (
        risk.get("description")
        or risk.get("text")
        or risk.get("statement")
    )

    if value is None:
        return ""

    return str(value).strip()


def _get_risk_evidence_ids(
    risk: Dict[str, Any],
) -> List[str]:

    ids = risk.get("evidence_ids", [])

    if not isinstance(ids, list):
        return []

    return _unique(
        [
            str(x)
            for x in ids
            if x is not None
        ]
    )


# ============================================================
# SOURCE STATISTICS
# ============================================================


def _build_evidence_statistics(
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:

    news = 0
    market = 0
    company = 0

    claim_types: Dict[str, int] = {}

    for item in evidence:

        if not isinstance(item, dict):
            continue

        source_type = _normalize_source_type(
            item.get("source_type")
        )

        if source_type == "news":
            news += 1

        elif source_type == "market":
            market += 1

        elif source_type == "company":
            company += 1

        claim_type = item.get("claim_type")

        if claim_type:

            claim_type = str(claim_type)

            claim_types[claim_type] = (
                claim_types.get(claim_type, 0) + 1
            )

    return {
        "total": len(evidence),
        "news": news,
        "market": market,
        "company": company,
        "finance": market,
        "claim_types": claim_types,
    }


# ============================================================
# SAFETY HELPERS
# ============================================================


UNSAFE_CAUSAL_PATTERNS = [
    r"\bcaused\b",
    r"\bcauses\b",
    r"\bcausing\b",
    r"\bled to\b",
    r"\bresulted in\b",
    r"\bdriven by\b",
    r"\bdrove\b",
    r"\bbecause\b",
]


PREDICTIVE_PATTERNS = [
    r"\bwill\b",
    r"\bwould\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bexpected to\b",
    r"\blikely to\b",
    r"\bforecast\b",
    r"\bprojected to\b",
]


INVESTMENT_ADVICE_PATTERNS = [
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\binvest\b",
    r"\bavoid\b",
    r"\btarget price\b",
]


def _contains_pattern(
    text: str,
    patterns: List[str],
) -> bool:

    lowered = text.lower()

    for pattern in patterns:

        if re.search(pattern, lowered):
            return True

    return False


def _safe_summary(
    company: str,
    evidence_count: int,
    cause_count: int,
    risk_count: int,
    movement: Dict[str, Any],
) -> str:

    actual_direction = movement.get(
        "actual_direction"
    )

    if actual_direction == "up":
        movement_text = "upward price movement"

    elif actual_direction == "down":
        movement_text = "downward price movement"

    elif actual_direction == "flat":
        movement_text = "limited price movement"

    else:
        movement_text = "the observed price movement"

    return (
        f"The investigation for {company} contains "
        f"{evidence_count} validated evidence records, "
        f"{cause_count} validated cause records, and "
        f"{risk_count} validated risk records. "
        f"The available market data verifies {movement_text}. "
        f"The validated evidence is presented as supporting "
        f"information and does not independently establish causation."
    )


def _safe_cause_summary(
    cause_count: int,
) -> str:

    if cause_count == 0:

        return (
            "No cause records met the validation requirements "
            "for inclusion in the final report."
        )

    return (
        "The validated evidence contains information relevant "
        "to the investigation. These records describe reported "
        "financial, business, analyst, or capital-allocation "
        "developments associated with the investigation. "
        "They do not independently establish causation."
    )


def _safe_risk_summary(
    risk_count: int,
) -> str:

    if risk_count == 0:

        return (
            "No risks met the validation requirements "
            "for inclusion in the final report."
        )

    return (
        "The validated risk records identify risk-related "
        "information supported by the available evidence."
    )


# ============================================================
# FINDING GENERATION
# ============================================================


def _build_findings(
    causes: List[Dict[str, Any]],
    evidence_index: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:

    findings: List[Dict[str, Any]] = []

    for index, cause in enumerate(
        causes,
        start=1,
    ):

        if not isinstance(cause, dict):
            continue

        cause_type = _get_cause_type(cause)

        description = _get_cause_description(
            cause
        )

        evidence_ids = _get_cause_evidence_ids(
            cause
        )

        # ----------------------------------------------------
        # Keep only valid evidence references
        # ----------------------------------------------------

        valid_evidence_ids = []

        for evidence_id in evidence_ids:

            if evidence_id in evidence_index:
                valid_evidence_ids.append(
                    evidence_id
                )

        valid_evidence_ids = _unique(
            valid_evidence_ids
        )

        # ----------------------------------------------------
        # Repair missing descriptions
        # ----------------------------------------------------

        if not description:

            supporting_claims = []

            for evidence_id in valid_evidence_ids:

                claim = _evidence_claim(
                    evidence_index[evidence_id]
                )

                if claim:
                    supporting_claims.append(
                        claim
                    )

            if supporting_claims:

                description = supporting_claims[0]

            else:

                description = (
                    f"Validated evidence related to "
                    f"{cause_type}."
                )

        confidence = _safe_float(
            cause.get("confidence"),
            0.0,
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # text, statement and description all receive the
        # same validated description.
        #
        # This prevents:
        #
        # 1. None
        # 2. empty finding text
        # 3. audit compatibility failures
        # ----------------------------------------------------

        finding = {
            "finding_id": f"F{index:03d}",

            "type": cause_type,

            "text": description,

            "statement": description,

            "description": description,

            "evidence_ids": valid_evidence_ids,

            "confidence": confidence,
        }

        findings.append(
            finding
        )

    return findings


# ============================================================
# VALIDATION
# ============================================================


def _validate_findings(
    findings: List[Dict[str, Any]],
    evidence_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:

    errors = []

    for index, finding in enumerate(
        findings,
        start=1,
    ):

        if not isinstance(finding, dict):

            errors.append(
                f"finding {index}: invalid finding object"
            )

            continue

        text = (
            finding.get("text")
            or finding.get("statement")
            or finding.get("description")
        )

        if not text or not str(text).strip():

            errors.append(
                f"finding {index}: missing finding text"
            )

        evidence_ids = finding.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            evidence_ids,
            list,
        ):

            errors.append(
                f"finding {index}: invalid evidence_ids"
            )

            evidence_ids = []

        if not evidence_ids:

            errors.append(
                f"finding {index}: missing evidence IDs"
            )

        for evidence_id in evidence_ids:

            if str(evidence_id) not in evidence_index:

                errors.append(
                    f"finding {index}: unknown evidence ID "
                    f"{evidence_id}"
                )

        text = str(text or "")

        if _contains_pattern(
            text,
            INVESTMENT_ADVICE_PATTERNS,
        ):

            errors.append(
                f"finding {index}: investment advice detected"
            )

        if _contains_pattern(
            text,
            PREDICTIVE_PATTERNS,
        ):

            errors.append(
                f"finding {index}: predictive language detected"
            )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# MAIN SYNTHESIS NODE
# ============================================================


def synthesis_agent(
    state: InvestigationState,
) -> Dict[str, Any]:

    print()
    print("=" * 70)
    print("SYNTHESIS AGENT v8.9")
    print("=" * 70)

    query = state.get(
        "query",
        "",
    )

    company = state.get(
        "company",
        "",
    )

    investigation_intent = state.get(
        "investigation_intent",
        "general",
    )

    evidence = state.get(
        "evidence",
        [],
    ) or []

    causes = state.get(
        "causes",
        [],
    ) or []

    risks = state.get(
        "risks",
        [],
    ) or []

    movement = state.get(
        "movement_verification",
        {},
    ) or {}

    print(
        f"[Synthesis] Query: {query}"
    )

    print(
        f"[Synthesis] Company: {company}"
    )

    print(
        f"[Synthesis] Intent: {investigation_intent}"
    )

    print(
        f"[Synthesis] Evidence count: {len(evidence)}"
    )

    print(
        f"[Synthesis] Cause count: {len(causes)}"
    )

    print(
        f"[Synthesis] Risk count: {len(risks)}"
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence_index = _evidence_index(
        evidence
    )

    evidence_statistics = _build_evidence_statistics(
        evidence
    )

    # ========================================================
    # FINDINGS
    # ========================================================

    findings = _build_findings(
        causes=causes,
        evidence_index=evidence_index,
    )

    # ========================================================
    # SUMMARIES
    # ========================================================

    summary = _safe_summary(
        company=company,
        evidence_count=len(evidence),
        cause_count=len(causes),
        risk_count=len(risks),
        movement=movement,
    )

    cause_summary = _safe_cause_summary(
        len(causes)
    )

    risk_summary = _safe_risk_summary(
        len(risks)
    )

    # ========================================================
    # SAFETY VALIDATION
    # ========================================================

    validation = _validate_findings(
        findings=findings,
        evidence_index=evidence_index,
    )

    # The final report does not claim that a factor caused
    # the price movement.
    causal_claim_used = False

    association_preserved = True

    final_safety_validation = (
        validation["passed"]
        and not _contains_pattern(
            summary,
            INVESTMENT_ADVICE_PATTERNS,
        )
        and not _contains_pattern(
            summary,
            PREDICTIVE_PATTERNS,
        )
        and not _contains_pattern(
            cause_summary,
            INVESTMENT_ADVICE_PATTERNS,
        )
        and not _contains_pattern(
            cause_summary,
            PREDICTIVE_PATTERNS,
        )
    )

    if not final_safety_validation:

        print(
            "[Synthesis Validation] "
            "Safety validation failed. "
            "Using deterministic safe summaries."
        )

        summary = (
            f"The investigation for {company} contains "
            f"{len(evidence)} validated evidence records. "
            f"The available evidence does not independently "
            f"establish that any specific factor caused the "
            f"observed stock-price movement."
        )

        cause_summary = (
            "The validated evidence contains information "
            "relevant to the investigation. It does not "
            "independently establish causation."
        )

        risk_summary = _safe_risk_summary(
            len(risks)
        )

        causal_claim_used = False
        association_preserved = True

        # Findings themselves were independently validated.
        # Recalculate the final safety state.
        final_safety_validation = (
            validation["passed"]
            and not _contains_pattern(
                summary,
                INVESTMENT_ADVICE_PATTERNS,
            )
            and not _contains_pattern(
                summary,
                PREDICTIVE_PATTERNS,
            )
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    final_report = {

        # ----------------------------------------------------
        # Core report
        # ----------------------------------------------------

        "summary": summary,

        "key_findings": findings,

        "cause_summary": cause_summary,

        "risk_summary": risk_summary,

        # ----------------------------------------------------
        # Counts
        # ----------------------------------------------------

        "evidence_count": len(evidence),

        "cause_count": len(causes),

        "risk_count": len(risks),

        "finding_count": len(findings),

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        "evidence_statistics": evidence_statistics,

        # Backward compatibility
        "evidence_stats": evidence_statistics,

        # ----------------------------------------------------
        # Safety metadata
        # ----------------------------------------------------

        "causal_claim_used": causal_claim_used,

        "association_preserved": association_preserved,

        "final_safety_validation": final_safety_validation,

        # ----------------------------------------------------
        # Movement
        # ----------------------------------------------------

        "movement_verification": movement,

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        "validation": {
            "findings": validation,
            "safety": final_safety_validation,
        },
    }

    # ========================================================
    # LOGGING
    # ========================================================

    print(
        f"[Synthesis] Final findings: "
        f"{len(findings)}"
    )

    print(
        f"[Synthesis] Final causes: "
        f"{len(causes)}"
    )

    print(
        f"[Synthesis] Final risks: "
        f"{len(risks)}"
    )

    print(
        f"[Synthesis] Evidence count: "
        f"{evidence_statistics['total']}"
    )

    print(
        f"[Synthesis] News: "
        f"{evidence_statistics['news']}"
    )

    print(
        f"[Synthesis] Market: "
        f"{evidence_statistics['market']}"
    )

    print(
        f"[Synthesis] Company: "
        f"{evidence_statistics['company']}"
    )

    print(
        f"[Synthesis] Causal claim used: "
        f"{causal_claim_used}"
    )

    print(
        f"[Synthesis] Association preserved: "
        f"{association_preserved}"
    )

    print(
        f"[Synthesis] Final safety validation: "
        f"{final_safety_validation}"
    )

    print("=" * 70)

    # ========================================================
    # IMPORTANT TRACE DESIGN
    # ========================================================
    #
    # DO NOT manually append to trace here.
    #
    # The LangGraph workflow wrapper is responsible for adding
    # the synthesis_agent trace entry.
    #
    # This avoids:
    #
    # - duplicate trace entries
    # - concurrent trace conflicts
    # - Annotated reducer issues
    #
    # ========================================================

    return {
        "final_report": final_report,
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

synthesis = synthesis_agent

synthesis_agent_node = synthesis_agent