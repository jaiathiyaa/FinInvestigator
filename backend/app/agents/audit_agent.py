from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

from app.graph.state import InvestigationState


# ============================================================
# HELPERS
# ============================================================


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


def _unique(
    values: List[str],
) -> List[str]:

    seen = set()
    result = []

    for value in values:

        if value is None:
            continue

        value = str(value)

        if value not in seen:

            seen.add(value)
            result.append(value)

    return result


# ============================================================
# SOURCE COUNTS
# ============================================================


def _normalize_source_type(
    source_type: Any,
) -> str:

    if source_type is None:
        return "unknown"

    source_type = str(
        source_type
    ).strip().lower()

    if source_type == "finance":
        return "market"

    return source_type


def _source_counts(
    evidence: List[Dict[str, Any]],
) -> Dict[str, int]:

    news = 0
    market = 0
    company = 0

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

    return {
        "news": news,
        "market": market,
        "finance": market,
        "company": company,
    }


# ============================================================
# EVIDENCE MANIFEST
# ============================================================


def _evidence_manifest(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    manifest = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        evidence_id = (
            item.get("id")
            or item.get("evidence_id")
        )

        manifest.append(
            {
                "id": (
                    str(evidence_id)
                    if evidence_id is not None
                    else None
                ),

                "claim": (
                    item.get("claim")
                    or item.get("text")
                    or item.get("description")
                    or item.get("statement")
                ),

                "claim_type": item.get(
                    "claim_type"
                ),

                "source_type": _normalize_source_type(
                    item.get("source_type")
                ),

                "source": item.get(
                    "source"
                ),

                "date": item.get(
                    "date"
                ),

                "url": item.get(
                    "url"
                ),
            }
        )

    return manifest


# ============================================================
# CAUSE MANIFEST
# ============================================================


def _cause_manifest(
    causes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    manifest = []

    for cause in causes:

        if not isinstance(cause, dict):
            continue

        cause_type = (
            cause.get("cause_type")
            or cause.get("type")
            or "other"
        )

        description = (
            cause.get("description")
            or cause.get("text")
            or cause.get("statement")
        )

        evidence_ids = cause.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            evidence_ids,
            list,
        ):
            evidence_ids = []

        manifest.append(
            {
                "type": str(cause_type),

                "cause_type": str(cause_type),

                "description": description,

                "evidence_ids": _unique(
                    [
                        str(x)
                        for x in evidence_ids
                        if x is not None
                    ]
                ),

                "confidence": cause.get(
                    "confidence"
                ),
            }
        )

    return manifest


# ============================================================
# RISK MANIFEST
# ============================================================


def _risk_manifest(
    risks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    manifest = []

    for risk in risks:

        if not isinstance(risk, dict):
            continue

        risk_type = (
            risk.get("risk_type")
            or risk.get("type")
            or "other"
        )

        description = (
            risk.get("description")
            or risk.get("text")
            or risk.get("statement")
        )

        evidence_ids = risk.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            evidence_ids,
            list,
        ):
            evidence_ids = []

        manifest.append(
            {
                "type": str(risk_type),

                "risk_type": str(risk_type),

                "description": description,

                "evidence_ids": _unique(
                    [
                        str(x)
                        for x in evidence_ids
                        if x is not None
                    ]
                ),

                "confidence": risk.get(
                    "confidence"
                ),
            }
        )

    return manifest


# ============================================================
# REPORT HELPERS
# ============================================================


def _get_report_evidence_stats(
    final_report: Dict[str, Any],
) -> Dict[str, Any]:

    stats = final_report.get(
        "evidence_statistics"
    )

    if isinstance(stats, dict):
        return stats

    stats = final_report.get(
        "evidence_stats"
    )

    if isinstance(stats, dict):
        return stats

    return {}


def _get_report_evidence_count(
    final_report: Dict[str, Any],
) -> int:

    if "evidence_count" in final_report:

        return _safe_int(
            final_report.get(
                "evidence_count"
            )
        )

    stats = _get_report_evidence_stats(
        final_report
    )

    return _safe_int(
        stats.get("total")
    )


def _get_report_cause_count(
    final_report: Dict[str, Any],
    actual_count: int,
) -> int:

    if "cause_count" in final_report:

        return _safe_int(
            final_report.get(
                "cause_count"
            )
        )

    return actual_count


def _get_report_risk_count(
    final_report: Dict[str, Any],
    actual_count: int,
) -> int:

    if "risk_count" in final_report:

        return _safe_int(
            final_report.get(
                "risk_count"
            )
        )

    return actual_count


def _get_finding_text(
    finding: Dict[str, Any],
) -> str:

    return _normalize_text(
        finding.get("text")
        or finding.get("statement")
        or finding.get("description")
    )


def _get_finding_type(
    finding: Dict[str, Any],
) -> str:

    return _normalize_text(
        finding.get("type")
        or finding.get("cause_type")
        or "other"
    )


def _get_finding_evidence_ids(
    finding: Dict[str, Any],
) -> List[str]:

    evidence_ids = finding.get(
        "evidence_ids",
        [],
    )

    if not isinstance(
        evidence_ids,
        list,
    ):
        return []

    return _unique(
        [
            str(x)
            for x in evidence_ids
            if x is not None
        ]
    )


# ============================================================
# FINDING MANIFEST
# ============================================================


def _finding_manifest(
    final_report: Dict[str, Any],
) -> List[Dict[str, Any]]:

    findings = final_report.get(
        "key_findings",
        [],
    )

    if not isinstance(
        findings,
        list,
    ):
        return []

    manifest = []

    for index, finding in enumerate(
        findings,
        start=1,
    ):

        if not isinstance(
            finding,
            dict,
        ):
            continue

        text = _get_finding_text(
            finding
        )

        evidence_ids = _get_finding_evidence_ids(
            finding
        )

        manifest.append(
            {
                "finding_id": (
                    finding.get("finding_id")
                    or f"F{index:03d}"
                ),

                "type": _get_finding_type(
                    finding
                ),

                "text": text,

                "statement": text,

                "description": text,

                "evidence_ids": evidence_ids,

                "confidence": finding.get(
                    "confidence"
                ),
            }
        )

    return manifest


# ============================================================
# EVIDENCE REFERENCE VALIDATION
# ============================================================


def _validate_evidence_references(
    evidence: List[Dict[str, Any]],
    causes: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
) -> Dict[str, Any]:

    evidence_ids = set()

    for item in evidence:

        if not isinstance(item, dict):
            continue

        evidence_id = (
            item.get("id")
            or item.get("evidence_id")
        )

        if evidence_id is not None:

            evidence_ids.add(
                str(evidence_id)
            )

    errors = []

    # --------------------------------------------------------
    # Causes
    # --------------------------------------------------------

    for index, cause in enumerate(
        causes,
        start=1,
    ):

        if not isinstance(
            cause,
            dict,
        ):
            continue

        ids = cause.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            ids,
            list,
        ):
            ids = []

        for evidence_id in ids:

            if str(evidence_id) not in evidence_ids:

                errors.append(
                    f"cause {index}: unknown "
                    f"evidence ID {evidence_id}"
                )

    # --------------------------------------------------------
    # Risks
    # --------------------------------------------------------

    for index, risk in enumerate(
        risks,
        start=1,
    ):

        if not isinstance(
            risk,
            dict,
        ):
            continue

        ids = risk.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            ids,
            list,
        ):
            ids = []

        for evidence_id in ids:

            if str(evidence_id) not in evidence_ids:

                errors.append(
                    f"risk {index}: unknown "
                    f"evidence ID {evidence_id}"
                )

    # --------------------------------------------------------
    # Findings
    # --------------------------------------------------------

    for index, finding in enumerate(
        findings,
        start=1,
    ):

        if not isinstance(
            finding,
            dict,
        ):
            continue

        ids = finding.get(
            "evidence_ids",
            [],
        )

        if not isinstance(
            ids,
            list,
        ):
            ids = []

        for evidence_id in ids:

            if str(evidence_id) not in evidence_ids:

                errors.append(
                    f"finding {index}: unknown "
                    f"evidence ID {evidence_id}"
                )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# FINDING VALIDATION
