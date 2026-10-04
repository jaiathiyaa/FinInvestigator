from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

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

from app.services.web_entity_search import (
    extract_candidates,
    search_entity_web,
)

from app.services.llm_evidence_extractor import (
    resolve_ticker_from_search_results,
)


# ============================================================
# HELPERS
# ============================================================

def _build_result_from_cached_entity(
    entity: str,
    cached: Any,
    *,
    cached_by: str = "user_input",
) -> dict[str, Any]:
    """
    Convert an existing database entity into the public resolver
    response format.
    """

    return {
        "input": entity,
        "resolved": True,
        "cached": True,
        "cached_by": cached_by,
        "company": cached.canonical_name,
        "ticker": cached.ticker,
        "exchange": cached.exchange,
        "finance_query": cached.finance_query,
        "resolution_method": cached.resolution_method,
        "confidence": cached.confidence,
        "entity_id": cached.id,
    }


def _get_existing_by_finance_query(
    db: Any,
    finance_query: str,
) -> Optional[dict[str, Any]]:
    """
    Look up an already-persisted entity by its unique
    finance_query.

    We intentionally use SQL text here so this resolver does
    not depend on the exact SQLAlchemy model import path.
    """

    if not finance_query:
        return None

    result = db.execute(
        text(
            """
            SELECT
                id,
                canonical_name,
                ticker,
                exchange,
                finance_query,
                resolution_method,
                confidence
            FROM stock_entities
            WHERE finance_query = :finance_query
            LIMIT 1
            """
        ),
        {
            "finance_query": finance_query,
        },
    )

    row = result.mappings().first()

    if not row:
        return None

    return dict(row)


