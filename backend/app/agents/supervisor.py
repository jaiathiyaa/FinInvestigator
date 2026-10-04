from __future__ import annotations

import re
from typing import Any, Dict, Optional


# ============================================================
# CONFIGURATION
# ============================================================

CAUSE_ANALYSIS_PATTERNS = [
    r"\bwhy\s+did\b",
    r"\bwhy\s+has\b",
    r"\bwhy\s+have\b",
    r"\bwhy\s+is\b",
    r"\bwhy\s+are\b",
    r"\bwhat\s+caused\b",
    r"\bwhat\s+causes\b",
    r"\bwhat\s+made\b",
    r"\bwhat\s+is\s+causing\b",
    r"\bwhat\s+are\s+the\s+reasons\b",
    r"\breason\s+for\b",
    r"\bcauses?\s+of\b",
]

UP_PATTERNS = [
    r"\brise\b",
    r"\brising\b",
    r"\brose\b",
    r"\bgain\b",
    r"\bgained\b",
    r"\bgaining\b",
    r"\bup\b",
    r"\bupward\b",
    r"\brally\b",
    r"\brallied\b",
    r"\brallying\b",
    r"\bincrease\b",
    r"\bincreased\b",
    r"\bincreasing\b",
    r"\bjump\b",
    r"\bjumped\b",
    r"\bjumping\b",
    r"\bsurge\b",
    r"\bsurged\b",
    r"\bsurging\b",
    r"\bclimb\b",
    r"\bclimbed\b",
    r"\bclimbing\b",
    r"\badvance\b",
    r"\badvanced\b",
    r"\badvancing\b",
]

DOWN_PATTERNS = [
    r"\bfall\b",
    r"\bfalling\b",
    r"\bfell\b",
    r"\bdown\b",
    r"\bdownward\b",
    r"\bdecline\b",
    r"\bdeclined\b",
    r"\bdeclining\b",
    r"\bdrop\b",
    r"\bdropped\b",
    r"\bdropping\b",
    r"\bslump\b",
    r"\bslumped\b",
    r"\bslumping\b",
    r"\bselloff\b",
    r"\bsell-off\b",
    r"\bselloff\b",
    r"\bdecrease\b",
    r"\bdecreased\b",
    r"\bdecreasing\b",
    r"\bplunge\b",
    r"\bplunged\b",
    r"\bplunging\b",
    r"\bslide\b",
    r"\bslid\b",
    r"\bsliding\b",
    r"\bretreat\b",
    r"\bretreated\b",
    r"\bretreating\b",
]

MARKET_SUFFIXES = [
    "stock",
    "shares",
    "share",
    "stock price",
    "share price",
    "stock value",
    "market price",
]

QUERY_PREFIXES = [
    "why did",
    "why has",
    "why have",
    "why is",
    "why are",
    "what caused",
    "what causes",
    "what made",
    "what is causing",
    "what are the reasons for",
    "reason for",
    "cause of",
    "causes of",
    "investigate",
    "investigation into",
    "analyze",
    "analyse",
    "analysis of",
]


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_query(query: str) -> str:
    """
    Normalize whitespace and punctuation without destroying
    company names.
    """
    query = str(query or "").strip()

    query = re.sub(
        r"\s+",
        " ",
        query,
    )

    return query


def _clean_company_name(company: str) -> str:
    """
    Clean extracted company/entity text.
    """

    company = str(company or "").strip()

    # Remove surrounding punctuation.
    company = company.strip(
        " \t\n\r.,!?;:\"'()[]{}"
    )

    # Remove common market descriptors at the end.
    company = re.sub(
        r"\s+(?:stock|shares?|stock\s+price|share\s+price)$",
        "",
        company,
        flags=re.IGNORECASE,
    )

    # Remove directional tails accidentally captured.
    company = re.sub(
        r"\s+(?:to|that\s+is|which\s+is)\s+"
        r"(?:rise|riseing|rising|fall|falling|"
        r"up|down|increase|decrease|gain|drop|"
        r"jump|surge|decline|plunge|slump|slide)$",
        "",
        company,
        flags=re.IGNORECASE,
    )

    company = company.strip(
        " \t\n\r.,!?;:\"'()[]{}"
    )

    return company