# ============================================================


def _validate_findings(
    findings: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:

    errors = []

    evidence_ids = set()

    for item in evidence:

        if not isinstance(item, dict):
            continue

        evidence_id = (
            item.get("id")
            or item.get("evidence_id")
        )

        if evidence_id is not None:

            evidence_ids.add(
                str(evidence_id)
            )

    for index, finding in enumerate(
        findings,
        start=1,
    ):

        if not isinstance(
            finding,
            dict,
        ):

            errors.append(
                f"finding {index}: invalid finding object"
            )

            continue

        text = _get_finding_text(
            finding
        )

        if not text:

            errors.append(
                f"finding {index}: "
                "missing finding text"
            )

        ids = _get_finding_evidence_ids(
            finding
        )

        if not ids:

            errors.append(
                f"finding {index}: "
                "missing evidence IDs"
            )

        for evidence_id in ids:

            if evidence_id not in evidence_ids:

                errors.append(
                    f"finding {index}: "
                    f"unknown evidence ID "
                    f"{evidence_id}"
                )

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# REPORT COUNT VALIDATION
# ============================================================


def _validate_report_counts(
    final_report: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    causes: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
) -> Dict[str, Any]:

    errors = []

    # ========================================================
    # ACTUAL COUNTS
    # ========================================================

    actual_evidence_count = len(
        evidence
    )

    actual_cause_count = len(
        causes
    )

    actual_risk_count = len(
        risks
    )

    # ========================================================
    # REPORT EVIDENCE COUNT
    # ========================================================

    report_evidence_count = (
        _get_report_evidence_count(
            final_report
        )
    )

    if (
        report_evidence_count
        != actual_evidence_count
    ):

        errors.append(
            "evidence_count mismatch: "
            f"report={report_evidence_count}, "
            f"actual={actual_evidence_count}"
        )

    # ========================================================
    # REPORT CAUSE COUNT
    # ========================================================

    report_cause_count = (
        _get_report_cause_count(
            final_report,
            actual_cause_count,
        )
    )

    if (
        report_cause_count
        != actual_cause_count
    ):

        errors.append(
            "cause_count mismatch: "
            f"report={report_cause_count}, "
            f"actual={actual_cause_count}"
        )

    # ========================================================
    # REPORT RISK COUNT
    # ========================================================

    report_risk_count = (
        _get_report_risk_count(
            final_report,
            actual_risk_count,
        )
    )

    if (
        report_risk_count
        != actual_risk_count
    ):

        errors.append(
            "risk_count mismatch: "
            f"report={report_risk_count}, "
            f"actual={actual_risk_count}"
        )

    # ========================================================
    # SOURCE STATISTICS
    # ========================================================

    actual_sources = _source_counts(
        evidence
    )

    report_stats = _get_report_evidence_stats(
        final_report
    )

    for source in (
        "news",
        "market",
        "company",
    ):

        report_value = _safe_int(
            report_stats.get(
                source,
                0,
            )
        )

        actual_value = actual_sources[
            source
        ]

        if report_value != actual_value:

            errors.append(
                f"{source} evidence mismatch: "
                f"report={report_value}, "
                f"actual={actual_value}"
            )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "passed": len(errors) == 0,
        "errors": errors,
    }


