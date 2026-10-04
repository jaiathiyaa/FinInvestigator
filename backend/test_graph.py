"""

FinInvestigator Graph Test

Version 8.9



Usage:

    python test_graph.py "Why did NVIDIA stock rise?"



This test:

    1. Executes the LangGraph workflow.

    2. Validates the final state.

    3. Validates evidence statistics.

    4. Validates causes and risks.

    5. Validates finding text and evidence references.

    6. Validates the complete trace.

    7. Validates safety flags.

    8. Prints a final PASS/FAIL result.



Important:

    The canonical agent names are:



        supervisor

        company_agent

        news_agent

        market_agent

        movement_agent

        evidence_agent

        cause_agent

        risk_agent

        synthesis_agent

        audit_agent



    Legacy names such as evidence_collector and risk_analyzer

    are NOT required.

"""



from __future__ import annotations

import asyncio

import sys

import traceback

from typing import Any, Dict, List





# ============================================================

# IMPORT WORKFLOW

# ============================================================



try:

    from app.graph.workflow import graph

except Exception as exc:

    print("=" * 70)

    print("GRAPH IMPORT FAILED")

    print("=" * 70)

    print(f"{type(exc).__name__}: {exc}")

    traceback.print_exc()

    sys.exit(1)





# ============================================================

# CONSTANTS

# ============================================================



VERSION = "8.9"



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

    "audit_agent",

]





TRACE_ALIASES = {

    "supervisor_agent": "supervisor",

    "supervisor_node": "supervisor",



    "company": "company_agent",

    "company_node": "company_agent",



    "news": "news_agent",

    "news_node": "news_agent",



    "market": "market_agent",

    "market_node": "market_agent",



    "movement": "movement_agent",

    "movement_node": "movement_agent",

    "movement_verification": "movement_agent",



    "evidence": "evidence_agent",

    "evidence_collector": "evidence_agent",



    "cause": "cause_agent",

    "cause_analyzer": "cause_agent",



    "risk": "risk_agent",

    "risk_analyzer": "risk_agent",



    "synthesis": "synthesis_agent",

    "synthesis_node": "synthesis_agent",



    "audit": "audit_agent",

    "audit_node": "audit_agent",

}





# ============================================================

# GENERIC HELPERS

# ============================================================





def safe_int(

    value: Any,

    default: int = 0,

) -> int:



    try:

        return int(value)



    except (TypeError, ValueError):

        return default





def safe_float(

    value: Any,

    default: float = 0.0,

) -> float:



    try:

        return float(value)



    except (TypeError, ValueError):

        return default





def normalize_text(

    value: Any,

) -> str:



    if value is None:

        return ""



    return str(value).strip()





def unique(

    values: List[str],

) -> List[str]:



    result = []

    seen = set()



    for value in values:



        if value is None:

            continue



        value = str(value)



        if value not in seen:



            seen.add(value)

            result.append(value)



    return result





# ============================================================

# SOURCE HELPERS

# ============================================================





def normalize_source_type(

    value: Any,

) -> str:



    if value is None:

        return "unknown"



    value = str(

        value

    ).strip().lower()



    if value == "finance":

        return "market"



    return value





def source_counts(

    evidence: List[Dict[str, Any]],

) -> Dict[str, int]:



    counts = {

        "news": 0,

        "market": 0,

        "company": 0,

    }



    for item in evidence:



        if not isinstance(

            item,

            dict,

        ):

            continue



        source_type = normalize_source_type(

            item.get("source_type")

        )



        if source_type in counts:



            counts[source_type] += 1



    return counts





# ============================================================

# EVIDENCE HELPERS

# ============================================================





def evidence_id(

    item: Dict[str, Any],

) -> str | None:



    value = (

        item.get("id")

        or item.get("evidence_id")

    )



    if value is None:

        return None



    return str(value)





def evidence_claim(

    item: Dict[str, Any],

) -> str:



    value = (

        item.get("claim")

        or item.get("text")

        or item.get("description")

        or item.get("statement")

    )



    return normalize_text(

        value

    )





def build_evidence_index(

    evidence: List[Dict[str, Any]],

) -> Dict[str, Dict[str, Any]]:



    index = {}



    for item in evidence:



        if not isinstance(

            item,

            dict,

        ):

            continue



        eid = evidence_id(

            item

        )



        if eid:



            index[eid] = item



    return index





# ============================================================

# REPORT HELPERS

# ============================================================





