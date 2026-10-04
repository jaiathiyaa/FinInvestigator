from typing import Any, Dict, List

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from app.graph.state import InvestigationState


# ============================================================
# Claim Types
# ============================================================

CLAIM_TYPES = {
    "market_observation",
    "financial_metric",
    "valuation_metric",
    "analyst_action",
    "business_event",
    "corporate_action",
    "executive_statement",
    "reported_claim",
    "risk",
    "guidance",
    "none",
}


# ============================================================
# Pydantic Models
# ============================================================

class ExtractedClaim(BaseModel):

    claim: str = Field(
        description=(
            "A concise factual claim directly supported "
            "by the supplied source text."
        )
    )

    claim_type: str = Field(
        description=(
            "Classification of the claim."
        )
    )

    date: str | None = Field(
        default=None,
        description=(
            "Date explicitly associated with the claim, "
            "if available."
        )
    )


class EvidenceExtraction(BaseModel):

    claims: List[ExtractedClaim]


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

evidence_llm = llm.with_structured_output(
    EvidenceExtraction
)


# ============================================================
# Text Cleaning
# ============================================================

def _clean_text(
    text: Any,
) -> str:

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\x00",
        " ",
    )

    text = " ".join(
        text.split()
    )

    return text.strip()


# ============================================================
# Chunking
# ============================================================

def _split_into_chunks(
    text: str,
    max_chars: int = 12000,
) -> List[str]:

    text = _clean_text(
        text
    )

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + max_chars,
            len(text),
        )

        chunk = text[
            start:end
        ]

        if chunk.strip():
            chunks.append(
                chunk.strip()
            )

        start = end

    return chunks


# ============================================================
# LLM Claim Extraction
# ============================================================

async def _extract_claims_from_chunk(
    text: str,
) -> List[ExtractedClaim]:

    text = _clean_text(
        text
    )

    if not text:
        return []

    prompt = f"""
You are an evidence extraction system for a financial investigation.

Extract ONLY factual claims that are explicitly supported by the
supplied source text.

Do not use outside knowledge.

Do not infer causes.

Do not predict outcomes.

Do not rewrite opinions as facts.

Do not convert speculation into facts.

Do not invent numbers, dates, companies, people, events, or metrics.

A claim should be useful as auditable evidence.

Allowed claim types:

- market_observation
- financial_metric
- valuation_metric
- analyst_action
- business_event
- corporate_action
- executive_statement
- reported_claim
- risk
- guidance
- none

Examples:

GOOD:
"Nvidia reported revenue of $96.2 billion."

BAD:
"Nvidia's revenue shows that the company is performing strongly."

GOOD:
"Goldman Sachs maintained a Buy rating."

BAD:
"Goldman Sachs believes the stock will definitely rise."

GOOD:
"Nvidia authorized a $150 billion share repurchase program."

BAD:
"The buyback will increase shareholder returns."

For analyst opinions, preserve the fact that it is an analyst
opinion or action.

For forecasts or guidance, classify them as guidance and preserve
the uncertainty.

SOURCE TEXT:

{text}
"""

    try:

        result = await evidence_llm.ainvoke(
            prompt
        )

        return result.claims

    except Exception as exc:

        print(
            f"[Evidence Agent] LLM extraction error: {exc}"
        )

        return []


# ============================================================
# Claim Normalization
# ============================================================

def _normalize_claim(
    claim: ExtractedClaim,
) -> Dict[str, Any]:

    claim_text = _clean_text(
        claim.claim
    )

    claim_type = _clean_text(
        claim.claim_type
    ).lower()

    if claim_type not in CLAIM_TYPES:
        claim_type = "reported_claim"

    date = _clean_text(
        claim.date
    )

    return {
        "claim": claim_text,
        "claim_type": claim_type,
        "date": date or None,
    }


# ============================================================
# Claim Validation
# ============================================================

def _validate_claim(
    claim: Dict[str, Any],
) -> bool:

    text = _clean_text(
        claim.get("claim")
    )

    if not text:
        return False

    claim_type = claim.get(
        "claim_type"
    )

    if claim_type not in CLAIM_TYPES:
        return False

    if claim_type == "none":
        return False

    return True


# ============================================================
# Claim Key
# ============================================================

def _claim_key(
    claim: Dict[str, Any],
) -> str:

    text = _clean_text(
        claim.get("claim")
    ).lower()

    claim_type = (
        claim.get(
            "claim_type",
            "",
        )
        .lower()
        .strip()
    )

    return (
        f"{claim_type}|{text}"
    )