# ============================================================
# TRACE VALIDATION
# ============================================================

#
# IMPORTANT:
#
# audit_agent is NOT required here.
#
# Why?
#
# audit_agent is currently executing. Its own trace entry
# cannot be present until this node finishes.
#
# The workflow wrapper will append:
#
#     audit_agent
#
# after this node returns.
#
# Therefore requiring audit_agent here creates a guaranteed
# false failure.
#

REQUIRED_TRACE_AGENTS = [
    "supervisor",
    "company_agent",
    "news_agent",
    "market_agent",
    "movement_agent",
    "evidence_agent",
    "cause_agent",
    "risk_agent",
    "synthesis_agent",
]


TRACE_ALIASES = {

    # --------------------------------------------------------
    # Supervisor
    # --------------------------------------------------------

    "supervisor_agent": "supervisor",
    "supervisor_node": "supervisor",

    # --------------------------------------------------------
    # Company
    # --------------------------------------------------------

    "company": "company_agent",
    "company_node": "company_agent",

    # --------------------------------------------------------
    # News
    # --------------------------------------------------------

    "news": "news_agent",
    "news_node": "news_agent",

    # --------------------------------------------------------
    # Market
    # --------------------------------------------------------

    "market": "market_agent",
    "market_node": "market_agent",

    # --------------------------------------------------------
    # Movement
    # --------------------------------------------------------

    "movement": "movement_agent",
    "movement_node": "movement_agent",
    "movement_verification": "movement_agent",

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    "evidence": "evidence_agent",

    # Legacy alias
    "evidence_collector": "evidence_agent",

    # --------------------------------------------------------
    # Cause
    # --------------------------------------------------------

    "cause": "cause_agent",

    # Legacy alias
    "cause_analyzer": "cause_agent",

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    "risk": "risk_agent",

    # Legacy alias
    "risk_analyzer": "risk_agent",

    # --------------------------------------------------------
    # Synthesis
    # --------------------------------------------------------

    "synthesis": "synthesis_agent",
    "synthesis_node": "synthesis_agent",

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    "audit": "audit_agent",
    "audit_node": "audit_agent",
}


