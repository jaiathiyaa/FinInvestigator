# backend/app/services/web_entity_search.py

import re
from typing import Any

from ddgs import DDGS


def search_entity_web(
    company_name: str,
) -> list[dict[str, Any]]:
    """
    Search the web for stock/entity information.

    Returns search-result content that can later be
    analyzed by the LLM if deterministic extraction fails.
    """

    query = (
        f'"{company_name}" '
        f'stock ticker exchange'
    )

    results = []

    with DDGS() as ddgs:

        search_results = ddgs.text(
            query,
            max_results=10,
        )

        for result in search_results:

            results.append(
                {
                    "source": "duckduckgo",
                    "title": result.get(
                        "title",
                        "",
                    ),
                    "snippet": result.get(
                        "body",
                        "",
                    ),
                    "url": result.get(
                        "href",
                        "",
                    ),
                }
            )

    return results


def extract_candidates(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    """
    Extract ticker + exchange only from strong,
    explicit patterns.

    We intentionally DO NOT extract arbitrary
    values from parentheses such as:

        (MAY)
        (SYMBOL)
        (COMMON)

    because these can create false positives.
    """

    candidates = []

    for result in results:

        title = result.get(
            "title",
            "",
        )

        snippet = result.get(
            "snippet",
            "",
        )

        url = result.get(
            "url",
            "",
        )

        text = (
            f"{title} "
            f"{snippet} "
            f"{url}"
        )

        # =====================================================
        # Pattern 1
        #
        # NASDAQ:MSFT
        # NYSE:IBM
        # NSE:RELIANCE
        # BSE:TCS
        # =====================================================

        matches = re.findall(
            r"\b"
            r"(NASDAQ|NYSE|NSE|BSE)"
            r"\s*:\s*"
            r"([A-Z][A-Z0-9.-]{1,9})"
            r"\b",
            text,
            re.IGNORECASE,
        )

        for exchange, ticker in matches:

            candidates.append(
                {
                    "ticker": ticker.upper(),
                    "exchange": exchange.upper(),
                    "source": result,
                    "pattern": "exchange:ticker",
                }
            )

        # =====================================================
        # Pattern 2
        #
        # MSFT:NASDAQ
        # IBM:NYSE
        # RELIANCE:NSE
        # =====================================================

        matches = re.findall(
            r"\b"
            r"([A-Z][A-Z0-9.-]{1,9})"
            r"\s*:\s*"
            r"(NASDAQ|NYSE|NSE|BSE)"
            r"\b",
            text,
            re.IGNORECASE,
        )

        for ticker, exchange in matches:

            candidates.append(
                {
                    "ticker": ticker.upper(),
                    "exchange": exchange.upper(),
                    "source": result,
                    "pattern": "ticker:exchange",
                }
            )

        # =====================================================
        # Pattern 3
        #
        # TSLA.US
        # RELIANCE.NS
        # TCS.BO
        # =====================================================

        matches = re.findall(
            r"\b"
            r"([A-Z][A-Z0-9.-]{1,9})"
            r"\."
            r"(NS|BO|US)"
            r"\b",
            text,
            re.IGNORECASE,
        )

        exchange_mapping = {
            "NS": "NSE",
            "BO": "BSE",
            "US": "US",
        }

        for ticker, suffix in matches:

            suffix = suffix.upper()

            candidates.append(
                {
                    "ticker": ticker.upper(),
                    "exchange": exchange_mapping[
                        suffix
                    ],
                    "source": result,
                    "pattern": "ticker:suffix",
                }
            )

    return candidates