# ============================================================
# PRICE DIRECTION
# ============================================================

def _contains_pattern(
    text: str,
    patterns: list[str],
) -> bool:
    for pattern in patterns:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def _detect_price_direction(
    query: str,
) -> str:
    """
    Return:
        up
        down
        unknown
    """

    normalized = query.lower()

    has_up = _contains_pattern(
        normalized,
        UP_PATTERNS,
    )

    has_down = _contains_pattern(
        normalized,
        DOWN_PATTERNS,
    )

    # Explicit directional phrase wins.
    if re.search(
        r"\b(?:rise|rising|rose|up|gain|gained|"
        r"rally|rallied|surge|surged|jump|jumped|"
        r"increase|increased)\b",
        normalized,
    ):
        if not re.search(
            r"\b(?:fall|falling|fell|down|decline|"
            r"declined|drop|dropped|slump|slumped|"
            r"decrease|decreased|plunge|plunged)\b",
            normalized,
        ):
            return "up"

    if re.search(
        r"\b(?:fall|falling|fell|down|decline|"
        r"declined|drop|dropped|slump|slumped|"
        r"decrease|decreased|plunge|plunged|"
        r"selloff|sell-off)\b",
        normalized,
    ):
        if not re.search(
            r"\b(?:rise|rising|rose|up|gain|gained|"
            r"rally|rallied|surge|surged|jump|jumped|"
            r"increase|increased)\b",
            normalized,
        ):
            return "down"

    if has_up and not has_down:
        return "up"

    if has_down and not has_up:
        return "down"

    return "unknown"


# ============================================================
# INTENT
# ============================================================

def _detect_investigation_intent(
    query: str,
) -> str:
    normalized = query.lower()

    for pattern in CAUSE_ANALYSIS_PATTERNS:
        if re.search(
            pattern,
            normalized,
        ):
            return "cause_analysis"

    return "general_investigation"


# ============================================================
# COMPANY EXTRACTION
# ============================================================

