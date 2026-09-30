# backend/app/services/stock_resolver.py

from typing import Any

from app.core.database import SessionLocal

from app.services.entity_repository import (
    find_cached_entity,
    save_entity,
)

from app.services.entity_validation import (
    select_candidate,
)

from app.services.finance_verifier import (
    verify_finance_entity,
)

from app.services.llm_entity_resolver import (
    resolve_entity_with_llm,
)

from app.services.llm_evidence_extractor import (
    resolve_ticker_from_search_results,
)

from app.services.web_entity_search import (
    extract_candidates,
    search_entity_web,
)


def resolve_stock(
    entity: str,
) -> dict[str, Any]:

    if not entity or not entity.strip():

        raise ValueError(
            "Stock/entity cannot be empty."
        )

    entity = entity.strip()

    db = SessionLocal()

    try:

        # =================================================
        # STEP 1 — DATABASE CACHE
        # =================================================

        cached = find_cached_entity(
            db,
            entity,
        )

        if cached:

            return {
                "input": entity,
                "resolved": True,
                "cached": True,
                "company": cached.canonical_name,
                "ticker": cached.ticker,
                "exchange": cached.exchange,
                "finance_query": (
                    cached.finance_query
                ),
                "resolution_method": (
                    cached.resolution_method
                ),
                "confidence": cached.confidence,
                "entity_id": cached.id,
            }

        # =================================================
        # STEP 2 — LLM COMPANY RESOLUTION
        # =================================================

        try:

            llm_result = (
                resolve_entity_with_llm(
                    entity
                )
            )

        except Exception as exc:

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "error_type": "llm_error",
                "message": str(exc),
            }

        company_name = (
            llm_result.company_name
        )

        if not company_name:

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "message": (
                    "Could not identify "
                    "the company."
                ),
            }

        # =================================================
        # STEP 3 — WEB SEARCH
        # =================================================

        try:

            web_results = (
                search_entity_web(
                    company_name
                )
            )

        except Exception as exc:

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "company": company_name,
                "error_type": (
                    "web_search_error"
                ),
                "message": str(exc),
            }

        # =================================================
        # STEP 4 — REGEX EXTRACTION
        # =================================================

        candidates = (
            extract_candidates(
                web_results
            )
        )

        candidate = (
            select_candidate(
                candidates
            )
        )

        ticker = None
        exchange = None

        candidate_confidence = 0.0

        resolution_method = (
            "web_regex"
        )

        # =================================================
        # STEP 5 — REGEX SUCCESS
        # =================================================

        if candidate:

            ticker = candidate[
                "ticker"
            ]

            exchange = candidate[
                "exchange"
            ]

            candidate_confidence = (
                candidate["confidence"]
            )

        # =================================================
        # STEP 6 — LLM FALLBACK
        # =================================================

        else:

            try:

                llm_evidence_result = (
                    resolve_ticker_from_search_results(
                        company_name=company_name,
                        search_results=web_results,
                    )
                )

            except Exception as exc:

                return {
                    "input": entity,
                    "resolved": False,
                    "cached": False,
                    "company": company_name,
                    "error_type": (
                        "llm_evidence_error"
                    ),
                    "message": str(exc),
                    "web_evidence": web_results,
                }

            ticker = (
                llm_evidence_result.ticker
            )

            exchange = (
                llm_evidence_result.exchange
            )

            candidate_confidence = (
                llm_evidence_result.confidence
            )

            resolution_method = (
                "llm_web_evidence"
            )

            # ---------------------------------------------
            # No ticker
            # ---------------------------------------------

            if not ticker:

                return {
                    "input": entity,
                    "resolved": False,
                    "cached": False,
                    "company": company_name,
                    "resolution_method": (
                        resolution_method
                    ),
                    "confidence": 0.0,
                    "message": (
                        "Could not determine "
                        "a reliable ticker "
                        "from the search evidence."
                    ),
                    "web_evidence": (
                        web_results
                    ),
                    "llm_reasoning": (
                        llm_evidence_result
                        .reasoning
                    ),
                    "evidence_indices": (
                        llm_evidence_result
                        .evidence_indices
                    ),
                }

            # ---------------------------------------------
            # Ticker found but exchange missing
            # ---------------------------------------------

            if not exchange:

                return {
                    "input": entity,
                    "resolved": False,
                    "cached": False,
                    "company": company_name,
                    "ticker": ticker,
                    "exchange": None,
                    "resolution_method": (
                        resolution_method
                    ),
                    "confidence": (
                        candidate_confidence
                    ),
                    "message": (
                        "Ticker was found, "
                        "but exchange could "
                        "not be determined "
                        "from the search "
                        "evidence."
                    ),
                    "web_evidence": (
                        web_results
                    ),
                    "llm_reasoning": (
                        llm_evidence_result
                        .reasoning
                    ),
                    "evidence_indices": (
                        llm_evidence_result
                        .evidence_indices
                    ),
                }

        # =================================================
        # STEP 7 — SERPAPI VERIFICATION
        # =================================================

        verification = (
            verify_finance_entity(
                company_name=company_name,
                ticker=ticker,
                exchange=exchange,
            )
        )

        # =================================================
        # STEP 8 — SERPAPI ERROR
        # =================================================

        if verification.get(
            "error_type"
        ):

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "company": company_name,
                "ticker": ticker,
                "exchange": exchange,
                "finance_query": (
                    f"{ticker}:{exchange}"
                ),
                "resolution_method": (
                    resolution_method
                ),
                "confidence": (
                    candidate_confidence
                ),
                "error_type": (
                    verification[
                        "error_type"
                    ]
                ),
                "retryable": (
                    verification.get(
                        "retryable",
                        False,
                    )
                ),
                "message": (
                    verification[
                        "message"
                    ]
                ),
            }

        # =================================================
        # STEP 9 — VERIFICATION FAILED
        # =================================================

        if not verification.get(
            "verified"
        ):

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "company": company_name,
                "ticker": ticker,
                "exchange": exchange,
                "finance_query": (
                    f"{ticker}:{exchange}"
                ),
                "resolution_method": (
                    resolution_method
                ),
                "confidence": 0.0,
                "message": (
                    "Financial identity "
                    "could not be verified."
                ),
                "web_evidence": (
                    web_results
                ),
            }

        # =================================================
        # STEP 10 — BUILD EVIDENCE
        # =================================================

        evidence = []

        for item in web_results:

            evidence.append(
                {
                    "source": "duckduckgo",
                    "title": item.get(
                        "title"
                    ),
                    "url": item.get(
                        "url"
                    ),
                    "snippet": item.get(
                        "snippet"
                    ),
                    "evidence_type": (
                        "entity_discovery"
                    ),
                }
            )

        # =================================================
        # SERPAPI EVIDENCE
        # =================================================

        evidence.append(
            {
                "source": (
                    "serpapi_google_finance"
                ),
                "title": (
                    "Google Finance "
                    "verification"
                ),
                "url": None,
                "snippet": (
                    f"{ticker}:{exchange} "
                    f"verified for "
                    f"{company_name}"
                ),
                "evidence_type": (
                    "financial_verification"
                ),
            }
        )

        # =================================================
        # STEP 11 — SAVE VERIFIED ENTITY
        # =================================================

        saved = save_entity(
            db,
            user_input=entity,
            canonical_name=(
                verification.get(
                    "company"
                )
                or company_name
            ),
            ticker=(
                verification.get(
                    "ticker"
                )
                or ticker
            ),
            exchange=(
                verification.get(
                    "exchange"
                )
                or exchange
            ),
            confidence=(
                candidate_confidence
            ),
            resolution_method=(
                resolution_method
            ),
            evidence=evidence,
        )

        # =================================================
        # STEP 12 — RETURN
        # =================================================

        return {
            "input": entity,
            "resolved": True,
            "cached": False,
            "company": (
                saved.canonical_name
            ),
            "ticker": saved.ticker,
            "exchange": saved.exchange,
            "finance_query": (
                saved.finance_query
            ),
            "resolution_method": (
                saved.resolution_method
            ),
            "confidence": (
                saved.confidence
            ),
            "entity_id": saved.id,
            "evidence": evidence,
        }

    finally:

        db.close()