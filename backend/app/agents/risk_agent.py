from __future__ import annotations



from typing import Any, Dict, List, Set, Tuple

import re



from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field





# ============================================================

# FININVESTIGATOR

# RISK AGENT v8.5

# ============================================================





# ============================================================

# 1. ALLOWED RISK TYPES

# ============================================================



ALLOWED_RISK_TYPES = {

    "financial",

    "valuation",

    "market_volatility",

    "business",

    "regulatory",

    "operational",

    "competitive",

    "execution",

    "geopolitical",

    "other",

}





# ============================================================

# 2. RISK TYPE ALIASES

# ============================================================



RISK_TYPE_ALIASES = {

    "financial_risk": "financial",

    "finance": "financial",



    "valuation_risk": "valuation",

    "valuation_concern": "valuation",



    "market": "market_volatility",

    "volatility": "market_volatility",

    "market_risk": "market_volatility",



    "business_risk": "business",

    "business_model": "business",



    "regulation": "regulatory",

    "regulatory_risk": "regulatory",



    "operations": "operational",

    "operational_risk": "operational",



    "competition": "competitive",

    "competitive_risk": "competitive",



    "execution_risk": "execution",



    "geopolitical_risk": "geopolitical",

}





# ============================================================

# 3. RISK SIGNALS

# ============================================================



FINANCIAL_RISK_SIGNALS = {

    "debt",

    "net debt",

    "leverage",

    "liquidity",

    "cash flow",

    "free cash flow",

    "cash burn",

    "loss",

    "losses",

    "declining revenue",

    "revenue decline",

    "profit decline",

    "margin pressure",

    "margin decline",

    "operating margin",

    "gross margin",

    "financial pressure",

    "financial weakness",

    "credit",

    "borrowing",

    "interest expense",

    "interest burden",

    "funding",

    "capital requirements",

}





VALUATION_RISK_SIGNALS = {

    "valuation",

    "p/e",

    "p/e ratio",

    "pe ratio",

    "forward p/e",

    "trailing p/e",

    "price-to-earnings",

    "price to earnings",

    "valuation multiple",

    "multiple",

    "premium valuation",

    "high valuation",

    "elevated valuation",

    "overvalued",

    "overvaluation",

    "expensive valuation",

    "rich valuation",

}





MARKET_VOLATILITY_SIGNALS = {

    "volatility",

    "volatile",

    "market volatility",

    "price volatility",

    "trading volatility",

    "sharp swings",

    "large swings",

    "price swings",

    "market selloff",

    "market sell-off",

    "market correction",

    "market turbulence",

    "uncertainty in markets",

}





BUSINESS_RISK_SIGNALS = {

    "demand weakness",

    "weak demand",

    "demand slowdown",

    "demand uncertainty",

    "customer concentration",

    "customer loss",

    "customer losses",

    "revenue concentration",

    "supply constraints",

    "supply constraint",

    "supply disruption",

    "supply chain",

    "product dependence",

    "dependency",

    "dependence",

    "business slowdown",

    "business uncertainty",

    "sales slowdown",

    "declining demand",

}





REGULATORY_RISK_SIGNALS = {

    "regulation",

    "regulatory",

    "regulator",

    "regulators",

    "regulatory scrutiny",

    "regulatory investigation",

    "investigation",

    "antitrust",

    "antitrust scrutiny",

    "compliance",

    "compliance requirements",

    "legal action",

    "lawsuit",

    "litigation",

    "government restrictions",

    "government restriction",

    "export controls",

    "export restriction",

    "sanctions",

    "license restrictions",

}





OPERATIONAL_RISK_SIGNALS = {

    "operational",

    "operations",

    "production disruption",

    "manufacturing disruption",

    "manufacturing issue",

    "factory shutdown",

    "facility disruption",

    "outage",

    "service disruption",

    "delivery delays",

    "delivery delay",

    "execution issue",

    "operational issue",

    "capacity constraint",

    "capacity constraints",

    "production constraint",

}





COMPETITIVE_RISK_SIGNALS = {

    "competition",

    "competitive pressure",

    "competitive pressures",

    "competitor",

    "competitors",

    "market share loss",

    "loss of market share",

    "pricing pressure",

    "price competition",

    "new entrant",

    "new entrants",

    "competitive threat",

    "competitive threats",

}