def _extract_after_prefix(
    query: str,
) -> Optional[str]:
    """
    Extract entity after phrases such as:

        Why did NVIDIA...
        What caused NVIDIA...
        Investigate NVIDIA
    """

    normalized = query.strip()

    prefix_pattern = (
        r"^(?:"
        + "|".join(
            re.escape(prefix)
            for prefix in sorted(
                QUERY_PREFIXES,
                key=len,
                reverse=True,
            )
        )
        + r")\s+"
    )

    match = re.match(
        prefix_pattern,
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    remainder = normalized[
        match.end():
    ].strip()

    if not remainder:
        return None

    return remainder


def _extract_company(
    query: str,
) -> str:
    """
    Deterministically extract the company/entity from a
    natural-language investment query.

    Important examples:

        Why did NVIDIA stock rise?
            -> NVIDIA

        Why did NVIDIA shares fall?
            -> NVIDIA

        What caused NVIDIA shares to rise?
            -> NVIDIA

        What caused NVIDIA shares to fall?
            -> NVIDIA

        Investigate NVIDIA
            -> NVIDIA
    """

    query = _normalize_query(
        query
    )

    if not query:
        return ""

    # --------------------------------------------------------
    # Direct ticker/company form
    #
    # Example:
    #   NVIDIA
    #   NVDA
    #   Microsoft
    # --------------------------------------------------------

    direct = query.strip(
        " \t\n\r.,!?;:"
    )

    if (
        len(direct.split()) <= 5
        and not re.search(
            r"\b(?:why|what|caused|cause|investigate|"
            r"stock|shares?|rise|fall|rising|falling|"
            r"up|down)\b",
            direct,
            flags=re.IGNORECASE,
        )
    ):
        return _clean_company_name(
            direct
        )

    # --------------------------------------------------------
    # Extract text following question prefix.
    # --------------------------------------------------------

    remainder = _extract_after_prefix(
        query
    )

    if remainder:
        candidate = remainder

        # ----------------------------------------------------
        # Critical fix:
        #
        # "NVIDIA shares to rise"
        # "NVIDIA stock rise"
        #
        # must become:
        #
        # "NVIDIA"
        # ----------------------------------------------------

        candidate = re.split(
            r"\s+(?:"
            r"stock|stocks|"
            r"shares?|"
            r"share\s+price|"
            r"stock\s+price|"
            r"price"
            r")\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        candidate = re.split(
            r"\s+(?:"
            r"to\s+"
            r"(?:rise|rising|"
            r"fall|falling|"
            r"gain|gaining|"
            r"drop|dropping|"
            r"jump|jumping|"
            r"surge|surging|"
            r"decline|declining|"
            r"increase|increasing|"
            r"decrease|decreasing|"
            r"plunge|plunging|"
            r"slump|slumping|"
            r"slide|sliding)"
            r")\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        candidate = _clean_company_name(
            candidate
        )

        if candidate:
            return candidate

    # --------------------------------------------------------
    # Fallback:
    #
    # Find the company before a market noun.
    #
    # "NVIDIA shares rose"
    # "NVIDIA stock fell"
    # --------------------------------------------------------

    market_match = re.search(
        r"^(?P<company>.+?)\s+"
        r"(?:stock|stocks|shares?|"
        r"stock\s+price|share\s+price)\b",
        query,
        flags=re.IGNORECASE,
    )

    if market_match:
        company = _clean_company_name(
            market_match.group(
                "company"
            )
        )

        if company:
            return company

    # --------------------------------------------------------
    # Final fallback:
    #
    # Remove generic question words and directions.
    # --------------------------------------------------------

    cleaned = query

    cleaned = re.sub(
        r"\b(?:why|did|does|do|has|have|is|are|"
        r"what|caused|cause|causes|made|"
        r"investigate|investigation|"
        r"the|stock|stocks|shares?|"
        r"rise|rising|rose|fall|falling|fell|"
        r"up|down|increase|increased|"
        r"decrease|decreased|gain|gained|"
        r"drop|dropped|jump|jumped|"
        r"surge|surged|decline|declined)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    return _clean_company_name(
        cleaned
    )


# ============================================================
# SUPERVISOR NODE
# ============================================================

def supervisor(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Supervisor node for the FinInvestigator graph.

    Responsibilities:
        1. Read the investigation query.
        2. Extract company/entity.
        3. Determine investigation intent.
        4. Determine price direction.
        5. Preserve graph trace.
        6. Preserve errors.
    """

    query = _normalize_query(
        state.get(
            "query",
            "",
        )
    )

    if not query:
        error = (
            "Investigation query cannot be empty."
        )

        print(
            f"[Supervisor] Error: {error}"
        )

        return {
            **state,
            "company": "",
            "investigation_intent": (
                "general_investigation"
            ),
            "price_direction": "unknown",
            "trace": [
                *state.get(
                    "trace",
                    [],
                ),
                {
                    "agent": "supervisor",
                    "status": "failed",
                    "error": error,
                },
            ],
            "errors": [
                *state.get(
                    "errors",
                    [],
                ),
                error,
            ],
        }

    company = _extract_company(
        query
    )

    intent = _detect_investigation_intent(
        query
    )

    price_direction = _detect_price_direction(
        query
    )

    print(
        f"[Supervisor] Query: {query}"
    )

    print(
        f"[Supervisor] Company: {company}"
    )

    print(
        f"[Supervisor] Intent: {intent}"
    )

    print(
        f"[Supervisor] Price direction: "
        f"{price_direction}"
    )

    trace_event = {
        "agent": "supervisor",
        "status": "completed",
        "query": query,
        "company": company,
        "intent": intent,
        "price_direction": price_direction,
    }

    errors = list(
        state.get(
            "errors",
            [],
        )
    )

    if not company:
        error = (
            "Could not identify a company/entity "
            "from the investigation query."
        )

        errors.append(
            error
        )

        trace_event[
            "status"
        ] = "failed"

        trace_event[
            "error"
        ] = error

        print(
            f"[Supervisor] Error: {error}"
        )

    return {
        **state,
        "query": query,
        "company": company,
        "investigation_intent": intent,
        "price_direction": price_direction,
        "trace": [
            *state.get(
                "trace",
                [],
            ),
            trace_event,
        ],
        "errors": errors,
    }


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

supervisor_agent = supervisor
supervisor_node = supervisor


__all__ = [
    "supervisor",
    "supervisor_agent",
    "supervisor_node",
]