def get_evidence_statistics(

    final_report: Dict[str, Any],

) -> Dict[str, Any]:



    stats = final_report.get(

        "evidence_statistics"

    )



    if isinstance(

        stats,

        dict,

    ):

        return stats



    stats = final_report.get(

        "evidence_stats"

    )



    if isinstance(

        stats,

        dict,

    ):

        return stats



    return {}





def get_report_evidence_count(

    final_report: Dict[str, Any],

) -> int:



    if "evidence_count" in final_report:



        return safe_int(

            final_report.get(

                "evidence_count"

            )

        )



    stats = get_evidence_statistics(

        final_report

    )



    return safe_int(

        stats.get("total")

    )





def get_report_cause_count(

    final_report: Dict[str, Any],

    actual_count: int,

) -> int:



    if "cause_count" in final_report:



        return safe_int(

            final_report.get(

                "cause_count"

            )

        )



    return actual_count





def get_report_risk_count(

    final_report: Dict[str, Any],

    actual_count: int,

) -> int:



    if "risk_count" in final_report:



        return safe_int(

            final_report.get(

                "risk_count"

            )

        )



    return actual_count





# ============================================================

# CAUSE / RISK HELPERS

# ============================================================





def get_cause_type(

    cause: Dict[str, Any],

) -> str:



    return normalize_text(

        cause.get("cause_type")

        or cause.get("type")

        or "other"

    )





def get_cause_description(

    cause: Dict[str, Any],

) -> str:



    return normalize_text(

        cause.get("description")

        or cause.get("text")

        or cause.get("statement")

    )





def get_cause_evidence_ids(

    cause: Dict[str, Any],

) -> List[str]:



    ids = cause.get(

        "evidence_ids",

        [],

    )



    if not isinstance(

        ids,

        list,

    ):

        return []



    return unique(

        [

            str(value)

            for value in ids

            if value is not None

        ]

    )





def get_risk_type(

    risk: Dict[str, Any],

) -> str:



    return normalize_text(

        risk.get("risk_type")

        or risk.get("type")

        or "other"

    )





def get_risk_description(

    risk: Dict[str, Any],

) -> str:



    return normalize_text(

        risk.get("description")

        or risk.get("text")

        or risk.get("statement")

    )





def get_risk_evidence_ids(

    risk: Dict[str, Any],

) -> List[str]:



    ids = risk.get(

        "evidence_ids",

        [],

    )



    if not isinstance(

        ids,

        list,

    ):

        return []



    return unique(

        [

            str(value)

            for value in ids

            if value is not None

        ]

    )





# ============================================================

# FINDING HELPERS

# ============================================================





def get_finding_text(

    finding: Dict[str, Any],

) -> str:



    return normalize_text(

        finding.get("text")

        or finding.get("statement")

        or finding.get("description")

    )





def get_finding_type(

    finding: Dict[str, Any],

) -> str:



    return normalize_text(

        finding.get("type")

        or finding.get("cause_type")

        or "other"

    )





def get_finding_evidence_ids(

    finding: Dict[str, Any],

) -> List[str]:



    ids = finding.get(

        "evidence_ids",

        [],

    )



    if not isinstance(

        ids,

        list,

    ):

        return []



    return unique(

        [

            str(value)

            for value in ids

            if value is not None

        ]

    )





# ============================================================

# TRACE HELPERS

# ============================================================





