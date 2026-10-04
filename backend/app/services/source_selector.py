from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


SOURCE_QUALITY = {
    "reuters.com": 5.0,
    "bloomberg.com": 5.0,
    "ft.com": 4.8,
    "wsj.com": 4.8,
    "cnbc.com": 4.8,
    "finance.yahoo.com": 4.0,
    "marketwatch.com": 4.0,
    "seekingalpha.com": 3.8,
    "investing.com": 3.6,
    "tradingview.com": 3.6,
    "fool.com": 3.2,
    "barrons.com": 4.5,
    "apnews.com": 4.5,
    "bbc.com": 4.2,
    "cnn.com": 4.0,
    "nytimes.com": 4.5,
    "blogs.nvidia.com": 2.5,
}


FINANCIAL_KEYWORDS = [
    "stock",
    "shares",
    "share price",
    "market cap",
    "valuation",
    "earnings",
    "revenue",
    "sales",
    "profit",
    "guidance",
    "forecast",
    "outlook",
    "financial",
    "quarter",
    "q1",
    "q2",
    "q3",
    "q4",
]


MARKET_KEYWORDS = [
    "stock",
    "shares",
    "price",
    "trading",
    "traded",
    "rally",
    "record high",
    "all-time high",
    "market cap",
    "investors",
    "wall street",
    "nasdaq",
    "dow",
    "s&p",
]


EVENT_KEYWORDS = [
    "earnings",
    "revenue",
    "guidance",
    "outlook",
    "analyst",
    "price target",
    "upgrade",
    "downgrade",
    "top pick",
    "partnership",
    "contract",
    "acquisition",
    "merger",
    "investment",
    "capital",
    "buyback",
    "product launch",
    "chip",
    "demand",
    "data center",
    "ai infrastructure",
]


PRICE_MOVEMENT_KEYWORDS = [
    "rose",
    "rises",
    "rally",
    "rallied",
    "gained",
    "gain",
    "up",
    "surged",
    "jumped",
    "record high",
    "all-time high",
    "fell",
    "falls",
    "dropped",
    "declined",
    "down",
]


POSITIVE_MOVEMENT_KEYWORDS = [
    "rose",
    "rises",
    "rally",
    "rallied",
    "gained",
    "gain",
    "up",
    "surged",
    "jumped",
    "record high",
    "all-time high",
]


NEGATIVE_MOVEMENT_KEYWORDS = [
    "fell",
    "falls",
    "dropped",
    "declined",
    "down",
    "selloff",
    "sell-off",
    "slumped",
]


IRRELEVANT_KEYWORDS = [
    "games",
    "gaming",
    "geforce now",
    "minecraft",
    "witcher",
    "steam",
    "epic games",
    "gameplay",
    "players",
    "esports",
    "trailer",
]


def _normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _get_domain(article: Dict[str, Any]) -> str:
    link = article.get("link", "")

    if not link:
        return ""

    try:
        domain = urlparse(link).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def _article_text(article: Dict[str, Any]) -> str:
    title = _normalize_text(
        str(article.get("title", ""))
    )

    snippet = _normalize_text(
        str(article.get("snippet", ""))
    )

    return f"{title} {snippet}".lower()


def _relevance_score(
    article: Dict[str, Any],
    company: str,
) -> float:

    text = _article_text(article)

    company_terms = [
        term.lower()
        for term in company.split()
        if len(term) >= 2
    ]

    score = 0.0

    for term in company_terms:
        if term in text:
            score += 1.5

    for keyword in FINANCIAL_KEYWORDS:
        if keyword in text:
            score += 0.6

    return min(score, 10.0)


def _domain_score(
    article: Dict[str, Any],
) -> float:

    domain = _get_domain(article)

    if domain in SOURCE_QUALITY:
        return SOURCE_QUALITY[domain]

    for known_domain, score in SOURCE_QUALITY.items():

        if domain.endswith(
            "." + known_domain
        ):
            return score

    return 2.0