# ============================================================
# Deduplicate Claims
# ============================================================

def _deduplicate_claims(
    claims: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    seen = set()

    result = []

    for claim in claims:

        key = _claim_key(
            claim
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            claim
        )

    return result


# ============================================================
# Build News Evidence
# ============================================================

async def _build_news_evidence(
    news_data: Dict[str, Any],
    start_index: int,
) -> List[Dict[str, Any]]:

    evidence = []

    articles = news_data.get(
        "articles",
        [],
    )

    if not isinstance(
        articles,
        list,
    ):
        return evidence

    print(
        f"[Evidence Agent] Processing "
        f"{len(articles)} news articles"
    )

    next_index = start_index

    for article_index, article in enumerate(
        articles,
        start=1,
    ):

        if not isinstance(
            article,
            dict,
        ):
            continue

        title = _clean_text(
            article.get("title")
        )

        content = _clean_text(
            article.get("content")
        )

        url = article.get(
            "url"
        )

        source = article.get(
            "source"
        )

        date = article.get(
            "date"
        )

        if not content:
            continue

        chunks = _split_into_chunks(
            content
        )

        print(
            f"[Evidence Agent] Article "
            f"{article_index}: "
            f"{len(chunks)} LLM chunks"
        )

        article_claims = []

        for chunk in chunks:

            claims = await _extract_claims_from_chunk(
                chunk
            )

            for extracted in claims:

                normalized = _normalize_claim(
                    extracted
                )

                if not _validate_claim(
                    normalized
                ):
                    continue

                article_claims.append(
                    normalized
                )

        article_claims = _deduplicate_claims(
            article_claims
        )

        for claim in article_claims:

            evidence.append(
                {
                    "id": f"E{next_index:03d}",

                    "claim": claim.get(
                        "claim"
                    ),

                    "claim_type": claim.get(
                        "claim_type"
                    ),

                    "date": (
                        claim.get("date")
                        or date
                    ),

                    "source": (
                        source
                        or title
                        or "News source"
                    ),

                    "source_type": "news",

                    "url": url,

                    "title": title,

                    "agent": "evidence_agent",
                }
            )

            next_index += 1

    return evidence


# ============================================================
# Build Market Evidence
# ============================================================

def _build_market_evidence(
    market_data: Dict[str, Any],
    start_index: int,
) -> List[Dict[str, Any]]:

    evidence = []

    if not market_data:
        return evidence

    result = market_data.get(
        "result"
    )

    if not result:
        return evidence

    resolution = market_data.get(
        "resolution",
        {},
    )

    company = (
        resolution.get("company")
        or market_data.get("company")
        or ""
    )

    ticker = (
        resolution.get("ticker")
        or market_data.get("ticker")
        or ""
    )

    exchange = (
        resolution.get("exchange")
        or market_data.get("exchange")
        or ""
    )

    finance_query = (
        market_data.get(
            "finance_query"
        )
        or f"{ticker}:{exchange}"
    )

    # --------------------------------------------------------
    # Google Finance result
    # --------------------------------------------------------

    finance_result = result

    if isinstance(
        result,
        dict,
    ):

        # Some MCP responses wrap the finance payload.
        if isinstance(
            result.get("result"),
            dict,
        ):
            finance_result = result.get(
                "result"
            )

    if not isinstance(
        finance_result,
        dict,
    ):
        return evidence

    summary = finance_result.get(
        "summary"
    )

    markets = finance_result.get(
        "markets"
    )

    graph = finance_result.get(
        "graph"
    )

    finance_url = (
        market_data.get(
            "finance_url"
        )
        or finance_result.get(
            "finance_url"
        )
    )

    # --------------------------------------------------------
    # Summary evidence
    # --------------------------------------------------------

    if isinstance(
        summary,
        dict,
    ):

        price = (
            summary.get("price")
            or summary.get("last_price")
        )

        change = (
            summary.get("change")
            or summary.get("price_change")
        )

        change_percent = (
            summary.get(
                "change_percent"
            )
            or summary.get(
                "change_percentage"
            )
        )

        if price is not None:

            claim = (
                f"{company or ticker} "
                f"({ticker}:{exchange}) "
                f"is trading at "
                f"{price}."
            )

            if (
                change is not None
                or change_percent is not None
            ):

                movement_parts = []

                if change is not None:
                    movement_parts.append(
                        f"change {change}"
                    )

                if change_percent is not None:
                    movement_parts.append(
                        f"{change_percent}%"
                    )

                claim += (
                    " The reported market movement "
                    f"is {', '.join(movement_parts)}."
                )

            evidence.append(
                {
                    "id": f"E{start_index:03d}",

                    "claim": claim,

                    "claim_type": "market_observation",

                    "date": summary.get(
                        "date"
                    ),

                    "source": "Google Finance",

                    "source_type": "finance",

                    "url": finance_url,

                    "agent": "evidence_agent",

                    "metadata": {
                        "company": company,
                        "ticker": ticker,
                        "exchange": exchange,
                        "finance_query": finance_query,
                        "price": price,
                        "change": change,
                        "change_percent": change_percent,
                    },
                }
            )

            start_index += 1

    # --------------------------------------------------------
    # Markets fallback
    # --------------------------------------------------------

    if not evidence and isinstance(
        markets,
        list,
    ):

        for market in markets:

            if not isinstance(
                market,
                dict,
            ):
                continue

            name = (
                market.get("name")
                or market.get("company")
                or company
                or ticker
            )

            price = (
                market.get("price")
                or market.get("last_price")
            )

            if price is None:
                continue

            claim = (
                f"{name} "
                f"({ticker}:{exchange}) "
                f"is trading at {price}."
            )

            evidence.append(
                {
                    "id": f"E{start_index:03d}",

                    "claim": claim,

                    "claim_type": "market_observation",

                    "date": market.get(
                        "date"
                    ),

                    "source": "Google Finance",

                    "source_type": "finance",

                    "url": finance_url,

                    "agent": "evidence_agent",

                    "metadata": {
                        "company": name,
                        "ticker": ticker,
                        "exchange": exchange,
                        "finance_query": finance_query,
                        "price": price,
                    },
                }
            )

            start_index += 1

            break

    # --------------------------------------------------------
    # Graph fallback
    # --------------------------------------------------------

    if not evidence and isinstance(
        graph,
        dict,
    ):

        price = (
            graph.get("price")
            or graph.get("last_price")
        )

        if price is not None:

            evidence.append(
                {
                    "id": f"E{start_index:03d}",

                    "claim": (
                        f"{company or ticker} "
                        f"({ticker}:{exchange}) "
                        f"has a reported market price "
                        f"of {price}."
                    ),

                    "claim_type": "market_observation",

                    "date": graph.get(
                        "date"
                    ),

                    "source": "Google Finance",

                    "source_type": "finance",

                    "url": finance_url,

                    "agent": "evidence_agent",

                    "metadata": {
                        "company": company,
                        "ticker": ticker,
                        "exchange": exchange,
                        "finance_query": finance_query,
                        "price": price,
                    },
                }
            )

    return evidence


# ============================================================
# Build Company Evidence
# ============================================================

def _build_company_evidence(
    company_data: Dict[str, Any],
    start_index: int,
) -> List[Dict[str, Any]]:

    evidence = []

    if not company_data:
        return evidence

    # Company Agent may return a wrapper.
    result = company_data.get(
        "result",
        company_data,
    )

    if not isinstance(
        result,
        dict,
    ):
        return evidence

    # --------------------------------------------------------
    # Explicit claims
    # --------------------------------------------------------

    claims = result.get(
        "claims"
    )

    if isinstance(
        claims,
        list,
    ):

        for claim in claims:

            if isinstance(
                claim,
                str,
            ):

                text = _clean_text(
                    claim
                )

                if not text:
                    continue

                evidence.append(
                    {
                        "id": f"E{start_index:03d}",

                        "claim": text,

                        "claim_type": "reported_claim",

                        "date": None,

                        "source": (
                            result.get(
                                "source"
                            )
                            or "Company research"
                        ),

                        "source_type": "company",

                        "url": result.get(
                            "url"
                        ),

                        "agent": "evidence_agent",
                    }
                )

                start_index += 1

    # --------------------------------------------------------
    # Explicit answer
    # --------------------------------------------------------

    answer = result.get(
        "answer"
    )

    if isinstance(
        answer,
        str,
    ):

        answer = _clean_text(
            answer
        )

        if answer:

            evidence.append(
                {
                    "id": f"E{start_index:03d}",

                    "claim": answer,

                    "claim_type": "reported_claim",

                    "date": None,

                    "source": (
                        result.get(
                            "source"
                        )
                        or "Company research"
                    ),

                    "source_type": "company",

                    "url": result.get(
                        "url"
                    ),

                    "agent": "evidence_agent",
                }
            )

    return evidence


# ============================================================
# Final Evidence Validation
# ============================================================

def _finalize_evidence(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    cleaned = []

    seen = set()

    for item in evidence:

        if not isinstance(
            item,
            dict,
        ):
            continue

        claim = _clean_text(
            item.get("claim")
        )

        if not claim:
            continue

        source_type = item.get(
            "source_type"
        )

        if source_type not in {
            "news",
            "finance",
            "company",
        }:
            continue

        key = (
            source_type,
            claim.lower(),
            item.get("url"),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        cleaned.append(
            item
        )

    # --------------------------------------------------------
    # Re-number evidence IDs
    # --------------------------------------------------------

    for index, item in enumerate(
        cleaned,
        start=1,
    ):

        item["id"] = (
            f"E{index:03d}"
        )

    return cleaned


# ============================================================
# Evidence Collector
# ============================================================

async def evidence_collector(
    state: InvestigationState,
) -> InvestigationState:

    print(
        "\n============================================================"
    )

    print(
        "[Evidence Agent] LLM-based evidence extraction"
    )

    print(
        "============================================================"
    )

    evidence = []

    # ========================================================
    # News
    # ========================================================

    news_data = state.get(
        "news_data",
        {},
    )

    news_evidence = await _build_news_evidence(
        news_data,
        1,
    )

    evidence.extend(
        news_evidence
    )

    print(
        f"[Evidence Agent] News evidence extracted: "
        f"{len(news_evidence)}"
    )

    # ========================================================
    # Market
    # ========================================================

    market_data = state.get(
        "market_data",
        {},
    )

    market_evidence = _build_market_evidence(
        market_data,
        len(evidence) + 1,
    )

    evidence.extend(
        market_evidence
    )

    print(
        f"[Evidence Agent] Market evidence extracted: "
        f"{len(market_evidence)}"
    )

    # ========================================================
    # Company
    # ========================================================

    company_data = state.get(
        "company_data",
        {},
    )

    company_evidence = _build_company_evidence(
        company_data,
        len(evidence) + 1,
    )

    evidence.extend(
        company_evidence
    )

    print(
        f"[Evidence Agent] Company evidence extracted: "
        f"{len(company_evidence)}"
    )

    # ========================================================
    # Finalize
    # ========================================================

    evidence = _finalize_evidence(
        evidence
    )

    # ========================================================
    # IMPORTANT:
    # Calculate final statistics from FINAL evidence list.
    #
    # Evidence schema:
    #
    # news
    # finance
    # company
    #
    # NOT:
    #
    # market
    # ========================================================

    news_count = sum(
        1
        for item in evidence
        if item.get("source_type") == "news"
    )

    market_count = sum(
        1
        for item in evidence
        if item.get("source_type") == "finance"
    )

    company_count = sum(
        1
        for item in evidence
        if item.get("source_type") == "company"
    )

    # ========================================================
    # Final statistics
    # ========================================================

    print(
        "\n[Evidence Agent] Final evidence statistics"
    )

    print(
        f"Total evidence: "
        f"{len(evidence)}"
    )

    print(
        f"News: "
        f"{news_count}"
    )

    print(
        f"Market: "
        f"{market_count}"
    )

    print(
        f"Company: "
        f"{company_count}"
    )

    # ========================================================
    # Claim type distribution
    # ========================================================

    claim_types = {}

    for item in evidence:

        claim_type = item.get(
            "claim_type",
            "unknown",
        )

        claim_types[claim_type] = (
            claim_types.get(
                claim_type,
                0,
            ) + 1
        )

    print(
        "\nClaim types:"
    )

    for claim_type, count in sorted(
        claim_types.items()
    ):

        print(
            f"  {claim_type}: {count}"
        )

    # ========================================================
    # Trace
    # ========================================================

    trace_entry = {
        "agent": "evidence_collector",
        "status": "success",
        "action": "extract_and_validate_evidence",
        "evidence_count": len(evidence),
        "news_evidence": news_count,
        "market_evidence": market_count,
        "company_evidence": company_count,
    }

    return {
        "evidence": evidence,

        "trace": state.get(
            "trace",
            [],
        ) + [
            trace_entry
        ],
    }