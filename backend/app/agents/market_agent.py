# backend/app/agents/market_agent.py

from app.graph.state import InvestigationState
from app.mcp.client import call_search_finance
from app.services.stock_resolver import resolve_stock


async def market_agent(
    state: InvestigationState,
) -> InvestigationState:

    company = state["company"]

    print(
        f"[Market Agent] Resolving stock identity for {company}"
    )

    # =================================================
    # STEP 1 — RESOLVE STOCK
    # =================================================

    try:

        resolved = resolve_stock(company)

    except Exception as exc:

        print(
            f"[Market Agent] Stock resolver error: {exc}"
        )

        return {
            "market_data": {
                "company": company,
                "result": None,
                "agent": "market_agent",
                "source_type": "finance",
                "error": str(exc),
                "error_type": "stock_resolution_error",
            }
        }

    # =================================================
    # STEP 2 — CHECK RESOLUTION
    # =================================================

    if not resolved.get("resolved"):

        print(
            "[Market Agent] Could not resolve stock identity"
        )

        return {
            "market_data": {
                "company": company,
                "result": None,
                "agent": "market_agent",
                "source_type": "finance",
                "error": resolved.get(
                    "message",
                    "Stock resolution failed.",
                ),
                "error_type": resolved.get(
                    "error_type",
                    "stock_resolution_failed",
                ),
                "resolution": resolved,
            }
        }

    # =================================================
    # STEP 3 — GET RESOLVED INFORMATION
    # =================================================

    canonical_company = resolved.get(
        "company",
        company,
    )

    ticker = resolved.get("ticker")
    exchange = resolved.get("exchange")
    finance_query = resolved.get("finance_query")

    print(
        f"[Market Agent] Resolved: "
        f"{canonical_company} | "
        f"{ticker} | "
        f"{exchange}"
    )

    print(
        f"[Market Agent] Finance query: "
        f"{finance_query}"
    )

    # =================================================
    # STEP 4 — VALIDATE FINANCE QUERY
    # =================================================

    if not finance_query:

        print(
            "[Market Agent] No finance query available"
        )

        return {
            "market_data": {
                "company": canonical_company,
                "ticker": ticker,
                "exchange": exchange,
                "result": None,
                "agent": "market_agent",
                "source_type": "finance",
                "error": (
                    "Stock was resolved but "
                    "finance query is missing."
                ),
                "error_type": (
                    "missing_finance_query"
                ),
                "resolution": resolved,
            }
        }

    # =================================================
    # STEP 5 — SEARCH GOOGLE FINANCE
    # =================================================

    print(
        f"[Market Agent] Searching finance: "
        f"{finance_query}"
    )

    try:

        result = await call_search_finance(
            finance_query
        )

        print(
            "[Market Agent] Finance MCP "
            "response received"
        )

        # =================================================
        # STEP 6 — RETURN MARKET DATA
        # =================================================

        return {
            "market_data": {
                "company": canonical_company,
                "ticker": ticker,
                "exchange": exchange,
                "query": finance_query,
                "result": result,
                "agent": "market_agent",
                "source_type": "finance",
                "resolution": {
                    "resolved": True,
                    "cached": resolved.get(
                        "cached",
                        False,
                    ),
                    "company": canonical_company,
                    "ticker": ticker,
                    "exchange": exchange,
                    "finance_query": finance_query,
                    "resolution_method": resolved.get(
                        "resolution_method"
                    ),
                    "confidence": resolved.get(
                        "confidence"
                    ),
                    "entity_id": resolved.get(
                        "entity_id"
                    ),
                },
            }
        }

    except Exception as exc:

        print(
            f"[Market Agent] Finance search error: "
            f"{exc}"
        )

        return {
            "market_data": {
                "company": canonical_company,
                "ticker": ticker,
                "exchange": exchange,
                "query": finance_query,
                "result": None,
                "agent": "market_agent",
                "source_type": "finance",
                "error": str(exc),
                "error_type": "finance_search_error",
                "resolution": {
                    "resolved": True,
                    "cached": resolved.get(
                        "cached",
                        False,
                    ),
                    "company": canonical_company,
                    "ticker": ticker,
                    "exchange": exchange,
                    "finance_query": finance_query,
                    "resolution_method": resolved.get(
                        "resolution_method"
                    ),
                    "confidence": resolved.get(
                        "confidence"
                    ),
                    "entity_id": resolved.get(
                        "entity_id"
                    ),
                },
            }
        }