EXECUTION_RISK_SIGNALS = {

    "execution risk",

    "execution challenge",

    "execution challenges",

    "implementation risk",

    "implementation challenges",

    "project delay",

    "project delays",

    "delayed rollout",

    "rollout delay",

    "delivery risk",

    "failure to execute",

    "execution uncertainty",

}





GEOPOLITICAL_RISK_SIGNALS = {

    "geopolitical",

    "geopolitical risk",

    "geopolitical tensions",

    "trade tensions",

    "trade restrictions",

    "trade war",

    "war",

    "conflict",

    "military conflict",

    "political instability",

    "tariffs",

    "tariff",

    "sanctions",

}





# ============================================================

# 4. OUTCOME / OBSERVATION LANGUAGE

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



    "market capitalization increased",

    "market capitalization rose",

    "market cap increased",

    "market cap rose",

}





# ============================================================

# 5. UNSAFE INFERENCE LANGUAGE

# ============================================================



INFERENTIAL_PHRASES = {

    "indicating",

    "indicates",

    "suggesting",

    "suggests",

    "reflecting",

    "reflects",

    "signaling",

    "signals",

    "implying",

    "implies",

    "demonstrating",

    "demonstrates",

    "showing that",

    "shows that",

    # Modal + inference combinations are unsafe because they turn
    # factual evidence into an unsupported interpretation.
    "may indicate",
    "might indicate",
    "could indicate",
    "may suggest",
    "might suggest",
    "could suggest",
    "may imply",
    "might imply",
    "could imply",
    "may reflect",
    "might reflect",
    "could reflect",
    "may signal",
    "might signal",
    "could signal",
    "may demonstrate",
    "might demonstrate",
    "could demonstrate",
    "may show that",
    "might show that",
    "could show that",
    "likely indicates",
    "likely suggests",
    "possibly indicates",
    "possibly suggests",

    "positive expectations",

    "negative expectations",

    "positive outlook",

    "negative outlook",



    "investor confidence",

    "investor perception",

    "market perception",

    "positive sentiment",

    "negative sentiment",

    "favorable perception",

    "favourable perception",

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



    "could lead to",

    "may lead to",

    "might lead to",

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

# 8. PYDANTIC MODELS

# ============================================================



class RiskRecord(BaseModel):

    risk_type: str = Field(

        description=(

            "One of the allowed risk categories."

        )

    )



    description: str = Field(

        description=(

            "A factual description of an actual risk factor "

            "supported by the supplied evidence."

        )

    )



    evidence_ids: List[str] = Field(

        default_factory=list,

        description=(

            "Evidence IDs supporting this risk. "

            "Use only IDs present in the supplied evidence."

        )

    )



    confidence: float = Field(

        ge=0.0,

        le=1.0,

    )





class RiskExtraction(BaseModel):

    risks: List[RiskRecord] = Field(

        default_factory=list

    )





# ============================================================

# 9. LLM

# ============================================================



llm = ChatOpenAI(

    model="gpt-4o-mini",

    temperature=0,

)



risk_llm = llm.with_structured_output(

    RiskExtraction

)





# ============================================================

# 10. TEXT HELPERS

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





# ============================================================

# 11. LANGUAGE VALIDATION

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

        INFERENTIAL_PHRASES,

    )





def _contains_investment_advice(

    description: str,

) -> str | None:



    return _find_phrase(

        description,

        INVESTMENT_ADVICE_PHRASES,

    )





# ============================================================

# 12. EVIDENCE ID

# ============================================================



def _get_evidence_id(

    record: Dict[str, Any],

) -> str:



    for key in (

        "evidence_id",

        "id",

        "evidenceId",

    ):



        value = record.get(

            key

        )



        if value:

            return str(

                value

            ).strip()



    return ""





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

