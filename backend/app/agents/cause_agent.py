from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
import re

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ============================================================
# FININVESTIGATOR
# CAUSE AGENT v8.6
# ============================================================


# ============================================================
# 1. ALLOWED CAUSE TYPES
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


# ============================================================
# 2. CAUSE TYPE ALIASES
# ============================================================

CAUSE_TYPE_ALIASES = {
    # Earnings / guidance
    "guidance": "earnings",
    "sales_guidance": "earnings",
    "revenue_guidance": "earnings",
    "forward_guidance": "earnings",
    "financial_guidance": "earnings",
    "earnings_guidance": "earnings",

    # Analyst activity
    "analyst_rating": "analyst_activity",
    "analyst_ratings": "analyst_activity",
    "analyst_action": "analyst_activity",
    "analyst_actions": "analyst_activity",
    "price_target": "analyst_activity",

    # Capital allocation
    "share_buyback": "capital_allocation",
    "buyback": "capital_allocation",
    "repurchase": "capital_allocation",
    "repurchase_program": "capital_allocation",

    # Sentiment
    "sentiment": "market_sentiment",
    "investor_sentiment": "market_sentiment",

    # Growth
    "growth": "business_growth",
    "revenue_growth": "business_growth",
    "business_growth": "business_growth",

    # Market
    "market": "market_conditions",
    "market_condition": "market_conditions",
    "market_conditions": "market_conditions",

    # Business event
    "event": "business_event",
    "business_events": "business_event",
}


# ============================================================
# 3. SIGNALS
# ============================================================

EARNINGS_SIGNALS = {
    "earnings",
    "earnings report",
    "earnings results",
    "quarterly earnings",
    "revenue",
    "net income",
    "operating income",
    "gross margin",
    "profit",
    "profitability",
    "eps",
    "earnings per share",
    "quarter",
    "quarterly",
    "financial results",
    "guidance",
    "revenue guidance",
    "sales guidance",
    "financial guidance",
    "outlook",
    "sales forecast",
    "revenue forecast",
}


CAPITAL_ALLOCATION_SIGNALS = {
    "buyback",
    "share buyback",
    "share repurchase",
    "repurchase",
    "repurchase program",
    "repurchase authorization",
    "share repurchase program",
    "dividend",
    "dividends",
    "capital return",
    "return capital",
    "returning capital",
}


ANALYST_SIGNALS = {
    "analyst",
    "analysts",
    "analyst rating",
    "analyst ratings",
    "price target",
    "price targets",
    "top pick",
    "overweight",
    "underweight",
    "equal weight",
    "upgrade",
    "upgraded",
    "downgrade",
    "downgraded",
    "reinstated",
    "initiated coverage",
    "coverage",
    "brokerage",
    "wall street analyst",
}


BUSINESS_GROWTH_SIGNALS = {
    "revenue growth",
    "sales growth",
    "customer growth",
    "customer demand",
    "demand",
    "orders",
    "backlog",
    "market share",
    "market-share",
    "growth",
    "strong demand",
    "ai demand",
    "data center demand",
    "cloud demand",
    "product demand",
}


SENTIMENT_SIGNALS = {
    "investor sentiment",
    "market sentiment",
    "investor reaction",
    "investors reacted",
    "investors responded",
    "investor confidence",
    "confidence",
    "optimism",
    "optimistic",
    "pessimism",
    "pessimistic",
    "bullish",
    "bearish",
    "positive reaction",
    "negative reaction",
    "positive sentiment",
    "negative sentiment",
    "enthusiasm",
    "concern",
    "concerns",
    "investor enthusiasm",
}


MARKET_CONDITION_SIGNALS = {
    "broader market",
    "stock market",
    "equity market",
    "nasdaq",
    "s&p",
    "s&p 500",
    "dow jones",
    "dow",
    "semiconductor sector",
    "semiconductor stocks",
    "technology sector",
    "tech sector",
    "technology stocks",
    "sector",
    "industry",
    "macro",
    "macroeconomic",
    "interest rates",
    "rate cut",
    "rate cuts",
    "rate hike",
    "rate hikes",
    "inflation",
    "economic data",
    "economic growth",
    "economic conditions",
}


BUSINESS_EVENT_SIGNALS = {
    "partnership",
    "partnerships",
    "contract",
    "contracts",
    "deal",
    "deals",
    "acquisition",
    "acquisitions",
    "merger",
    "mergers",
    "launch",
    "product launch",
    "product release",
    "expansion",
    "facility",
    "data center",
    "data centre",
    "agreement",
    "investment",
    "new product",
    "product announcement",
    "strategic agreement",
}


VALUATION_SIGNALS = {
    "valuation",
    "p/e",
    "p/e ratio",
    "pe ratio",
    "forward p/e",
    "trailing p/e",
    "price-to-earnings",
    "price to earnings",
    "multiple",
    "valuation multiple",
    "undervalued",
    "overvalued",
}


# ============================================================
# 4. STOCK-MOVEMENT / OUTCOME LANGUAGE
# ============================================================

OUTCOME_PHRASES = {
    "stock rose",
    "stock fell",
    "stock increased",
    "stock decreased",
    "stock gained",
    "stock declined",
    "stock dropped",
    "stock climbed",
    "stock surged",
    "stock rallied",
    "stock sold off",

    "shares rose",
    "shares fell",
    "shares increased",
    "shares decreased",
    "shares gained",
    "shares declined",
    "shares dropped",
    "shares climbed",
    "shares surged",
    "shares rallied",

    "share price rose",
    "share price fell",
    "share price increased",
    "share price decreased",

    "stock price rose",
    "stock price fell",
    "stock price increased",
    "stock price decreased",
    "stock price climbed",
    "stock price dropped",

    "hit an all-time high",
    "hit a new all-time high",
    "reached an all-time high",
    "reached a record high",
    "fresh record high",
    "new record high",
    "record high",

    "intraday high",
    "intraday low",

    "rose by",
    "fell by",
    "gained by",
    "declined by",
    "increased by",
    "decreased by",

    "market capitalization increased",
    "market capitalization rose",
    "market cap increased",
    "market cap rose",
}