def canonical_agent_name(

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





def get_trace_agents(

    trace: List[Dict[str, Any]],

) -> List[str]:



    agents = []



    for item in trace:



        if not isinstance(

            item,

            dict,

        ):

            continue



        agent = canonical_agent_name(

            item.get("agent")

        )



        if agent and agent not in agents:



            agents.append(agent)



    return agents





# ============================================================

# VALIDATION: EVIDENCE

# ============================================================





def validate_evidence(

    evidence: List[Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    ids = []



    for index, item in enumerate(

        evidence,

        start=1,

    ):



        if not isinstance(

            item,

            dict,

        ):



            errors.append(

                f"evidence {index}: "

                "not a dictionary"

            )



            continue



        eid = evidence_id(

            item

        )



        if not eid:



            errors.append(

                f"evidence {index}: "

                "missing ID"

            )



        else:



            ids.append(eid)



        claim = evidence_claim(

            item

        )



        if not claim:



            errors.append(

                f"evidence {index}: "

                "missing claim text"

            )



        source_type = normalize_source_type(

            item.get("source_type")

        )



        if source_type not in {

            "news",

            "market",

            "company",

        }:



            errors.append(

                f"evidence {index}: "

                f"invalid source_type "

                f"'{source_type}'"

            )



    duplicate_ids = [

        eid

        for eid in set(ids)

        if ids.count(eid) > 1

    ]



    if duplicate_ids:



        errors.append(

            "duplicate evidence IDs: "

            + ", ".join(

                sorted(

                    duplicate_ids

                )

            )

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "unique_ids": len(

            set(ids)

        ) == len(ids),

    }





# ============================================================

# VALIDATION: EVIDENCE STATISTICS

# ============================================================





def validate_evidence_statistics(

    evidence: List[Dict[str, Any]],

    final_report: Dict[str, Any],

) -> Dict[str, Any]:



    errors = []



    actual = source_counts(

        evidence

    )



    report = get_evidence_statistics(

        final_report

    )



    report_total = safe_int(

        report.get(

            "total",

            final_report.get(

                "evidence_count",

                0,

            ),

        )

    )



    actual_total = len(

        evidence

    )



    if report_total != actual_total:



        errors.append(

            "evidence total mismatch: "

            f"report={report_total}, "

            f"actual={actual_total}"

        )



    for source in (

        "news",

        "market",

        "company",

    ):



        report_value = safe_int(

            report.get(

                source,

                0,

            )

        )



        actual_value = actual[

            source

        ]



        if report_value != actual_value:



            errors.append(

                f"{source} evidence mismatch: "

                f"report={report_value}, "

                f"actual={actual_value}"

            )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "actual": actual,

        "report": report,

    }





# ============================================================

# VALIDATION: COUNTS

# ============================================================





def validate_report_counts(

    evidence: List[Dict[str, Any]],

    causes: List[Dict[str, Any]],

    risks: List[Dict[str, Any]],

    final_report: Dict[str, Any],

) -> Dict[str, Any]:



    errors = []



    actual_evidence_count = len(

        evidence

    )



    actual_cause_count = len(

        causes

    )



    actual_risk_count = len(

        risks

    )



    report_evidence_count = (

        get_report_evidence_count(

            final_report

        )

    )



    report_cause_count = (

        get_report_cause_count(

            final_report,

            actual_cause_count,

        )

    )



    report_risk_count = (

        get_report_risk_count(

            final_report,

            actual_risk_count,

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



    if (

        report_cause_count

        != actual_cause_count

    ):



        errors.append(

            "cause_count mismatch: "

            f"report={report_cause_count}, "

            f"actual={actual_cause_count}"

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



    return {

        "passed": len(errors) == 0,

        "errors": errors,

    }





# ============================================================

# VALIDATION: CAUSES

# ============================================================





def validate_causes(

    causes: List[Dict[str, Any]],

    evidence_index: Dict[str, Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    cause_keys = []



    for index, cause in enumerate(

        causes,

        start=1,

    ):



        if not isinstance(

            cause,

            dict,

        ):



            errors.append(

                f"cause {index}: "

                "invalid object"

            )



            continue



        cause_type = get_cause_type(

            cause

        )



        description = get_cause_description(

            cause

        )



        evidence_ids = (

            get_cause_evidence_ids(

                cause

            )

        )



        if not cause_type:



            errors.append(

                f"cause {index}: "

                "missing type"

            )



        if not description:



            errors.append(

                f"cause {index}: "

                "missing description"

            )



        if not evidence_ids:



            errors.append(

                f"cause {index}: "

                "missing evidence IDs"

            )



        for eid in evidence_ids:



            if eid not in evidence_index:



                errors.append(

                    f"cause {index}: "

                    f"unknown evidence ID "

                    f"{eid}"

                )



        normalized_key = (

            cause_type.lower(),

            description.lower(),

        )



        cause_keys.append(

            normalized_key

        )



    duplicates = [

        key

        for key in set(cause_keys)

        if cause_keys.count(key) > 1

    ]



    if duplicates:



        errors.append(

            "duplicate causes detected"

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "deduplicated": (

            len(cause_keys)

            == len(set(cause_keys))

        ),

    }





# ============================================================

# VALIDATION: RISKS

# ============================================================





def validate_risks(

    risks: List[Dict[str, Any]],

    evidence_index: Dict[str, Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    risk_keys = []



    for index, risk in enumerate(

        risks,

        start=1,

    ):



        if not isinstance(

            risk,

            dict,

        ):



            errors.append(

                f"risk {index}: "

                "invalid object"

            )



            continue



        risk_type = get_risk_type(

            risk

        )



        description = get_risk_description(

            risk

        )



        evidence_ids = (

            get_risk_evidence_ids(

                risk

            )

        )



        if not risk_type:



            errors.append(

                f"risk {index}: "

                "missing type"

            )



        if not description:



            errors.append(

                f"risk {index}: "

                "missing description"

            )



        if not evidence_ids:



            errors.append(

                f"risk {index}: "

                "missing evidence IDs"

            )



        for eid in evidence_ids:



            if eid not in evidence_index:



                errors.append(

                    f"risk {index}: "

                    f"unknown evidence ID "

                    f"{eid}"

                )



        normalized_key = (

            risk_type.lower(),

            description.lower(),

        )



        risk_keys.append(

            normalized_key

        )



    duplicates = [

        key

        for key in set(risk_keys)

        if risk_keys.count(key) > 1

    ]



    if duplicates:



        errors.append(

            "duplicate risks detected"

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "deduplicated": (

            len(risk_keys)

            == len(set(risk_keys))

        ),

    }





# ============================================================

# VALIDATION: RISK LANGUAGE

# ============================================================





def validate_risk_language(

    risks: List[Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    forbidden_phrases = [

        "may ",

        "might ",

        "could ",

        "would ",

        "likely ",

        "expected to",

        "expect to",

        "will ",

        "indicating ",

        "indicates ",

        "suggesting ",

        "suggests ",

        "leading to",

        "lead to",

        "result in",

        "resulted in",

        "caused ",

        "causes ",

        "causing ",

    ]



    for index, risk in enumerate(

        risks,

        start=1,

    ):



        if not isinstance(

            risk,

            dict,

        ):

            continue



        description = get_risk_description(

            risk

        )



        lowered = (

            " "

            + description.lower()

            + " "

        )



        for phrase in forbidden_phrases:



            if phrase in lowered:



                errors.append(

                    f"Risk {index} "

                    f"({get_risk_type(risk)}): "

                    f"forbidden phrase "

                    f"'{phrase}'"

                )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

    }





# ============================================================

# VALIDATION: FINDINGS

# ============================================================





def validate_findings(

    findings: List[Dict[str, Any]],

    evidence_index: Dict[str, Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    finding_ids = []



    for index, finding in enumerate(

        findings,

        start=1,

    ):



        if not isinstance(

            finding,

            dict,

        ):



            errors.append(

                f"finding {index}: "

                "invalid object"

            )



            continue



        finding_id = normalize_text(

            finding.get(

                "finding_id"

            )

        )



        text = get_finding_text(

            finding

        )



        evidence_ids = (

            get_finding_evidence_ids(

                finding

            )

        )



        if not finding_id:



            errors.append(

                f"finding {index}: "

                "missing finding_id"

            )



        else:



            finding_ids.append(

                finding_id

            )



        if not text:



            errors.append(

                f"finding {index}: "

                "missing finding text"

            )



        if not evidence_ids:



            errors.append(

                f"finding {index}: "

                "missing evidence IDs"

            )



        for eid in evidence_ids:



            if eid not in evidence_index:



                errors.append(

                    f"finding {index}: "

                    f"unknown evidence ID "

                    f"{eid}"

                )



    duplicate_ids = [

        fid

        for fid in set(finding_ids)

        if finding_ids.count(fid) > 1

    ]



    if duplicate_ids:



        errors.append(

            "duplicate finding IDs: "

            + ", ".join(

                sorted(

                    duplicate_ids

                )

            )

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "unique_ids": (

            len(finding_ids)

            == len(set(finding_ids))

        ),

    }





# ============================================================

# VALIDATION: SAFETY FLAGS

# ============================================================





def validate_safety_flags(

    final_report: Dict[str, Any],

) -> Dict[str, Any]:



    errors = []



    causal_claim_used = final_report.get(

        "causal_claim_used"

    )



    association_preserved = final_report.get(

        "association_preserved"

    )



    final_safety_validation = final_report.get(

        "final_safety_validation"

    )



    if causal_claim_used is True:



        errors.append(

            "causal_claim_used=True"

        )



    if association_preserved is False:



        errors.append(

            "association_preserved=False"

        )



    if final_safety_validation is False:



        errors.append(

            "final_safety_validation=False"

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

    }





# ============================================================

# VALIDATION: TRACE

# ============================================================





def validate_trace(

    trace: List[Dict[str, Any]],

) -> Dict[str, Any]:



    errors = []



    found_agents = get_trace_agents(

        trace

    )



    for required_agent in (

        REQUIRED_TRACE_AGENTS

    ):



        if required_agent not in found_agents:



            errors.append(

                f"Missing agent: "

                f"{required_agent}"

            )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "found_agents": found_agents,

        "required_agents": (

            REQUIRED_TRACE_AGENTS

        ),

    }





# ============================================================

# VALIDATION: MOVEMENT

# ============================================================





def validate_movement(

    state: Dict[str, Any],

) -> Dict[str, Any]:



    movement = state.get(

        "movement_verification",

        {},

    ) or {}



    errors = []



    if not isinstance(

        movement,

        dict,

    ):



        errors.append(

            "movement_verification "

            "is not a dictionary"

        )



        return {

            "passed": False,

            "errors": errors,

        }



    requested = normalize_text(

        movement.get(

            "requested_direction"

        )

    ).lower()



    actual = normalize_text(

        movement.get(

            "actual_direction"

        )

    ).lower()



    verified = movement.get(

        "verified"

    )



    matches_request = movement.get(

        "matches_request"

    )



    if not requested:



        errors.append(

            "missing requested_direction"

        )



    if not actual:



        errors.append(

            "missing actual_direction"

        )



    if verified is not True:



        errors.append(

            "movement verification "

            "did not pass"

        )



    # If the requested direction is explicit,

    # require the verifier to confirm it.

    if requested in {

        "up",

        "down",

        "flat",

    }:



        if matches_request is not True:



            errors.append(

                "movement does not match "

                "requested direction"

            )



    return {

        "passed": len(errors) == 0,

        "errors": errors,

        "movement": movement,

    }





# ============================================================

# FINAL STATE VALIDATION

# ============================================================





def validate_state(

    state: Dict[str, Any],

) -> Dict[str, Any]:



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



    trace = state.get(

        "trace",

        [],

    ) or []



    evidence_index = build_evidence_index(

        evidence

    )



    evidence_validation = (

        validate_evidence(

            evidence

        )

    )



    evidence_statistics_validation = (

        validate_evidence_statistics(

            evidence,

            final_report,

        )

    )



    report_count_validation = (

        validate_report_counts(

            evidence,

            causes,

            risks,

            final_report,

        )

    )



    cause_validation = validate_causes(

        causes,

        evidence_index,

    )



    risk_validation = validate_risks(

        risks,

        evidence_index,

    )



    risk_language_validation = (

        validate_risk_language(

            risks

        )

    )



    findings = final_report.get(

        "key_findings",

        [],

    )



    if not isinstance(

        findings,

        list,

    ):



        findings = []



    finding_validation = (

        validate_findings(

            findings,

            evidence_index,

        )

    )



    safety_validation = (

        validate_safety_flags(

            final_report

        )

    )



    trace_validation = validate_trace(

        trace

    )



    movement_validation = (

        validate_movement(

            state

        )

    )



    all_validations = [

        evidence_validation,

        evidence_statistics_validation,

        report_count_validation,

        cause_validation,

        risk_validation,

        risk_language_validation,

        finding_validation,

        safety_validation,

        trace_validation,

        movement_validation,

    ]



    errors = []



    for validation in all_validations:



        errors.extend(

            validation.get(

                "errors",

                [],

            )

        )



    return {

        "passed": len(errors) == 0,

        "errors": errors,



        "evidence": evidence_validation,



        "evidence_statistics": (

            evidence_statistics_validation

        ),



        "report_counts": (

            report_count_validation

        ),



        "causes": cause_validation,



        "risks": risk_validation,



        "risk_language": (

            risk_language_validation

        ),



        "findings": finding_validation,



        "safety": safety_validation,



        "trace": trace_validation,



        "movement": movement_validation,

    }





# ============================================================

# PRINT HELPERS

# ============================================================





def print_validation_result(

    label: str,

    validation: Dict[str, Any],

) -> None:



    status = (

        "PASS"

        if validation.get("passed")

        else "FAIL"

    )



    print(

        f"- {label}: {status}"

    )



    errors = validation.get(

        "errors",

        [],

    )



    for error in errors:



        print(

            f"    - {error}"

        )





# ============================================================

# PRINT INVESTIGATION SUMMARY

# ============================================================





def print_investigation_summary(

    state: Dict[str, Any],

) -> None:



    company = state.get(

        "company",

        "",

    )



    intent = state.get(

        "investigation_intent",

        "",

    )



    price_direction = state.get(

        "price_direction",

        "",

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



    final_report = state.get(

        "final_report",

        {},

    ) or {}



    print()

    print("Supervisor:")

    print(

        f"Company: {company}"

    )

    print(

        f"Intent: {intent}"

    )

    print(

        f"Price direction: {price_direction}"

    )



    news_data = state.get(

        "news_data",

        {},

    ) or {}



    print()

    print("News:")

    search_results_raw = news_data.get(
        "search_results",
        [],
    )

    if isinstance(search_results_raw, int):
        search_result_count = search_results_raw
    elif isinstance(search_results_raw, list):
        search_result_count = len(search_results_raw)
    else:
        search_result_count = safe_int(
            news_data.get(
                "result_count",
                news_data.get("total_results", 0),
            )
        )

    candidate_count_raw = news_data.get(
        "candidate_count",
        news_data.get("selected_source_count", 0),
    )

    if isinstance(candidate_count_raw, int):
        candidate_count = candidate_count_raw
    elif isinstance(candidate_count_raw, list):
        candidate_count = len(candidate_count_raw)
    else:
        candidate_count = safe_int(candidate_count_raw)

    articles_raw = news_data.get(
        "articles",
        [],
    )

    if isinstance(articles_raw, int):
        article_count = articles_raw
    elif isinstance(articles_raw, list):
        article_count = len(articles_raw)
    else:
        article_count = 0

    successful_raw = news_data.get(
        "successful_articles",
        0,
    )

    if isinstance(successful_raw, int):
        successful_count = successful_raw
    elif isinstance(successful_raw, list):
        successful_count = len(successful_raw)
    else:
        successful_count = 0

    failed_raw = news_data.get(
        "failed",
        news_data.get("failed_articles", 0),
    )

    if isinstance(failed_raw, int):
        failed_count = failed_raw
    elif isinstance(failed_raw, list):
        failed_count = len(failed_raw)
    else:
        failed_count = 0

    attempted_count = successful_count + failed_count

    print(f"{search_result_count} results")
    print(f"{candidate_count} candidates")
    print(f"{article_count} article records")
    print(
        f"{successful_count} successful, "
        f"{failed_count} failed, "
        f"{attempted_count} attempted"
    )

    counts = source_counts(

        evidence

    )



    print()

    print("Evidence:")



    print(

        f"Total evidence: {len(evidence)}"

    )



    print(

        f"News: {counts['news']}"

    )



    print(

        f"Market: {counts['market']}"

    )



    print(

        f"Company: {counts['company']}"

    )



    claim_types = {}



    for item in evidence:



        if not isinstance(

            item,

            dict,

        ):

            continue



        claim_type = item.get(

            "claim_type"

        )



        if claim_type:



            claim_type = str(

                claim_type

            )



            claim_types[claim_type] = (

                claim_types.get(

                    claim_type,

                    0,

                )

                + 1

            )



    if claim_types:



        print()

        print("Claim types:")



        for claim_type in sorted(

            claim_types

        ):



            print(

                f"  {claim_type}: "

                f"{claim_types[claim_type]}"

            )



    print()

    print("Cause Agent:")

    print(

        f"Validated {len(causes)} causes"

    )



    for cause in causes:



        cause_type = get_cause_type(

            cause

        )



        description = (

            get_cause_description(

                cause

            )

        )



        evidence_ids = (

            get_cause_evidence_ids(

                cause

            )

        )



        confidence = safe_float(

            cause.get(

                "confidence"

            )

        )



        print(

            f"- {cause_type}"

        )



        print(

            f"  Description: {description}"

        )



        print(

            f"  Evidence: "

            f"{', '.join(evidence_ids)}"

        )



        print(

            f"  Confidence: {confidence}"

        )



    print()

    print("Risk Agent:")

    print(

        f"Validated {len(risks)} risks"

    )



    for risk in risks:



        risk_type = get_risk_type(

            risk

        )



        description = (

            get_risk_description(

                risk

            )

        )



        evidence_ids = (

            get_risk_evidence_ids(

                risk

            )

        )



        confidence = safe_float(

            risk.get(

                "confidence"

            )

        )



        print(

            f"- {risk_type}"

        )



        print(

            f"  Description: {description}"

        )



        print(

            f"  Evidence: "

            f"{', '.join(evidence_ids)}"

        )



        print(

            f"  Confidence: {confidence}"

        )



    print()

    print("Synthesis:")



    print(

        f"Evidence Count: "

        f"{len(evidence)}"

    )



    print(

        f"Cause Count: "

        f"{len(causes)}"

    )



    print(

        f"Risk Count: "

        f"{len(risks)}"

    )



    report_stats = (

        get_evidence_statistics(

            final_report

        )

    )



    print(

        f"News: "

        f"{safe_int(report_stats.get('news'))}"

    )



    print(

        f"Market: "

        f"{safe_int(report_stats.get('market'))}"

    )



    print(

        f"Company: "

        f"{safe_int(report_stats.get('company'))}"

    )



    print()

    print("Final report:")



    summary = final_report.get(

        "summary"

    )



    if summary:

        print(

            f"summary: {summary}"

        )



    findings = final_report.get(

        "key_findings",

        [],

    )



    print()

    print("key findings:")



    for index, finding in enumerate(

        findings,

        start=1,

    ):



        if not isinstance(

            finding,

            dict,

        ):

            continue



        text = get_finding_text(

            finding

        )



        evidence_ids = (

            get_finding_evidence_ids(

                finding

            )

        )



        evidence_suffix = ""



        if evidence_ids:



            evidence_suffix = (

                " ("

                + ", ".join(

                    evidence_ids

                )

                + ")"

            )



        print(

            f"{index}. "

            f"{text}"

            f"{evidence_suffix}"

        )



    cause_summary = final_report.get(

        "cause_summary"

    )



    if cause_summary:



        print()

        print(

            f"cause_summary: "

            f"{cause_summary}"

        )



    risk_summary = final_report.get(

        "risk_summary"

    )



    if risk_summary:



        print()

        print(

            f"risk_summary: "

            f"{risk_summary}"

        )





# ============================================================

# MAIN

# ============================================================





async def main() -> int:



    # --------------------------------------------------------

    # Query

    # --------------------------------------------------------



    if len(sys.argv) > 1:



        query = " ".join(

            sys.argv[1:]

        ).strip()



    else:



        query = (

            "Why did NVIDIA stock rise?"

        )



    print("=" * 70)

    print(

        f"FININVESTIGATOR - VERSION {VERSION} GRAPH TEST"

    )

    print("=" * 70)



    print()

    print(

        f"Query: {query}"

    )



    # --------------------------------------------------------

    # Initial state

    # --------------------------------------------------------



    initial_state = {

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



    # --------------------------------------------------------

    # Execute graph

    # --------------------------------------------------------



    try:



        result = await graph.ainvoke(

            initial_state

        )



    except Exception as exc:



        print()

        print("=" * 70)

        print("GRAPH EXECUTION FAILED")

        print("=" * 70)



        print(

            f"{type(exc).__name__}: "

            f"{exc}"

        )



        print()



        traceback.print_exc()



        return 1



    # --------------------------------------------------------

    # Ensure dictionary

    # --------------------------------------------------------



    if not isinstance(

        result,

        dict,

    ):



        print()

        print(

            "GRAPH EXECUTION FAILED"

        )



        print(

            "Graph returned "

            f"{type(result).__name__} "

            "instead of a dictionary."

        )



        return 1



    # --------------------------------------------------------

    # Validate final state

    # --------------------------------------------------------



    validation = validate_state(

        result

    )



    # --------------------------------------------------------

    # Print investigation

    # --------------------------------------------------------



    print_investigation_summary(

        result

    )



    # --------------------------------------------------------

    # Validation section

    # --------------------------------------------------------



    print()

    print("Validation:")



    evidence_validation = (

        validation["evidence"]

    )



    print(

        "- Unique IDs: "

        + (

            "PASS"

            if evidence_validation.get(

                "unique_ids"

            )

            else "FAIL"

        )

    )



    print(

        "- Evidence required fields: "

        + (

            "PASS"

            if evidence_validation.get(

                "passed"

            )

            else "FAIL"

        )

    )



    print(

        "- All evidence source_type valid: "

        + (

            "PASS"

            if evidence_validation.get(

                "passed"

            )

            else "FAIL"

        )

    )



    # --------------------------------------------------------

    # Evidence statistics

    # --------------------------------------------------------



    evidence_stats_validation = (

        validation[

            "evidence_statistics"

        ]

    )



    actual_stats = (

        evidence_stats_validation[

            "actual"

        ]

    )



    report_stats = (

        evidence_stats_validation[

            "report"

        ]

    )



    print()

    print("Evidence Statistics:")



    print(

        f"News    -> Report: "

        f"{safe_int(report_stats.get('news'))} "

        f"| Actual: "

        f"{actual_stats['news']}"

    )



    print(

        f"Market  -> Report: "

        f"{safe_int(report_stats.get('market'))} "

        f"| Actual: "

        f"{actual_stats['market']}"

    )



    print(

        f"Company -> Report: "

        f"{safe_int(report_stats.get('company'))} "

        f"| Actual: "

        f"{actual_stats['company']}"

    )



    print_validation_result(

        "Evidence stats",

        evidence_stats_validation,

    )



    # --------------------------------------------------------

    # Causes

    # --------------------------------------------------------



    causes_validation = (

        validation[

            "causes"

        ]

    )



    print(

        f"- Causes: "

        f"{'PASS' if causes_validation['passed'] else 'FAIL'} "

        f"({len(result.get('causes', []) or [])} validated)"

    )



    print(

        "- Cause count: "

        + (

            "PASS"

            if validation[

                "report_counts"

            ]["passed"]

            else "FAIL"

        )

    )



    print(

        "- Cause deduplication: "

        + (

            "PASS"

            if causes_validation.get(

                "deduplicated"

            )

            else "FAIL"

        )

    )



    # --------------------------------------------------------

    # Risks

    # --------------------------------------------------------



    risks_validation = (

        validation[

            "risks"

        ]

    )



    risk_language_validation = (

        validation[

            "risk_language"

        ]

    )



    print(

        f"- Risks: "

        f"{'PASS' if risks_validation['passed'] else 'FAIL'} "

        f"({len(result.get('risks', []) or [])} validated)"

    )



    print(

        "- Risk count: "

        + (

            "PASS"

            if validation[

                "report_counts"

            ]["passed"]

            else "FAIL"

        )

    )



    print(

        "- Risk deduplication: "

        + (

            "PASS"

            if risks_validation.get(

                "deduplicated"

            )

            else "FAIL"

        )

    )



    print_validation_result(

        "Risk language",

        risk_language_validation,

    )



    # --------------------------------------------------------

    # Findings

    # --------------------------------------------------------



    finding_validation = (

        validation[

            "findings"

        ]

    )



    print_validation_result(

        "Report validation",

        finding_validation,

    )



    # --------------------------------------------------------

    # Safety

    # --------------------------------------------------------



    safety_validation = (

        validation[

            "safety"

        ]

    )



    print_validation_result(

        "Causal language",

        safety_validation,

    )



    print_validation_result(

        "Predictive language",

        safety_validation,

    )



    print_validation_result(

        "Investment advice",

        safety_validation,

    )



    # --------------------------------------------------------

    # Trace

    # --------------------------------------------------------



    trace_validation = (

        validation[

            "trace"

        ]

    )



    if trace_validation["passed"]:



        print(

            "- Trace: PASS"

        )



        print(

            "  Pipeline agents present: "

            f"{len(trace_validation['found_agents'])}/"

            f"{len(REQUIRED_TRACE_AGENTS)}"

        )



    else:



        print(

            "- Trace: FAIL"

        )



        print(

            "  Missing agents:"

        )



        for error in (

            trace_validation[

                "errors"

            ]

        ):



            print(

                f"    - {error}"

            )



    print()

    print(

        "Actual trace agents:"

    )



    for agent in (

        trace_validation[

            "found_agents"

        ]

    ):



        print(

            f"  - {agent}"

        )



    # --------------------------------------------------------

    # Movement

    # --------------------------------------------------------



    movement_validation = (

        validation[

            "movement"

        ]

    )



    print()

    print_validation_result(

        "Movement verification",

        movement_validation,

    )



    # --------------------------------------------------------

    # Errors

    # --------------------------------------------------------



    graph_errors = (

        result.get(

            "errors",

            [],

        )

        or []

    )



    print()



    if graph_errors:



        print(

            "- Graph errors: FAIL"

        )



        for error in graph_errors:



            print(

                f"  - {error}"

            )



    else:



        print(

            "- Graph errors: PASS"

        )



    # --------------------------------------------------------

    # Final errors

    # --------------------------------------------------------



    if validation["errors"]:



        print()

        print(

            "[Test Validation] "

            "Validation errors:"

        )



        for error in (

            validation["errors"]

        ):



            print(

                f"  - {error}"

            )



    # --------------------------------------------------------

    # Overall

    # --------------------------------------------------------



    overall_pass = (

        validation["passed"]

        and not graph_errors

    )



    print()

    print("=" * 70)



    if overall_pass:



        print(

            "Overall: PASS"

        )



    else:



        print(

            "Overall: FAIL"

        )



    print("=" * 70)



    return 0 if overall_pass else 1





# ============================================================

# ENTRY POINT

# ============================================================



if __name__ == "__main__":

    asyncio.run(main())