# 14. EVIDENCE TEXT

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

        "event",

        "observation",

        "risk",

        "risk_factor",

        "risk_description",

    ]



    parts: List[str] = []



    for field in fields:



        value = record.get(

            field

        )



        if value is None:

            continue



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

    risk_text: str,

    evidence_text: str,

) -> float:



    risk_tokens = _tokenize(

        risk_text

    )



    evidence_tokens = _tokenize(

        evidence_text

    )



    if (

        not risk_tokens

        or not evidence_tokens

    ):

        return 0.0



    intersection = (

        risk_tokens.intersection(

            evidence_tokens

        )

    )



    token_score = (

        len(intersection)

        / max(

            len(risk_tokens),

            1,

        )

    )



    risk_phrases = (

        _important_phrases(

            risk_text

        )

    )



    evidence_phrases = (

        _important_phrases(

            evidence_text

        )

    )



    phrase_score = 0.0



    if risk_phrases:



        matches = (

            risk_phrases.intersection(

                evidence_phrases

            )

        )



        phrase_score = (

            len(matches)

            / len(risk_phrases)

        )



    return (

        0.75 * token_score

        + 0.25 * phrase_score

    )





# ============================================================

# 17. FIND BEST EVIDENCE

# ============================================================



def _find_best_evidence_matches(

    risk: RiskRecord,

    evidence_index: Dict[

        str,

        Dict[str, Any],

    ],

    max_matches: int = 3,

) -> List[str]:



    risk_text = " ".join(

        [

            risk.risk_type,

            risk.description,

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

                risk_text,

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

    risk: RiskRecord,

    evidence_index: Dict[

        str,

        Dict[str, Any],

    ],

) -> List[str]:



    valid_ids: List[str] = []



    for evidence_id in (

        risk.evidence_ids

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

        risk=risk,

        evidence_index=evidence_index,

        max_matches=3,

    )





# ============================================================

# 19. OUTCOME DETECTION

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

# 20. OUTCOME-ONLY RISK

# ============================================================



def _is_outcome_only_risk(

    description: str,

    evidence_text: str,

) -> bool:



    description_text = (

        _normalize_text(

            description

        )

    )



    evidence_text = (

        _normalize_text(

            evidence_text

        )

    )



    if not _contains_outcome_language(

        description_text

    ):

        return False



    actual_risk_signals = (

        FINANCIAL_RISK_SIGNALS

        | VALUATION_RISK_SIGNALS

        | MARKET_VOLATILITY_SIGNALS

        | BUSINESS_RISK_SIGNALS

        | REGULATORY_RISK_SIGNALS

        | OPERATIONAL_RISK_SIGNALS

        | COMPETITIVE_RISK_SIGNALS

        | EXECUTION_RISK_SIGNALS

        | GEOPOLITICAL_RISK_SIGNALS

    )



    description_signal_count = (

        _signal_count(

            description_text,

            actual_risk_signals,

        )

    )



    evidence_signal_count = (

        _signal_count(

            evidence_text,

            actual_risk_signals,

        )

    )



    if description_signal_count >= 2:

        return False



    if (

        description_signal_count >= 1

        and evidence_signal_count >= 2

    ):

        return False



    return True





# ============================================================

# 21. CLAIM TYPE PRIORITY

# ============================================================



CLAIM_TYPE_PRIORITY = {

    "risk": "other",



    "valuation_metric": "valuation",



    "financial_metric": "financial",



    "analyst_action": None,

    "guidance": None,

    "market_observation": None,



    "corporate_action": None,

    "business_event": "business",



    "executive_statement": None,

    "reported_claim": None,

}





# ============================================================

# 22. RISK TYPE INFERENCE

# ============================================================



def _infer_better_risk_type(

    risk_type: str,

    description: str,

    evidence_ids: List[str],

    evidence_index: Dict[

        str,

        Dict[str, Any],

    ],

) -> str:



    description_text = (

        _normalize_text(

            description

        )

    )



    # --------------------------------------------------------

    # Explicit evidence claim types first.

    # --------------------------------------------------------



    claim_votes: Dict[

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

                "",

            )

        )



        mapped_type = (

            CLAIM_TYPE_PRIORITY.get(

                claim_type

            )

        )



        if mapped_type:



            claim_votes[

                mapped_type

            ] = (

                claim_votes.get(

                    mapped_type,

                    0,

                )

                + 1

            )



    if claim_votes:



        strongest_type = max(

            claim_votes,

            key=claim_votes.get,

        )



        if claim_votes[

            strongest_type

        ] >= 1:



            return strongest_type



    # --------------------------------------------------------

    # Evidence text.

    # --------------------------------------------------------



    evidence_text = " ".join(

        _evidence_text_for_id(

            evidence_id,

            evidence_index,

        )

        for evidence_id in evidence_ids

    )



    text = _normalize_text(

        f"{description_text} "

        f"{evidence_text}"

    )



    # --------------------------------------------------------

    # Deterministic risk priority.

    # --------------------------------------------------------



    if _contains_any_signal(

        text,

        REGULATORY_RISK_SIGNALS,

    ):

        return "regulatory"



    if _contains_any_signal(

        text,

        GEOPOLITICAL_RISK_SIGNALS,

    ):

        return "geopolitical"



    if _contains_any_signal(

        text,

        COMPETITIVE_RISK_SIGNALS,

    ):

        return "competitive"



    if _contains_any_signal(

        text,

        OPERATIONAL_RISK_SIGNALS,

    ):

        return "operational"



    if _contains_any_signal(

        text,

        EXECUTION_RISK_SIGNALS,

    ):

        return "execution"



    if _contains_any_signal(

        text,

        FINANCIAL_RISK_SIGNALS,

    ):

        return "financial"



    if _contains_any_signal(

        text,

        VALUATION_RISK_SIGNALS,

    ):

        return "valuation"



    if _contains_any_signal(

        text,

        MARKET_VOLATILITY_SIGNALS,

    ):

        return "market_volatility"



    if _contains_any_signal(

        text,

        BUSINESS_RISK_SIGNALS,

    ):

        return "business"



    return risk_type