def _parse_date(
    article: Dict[str, Any],
) -> Optional[datetime]:

    raw_date = (
        article.get("iso_date")
        or article.get("date")
    )

    if not raw_date:
        return None

    if isinstance(
        raw_date,
        datetime,
    ):
        return raw_date

    raw_date = str(
        raw_date
    ).strip()

    try:

        parsed = datetime.fromisoformat(
            raw_date.replace(
                "Z",
                "+00:00",
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    except ValueError:
        pass

    return None


def _recency_score(
    article: Dict[str, Any],
) -> float:

    date = _parse_date(
        article
    )

    if not date:
        return 0.0

    now = datetime.now(
        timezone.utc
    )

    age_hours = max(
        0.0,
        (
            now - date
        ).total_seconds()
        / 3600,
    )

    if age_hours <= 6:
        return 10.0

    if age_hours <= 24:
        return 9.0

    if age_hours <= 48:
        return 8.0

    if age_hours <= 72:
        return 7.0

    if age_hours <= 7 * 24:
        return 5.0

    if age_hours <= 14 * 24:
        return 3.0

    return 1.0


def _event_relevance_score(
    article: Dict[str, Any],
) -> float:

    text = _article_text(
        article
    )

    matches = sum(
        1
        for keyword in EVENT_KEYWORDS
        if keyword in text
    )

    return min(
        matches * 0.8,
        5.0,
    )


def _direction_score(
    article: Dict[str, Any],
    query: str,
) -> float:

    text = _article_text(
        article
    )

    query = query.lower()

    score = 0.0

    positive = any(
        keyword in query
        for keyword in [
            "up",
            "rise",
            "rising",
            "increase",
            "gain",
            "gained",
            "rally",
        ]
    )

    negative = any(
        keyword in query
        for keyword in [
            "down",
            "fall",
            "falling",
            "drop",
            "decline",
            "declined",
            "loss",
        ]
    )

    if positive:

        matches = sum(
            1
            for keyword in POSITIVE_MOVEMENT_KEYWORDS
            if keyword in text
        )

        score += min(
            matches * 0.8,
            3.0,
        )

    if negative:

        matches = sum(
            1
            for keyword in NEGATIVE_MOVEMENT_KEYWORDS
            if keyword in text
        )

        score += min(
            matches * 0.8,
            3.0,
        )

    return score


def _investigation_relevance(
    article: Dict[str, Any],
) -> float:

    text = _article_text(
        article
    )

    financial_matches = sum(
        1
        for keyword in FINANCIAL_KEYWORDS
        if keyword in text
    )

    market_matches = sum(
        1
        for keyword in MARKET_KEYWORDS
        if keyword in text
    )

    event_matches = sum(
        1
        for keyword in EVENT_KEYWORDS
        if keyword in text
    )

    irrelevant_matches = sum(
        1
        for keyword in IRRELEVANT_KEYWORDS
        if keyword in text
    )

    score = (
        financial_matches * 1.0
        + market_matches * 0.8
        + event_matches * 1.2
        - irrelevant_matches * 2.5
    )

    return max(
        0.0,
        min(score, 12.0),
    )


def _total_score(
    article: Dict[str, Any],
    company: str,
    query: str,
) -> float:

    relevance = _relevance_score(
        article,
        company,
    )

    source_quality = _domain_score(
        article
    )

    recency = _recency_score(
        article
    )

    event_relevance = _event_relevance_score(
        article
    )

    direction = _direction_score(
        article,
        query,
    )

    investigation = _investigation_relevance(
        article
    )

    score = (
        relevance
        + source_quality
        + recency * 1.2
        + event_relevance
        + direction
        + investigation
    )

    # Store scoring details for debugging.
    article["_domain"] = _get_domain(
        article
    )

    article["_relevance_score"] = round(
        relevance,
        2,
    )

    article["_domain_score"] = round(
        source_quality,
        2,
    )

    article["_recency_score"] = round(
        recency,
        2,
    )

    article["_event_relevance_score"] = round(
        event_relevance,
        2,
    )

    article["_direction_score"] = round(
        direction,
        2,
    )

    article["_investigation_relevance"] = round(
        investigation,
        2,
    )

    article["_selection_score"] = round(
        score,
        2,
    )

    return score


def _select_diverse_sources(
    candidates: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:

    selected: List[Dict[str, Any]] = []

    domains_used = set()

    # ---------------------------------------------------------------
    # First pass:
    # Prefer one article per domain.
    # ---------------------------------------------------------------

    for article in candidates:

        if len(selected) >= limit:
            break

        domain = article.get(
            "_domain",
            "",
        )

        if domain in domains_used:
            continue

        selected.append(
            article
        )

        domains_used.add(
            domain
        )

    # ---------------------------------------------------------------
    # Second pass:
    # Allow a maximum of two articles per domain.
    # ---------------------------------------------------------------

    domain_counts: Dict[str, int] = {}

    for article in selected:

        domain = article.get(
            "_domain",
            "",
        )

        domain_counts[domain] = (
            domain_counts.get(
                domain,
                0,
            )
            + 1
        )

    for article in candidates:

        if len(selected) >= limit:
            break

        if article in selected:
            continue

        domain = article.get(
            "_domain",
            "",
        )

        count = domain_counts.get(
            domain,
            0,
        )

        if count >= 2:
            continue

        selected.append(
            article
        )

        domain_counts[domain] = (
            count + 1
        )

    return selected


def select_sources(
    news_results: List[Dict[str, Any]],
    company: str,
    limit: int = 5,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:

    if not news_results:
        return []

    query = query or ""

    candidates = []

    for article in news_results:

        if not isinstance(
            article,
            dict,
        ):
            continue

        if not article.get(
            "link"
        ):
            continue

        title = _normalize_text(
            str(
                article.get(
                    "title",
                    "",
                )
            )
        )

        if not title:
            continue

        # Calculate total score.
        score = _total_score(
            article,
            company,
            query,
        )

        # -----------------------------------------------------------
        # Hard relevance filter.
        #
        # An article that is mostly about gaming, games, etc.
        # should not survive merely because it comes from NVIDIA.
        # -----------------------------------------------------------

        investigation_score = article.get(
            "_investigation_relevance",
            0.0,
        )

        if investigation_score < 1.5:
            continue

        article["_selection_score"] = round(
            score,
            2,
        )

        candidates.append(
            article
        )

    candidates.sort(
        key=lambda item: item.get(
            "_selection_score",
            0.0,
        ),
        reverse=True,
    )

    selected = _select_diverse_sources(
        candidates,
        limit,
    )

    return selected