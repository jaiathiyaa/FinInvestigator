from __future__ import annotations

import re
from typing import Any, Dict, List


MAX_EVIDENCE_PER_ARTICLE = 8


BOILERPLATE_PHRASES = [
    "skip navigation",
    "skip to content",
    "skip to main content",
    "markets",
    "business",
    "investing",
    "technology",
    "tech",
    "politics",
    "video",
    "watchlist",
    "sign in",
    "log in",
    "subscribe",
    "newsletter",
    "advertisement",
    "advertising",
    "privacy policy",
    "terms of use",
    "cookie policy",
    "all rights reserved",
    "follow us",
    "download the app",
    "menu",
    "search",
    "home",
]


INVESTIGATION_KEYWORDS = [
    "stock",
    "shares",
    "share price",
    "market cap",
    "valuation",
    "trading",
    "traded",
    "rally",
    "gain",
    "gained",
    "rise",
    "rose",
    "fell",
    "fall",
    "drop",
    "dropped",
    "decline",
    "declined",
    "record high",
    "all-time high",
    "low",
    "revenue",
    "sales",
    "profit",
    "earnings",
    "income",
    "margin",
    "guidance",
    "forecast",
    "outlook",
    "expects",
    "expected",
    "reported",
    "billion",
    "million",
    "growth",
    "demand",
    "customer",
    "customers",
    "partnership",
    "partner",
    "contract",
    "deal",
    "launch",
    "product",
    "acquisition",
    "merger",
    "investment",
    "capital",
    "buyback",
    "analyst",
    "rating",
    "price target",
    "overweight",
    "underweight",
    "top pick",
    "upgrade",
    "downgrade",
    "risk",
    "concern",
    "uncertainty",
    "constraint",
    "shortage",
    "regulation",
    "regulatory",
    "competition",
    "supply chain",
    "geopolitical",
    "tariff",
]


GUIDANCE_PATTERNS = [
    r"\bexpects?\b",
    r"\bexpecting\b",
    r"\bforecast\b",
    r"\bguidance\b",
    r"\boutlook\b",
    r"\bprojects?\b",
    r"\bprojected\b",
    r"\banticipates?\b",
]


ANALYST_ACTION_PATTERNS = [
    r"\banalyst\b",
    r"\bprice target\b",
    r"\btop pick\b",
    r"\boverweight\b",
    r"\bunderweight\b",
    r"\bupgrade\b",
    r"\bdowngrade\b",
    r"\breiterate\b",
    r"\brecommendation\b",
]


FINANCIAL_METRIC_PATTERNS = [
    r"\brevenue\b",
    r"\bsales\b",
    r"\bprofit\b",
    r"\bearnings\b",
    r"\bincome\b",
    r"\bmargin\b",
    r"\bmarket cap\b",
    r"\bvaluation\b",
    r"\b\d+(?:\.\d+)?\s*(?:billion|million|trillion)\b",
]


MARKET_OBSERVATION_PATTERNS = [
    r"\bshares?\b",
    r"\bstock\b",
    r"\bshare price\b",
    r"\btrading\b",
    r"\btraded\b",
    r"\bup\s+\d",
    r"\bdown\s+\d",
    r"\bgained\b",
    r"\blost\b",
    r"\brose\b",
    r"\bfell\b",
    r"\bdropped\b",
    r"\brall(?:y|ied)\b",
    r"\brecord high\b",
    r"\ball-time high\b",
]


BUSINESS_EVENT_PATTERNS = [
    r"\blaunch(?:ed|es)?\b",
    r"\bpartnership\b",
    r"\bpartner(?:ed|s)?\b",
    r"\bcontract\b",
    r"\bdeal\b",
    r"\bacquisition\b",
    r"\bacquire(?:d|s)?\b",
    r"\bmerger\b",
    r"\binvest(?:ed|ment|ing)\b",
    r"\bdata center\b",
]


