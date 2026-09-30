# backend/app/services/finance_verifier.py

import os
from typing import Any
from dotenv import load_dotenv
import serpapi
import re

load_dotenv()

def get_serpapi_client() -> serpapi.Client:

    api_key = os.getenv(
        "SERPAPI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "SERPAPI_API_KEY is not configured."
        )

    return serpapi.Client(
        api_key=api_key,
        timeout=15,
    )


def normalize(value: Any) -> str:
    if value is None:
        return ""

    value = str(value).lower()

    # Remove punctuation
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    # Normalize multiple spaces
    value = re.sub(r"\s+", " ", value).strip()

    return value

def company_names_match(
    requested_company: str,
    returned_company: str,
) -> bool:
    """
    Compare two company names after normalization.
    """

    if not requested_company or not returned_company:
        return False

    requested = normalize(requested_company)
    returned = normalize(returned_company)


    # --------------------------------------------------------
    # 1. Exact normalized match
    # --------------------------------------------------------

    if requested == returned:
        print("Company match method: exact")
        return True

    # --------------------------------------------------------
    # 2. Substring match
    # --------------------------------------------------------

    if requested in returned or returned in requested:
        print("Company match method: substring")
        return True

    # --------------------------------------------------------
    # 3. Token comparison
    # --------------------------------------------------------

    requested_words = set(requested.split())
    returned_words = set(returned.split())

    # Remove common legal/company suffixes
    ignored_words = {
        "inc",
        "incorporated",
        "corp",
        "corporation",
        "co",
        "company",
        "ltd",
        "limited",
        "plc",
        "llc",
        "holdings",
    }

    requested_words -= ignored_words
    returned_words -= ignored_words

    common_words = (
        requested_words
        & returned_words
    )

    if common_words:
        print("Company match method: common-token")
        return True

    print("Company match method: no-match")

    return False

def verify_finance_entity(
    company_name: str,
    ticker: str,
    exchange: str,
) -> dict[str, Any]:

    client = get_serpapi_client()

    finance_query = (
        f"{ticker}:{exchange}"
    )

    # =====================================================
    # SERPAPI REQUEST
    # =====================================================

    try:

        results = client.search(
            {
                "engine": "google_finance",
                "q": finance_query,
                "output": "json",
            }
        )

        data = dict(results)

    except TimeoutError:

        return {
            "verified": False,
            "error_type": "timeout",
            "retryable": True,
            "message": (
                "SerpApi Finance request timed out."
            ),
        }

    except Exception as exc:

        return {
            "verified": False,
            "error_type": "serpapi_error",
            "retryable": True,
            "message": str(exc),
        }


    # =====================================================
    # EXTRACT SUMMARY
    # =====================================================

    summary = data.get(
        "summary"
    ) or {}

    finance_company = (
        summary.get("title")
        or summary.get("name")
    )

    finance_ticker = (
        summary.get("stock")
        or summary.get("ticker")
    )

    finance_exchange = (
        summary.get("exchange")
    )

    # =====================================================
    # NORMALIZE
    # =====================================================

    requested_ticker = normalize(
        ticker
    )

    requested_exchange = normalize(
        exchange
    )

    returned_ticker = normalize(
        finance_ticker
    )

    returned_exchange = normalize(
        finance_exchange
    )


    # =====================================================
    # TICKER VERIFICATION
    # =====================================================

    ticker_match = (
        returned_ticker
        == requested_ticker
    )

    # =====================================================
    # EXCHANGE VERIFICATION
    # =====================================================

    exchange_match = (
        returned_exchange
        == requested_exchange
    )

    # =====================================================
    # COMPANY VERIFICATION
    # =====================================================

    company_match = company_names_match(
        requested_company=company_name,
        returned_company=finance_company,
    )


    # ========================================================
    # FINAL VERIFICATION
    # ========================================================

    verified = (
        ticker_match
        and exchange_match
        and company_match
    )

    return {
        "verified": verified,

        "finance_query": finance_query,

        "company": finance_company,

        "ticker": (
            returned_ticker.upper()
            or requested_ticker.upper()
        ),

        "exchange": (
            returned_exchange.upper()
            or requested_exchange.upper()
        ),

        "ticker_match": ticker_match,

        "exchange_match": exchange_match,

        "company_match": company_match,

        "summary": summary,

        "raw_data": data,
    }