def _build_result_from_existing_row(
    entity: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a raw stock_entities row into the resolver
    response format.
    """

    return {
        "input": entity,
        "resolved": True,
        "cached": True,
        "cached_by": "finance_query",
        "company": row.get(
            "canonical_name"
        ),
        "ticker": row.get(
            "ticker"
        ),
        "exchange": row.get(
            "exchange"
        ),
        "finance_query": row.get(
            "finance_query"
        ),
        "resolution_method": row.get(
            "resolution_method"
        ),
        "confidence": row.get(
            "confidence"
        ),
        "entity_id": row.get(
            "id"
        ),
    }


def _build_entity_evidence(
    web_results: list[dict[str, Any]],
    company_name: str,
    ticker: str,
    exchange: str,
) -> list[dict[str, Any]]:
    """
    Build entity-resolution evidence.
    """

    evidence: list[
        dict[str, Any]
    ] = []

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

    evidence.append(
        {
            "source": (
                "serpapi_google_finance"
            ),
            "title": (
                "Google Finance verification"
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

    return evidence


# ============================================================
# MAIN RESOLVER
# ============================================================

def resolve_stock(
    entity: str,
) -> dict[str, Any]:
    """
    Resolve a company/stock entity into a canonical:

        company
        ticker
        exchange
        finance_query

    Resolution pipeline:

        1. Database cache
        2. LLM entity resolution
        3. Web discovery
        4. Deterministic candidate selection
        5. LLM evidence fallback
        6. Google Finance verification
        7. Duplicate-safe persistence
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not entity or not entity.strip():
        raise ValueError(
            "Stock/entity cannot be empty."
        )

    entity = entity.strip()

    db = SessionLocal()

    try:
        # ====================================================
        # STEP 1 — DATABASE CACHE
        # ====================================================

        cached = find_cached_entity(
            db,
            entity,
        )

        if cached:
            return _build_result_from_cached_entity(
                entity,
                cached,
                cached_by="user_input",
            )

        # ====================================================
        # STEP 2 — LLM ENTITY RESOLUTION
        # ====================================================

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

        # ====================================================
        # STEP 3 — WEB DISCOVERY
        # ====================================================

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

        if not isinstance(
            web_results,
            list,
        ):
            web_results = []

        # ====================================================
        # STEP 4 — DETERMINISTIC CANDIDATE SELECTION
        # ====================================================

        candidates = extract_candidates(
            web_results
        )

        if not isinstance(
            candidates,
            list,
        ):
            candidates = []

        candidate = select_candidate(
            candidates
        )

        ticker: Optional[str] = None
        exchange: Optional[str] = None

        resolution_method = (
            "llm_web"
        )

        candidate_confidence = float(
            getattr(
                llm_result,
                "confidence",
                0.0,
            )
            or 0.0
        )

        if candidate:
            ticker = candidate.get(
                "ticker"
            )

            exchange = candidate.get(
                "exchange"
            )

            candidate_confidence = float(
                candidate.get(
                    "confidence",
                    candidate_confidence,
                )
                or candidate_confidence
            )

            resolution_method = (
                "web_regex"
            )

        # ====================================================
        # STEP 5 — LLM EVIDENCE FALLBACK
        # ====================================================

        if not ticker or not exchange:

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
                }

            ticker = (
                llm_evidence_result.ticker
            )

            exchange = (
                llm_evidence_result.exchange
            )

            candidate_confidence = float(
                getattr(
                    llm_evidence_result,
                    "confidence",
                    candidate_confidence,
                )
                or candidate_confidence
            )

            if not ticker:
                return {
                    "input": entity,
                    "resolved": False,
                    "cached": False,
                    "company": company_name,
                    "resolution_method": (
                        "llm_web_evidence"
                    ),
                    "confidence": 0.0,
                    "message": (
                        "Could not determine "
                        "a reliable ticker from "
                        "the search evidence."
                    ),
                    "web_evidence": web_results,
                }

            if not exchange:
                return {
                    "input": entity,
                    "resolved": False,
                    "cached": False,
                    "company": company_name,
                    "ticker": ticker,
                    "exchange": None,
                    "resolution_method": (
                        "llm_web_evidence"
                    ),
                    "confidence": candidate_confidence,
                    "message": (
                        "Ticker was found, "
                        "but the exchange could "
                        "not be determined."
                    ),
                    "web_evidence": web_results,
                    "llm_reasoning": getattr(
                        llm_evidence_result,
                        "reasoning",
                        None,
                    ),
                    "evidence_indices": getattr(
                        llm_evidence_result,
                        "evidence_indices",
                        [],
                    ),
                }

            resolution_method = (
                "llm_web_evidence"
            )

        # ====================================================
        # STEP 6 — NORMALIZE TICKER / EXCHANGE
        # ====================================================

        ticker = str(
            ticker
        ).strip().upper()

        exchange = str(
            exchange
        ).strip().upper()

        if not ticker or not exchange:
            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "company": company_name,
                "message": (
                    "Ticker and exchange "
                    "are required."
                ),
            }

        finance_query = (
            f"{ticker}:{exchange}"
        )

        # ====================================================
        # STEP 7 — CHECK UNIQUE KEY BEFORE EXPENSIVE SAVE
        # ====================================================

        existing_row = (
            _get_existing_by_finance_query(
                db,
                finance_query,
            )
        )

        if existing_row:
            print(
                "[Stock Resolver] Existing "
                f"entity found for "
                f"{finance_query}"
            )

            return (
                _build_result_from_existing_row(
                    entity,
                    existing_row,
                )
            )

        # ====================================================
        # STEP 8 — GOOGLE FINANCE VERIFICATION
        # ====================================================

        verification = (
            verify_finance_entity(
                company_name=company_name,
                ticker=ticker,
                exchange=exchange,
            )
        )

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
                "finance_query": finance_query,
                "resolution_method": (
                    resolution_method
                ),
                "confidence": candidate_confidence,
                "error_type": verification[
                    "error_type"
                ],
                "retryable": verification.get(
                    "retryable",
                    False,
                ),
                "message": verification[
                    "message"
                ],
            }

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
                "finance_query": finance_query,
                "resolution_method": (
                    resolution_method
                ),
                "confidence": 0.0,
                "message": (
                    "Financial identity "
                    "could not be verified."
                ),
                "web_evidence": web_results,
            }

        # ====================================================
        # STEP 9 — USE VERIFIED VALUES
        # ====================================================

        verified_company = (
            verification.get(
                "company"
            )
            or company_name
        )

        verified_ticker = (
            verification.get(
                "ticker"
            )
            or ticker
        )

        verified_exchange = (
            verification.get(
                "exchange"
            )
            or exchange
        )

        verified_ticker = str(
            verified_ticker
        ).strip().upper()

        verified_exchange = str(
            verified_exchange
        ).strip().upper()

        verified_finance_query = (
            f"{verified_ticker}:"
            f"{verified_exchange}"
        )

        # ====================================================
        # STEP 10 — CHECK AGAIN AFTER VERIFICATION
        #
        # This protects against another process inserting
        # the same entity while Google Finance verification
        # was running.
        # ====================================================

        existing_row = (
            _get_existing_by_finance_query(
                db,
                verified_finance_query,
            )
        )

        if existing_row:
            print(
                "[Stock Resolver] Entity "
                "already persisted by another "
                "request: "
                f"{verified_finance_query}"
            )

            return (
                _build_result_from_existing_row(
                    entity,
                    existing_row,
                )
            )

        # ====================================================
        # STEP 11 — BUILD EVIDENCE
        # ====================================================

        evidence = _build_entity_evidence(
            web_results=web_results,
            company_name=verified_company,
            ticker=verified_ticker,
            exchange=verified_exchange,
        )

        confidence = max(
            candidate_confidence,
            float(
                getattr(
                    llm_result,
                    "confidence",
                    0.0,
                )
                or 0.0
            ),
        )

        # ====================================================
        # STEP 12 — SAVE VERIFIED ENTITY
        # ====================================================

        try:
            saved = save_entity(
                db,
                user_input=entity,
                canonical_name=verified_company,
                ticker=verified_ticker,
                exchange=verified_exchange,
                confidence=confidence,
                resolution_method=(
                    resolution_method
                ),
                evidence=evidence,
            )

        except IntegrityError as exc:
            """
            Race-condition protection.

            Another request may have inserted the same
            finance_query after our pre-check but before
            save_entity().
            """

            db.rollback()

            print(
                "[Stock Resolver] Duplicate "
                "finance_query detected during "
                f"save: {verified_finance_query}"
            )

            existing_row = (
                _get_existing_by_finance_query(
                    db,
                    verified_finance_query,
                )
            )

            if existing_row:
                return (
                    _build_result_from_existing_row(
                        entity,
                        existing_row,
                    )
                )

            return {
                "input": entity,
                "resolved": False,
                "cached": False,
                "company": verified_company,
                "ticker": verified_ticker,
                "exchange": verified_exchange,
                "finance_query": (
                    verified_finance_query
                ),
                "error_type": (
                    "entity_persistence_error"
                ),
                "message": (
                    "The entity could not be "
                    "persisted because of a "
                    "database integrity conflict."
                ),
                "details": str(exc),
            }

        # ====================================================
        # STEP 13 — RETURN
        # ====================================================

        return {
            "input": entity,
            "resolved": True,
            "cached": False,
            "company": saved.canonical_name,
            "ticker": saved.ticker,
            "exchange": saved.exchange,
            "finance_query": saved.finance_query,
            "resolution_method": saved.resolution_method,
            "confidence": saved.confidence,
            "entity_id": saved.id,
            "evidence": evidence,
        }

    finally:
        db.close()


__all__ = [
    "resolve_stock",
]