def _canonical_agent_name(
    value: Any,
) -> str:

    if value is None:
        return ""

    value = str(
        value
    ).strip()

    return TRACE_ALIASES.get(
        value,
        value,
    )


def _validate_trace(
    trace: List[Dict[str, Any]],
) -> Dict[str, Any]:

    errors = []

    found_agents = set()

    for item in trace:

        if not isinstance(
            item,
            dict,
        ):
            continue

        agent = item.get(
            "agent"
        )

        canonical = _canonical_agent_name(
            agent
        )

        if canonical:

            found_agents.add(
                canonical
            )

    for required_agent in REQUIRED_TRACE_AGENTS:

        if required_agent not in found_agents:

            errors.append(
                f"Missing agent: "
                f"{required_agent}"
            )

    return {
        "passed": len(errors) == 0,

        "errors": errors,

        "found_agents": sorted(
            found_agents
        ),

        "required_agents": REQUIRED_TRACE_AGENTS,
    }


# ============================================================
# MAIN AUDIT NODE
# ============================================================


def audit_agent(
    state: InvestigationState,
) -> Dict[str, Any]:

    print()
    print("=" * 70)
    print("[Audit Agent] Building investigation audit")
    print("=" * 70)

    # ========================================================
    # DATA
    # ========================================================

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

    final_report = state.get(
        "final_report",
        {},
    ) or {}

    trace = list(
        state.get(
            "trace",
            [],
        )
        or []
    )

    investigation_id = (
        final_report.get(
            "investigation_id"
        )
        or f"INV-{uuid4().hex[:12].upper()}"
    )

    # ========================================================
    # SOURCE STATISTICS
    # ========================================================

    source_counts = _source_counts(
        evidence
    )

    print(
        f"[Audit Agent] Investigation ID: "
        f"{investigation_id}"
    )

    print(
        f"[Audit Agent] Evidence records: "
        f"{len(evidence)}"
    )

    print(
        f"[Audit Agent] Cause records: "
        f"{len(causes)}"
    )

    print(
        f"[Audit Agent] Risk records: "
        f"{len(risks)}"
    )

    # ========================================================
    # MANIFESTS
    # ========================================================

    evidence_manifest = _evidence_manifest(
        evidence
    )

    cause_manifest = _cause_manifest(
        causes
    )

    risk_manifest = _risk_manifest(
        risks
    )

    finding_manifest = _finding_manifest(
        final_report
    )

    print(
        f"[Audit Agent] Findings: "
        f"{len(finding_manifest)}"
    )

    print(
        f"[Audit Agent] News evidence: "
        f"{source_counts['news']}"
    )

    print(
        f"[Audit Agent] Market evidence: "
        f"{source_counts['market']}"
    )

    print(
        f"[Audit Agent] Company evidence: "
        f"{source_counts['company']}"
    )

    # ========================================================
    # VALIDATIONS
    # ========================================================

    report_count_validation = (
        _validate_report_counts(
            final_report=final_report,
            evidence=evidence,
            causes=causes,
            risks=risks,
        )
    )

    finding_validation = _validate_findings(
        findings=finding_manifest,
        evidence=evidence,
    )

    reference_validation = (
        _validate_evidence_references(
            evidence=evidence,
            causes=causes,
            risks=risks,
            findings=finding_manifest,
        )
    )

    trace_validation = _validate_trace(
        trace
    )

    # ========================================================
    # LOG VALIDATIONS
    # ========================================================

    print(
        "[Audit Agent] Evidence statistics: "
        f"{'PASS' if report_count_validation['passed'] else 'FAIL'}"
    )

    print(
        "[Audit Agent] Finding validation: "
        f"{'PASS' if finding_validation['passed'] else 'FAIL'}"
    )

    print(
        "[Audit Agent] Evidence references: "
        f"{'PASS' if reference_validation['passed'] else 'FAIL'}"
    )

    print(
        "[Audit Agent] Trace validation: "
        f"{'PASS' if trace_validation['passed'] else 'FAIL'}"
    )

    # ========================================================
    # BUILD ERRORS
    # ========================================================

    validation_errors = []

    validation_errors.extend(
        report_count_validation[
            "errors"
        ]
    )

    validation_errors.extend(
        finding_validation[
            "errors"
        ]
    )

    validation_errors.extend(
        reference_validation[
            "errors"
        ]
    )

    validation_errors.extend(
        trace_validation[
            "errors"
        ]
    )

    overall_pass = (
        len(validation_errors) == 0
    )

    # ========================================================
    # AUDIT OBJECT
    # ========================================================

    audit = {

        "investigation_id": investigation_id,

        "execution": {

            "query": state.get(
                "query"
            ),

            "company": state.get(
                "company"
            ),

            "investigation_intent": state.get(
                "investigation_intent"
            ),

            "price_direction": state.get(
                "price_direction"
            ),

            "movement_verification": state.get(
                "movement_verification",
                {},
            ),
        },

        "evidence": {

            "count": len(evidence),

            "source_counts": source_counts,

            "manifest": evidence_manifest,
        },

        "causes": {

            "count": len(causes),

            "manifest": cause_manifest,
        },

        "risks": {

            "count": len(risks),

            "manifest": risk_manifest,
        },

        "report": {

            "evidence_count": (
                _get_report_evidence_count(
                    final_report
                )
            ),

            "cause_count": (
                _get_report_cause_count(
                    final_report,
                    len(causes),
                )
            ),

            "risk_count": (
                _get_report_risk_count(
                    final_report,
                    len(risks),
                )
            ),

            "evidence_stats": (
                _get_report_evidence_stats(
                    final_report
                )
            ),

            "evidence_statistics": (
                _get_report_evidence_stats(
                    final_report
                )
            ),

            "finding_count": len(
                finding_manifest
            ),

            "findings": finding_manifest,

            "cause_summary": final_report.get(
                "cause_summary"
            ),

            "risk_summary": final_report.get(
                "risk_summary"
            ),

            "summary": final_report.get(
                "summary"
            ),
        },

        "validation": {

            "report_counts": {

                "status": (
                    "PASS"
                    if report_count_validation["passed"]
                    else "FAIL"
                ),

                "errors": report_count_validation[
                    "errors"
                ],
            },

            "findings": {

                "status": (
                    "PASS"
                    if finding_validation["passed"]
                    else "FAIL"
                ),

                "errors": finding_validation[
                    "errors"
                ],
            },

            "evidence_references": {

                "status": (
                    "PASS"
                    if reference_validation["passed"]
                    else "FAIL"
                ),

                "errors": reference_validation[
                    "errors"
                ],
            },

            "trace": {

                "status": (
                    "PASS"
                    if trace_validation["passed"]
                    else "FAIL"
                ),

                "errors": trace_validation[
                    "errors"
                ],

                "found_agents": trace_validation[
                    "found_agents"
                ],

                "required_agents": trace_validation[
                    "required_agents"
                ],
            },

            "overall": (
                "PASS"
                if overall_pass
                else "FAIL"
            ),

            "errors": validation_errors,
        },

        "overall": (
            "PASS"
            if overall_pass
            else "FAIL"
        ),
    }

    # ========================================================
    # PRINT ERRORS
    # ========================================================

    if not overall_pass:

        print(
            "[Audit Validation] "
            "Validation errors:"
        )

        for error in validation_errors:

            print(
                f"  - {error}"
            )

    print(
        f"[Audit Agent] Overall: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    print(
        f"[Audit Agent] Audit result: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    print("=" * 70)

    # ========================================================
    # IMPORTANT TRACE DESIGN
    # ========================================================
    #
    # DO NOT append audit_agent to trace here.
    #
    # The workflow wrapper must add the audit_agent trace
    # after this node returns.
    #
    # This is necessary because _validate_trace() executes
    # before the audit node has completed.
    #
    # ========================================================

    return {
        "audit": audit,
    }


# ============================================================
# BACKWARD-COMPATIBLE ALIASES
# ============================================================

audit = audit_agent

audit_agent_node = audit_agent