# ============================================================

# 23. RISK TYPE QUALITY

# ============================================================



def _validate_risk_type_quality(

    risk_type: str,

    description: str,

    evidence_text: str,

) -> bool:



    text = _normalize_text(

        f"{description} {evidence_text}"

    )



    if risk_type == "financial":



        return _contains_any_signal(

            text,

            FINANCIAL_RISK_SIGNALS,

        )



    if risk_type == "valuation":



        return _contains_any_signal(

            text,

            VALUATION_RISK_SIGNALS,

        )



    if risk_type == "market_volatility":



        return _contains_any_signal(

            text,

            MARKET_VOLATILITY_SIGNALS,

        )



    if risk_type == "business":



        return _contains_any_signal(

            text,

            BUSINESS_RISK_SIGNALS,

        )



    if risk_type == "regulatory":



        return _contains_any_signal(

            text,

            REGULATORY_RISK_SIGNALS,

        )



    if risk_type == "operational":



        return _contains_any_signal(

            text,

            OPERATIONAL_RISK_SIGNALS,

        )



    if risk_type == "competitive":



        return _contains_any_signal(

            text,

            COMPETITIVE_RISK_SIGNALS,

        )



    if risk_type == "execution":



        return _contains_any_signal(

            text,

            EXECUTION_RISK_SIGNALS,

        )



    if risk_type == "geopolitical":



        return _contains_any_signal(

            text,

            GEOPOLITICAL_RISK_SIGNALS,

        )



    return True





# ============================================================

# 24. RISK QUALITY SCORE

# ============================================================



def _calculate_risk_quality(

    risk_type: str,

    description: str,

    evidence_ids: List[str],

    evidence_index: Dict[

        str,

        Dict[str, Any],

    ],

) -> float:



    score = 0.0



    # Evidence grounding.

    if len(evidence_ids) >= 1:

        score += 0.25



    if len(evidence_ids) >= 2:

        score += 0.10



    if len(evidence_ids) >= 3:

        score += 0.05



    evidence_text = " ".join(

        _evidence_text_for_id(

            evidence_id,

            evidence_index,

        )

        for evidence_id in evidence_ids

    )



    combined_text = _normalize_text(

        f"{description} "

        f"{evidence_text}"

    )



    risk_signals = (

        FINANCIAL_RISK_SIGNALS

        | VALUATION_RISK_SIGNALS

        | MARKET_VOLATILITY_SIGNALS

        | BUSINESS_RISK_SIGNALS

        | REGULATORY_RISK_SIGNALS

        | OPERATIONAL_RISK_SIGNALS

        | COMPETITIVE_RISK_SIGNALS

        | EXECUTION_RISK_SIGNALS

        | GEOPOLITICAL_RISK_SIGNALS

    )



    signal_count = _signal_count(

        combined_text,

        risk_signals,

    )



    score += min(

        0.35,

        signal_count * 0.05,

    )



    if _validate_risk_type_quality(

        risk_type=risk_type,

        description=description,

        evidence_text=evidence_text,

    ):

        score += 0.20



    if _is_outcome_only_risk(

        description=description,

        evidence_text=evidence_text,

    ):

        score -= 0.40



    return max(

        0.0,

        min(

            1.0,

            score,

        )

    )