# ============================================================
# 5. UNSAFE CAUSAL / INFERENTIAL LANGUAGE
# ============================================================

EXPLICIT_CAUSAL_PHRASES = {
    "caused",
    "causes",
    "cause",
    "caused by",
    "driven by",
    "drove",
    "drives",
    "led to",
    "resulted in",
    "triggered",
    "prompted",
    "boosted",
    "weighed on",
    "pressured",
    "responsible for",
    "attributed to",
    "cited as the reason",
    "reason for",
    "reason behind",
}


INFERENTIAL_CAUSAL_PHRASES = {
    "may have contributed",
    "might have contributed",
    "could have contributed",

    "may have influenced",
    "might have influenced",
    "could have influenced",

    "may explain",
    "might explain",
    "could explain",

    "suggesting",
    "suggests",
    "indicating",
    "indicates",

    "reflecting",
    "reflects",

    "likely reflects",
    "likely indicates",
    "likely suggests",

    "favorable perception",
    "favourable perception",
    "positive perception",
    "negative perception",

    "investor perception",

    "could be viewed as",
    "may be viewed as",
    "might be viewed as",

    "appears to have",
    "appears to",
    "seems to have",
    "seems to",
}


# ============================================================
# 6. PREDICTIVE LANGUAGE
# ============================================================

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

    "might rise",
    "might fall",
    "might increase",
    "might decrease",

    "expected to rise",
    "expected to fall",
    "expected to increase",
    "expected to decrease",

    "likely to rise",
    "likely to fall",
    "likely to increase",
    "likely to decrease",

    "forecast to rise",
    "forecast to fall",
    "forecast to increase",
    "forecast to decrease",
}


# ============================================================
# 7. INVESTMENT ADVICE
# ============================================================

INVESTMENT_ADVICE_PHRASES = {
    "buy the stock",
    "sell the stock",
    "buy shares",
    "sell shares",
    "you should buy",
    "you should sell",
    "invest in",
    "avoid the stock",
    "hold the stock",
    "strong buy",
    "strong sell",
    "buy signal",
    "sell signal",
}


# ============================================================
# 8. FACTUAL / NON-CAUSAL RELATIONSHIP PHRASES
# ============================================================

SAFE_ASSOCIATION_PHRASES = {
    "was reported alongside",
    "was reported at the same time",
    "coincided with",
    "occurred alongside",
    "was observed during",
    "was reported around the same period",
    "was announced alongside",
    "was reported during",
    "was disclosed during",
    "was announced during",
}


# ============================================================
# 9. PYDANTIC STRUCTURED OUTPUT
# ============================================================