CORPORATE_ACTION_PATTERNS = [
    r"\bbuyback\b",
    r"\bshare repurchase\b",
    r"\bdividend\b",
    r"\bcapital allocation\b",
    r"\bdebt issuance\b",
    r"\bstock split\b",
]


RISK_PATTERNS = [
    r"\brisk\b",
    r"\bconcern\b",
    r"\buncertainty\b",
    r"\bconstraint\b",
    r"\bshortage\b",
    r"\bregulation\b",
    r"\bregulatory\b",
    r"\bcompetition\b",
    r"\bsupply chain\b",
    r"\bgeopolitical\b",
    r"\btariff\b",
    r"\bdependence\b",
    r"\bvulnerability\b",
]


EXECUTIVE_PATTERNS = [
    r"\bsaid\b",
    r"\bsays\b",
    r"\baccording to\b",
    r"\bchief executive\b",
    r"\bceo\b",
    r"\bcfo\b",
    r"\bpresident\b",
    r"\bchairman\b",
]


def _normalize_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = text.replace(
        "\xa0",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _normalize_for_comparison(
    text: str,
) -> str:

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _contains_pattern(
    text: str,
    patterns: List[str],
) -> bool:

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _split_sentences(
    text: str,
) -> List[str]:

    if not text:
        return []

    text = text.replace(
        "\n",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9\"'])",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def _is_boilerplate(
    sentence: str,
) -> bool:

    normalized = _normalize_text(
        sentence
    )

    lowered = normalized.lower()

    if not normalized:
        return True

    if len(normalized) < 35:
        return True

    if lowered in BOILERPLATE_PHRASES:
        return True

    words = lowered.split()

    if len(words) <= 12:

        boilerplate_matches = sum(
            1
            for phrase in BOILERPLATE_PHRASES
            if phrase in lowered
        )

        if boilerplate_matches >= 2:
            return True

    if (
        " | " in normalized
        and len(words) < 15
    ):
        return True

    return False


def _is_useful_sentence(
    sentence: str,
    company: str,
) -> bool:

    normalized = _normalize_text(
        sentence
    )

    if _is_boilerplate(
        normalized
    ):
        return False

    lowered = normalized.lower()

    company_lower = company.lower().strip()

    if (
        company_lower
        and company_lower in lowered
    ):
        return True

    keyword_matches = sum(
        1
        for keyword in INVESTIGATION_KEYWORDS
        if keyword.lower() in lowered
    )

    if keyword_matches == 0:
        return False

    if len(normalized.split()) < 8:
        return False

    return True


def _classify_claim(
    sentence: str,
) -> str:

    text = _normalize_text(
        sentence
    )

    if _contains_pattern(
        text,
        GUIDANCE_PATTERNS,
    ):
        return "guidance"

    if _contains_pattern(
        text,
        ANALYST_ACTION_PATTERNS,
    ):
        return "analyst_action"

    if _contains_pattern(
        text,
        CORPORATE_ACTION_PATTERNS,
    ):
        return "corporate_action"

    if _contains_pattern(
        text,
        RISK_PATTERNS,
    ):
        return "risk"

    if _contains_pattern(
        text,
        FINANCIAL_METRIC_PATTERNS,
    ):
        return "financial_metric"

    if _contains_pattern(
        text,
        MARKET_OBSERVATION_PATTERNS,
    ):
        return "market_observation"

    if _contains_pattern(
        text,
        BUSINESS_EVENT_PATTERNS,
    ):
        return "business_event"

    if _contains_pattern(
        text,
        EXECUTIVE_PATTERNS,
    ):
        return "executive_statement"

    return "reported_claim"


def _extract_claims_from_article(
    article: Dict[str, Any],
    company: str,
) -> List[Dict[str, Any]]:

    content = _normalize_text(
        article.get(
            "content",
            "",
        )
    )

    if not content:
        return []

    sentences = _split_sentences(
        content
    )

    claims: List[Dict[str, Any]] = []

    seen = set()

    for sentence in sentences:

        sentence = _normalize_text(
            sentence
        )

        if not _is_useful_sentence(
            sentence,
            company,
        ):
            continue

        normalized_claim = (
            _normalize_for_comparison(
                sentence
            )
        )

        if not normalized_claim:
            continue

        if normalized_claim in seen:
            continue

        seen.add(
            normalized_claim
        )

        claim_type = _classify_claim(
            sentence
        )

        claims.append(
            {
                "claim": sentence,
                "claim_type": claim_type,
                "evidence_source_type": "news",
                "source": article.get(
                    "source"
                ),
                "url": article.get(
                    "url"
                ),
                "date": article.get(
                    "date"
                ),
                "title": article.get(
                    "title"
                ),
            }
        )

        if len(claims) >= MAX_EVIDENCE_PER_ARTICLE:
            break

    return claims


def _extract_market_evidence(
    market_data: Dict[str, Any],
) -> List[Dict[str, Any]]:

    result = market_data.get(
        "result"
    )

    if not isinstance(
        result,
        dict,
    ):
        return []

    evidence: List[Dict[str, Any]] = []

    summary = result.get(
        "summary"
    )

    if not isinstance(
        summary,
        dict,
    ):
        return evidence

    symbol = (
        summary.get("symbol")
        or summary.get("ticker")
        or ""
    )

    price = (
        summary.get("price")
        or summary.get("value")
    )

    change = (
        summary.get("price_movement")
        or summary.get("change")
    )

    if symbol and price is not None:

        claim = (
            f"{symbol} is currently trading "
            f"at {price}."
        )

        if change is not None:

            claim += (
                f" The reported price movement "
                f"is {change}."
            )

        evidence.append(
            {
                "claim": claim,
                "claim_type": (
                    "market_observation"
                ),
                "evidence_source_type": (
                    "market"
                ),
                "source": "Google Finance",
                "url": result.get(
                    "finance_url"
                ),
                "date": None,
                "title": (
                    "Google Finance market data"
                ),
            }
        )

    return evidence


def _extract_company_evidence(
    company_data: Dict[str, Any],
) -> List[Dict[str, Any]]:

    evidence: List[Dict[str, Any]] = []

    result = company_data.get(
        "result"
    )

    if not isinstance(
        result,
        dict,
    ):
        return evidence

    description = result.get(
        "description"
    )

    if description:

        description = _normalize_text(
            str(description)
        )

        if len(description) >= 40:

            evidence.append(
                {
                    "claim": description,
                    "claim_type": (
                        "reported_claim"
                    ),
                    "evidence_source_type": (
                        "company"
                    ),
                    "source": company_data.get(
                        "source",
                        "Company research",
                    ),
                    "url": result.get(
                        "url"
                    ),
                    "date": None,
                    "title": (
                        "Company research"
                    ),
                }
            )

    return evidence


async def evidence_collector(
    state: Dict[str, Any],
) -> Dict[str, Any]:

    company = state.get(
        "company",
        "Unknown",
    )

    news_data = state.get(
        "news_data",
        {},
    )

    market_data = state.get(
        "market_data",
        {},
    )

    company_data = state.get(
        "company_data",
        {},
    )

    print(
        f"[Evidence Collector] "
        f"Collecting evidence for {company}"
    )

    all_evidence: List[Dict[str, Any]] = []

    # =============================================================
    # NEWS
    # =============================================================

    articles = news_data.get(
        "articles",
        [],
    )

    if not isinstance(
        articles,
        list,
    ):
        articles = []

    print(
        f"[Evidence Collector] "
        f"Processing {len(articles)} news articles"
    )

    for article_index, article in enumerate(
        articles,
        start=1,
    ):

        if not isinstance(
            article,
            dict,
        ):
            continue

        scrape_status = article.get(
            "scrape_status",
            "success",
        )

        if scrape_status != "success":

            print(
                f"[Evidence Collector] "
                f"Skipping failed article "
                f"{article_index}: "
                f"{article.get('title', 'Unknown')}"
            )

            continue

        claims = _extract_claims_from_article(
            article=article,
            company=company,
        )

        print(
            f"[Evidence Collector] "
            f"Article {article_index}: "
            f"{len(claims)} claims"
        )

        all_evidence.extend(
            claims
        )

    # =============================================================
    # MARKET
    # =============================================================

    market_evidence = (
        _extract_market_evidence(
            market_data
        )
    )

    if market_evidence:

        print(
            f"[Evidence Collector] "
            f"Market evidence: "
            f"{len(market_evidence)}"
        )

    all_evidence.extend(
        market_evidence
    )

    # =============================================================
    # COMPANY
    # =============================================================

    company_evidence = (
        _extract_company_evidence(
            company_data
        )
    )

    if company_evidence:

        print(
            f"[Evidence Collector] "
            f"Company evidence: "
            f"{len(company_evidence)}"
        )

    all_evidence.extend(
        company_evidence
    )

    # =============================================================
    # GLOBAL DUPLICATE REMOVAL
    # =============================================================

    unique_evidence: List[
        Dict[str, Any]
    ] = []

    seen_claims = set()

    for item in all_evidence:

        claim = item.get(
            "claim",
            "",
        )

        normalized_claim = (
            _normalize_for_comparison(
                claim
            )
        )

        if not normalized_claim:
            continue

        if normalized_claim in seen_claims:
            continue

        seen_claims.add(
            normalized_claim
        )

        unique_evidence.append(
            item
        )

    # =============================================================
    # ASSIGN EVIDENCE IDs
    # =============================================================

    evidence = []

    for index, item in enumerate(
        unique_evidence,
        start=1,
    ):

        evidence_item = {
            "evidence_id": f"E{index:03d}",
            "claim": item.get(
                "claim"
            ),
            "claim_type": item.get(
                "claim_type",
                "reported_claim",
            ),
            "evidence_source_type": item.get(
                "evidence_source_type",
                "unknown",
            ),
            "source": item.get(
                "source"
            ),
            "url": item.get(
                "url"
            ),
            "date": item.get(
                "date"
            ),
            "title": item.get(
                "title"
            ),
        }

        evidence.append(
            evidence_item
        )

    # =============================================================
    # COUNTS
    # =============================================================

    news_count = sum(
        1
        for item in evidence
        if item.get(
            "evidence_source_type"
        ) == "news"
    )

    market_count = sum(
        1
        for item in evidence
        if item.get(
            "evidence_source_type"
        ) == "market"
    )

    company_count = sum(
        1
        for item in evidence
        if item.get(
            "evidence_source_type"
        ) == "company"
    )

    claim_type_counts: Dict[
        str,
        int,
    ] = {}

    for item in evidence:

        claim_type = item.get(
            "claim_type",
            "unknown",
        )

        claim_type_counts[
            claim_type
        ] = (
            claim_type_counts.get(
                claim_type,
                0,
            )
            + 1
        )

    # =============================================================
    # DEBUG
    # =============================================================

    print(
        f"[Evidence Collector] "
        f"Total evidence: {len(evidence)}"
    )

    print(
        f"[Evidence Collector] "
        f"News: {news_count}"
    )

    print(
        f"[Evidence Collector] "
        f"Market: {market_count}"
    )

    print(
        f"[Evidence Collector] "
        f"Company: {company_count}"
    )

    print(
        "[Evidence Collector] "
        "Claim types:"
    )

    for claim_type, count in sorted(
        claim_type_counts.items()
    ):

        print(
            f"  - {claim_type}: "
            f"{count}"
        )

    for item in evidence:

        print(
            f"[Evidence Collector] "
            f"{item['evidence_id']} | "
            f"{item['evidence_source_type']} | "
            f"{item['claim_type']} | "
            f"{item['claim'][:150]}"
        )

    return {
        "evidence": evidence,
    }