# ============================================================

# 25. GROUND RISK DESCRIPTION

# ============================================================



def _ground_risk_description(

    description: str,

    risk: RiskRecord,

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

    # Predictions are never allowed.

    # --------------------------------------------------------



    predictive_phrase = (

        _contains_predictive_language(

            description

        )

    )



    if predictive_phrase:



        print(

            "[Risk Validation] "

            "Predictive language detected: "

            f"{predictive_phrase}"

        )



        return None



    # --------------------------------------------------------

    # Investment advice is never allowed.

    # --------------------------------------------------------



    advice_phrase = (

        _contains_investment_advice(

            description

        )

    )



    if advice_phrase:



        print(

            "[Risk Validation] "

            "Investment advice detected: "

            f"{advice_phrase}"

        )



        return None



    # --------------------------------------------------------

    # Evidence text.

    # --------------------------------------------------------



    evidence_parts: List[str] = []



    for evidence_id in evidence_ids:



        text = (

            _evidence_text_for_id(

                evidence_id,

                evidence_index,

            )

        )



        if text:

            evidence_parts.append(

                text

            )



    evidence_text = " ".join(

        evidence_parts

    )



    # --------------------------------------------------------

    # Reject stock movement as risk.

    # --------------------------------------------------------



    if _is_outcome_only_risk(

        description=description,

        evidence_text=evidence_text,

    ):



        print(

            "[Risk Validation] "

            "Outcome-only observation rejected."

        )



        return None



    # --------------------------------------------------------

    # Unsupported inference.

    # --------------------------------------------------------



    inferential_phrase = (

        _contains_inferential_language(

            description

        )

    )



    if inferential_phrase:



        print(

            "[Risk Validation] "

            "Unsupported inferential language: "

            f"{inferential_phrase}"

        )



        return None



    # --------------------------------------------------------

    # Return only factual description.

    # --------------------------------------------------------



    return description





# ============================================================

# 26. VALIDATE RISKS

# ============================================================



def _validate_risks(

    risks: List[RiskRecord],

    evidence_index: Dict[

        str,

        Dict[str, Any],

    ],

) -> List[Dict[str, Any]]:



    validated: List[

        Dict[str, Any]

    ] = []



    for risk in risks:



        risk_type = _normalize_text(

            risk.risk_type

        )



        if risk_type in RISK_TYPE_ALIASES:



            risk_type = (

                RISK_TYPE_ALIASES[

                    risk_type

                ]

            )



        elif (

            risk_type

            not in ALLOWED_RISK_TYPES

        ):



            risk_type = "other"



        # ----------------------------------------------------

        # Evidence IDs

        # ----------------------------------------------------



        repaired_ids = (

            _repair_evidence_ids(

                risk=risk,

                evidence_index=evidence_index,

            )

        )



        if not repaired_ids:



            print(

                "[Risk Validation] "

                "Rejected risk with no grounded evidence: "

                f"{risk_type}"

            )



            continue



        # ----------------------------------------------------

        # Evidence text

        # ----------------------------------------------------



        evidence_parts: List[str] = []



        for evidence_id in repaired_ids:



            text = (

                _evidence_text_for_id(

                    evidence_id,

                    evidence_index,

                )

            )



            if text:

                evidence_parts.append(

                    text

                )



        evidence_text = " ".join(

            evidence_parts

        )



        # ----------------------------------------------------

        # Correct risk type

        # ----------------------------------------------------



        corrected_type = (

            _infer_better_risk_type(

                risk_type=risk_type,

                description=risk.description,

                evidence_ids=repaired_ids,

                evidence_index=evidence_index,

            )

        )



        if corrected_type != risk_type:



            print(

                "[Risk Validation] "

                f"Risk type corrected: "

                f"{risk_type} -> {corrected_type}"

            )



            risk_type = corrected_type



        # ----------------------------------------------------

        # Ground description

        # ----------------------------------------------------



        grounded_description = (

            _ground_risk_description(

                description=risk.description,

                risk=risk,

                evidence_ids=repaired_ids,

                evidence_index=evidence_index,

            )

        )



        if not grounded_description:



            print(

                "[Risk Validation] "

                f"Rejected unsafe/outcome-only risk: "

                f"{risk_type}"

            )



            continue



        # ----------------------------------------------------

        # Validate type

        # ----------------------------------------------------



        if not _validate_risk_type_quality(

            risk_type=risk_type,

            description=grounded_description,

            evidence_text=evidence_text,

        ):



            print(

                "[Risk Validation] "

                f"Rejected unsupported risk type: "

                f"{risk_type}"

            )



            continue



        # ----------------------------------------------------

        # Quality

        # ----------------------------------------------------



        quality_score = (

            _calculate_risk_quality(

                risk_type=risk_type,

                description=grounded_description,

                evidence_ids=repaired_ids,

                evidence_index=evidence_index,

            )

        )



        if quality_score < 0.30:



            print(

                "[Risk Validation] "

                f"Rejected low-quality risk: "

                f"{risk_type} "

                f"(quality={quality_score:.2f})"

            )



            continue



        # ----------------------------------------------------

        # Confidence

        # ----------------------------------------------------



        try:



            confidence = float(

                risk.confidence

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



        confidence = min(

            confidence,

            quality_score,

        )



        validated.append(

            {

                "risk_type": risk_type,

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

# 27. DEDUPLICATE RISKS

# ============================================================



def _deduplicate_risks(

    risks: List[Dict[str, Any]],

) -> List[Dict[str, Any]]:



    grouped: Dict[

        str,

        Dict[str, Any],

    ] = {}



    for risk in risks:



        risk_type = risk.get(

            "risk_type",

            "other",

        )



        if risk_type not in grouped:



            grouped[risk_type] = {

                "risk_type": risk_type,

                "description": risk.get(

                    "description",

                    "",

                ),

                "evidence_ids": list(

                    risk.get(

                        "evidence_ids",

                        [],

                    )

                ),

                "confidence": float(

                    risk.get(

                        "confidence",

                        0.0,

                    )

                ),

                "quality_score": float(

                    risk.get(

                        "quality_score",

                        0.0,

                    )

                ),

            }



            continue



        existing = grouped[

            risk_type

        ]



        existing_ids = set(

            existing.get(

                "evidence_ids",

                [],

            )

        )



        for evidence_id in (

            risk.get(

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

                risk.get(

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

                risk.get(

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

            risk.get(

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

            risk.get(

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

# 28. REMOVE INTERNAL FIELDS

# ============================================================



def _remove_internal_fields(

    risks: List[Dict[str, Any]],

) -> List[Dict[str, Any]]:



    cleaned: List[

        Dict[str, Any]

    ] = []



    for risk in risks:



        cleaned.append(

            {

                "risk_type": risk[

                    "risk_type"

                ],

                "description": risk[

                    "description"

                ],

                "evidence_ids": risk[

                    "evidence_ids"

                ],

                "confidence": risk[

                    "confidence"

                ],

            }

        )



    return cleaned





# ============================================================

# 29. RISK AGENT PROMPT

# ============================================================



RISK_PROMPT = """

You are the Risk Analysis Agent in a financial investigation system.



Your job is to identify ACTUAL RISK FACTORS supported by the supplied

evidence.



============================================================

1. EVIDENCE GROUNDING

============================================================



Every risk MUST reference one or more evidence IDs.



Use ONLY evidence IDs that exist in the supplied evidence.



Never invent evidence IDs.



============================================================

2. WHAT IS A RISK?

============================================================



A risk must describe an actual uncertainty, weakness, exposure,

constraint, threat, or adverse condition.



Examples:



- high valuation multiple

- high debt

- declining margins

- demand weakness

- supply constraints

- regulatory investigation

- export restrictions

- strong competitive pressure

- operational disruption

- geopolitical tensions

- market volatility



============================================================

3. DO NOT TURN AN OBSERVATION INTO A RISK

============================================================



The following are NOT automatically risks:



- stock rose

- stock fell

- stock hit an all-time high

- stock reached a record high

- market capitalization increased

- shares gained 2%



A stock-price observation alone is not a valuation risk.



For example:



BAD:

"Nvidia hit an all-time high, indicating a significant increase

in market valuation."



This is not sufficient evidence of a valuation risk.



GOOD:

"Nvidia trades at a high forward P/E multiple relative to historical

or sector measures."



Only make this statement if the evidence actually contains the

valuation information.



============================================================

4. VALUATION

============================================================



Use valuation only when the evidence contains actual valuation

information such as:



- P/E

- forward P/E

- trailing P/E

- valuation multiple

- premium valuation

- elevated valuation

- overvaluation



Do not infer valuation risk merely from a stock reaching a record high.



============================================================

5. FINANCIAL

============================================================



Use financial when evidence shows:



- debt

- leverage

- liquidity pressure

- cash-flow weakness

- margin pressure

- revenue decline

- profit decline

- funding requirements



Do not call positive revenue guidance a financial risk by itself.



============================================================

6. MARKET VOLATILITY

============================================================



Use market_volatility only when evidence explicitly refers to:



- volatility

- price swings

- market turbulence

- market selloffs

- sharp market movements



A normal one-day stock increase is not automatically market volatility.



============================================================

7. BUSINESS

============================================================



Use business when evidence shows:



- weak demand

- customer concentration

- supply constraints

- business slowdown

- product dependence

- revenue concentration

- demand uncertainty



============================================================

8. REGULATORY

============================================================



Use regulatory for:



- regulation

- investigations

- antitrust

- litigation

- compliance requirements

- export controls

- government restrictions

- sanctions



============================================================

9. OPERATIONAL

============================================================



Use operational for:



- production disruptions

- manufacturing problems

- outages

- facility disruptions

- capacity constraints

- delivery delays

- operational problems



============================================================

10. COMPETITIVE

============================================================



Use competitive for:



- competitors

- competitive pressure

- market share loss

- pricing pressure

- new entrants

- competitive threats



============================================================

11. EXECUTION

============================================================



Use execution for:



- implementation difficulties

- project delays

- rollout delays

- execution uncertainty

- failure to execute



============================================================

12. GEOPOLITICAL

============================================================



Use geopolitical for:



- geopolitical tensions

- trade restrictions

- tariffs

- war

- conflicts

- sanctions

- political instability



============================================================

13. NO UNSUPPORTED INFERENCE

============================================================



Do NOT use:



- indicating

- indicates

- suggesting

- suggests

- reflecting

- reflects

- signaling

- signals

- implying

- implies

- investor confidence

- investor perception

- positive expectations

- negative expectations



unless the evidence explicitly establishes the relationship.



Prefer factual descriptions.



GOOD:

"The company faces export restrictions affecting sales to China."



BAD:

"Export restrictions may hurt future revenue."



============================================================

14. NO PREDICTIONS

============================================================



Do not predict future stock or business performance.



Do not say:



- will rise

- will fall

- may rise

- may fall

- could increase

- expected to decline

- likely to weaken



============================================================

15. NO INVESTMENT ADVICE

============================================================



Do not provide:



- buy recommendations

- sell recommendations

- hold recommendations

- investment advice



============================================================

16. QUALITY OVER QUANTITY

============================================================



Return only genuine risks.



If the evidence does not contain a meaningful risk, return fewer

risks or an empty list.



Never manufacture a risk.



============================================================

17. IMPORTANT DISTINCTION

============================================================



The investigation may contain positive information.



Positive information is NOT automatically a risk.



For example:



"Revenue is expected to reach $110 billion."



This is a financial fact, not necessarily a financial risk.



Do not convert positive evidence into a risk unless the evidence

contains an actual adverse condition or uncertainty.

"""





# ============================================================

# 30. MAIN RISK AGENT

# ============================================================



async def risk_analyzer(

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



    evidence = state.get(

        "evidence",

        [],

    )



    causes = state.get(

        "causes",

        [],

    )



    movement_mismatch = bool(

        state.get(

            "movement_mismatch",

            False,

        )

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

    # START

    # ========================================================



    print(

        "[Risk Agent] Starting risk analysis"

    )



    # ========================================================

    # NO EVIDENCE

    # ========================================================



    if not evidence:



        print(

            "[Risk Agent] No evidence available."

        )



        errors.append(

            "Risk analysis failed: no evidence available."

        )



        trace.append(

            {

                "agent": "risk_analyzer",

                "status": "failed",

                "reason": "no_evidence",

            }

        )



        return {

            "risks": [],

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

        "[Risk Agent] Evidence index contains "

        f"{len(evidence_index)} records."

    )



    if not evidence_index:



        errors.append(

            "Risk analysis failed: evidence index is empty."

        )



        trace.append(

            {

                "agent": "risk_analyzer",

                "status": "failed",

                "reason": "empty_evidence_index",

            }

        )



        return {

            "risks": [],

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

    # CAUSE CONTEXT

    # ========================================================



    cause_context = ""



    if causes:



        cause_parts: List[str] = []



        for cause in causes:



            if not isinstance(

                cause,

                dict,

            ):

                continue



            cause_parts.append(

                f"""

Cause type:

{cause.get("cause_type", "unknown")}



Cause:

{cause.get("description", "")}



Evidence IDs:

{cause.get("evidence_ids", [])}

"""

            )



        cause_context = "\n".join(

            cause_parts

        )



    # ========================================================

    # PROMPT

    # ========================================================



    prompt = f"""

{RISK_PROMPT}



============================================================

INVESTIGATION

============================================================



Company:

{company}



Query:

{query}



Movement mismatch:

{movement_mismatch}



============================================================

CAUSES ALREADY IDENTIFIED

============================================================



{cause_context}



============================================================

AVAILABLE EVIDENCE

============================================================



{evidence_context}



============================================================

TASK

============================================================



Identify only genuine risk factors supported by the evidence.



Every risk must reference one or more valid evidence IDs.



Do not turn positive financial information into a risk.



Do not turn stock-price observations into valuation risk.



Do not predict future outcomes.



Do not provide investment advice.



If there are no meaningful evidence-grounded risks, return an empty

risk list.

"""



    # ========================================================

    # LLM

    # ========================================================



    try:



        extraction = await risk_llm.ainvoke(

            prompt

        )



        raw_risks = list(

            extraction.risks

        )



        print(

            "[Risk Agent] LLM generated "

            f"{len(raw_risks)} raw risks"

        )



    except Exception as exc:



        print(

            "[Risk Agent] LLM error: "

            f"{exc}"

        )



        errors.append(

            f"Risk analysis LLM error: {exc}"

        )



        trace.append(

            {

                "agent": "risk_analyzer",

                "status": "failed",

                "reason": "llm_error",

                "error": str(exc),

            }

        )



        return {

            "risks": [],

            "trace": trace,

            "errors": errors,

        }



    # ========================================================

    # VALIDATION

    # ========================================================



    validated_risks = (

        _validate_risks(

            risks=raw_risks,

            evidence_index=evidence_index,

        )

    )



    print(

        "[Risk Agent] Validated "

        f"{len(validated_risks)} risks"

    )



    # ========================================================

    # DEDUPLICATION

    # ========================================================



    deduplicated_risks = (

        _deduplicate_risks(

            validated_risks

        )

    )



    print(

        "[Risk Agent] Deduplicated to "

        f"{len(deduplicated_risks)} risks"

    )



    # ========================================================

    # CLEAN INTERNAL FIELDS

    # ========================================================



    final_risks = (

        _remove_internal_fields(

            deduplicated_risks

        )

    )



    # ========================================================

    # TRACE

    # ========================================================



    trace.append(

        {

            "agent": "risk_analyzer",

            "status": "completed",

            "mode": "risk_analysis",

            "version": "8.5",

            "raw_count": len(

                raw_risks

            ),

            "validated_count": len(

                validated_risks

            ),

            "deduplicated_count": len(

                deduplicated_risks

            ),

        }

    )



    return {

        "risks": final_risks,

        "trace": trace,

        "errors": errors,

    }





# ============================================================

# 31. COMPATIBILITY ALIASES

# ============================================================



risk_agent = risk_analyzer



risk_agent_node = risk_analyzer