class CauseRecord(BaseModel):
    cause_type: str = Field(
        description=(
            "One of the allowed cause categories."
        )
    )

    description: str = Field(
        description=(
            "A factual, evidence-grounded description of the "
            "underlying event or factor. Do not claim that the "
            "factor caused the stock movement unless the evidence "
            "explicitly establishes that relationship."
        )
    )

    evidence_ids: List[str] = Field(
        default_factory=list,
        description=(
            "Evidence IDs supporting this factor. "
            "Use only IDs present in the supplied evidence."
        ),
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
# 10. LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

cause_llm = llm.with_structured_output(
    CauseExtraction
)


# ============================================================
# 11. TEXT HELPERS
# ============================================================

def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(value).lower().strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def _get_evidence_id(
    record: Dict[str, Any],
) -> str:

    for key in (
        "evidence_id",
        "id",
        "evidenceId",
    ):

        value = record.get(key)

        if value:
            return str(value).strip()

    return ""


def _normalize_cause_type(
    value: Any,
) -> str:

    normalized = _normalize_text(
        value
    )

    if normalized in ALLOWED_CAUSE_TYPES:
        return normalized

    if normalized in CAUSE_TYPE_ALIASES:
        return CAUSE_TYPE_ALIASES[
            normalized
        ]

    return "other"


def _contains_any_signal(
    text: str,
    signals: Set[str],
) -> bool:

    normalized = _normalize_text(
        text
    )

    return any(
        signal in normalized
        for signal in signals
    )


def _signal_count(
    text: str,
    signals: Set[str],
) -> int:

    normalized = _normalize_text(
        text
    )

    return sum(
        1
        for signal in signals
        if signal in normalized
    )


def _find_phrase(
    text: str,
    phrases: Set[str],
) -> str | None:

    normalized = _normalize_text(
        text
    )

    for phrase in phrases:

        if phrase in normalized:
            return phrase

    return None


# ============================================================
# 12. LANGUAGE DETECTORS
# ============================================================

def _contains_predictive_language(
    description: str,
) -> str | None:

    return _find_phrase(
        description,
        PREDICTIVE_PHRASES,
    )


def _contains_inferential_language(
    description: str,
) -> str | None:

    return _find_phrase(
        description,
        INFERENTIAL_CAUSAL_PHRASES,
    )


def _contains_explicit_causal_language(
    description: str,
) -> str | None:

    return _find_phrase(
        description,
        EXPLICIT_CAUSAL_PHRASES,
    )


def _contains_investment_advice(
    description: str,
) -> str | None:

    return _find_phrase(
        description,
        INVESTMENT_ADVICE_PHRASES,
    )


# ============================================================
# 13. EVIDENCE INDEX
# ============================================================

def _build_evidence_index(
    evidence: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:

    index: Dict[
        str,
        Dict[str, Any],
    ] = {}

    for record in evidence:

        if not isinstance(
            record,
            dict,
        ):
            continue

        evidence_id = _get_evidence_id(
            record
        )

        if not evidence_id:
            continue

        index[evidence_id] = record

    return index


# ============================================================
# 14. EXTRACT TEXT FROM EVIDENCE
# ============================================================

def _claim_text(
    record: Dict[str, Any],
) -> str:

    fields = [
        "claim",
        "description",
        "text",
        "snippet",
        "content",
        "title",
        "headline",
        "summary",
        "reason",
        "impact",
        "why",
        "causal_relationship",
        "causal_link",
        "event",
        "observation",
    ]

    parts: List[str] = []

    for field in fields:

        value = record.get(
            field
        )

        if value is None:
            continue

        if isinstance(
            value,
            (dict, list),
        ):
            parts.append(
                str(value)
            )
        else:
            parts.append(
                str(value)
            )

    return " ".join(
        parts
    )


def _evidence_text_for_id(
    evidence_id: str,
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> str:

    record = evidence_index.get(
        evidence_id
    )

    if not record:
        return ""

    return _normalize_text(
        _claim_text(record)
    )


# ============================================================
# 15. TOKENIZATION
# ============================================================

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "from",
    "by",
    "at",
    "as",
    "is",
    "was",
    "were",
    "are",
    "has",
    "have",
    "had",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "their",
    "there",
    "than",
    "then",
    "into",
    "after",
    "before",
    "during",
    "while",
    "also",
    "reported",
    "according",
    "said",
}


def _tokenize(
    text: str,
) -> Set[str]:

    normalized = _normalize_text(
        text
    )

    tokens = re.findall(
        r"[a-z0-9]+",
        normalized,
    )

    return {
        token
        for token in tokens
        if len(token) >= 3
        and token not in STOPWORDS
    }


def _important_phrases(
    text: str,
) -> Set[str]:

    tokens = list(
        _tokenize(text)
    )

    phrases: Set[str] = set()

    for index in range(
        len(tokens) - 1
    ):

        phrases.add(
            f"{tokens[index]} "
            f"{tokens[index + 1]}"
        )

    return phrases


# ============================================================
# 16. EVIDENCE OVERLAP
# ============================================================

def _calculate_text_overlap(
    cause_text: str,
    evidence_text: str,
) -> float:

    cause_tokens = _tokenize(
        cause_text
    )

    evidence_tokens = _tokenize(
        evidence_text
    )

    if (
        not cause_tokens
        or not evidence_tokens
    ):
        return 0.0

    intersection = (
        cause_tokens.intersection(
            evidence_tokens
        )
    )

    token_score = (
        len(intersection)
        / max(
            len(cause_tokens),
            1,
        )
    )

    cause_phrases = (
        _important_phrases(
            cause_text
        )
    )

    evidence_phrases = (
        _important_phrases(
            evidence_text
        )
    )

    phrase_score = 0.0

    if cause_phrases:

        phrase_matches = (
            cause_phrases.intersection(
                evidence_phrases
            )
        )

        phrase_score = (
            len(phrase_matches)
            / len(cause_phrases)
        )

    return (
        0.75 * token_score
        + 0.25 * phrase_score
    )


# ============================================================
# 17. FIND BEST EVIDENCE
# ============================================================

def _find_best_evidence_matches(
    cause: CauseRecord,
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
    max_matches: int = 3,
) -> List[str]:

    cause_text = " ".join(
        [
            cause.description,
            cause.cause_type,
        ]
    )

    scored: List[
        Tuple[str, float]
    ] = []

    for (
        evidence_id,
        record,
    ) in evidence_index.items():

        evidence_text = (
            _normalize_text(
                _claim_text(record)
            )
        )

        if not evidence_text:
            continue

        score = (
            _calculate_text_overlap(
                cause_text,
                evidence_text,
            )
        )

        if score <= 0:
            continue

        scored.append(
            (
                evidence_id,
                score,
            )
        )

    scored.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        evidence_id
        for (
            evidence_id,
            score,
        ) in scored[
            :max_matches
        ]
        if score >= 0.30
    ]


# ============================================================
# 18. REPAIR EVIDENCE IDS
# ============================================================

def _repair_evidence_ids(
    cause: CauseRecord,
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> List[str]:

    valid_ids: List[str] = []

    for evidence_id in (
        cause.evidence_ids
    ):

        normalized_id = str(
            evidence_id
        ).strip()

        if (
            normalized_id
            in evidence_index
        ):

            if (
                normalized_id
                not in valid_ids
            ):
                valid_ids.append(
                    normalized_id
                )

    if valid_ids:
        return valid_ids

    return _find_best_evidence_matches(
        cause=cause,
        evidence_index=evidence_index,
        max_matches=3,
    )


# ============================================================
# 19. EXPLICIT CAUSAL SUPPORT
# ============================================================

def _evidence_explicitly_supports_cause(
    cause: CauseRecord,
    evidence_ids: List[str],
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> bool:

    for evidence_id in evidence_ids:

        record = evidence_index.get(
            evidence_id
        )

        if not record:
            continue

        text = _normalize_text(
            _claim_text(record)
        )

        # Evidence itself must contain
        # an explicit causal relationship.
        if _contains_explicit_causal_language(
            text
        ):
            return True

    return False


# ============================================================
# 20. OUTCOME DETECTION
# ============================================================

def _contains_outcome_language(
    text: str,
) -> bool:

    normalized = _normalize_text(
        text
    )

    for phrase in OUTCOME_PHRASES:

        if phrase in normalized:
            return True

    if re.search(
        r"\b(?:rose|fell|gained|declined|"
        r"increased|decreased|climbed|"
        r"dropped|surged|rallied)\b"
        r".{0,40}"
        r"\d+(?:\.\d+)?\s*%",
        normalized,
    ):

        return True

    return False


# ============================================================
# 21. OUTCOME-ONLY VALIDATION
# ============================================================

def _is_outcome_only_statement(
    description: str,
    evidence_text: str,
) -> bool:

    description_normalized = (
        _normalize_text(
            description
        )
    )

    evidence_normalized = (
        _normalize_text(
            evidence_text
        )
    )

    if not _contains_outcome_language(
        description_normalized
    ):
        return False

    explanatory_signals = (
        EARNINGS_SIGNALS
        | CAPITAL_ALLOCATION_SIGNALS
        | ANALYST_SIGNALS
        | BUSINESS_GROWTH_SIGNALS
        | SENTIMENT_SIGNALS
        | MARKET_CONDITION_SIGNALS
        | BUSINESS_EVENT_SIGNALS
        | VALUATION_SIGNALS
    )

    description_signal_count = (
        _signal_count(
            description_normalized,
            explanatory_signals,
        )
    )

    evidence_signal_count = (
        _signal_count(
            evidence_normalized,
            explanatory_signals,
        )
    )

    # If description contains multiple
    # explanatory signals, it is probably
    # describing a real factor.
    if description_signal_count >= 2:
        return False

    # One signal in the description can be
    # accepted when the underlying evidence
    # contains several explanatory signals.
    if (
        description_signal_count >= 1
        and evidence_signal_count >= 2
    ):
        return False

    return True


# ============================================================
# 22. CLAIM TYPE PRIORITY
# ============================================================

CLAIM_TYPE_PRIORITY = {
    "guidance": "earnings",
    "financial_metric": "earnings",
    "valuation_metric": "valuation",
    "analyst_action": "analyst_activity",
    "corporate_action": "capital_allocation",
    "business_event": "business_event",
    "executive_statement": "business_event",
    "risk": "other",
    "market_observation": None,
    "reported_claim": None,
}


# ============================================================
# 23. INFER BETTER CAUSE TYPE
# ============================================================

def _infer_better_cause_type(
    cause_type: str,
    description: str,
    evidence_ids: List[str],
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> str:

    normalized_description = (
        _normalize_text(
            description
        )
    )

    # --------------------------------------------------------
    # First use explicit claim types.
    # This prevents broad signals such as
    # "results" or "forecast" from incorrectly
    # overriding analyst/corporate evidence.
    # --------------------------------------------------------

    claim_type_votes: Dict[
        str,
        int,
    ] = {}

    for evidence_id in evidence_ids:

        record = evidence_index.get(
            evidence_id
        )

        if not record:
            continue

        claim_type = _normalize_text(
            record.get(
                "claim_type",
                ""
            )
        )

        mapped_type = (
            CLAIM_TYPE_PRIORITY.get(
                claim_type
            )
        )

        if mapped_type:

            claim_type_votes[
                mapped_type
            ] = (
                claim_type_votes.get(
                    mapped_type,
                    0,
                )
                + 1
            )

    if claim_type_votes:

        strongest_type = max(
            claim_type_votes,
            key=claim_type_votes.get,
        )

        strongest_count = (
            claim_type_votes[
                strongest_type
            ]
        )

        if strongest_count >= 1:
            return strongest_type

    # --------------------------------------------------------
    # Build combined text.
    # --------------------------------------------------------

    evidence_text = " ".join(
        _evidence_text_for_id(
            evidence_id,
            evidence_index,
        )
        for evidence_id in evidence_ids
    )

    text = _normalize_text(
        f"{normalized_description} "
        f"{evidence_text}"
    )

    # --------------------------------------------------------
    # Strongest deterministic signals.
    # --------------------------------------------------------

    if _contains_any_signal(
        text,
        CAPITAL_ALLOCATION_SIGNALS,
    ):
        return "capital_allocation"

    if _contains_any_signal(
        text,
        ANALYST_SIGNALS,
    ):
        return "analyst_activity"

    if _contains_any_signal(
        text,
        VALUATION_SIGNALS,
    ):
        return "valuation"

    if _contains_any_signal(
        text,
        BUSINESS_EVENT_SIGNALS,
    ):
        return "business_event"

    if _contains_any_signal(
        text,
        BUSINESS_GROWTH_SIGNALS,
    ):
        return "business_growth"

    if _contains_any_signal(
        text,
        SENTIMENT_SIGNALS,
    ):
        return "market_sentiment"

    if _contains_any_signal(
        text,
        MARKET_CONDITION_SIGNALS,
    ):
        return "market_conditions"

    if _contains_any_signal(
        text,
        EARNINGS_SIGNALS,
    ):
        return "earnings"

    return cause_type


# ============================================================
# 24. CAUSE TYPE QUALITY
# ============================================================

def _validate_cause_type_quality(
    cause_type: str,
    description: str,
    evidence_text: str,
) -> bool:

    text = _normalize_text(
        f"{description} {evidence_text}"
    )

    if cause_type == "market_sentiment":

        return _contains_any_signal(
            text,
            SENTIMENT_SIGNALS,
        )

    if cause_type == "market_conditions":

        return _contains_any_signal(
            text,
            MARKET_CONDITION_SIGNALS,
        )

    if cause_type == "valuation":

        return _contains_any_signal(
            text,
            VALUATION_SIGNALS,
        )

    if cause_type == "analyst_activity":

        return _contains_any_signal(
            text,
            ANALYST_SIGNALS,
        )

    if cause_type == "capital_allocation":

        return _contains_any_signal(
            text,
            CAPITAL_ALLOCATION_SIGNALS,
        )

    if cause_type == "earnings":

        return _contains_any_signal(
            text,
            EARNINGS_SIGNALS,
        )

    if cause_type == "business_growth":

        return _contains_any_signal(
            text,
            BUSINESS_GROWTH_SIGNALS,
        )

    if cause_type == "business_event":

        return _contains_any_signal(
            text,
            BUSINESS_EVENT_SIGNALS,
        )

    # "other" is allowed when the evidence
    # contains a genuine event/factor but does
    # not fit one of the predefined categories.
    return True


# ============================================================
# 25. QUALITY SCORE
# ============================================================

def _calculate_cause_quality(
    cause_type: str,
    description: str,
    evidence_ids: List[str],
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> float:

    score = 0.0

    description_normalized = (
        _normalize_text(
            description
        )
    )

    # Evidence grounding.
    if len(evidence_ids) >= 1:
        score += 0.25

    if len(evidence_ids) >= 2:
        score += 0.10

    if len(evidence_ids) >= 3:
        score += 0.05

    all_evidence_text = " ".join(
        _evidence_text_for_id(
            evidence_id,
            evidence_index,
        )
        for evidence_id in evidence_ids
    )

    all_text = (
        f"{description_normalized} "
        f"{_normalize_text(all_evidence_text)}"
    )

    explanatory_signals = (
        EARNINGS_SIGNALS
        | CAPITAL_ALLOCATION_SIGNALS
        | ANALYST_SIGNALS
        | BUSINESS_GROWTH_SIGNALS
        | SENTIMENT_SIGNALS
        | MARKET_CONDITION_SIGNALS
        | BUSINESS_EVENT_SIGNALS
        | VALUATION_SIGNALS
    )

    signal_count = _signal_count(
        all_text,
        explanatory_signals,
    )

    score += min(
        0.35,
        signal_count * 0.05,
    )

    if _validate_cause_type_quality(
        cause_type=cause_type,
        description=description,
        evidence_text=all_evidence_text,
    ):
        score += 0.20

    if _is_outcome_only_statement(
        description=description,
        evidence_text=all_evidence_text,
    ):
        score -= 0.40

    # Explicit causal wording receives
    # no bonus. Causality must be independently
    # validated.
    return max(
        0.0,
        min(
            1.0,
            score,
        )
    )


# ============================================================
# 26. DESCRIPTION GROUNDING
# ============================================================

def _ground_description(
    description: str,
    cause: CauseRecord,
    evidence_ids: List[str],
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> str | None:

    description = (
        description or ""
    ).strip()

    if not description:
        return None

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictive_phrase = (
        _contains_predictive_language(
            description
        )
    )

    if predictive_phrase:

        print(
            "[Cause Validation] "
            "Predictive language detected: "
            f"{predictive_phrase}"
        )

        return None

    # --------------------------------------------------------
    # Investment advice
    # --------------------------------------------------------

    advice_phrase = (
        _contains_investment_advice(
            description
        )
    )

    if advice_phrase:

        print(
            "[Cause Validation] "
            "Investment advice detected: "
            f"{advice_phrase}"
        )

        return None

    # --------------------------------------------------------
    # Evidence text
    # --------------------------------------------------------

    evidence_text_parts: List[str] = []

    for evidence_id in evidence_ids:

        evidence_text = (
            _evidence_text_for_id(
                evidence_id,
                evidence_index,
            )
        )

        if evidence_text:
            evidence_text_parts.append(
                evidence_text
            )

    evidence_text = " ".join(
        evidence_text_parts
    )

    # --------------------------------------------------------
    # Outcome-only cause
    # --------------------------------------------------------

    if _is_outcome_only_statement(
        description=description,
        evidence_text=evidence_text,
    ):

        print(
            "[Cause Validation] "
            "Outcome-only description detected."
        )

        return None

    # --------------------------------------------------------
    # Inferential language
    # --------------------------------------------------------

    inferential_phrase = (
        _contains_inferential_language(
            description
        )
    )

    if inferential_phrase:

        print(
            "[Cause Validation] "
            "Unsupported inferential language: "
            f"{inferential_phrase}"
        )

        return None

    # --------------------------------------------------------
    # Explicit causal language
    # --------------------------------------------------------

    explicit_phrase = (
        _contains_explicit_causal_language(
            description
        )
    )

    if explicit_phrase:

        explicitly_supported = (
            _evidence_explicitly_supports_cause(
                cause=cause,
                evidence_ids=evidence_ids,
                evidence_index=evidence_index,
            )
        )

        if not explicitly_supported:

            print(
                "[Cause Validation] "
                "Explicit causal wording is not "
                "supported by the cited evidence: "
                f"{explicit_phrase}"
            )

            return None

    # --------------------------------------------------------
    # Remove accidental causal tail if the LLM
    # generates a mixed factual/causal sentence.
    #
    # Example:
    #
    # "Revenue was above expectations, which
    # contributed to positive sentiment."
    #
    # We do NOT silently rewrite it here.
    # Rejecting it is safer because the system
    # should not alter an unsupported claim.
    # --------------------------------------------------------

    return description


# ============================================================
# 27. VALIDATE CAUSES
# ============================================================

def _validate_causes(
    causes: List[CauseRecord],
    evidence_index: Dict[
        str,
        Dict[str, Any],
    ],
) -> List[Dict[str, Any]]:

    validated: List[
        Dict[str, Any]
    ] = []

    for cause in causes:

        cause_type = _normalize_cause_type(
            cause.cause_type
        )

        # ----------------------------------------------------
        # Repair / validate evidence IDs
        # ----------------------------------------------------

        repaired_ids = (
            _repair_evidence_ids(
                cause=cause,
                evidence_index=evidence_index,
            )
        )

        if not repaired_ids:

            print(
                "[Cause Validation] "
                "Rejected cause with no grounded evidence: "
                f"{cause_type}"
            )

            continue

        # ----------------------------------------------------
        # Gather evidence text
        # ----------------------------------------------------

        evidence_text_parts: List[str] = []

        for evidence_id in repaired_ids:

            text = (
                _evidence_text_for_id(
                    evidence_id,
                    evidence_index,
                )
            )

            if text:
                evidence_text_parts.append(
                    text
                )

        evidence_text = " ".join(
            evidence_text_parts
        )

        # ----------------------------------------------------
        # Correct cause type
        # ----------------------------------------------------

        corrected_type = (
            _infer_better_cause_type(
                cause_type=cause_type,
                description=cause.description,
                evidence_ids=repaired_ids,
                evidence_index=evidence_index,
            )
        )

        if corrected_type != cause_type:

            print(
                "[Cause Validation] "
                f"Cause type corrected: "
                f"{cause_type} -> {corrected_type}"
            )

            cause_type = corrected_type

        # ----------------------------------------------------
        # Ground description
        # ----------------------------------------------------

        grounded_description = (
            _ground_description(
                description=cause.description,
                cause=cause,
                evidence_ids=repaired_ids,
                evidence_index=evidence_index,
            )
        )

        if not grounded_description:

            print(
                "[Cause Validation] "
                f"Rejected unsafe/outcome-only cause: "
                f"{cause_type}"
            )

            continue

        # ----------------------------------------------------
        # Validate type
        # ----------------------------------------------------

        if not _validate_cause_type_quality(
            cause_type=cause_type,
            description=grounded_description,
            evidence_text=evidence_text,
        ):

            print(
                "[Cause Validation] "
                f"Rejected low-quality cause type: "
                f"{cause_type}"
            )

            continue

        # ----------------------------------------------------
        # Quality score
        # ----------------------------------------------------

        quality_score = (
            _calculate_cause_quality(
                cause_type=cause_type,
                description=grounded_description,
                evidence_ids=repaired_ids,
                evidence_index=evidence_index,
            )
        )

        if quality_score < 0.30:

            print(
                "[Cause Validation] "
                f"Rejected low-quality cause: "
                f"{cause_type} "
                f"(quality={quality_score:.2f})"
            )

            continue

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        try:

            confidence = float(
                cause.confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        # Never allow model confidence
        # to exceed deterministic quality.
        confidence = min(
            confidence,
            quality_score,
        )

        validated.append(
            {
                "cause_type": cause_type,
                "description": grounded_description,
                "evidence_ids": repaired_ids,
                "confidence": round(
                    confidence,
                    3,
                ),
                "quality_score": round(
                    quality_score,
                    3,
                ),
            }
        )

    return validated


# ============================================================
# 28. DEDUPLICATION
# ============================================================

def _deduplicate_causes(
    causes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    grouped: Dict[
        str,
        Dict[str, Any],
    ] = {}

    for cause in causes:

        cause_type = cause.get(
            "cause_type",
            "other",
        )

        if cause_type not in grouped:

            grouped[cause_type] = {
                "cause_type": cause_type,
                "description": cause.get(
                    "description",
                    "",
                ),
                "evidence_ids": list(
                    cause.get(
                        "evidence_ids",
                        [],
                    )
                ),
                "confidence": float(
                    cause.get(
                        "confidence",
                        0.0,
                    )
                ),
                "quality_score": float(
                    cause.get(
                        "quality_score",
                        0.0,
                    )
                ),
            }

            continue

        existing = grouped[
            cause_type
        ]

        existing_ids = set(
            existing.get(
                "evidence_ids",
                [],
            )
        )

        for evidence_id in (
            cause.get(
                "evidence_ids",
                [],
            )
        ):

            if evidence_id not in existing_ids:

                existing[
                    "evidence_ids"
                ].append(
                    evidence_id
                )

                existing_ids.add(
                    evidence_id
                )

        existing[
            "confidence"
        ] = max(
            existing.get(
                "confidence",
                0.0,
            ),
            float(
                cause.get(
                    "confidence",
                    0.0,
                )
            ),
        )

        existing[
            "quality_score"
        ] = max(
            existing.get(
                "quality_score",
                0.0,
            ),
            float(
                cause.get(
                    "quality_score",
                    0.0,
                )
            ),
        )

        current_description = (
            existing.get(
                "description",
                "",
            )
        )

        new_description = (
            cause.get(
                "description",
                "",
            )
        )

        current_quality = (
            existing.get(
                "quality_score",
                0.0,
            )
        )

        new_quality = float(
            cause.get(
                "quality_score",
                0.0,
            )
        )

        if (
            new_quality > current_quality
            or (
                new_quality == current_quality
                and len(new_description)
                > len(current_description)
            )
        ):

            existing[
                "description"
            ] = new_description

    return list(
        grouped.values()
    )


# ============================================================
# 29. REMOVE INTERNAL FIELDS
# ============================================================

def _remove_internal_fields(
    causes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    cleaned: List[
        Dict[str, Any]
    ] = []

    for cause in causes:

        cleaned.append(
            {
                "cause_type": cause[
                    "cause_type"
                ],
                "description": cause[
                    "description"
                ],
                "evidence_ids": cause[
                    "evidence_ids"
                ],
                "confidence": cause[
                    "confidence"
                ],
            }
        )

    return cleaned


# ============================================================
# 30. CAUSE AGENT PROMPT
# ============================================================

CAUSE_PROMPT = """
You are the Cause Analysis Agent in a financial investigation system.

Your job is to identify factual, evidence-grounded factors associated
with an observed stock movement.

============================================================
1. EVIDENCE GROUNDING
============================================================

Every cause MUST reference one or more evidence IDs.

Use ONLY evidence IDs that exist in the supplied evidence.

Never invent evidence IDs.

Prefer evidence records that directly describe the underlying event,
financial result, analyst action, business development, market condition,
or other factor.

============================================================
2. IDENTIFY A REAL FACTOR
============================================================

A cause must describe an EVENT, FACTOR, DEVELOPMENT, CONDITION, or
BUSINESS CHANGE.

Do NOT use the stock movement itself as a cause.

INVALID:

- the stock rose
- the stock fell
- shares hit an all-time high
- shares reached a record high
- market capitalization increased
- the stock gained 2%
- the stock price climbed

Those describe the outcome rather than an explanatory factor.

============================================================
3. EARNINGS
============================================================

Use earnings for evidence involving:

- revenue
- profit
- EPS
- earnings
- quarterly results
- financial results
- guidance
- financial outlook

Do not use earnings merely because an article mentions the word
"results" without describing an actual financial development.

============================================================
4. CAPITAL ALLOCATION
============================================================

Use capital_allocation for:

- share buybacks
- repurchase programs
- dividends
- capital returns

============================================================
5. ANALYST ACTIVITY
============================================================

Use analyst_activity for:

- analyst upgrades
- analyst downgrades
- analyst ratings
- price targets
- top picks
- analyst coverage

Do not classify analyst evidence as earnings merely because the article
mentions revenue, forecasts, or financial performance.

============================================================
6. BUSINESS GROWTH
============================================================

Use business_growth for:

- demand
- customer growth
- revenue growth
- orders
- backlog
- market share
- AI demand
- cloud demand

============================================================
7. MARKET SENTIMENT
============================================================

Only use market_sentiment when the evidence explicitly discusses:

- investor sentiment
- investor reaction
- investor confidence
- optimism
- pessimism
- bullish/bearish sentiment
- positive or negative investor reaction

Do NOT infer sentiment merely because a stock price increased.

============================================================
8. MARKET CONDITIONS
============================================================

Only use market_conditions for broader conditions such as:

- Nasdaq
- S&P 500
- Dow
- semiconductor sector
- technology sector
- interest rates
- inflation
- macroeconomic conditions
- broader market movements

A company's own stock movement is NOT a market condition.

============================================================
9. BUSINESS EVENTS
============================================================

Use business_event for:

- partnerships
- contracts
- acquisitions
- mergers
- launches
- product announcements
- facility expansion
- strategic agreements
- major business developments

============================================================
10. VALUATION
============================================================

Use valuation for:

- P/E
- valuation multiples
- price-to-earnings
- overvaluation
- undervaluation
- valuation metrics

============================================================
11. CAUSAL LANGUAGE
============================================================

This is extremely important.

Do NOT claim that an event caused the stock movement unless the
supplied evidence explicitly establishes that causal relationship.

Avoid:

- caused
- caused by
- drove
- driven by
- led to
- resulted in
- triggered
- prompted
- boosted
- responsible for
- attributed to

Also avoid unsupported inferential language:

- may have contributed
- might have contributed
- could have contributed
- may have influenced
- might have influenced
- could have influenced
- may explain
- might explain
- could explain
- suggesting
- indicating
- reflecting
- likely reflects
- investor perception

Prefer factual wording:

- reported
- announced
- disclosed
- recorded
- posted
- authorized
- forecast
- raised
- lowered
- upgraded
- downgraded
- entered into
- expanded
- launched

============================================================
12. PREDICTIONS
============================================================

Do not predict future stock movements.

Do not say:

- will rise
- will fall
- expected to increase
- likely to decline

============================================================
13. INVESTMENT ADVICE
============================================================

Do not provide:

- buy recommendations
- sell recommendations
- hold recommendations
- investment advice

============================================================
14. QUALITY OVER QUANTITY
============================================================

Return only strong evidence-grounded factors.

If the evidence does not support a meaningful factor, return fewer causes.

Never manufacture a cause to increase the result count.

============================================================
15. DESCRIPTION STYLE
============================================================

Descriptions must state the FACT.

GOOD:

"Nvidia reported revenue of $96.2 billion in its August Q2 earnings
report, above expectations."

GOOD:

"Nvidia authorized a $150 billion increase to its share repurchase
program."

GOOD:

"Barclays analyst coverage projected substantial hyperscaler revenue."

BAD:

"Nvidia's strong revenue caused the stock to rise."

BAD:

"Nvidia's revenue contributed to positive investor sentiment."

BAD:

"The buyback boosted investor confidence."

Unless the supplied evidence explicitly states those relationships,
do not make those claims.
"""


# ============================================================
# 31. MAIN CAUSE AGENT
# ============================================================

async def cause_analyzer(
    state: Dict[str, Any],
) -> Dict[str, Any]:

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
        "general_investigation",
    )

    movement_mismatch = bool(
        state.get(
            "movement_mismatch",
            False,
        )
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

    errors = list(
        state.get(
            "errors",
            [],
        )
    )

    # ========================================================
    # MOVEMENT MISMATCH
    # ========================================================

    if movement_mismatch:

        print(
            "[Cause Agent] Movement mismatch detected."
        )

        print(
            "[Cause Agent] "
            "Skipping causal analysis because the requested "
            "price movement is not supported by market data."
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "completed",
                "mode": "movement_mismatch",
                "reason": (
                    "requested_movement_not_supported"
                ),
            }
        )

        return {
            "causes": [],
            "trace": trace,
            "errors": errors,
        }

    # ========================================================
    # GENERAL INVESTIGATION
    # ========================================================

    if investigation_intent != "cause_analysis":

        print(
            "[Cause Agent] Investigation intent: "
            f"{investigation_intent}"
        )

        print(
            "[Cause Agent] "
            "Skipping causal analysis because cause analysis "
            "was not requested."
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "skipped",
                "mode": "general_investigation",
                "reason": (
                    "cause_analysis_not_requested"
                ),
            }
        )

        return {
            "causes": [],
            "trace": trace,
            "errors": errors,
        }

    # ========================================================
    # START
    # ========================================================

    print(
        "[Cause Agent] Investigation intent: "
        f"{investigation_intent}"
    )

    print(
        "[Cause Agent] Starting cause analysis"
    )

    # ========================================================
    # NO EVIDENCE
    # ========================================================

    if not evidence:

        print(
            "[Cause Agent] No evidence available."
        )

        errors.append(
            "Cause analysis failed: no evidence available."
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
            "errors": errors,
        }

    # ========================================================
    # EVIDENCE INDEX
    # ========================================================

    evidence_index = (
        _build_evidence_index(
            evidence
        )
    )

    print(
        "[Cause Agent] Evidence index contains "
        f"{len(evidence_index)} records."
    )

    if not evidence_index:

        print(
            "[Cause Agent] "
            "No valid evidence IDs found."
        )

        errors.append(
            "Cause analysis failed: evidence index is empty."
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "failed",
                "reason": "empty_evidence_index",
            }
        )

        return {
            "causes": [],
            "trace": trace,
            "errors": errors,
        }

    # ========================================================
    # BUILD EVIDENCE CONTEXT
    # ========================================================

    evidence_context_parts: List[str] = []

    for (
        evidence_id,
        record,
    ) in evidence_index.items():

        evidence_text = _claim_text(
            record
        )

        if not evidence_text:
            continue

        evidence_context_parts.append(
            f"""
Evidence ID: {evidence_id}

Source type:
{record.get("source_type", "unknown")}

Claim type:
{record.get("claim_type", "unknown")}

Evidence:
{evidence_text}
"""
        )

    evidence_context = "\n".join(
        evidence_context_parts
    )

    # ========================================================
    # LLM PROMPT
    # ========================================================

    prompt = f"""
{CAUSE_PROMPT}

============================================================
INVESTIGATION
============================================================

Company:
{company}

Query:
{query}

============================================================
AVAILABLE EVIDENCE
============================================================

{evidence_context}

============================================================
TASK
============================================================

Identify the strongest factual factors associated with the requested
stock movement.

Do not return the stock movement itself as a cause.

Every cause must reference one or more valid evidence IDs.

If the evidence does not support a meaningful cause, return an empty
cause list.

Do not manufacture explanations.
"""

    # ========================================================
    # LLM CALL
    # ========================================================

    try:

        extraction = await cause_llm.ainvoke(
            prompt
        )

        raw_causes = list(
            extraction.causes
        )

        print(
            "[Cause Agent] LLM generated "
            f"{len(raw_causes)} raw causes"
        )

    except Exception as exc:

        print(
            "[Cause Agent] LLM error: "
            f"{exc}"
        )

        errors.append(
            f"Cause analysis LLM error: {exc}"
        )

        trace.append(
            {
                "agent": "cause_analyzer",
                "status": "failed",
                "reason": "llm_error",
                "error": str(exc),
            }
        )

        return {
            "causes": [],
            "trace": trace,
            "errors": errors,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    validated_causes = (
        _validate_causes(
            causes=raw_causes,
            evidence_index=evidence_index,
        )
    )

    print(
        "[Cause Agent] Validated "
        f"{len(validated_causes)} causes"
    )

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    deduplicated_causes = (
        _deduplicate_causes(
            validated_causes
        )
    )

    print(
        "[Cause Agent] Deduplicated to "
        f"{len(deduplicated_causes)} causes"
    )

    # ========================================================
    # REMOVE INTERNAL QUALITY SCORE
    # ========================================================

    final_causes = (
        _remove_internal_fields(
            deduplicated_causes
        )
    )

    # ========================================================
    # TRACE
    # ========================================================

    trace.append(
        {
            "agent": "cause_analyzer",
            "status": "completed",
            "mode": "cause_analysis",
            "version": "8.6",
            "raw_count": len(
                raw_causes
            ),
            "validated_count": len(
                validated_causes
            ),
            "deduplicated_count": len(
                deduplicated_causes
            ),
        }
    )

    return {
        "causes": final_causes,
        "trace": trace,
        "errors": errors,
    }


# ============================================================
# 32. COMPATIBILITY ALIASES
# ============================================================

cause_agent = cause_analyzer

cause_agent_node = cause_analyzer