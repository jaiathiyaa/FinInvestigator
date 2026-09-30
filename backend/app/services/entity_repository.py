from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entity import (
    EntityEvidence,
    StockEntity,
)


def find_cached_entity(
    db: Session,
    user_input: str,
) -> StockEntity | None:

    normalized = user_input.strip().lower()

    result = db.execute(
        select(StockEntity)
        .where(
            StockEntity.user_input
            == normalized
        )
        .order_by(
            StockEntity.updated_at.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


def save_entity(
    db: Session,
    *,
    user_input: str,
    canonical_name: str,
    ticker: str,
    exchange: str,
    confidence: float,
    resolution_method: str,
    evidence: list[dict],
    country: str | None = None,
    currency: str | None = None,
) -> StockEntity:

    normalized_input = (
        user_input.strip().lower()
    )

    finance_query = (
        f"{ticker}:{exchange}"
    )

    entity = StockEntity(
        user_input=normalized_input,
        canonical_name=canonical_name,
        ticker=ticker.upper(),
        exchange=exchange.upper(),
        finance_query=finance_query,
        country=country,
        currency=currency,
        resolution_method=resolution_method,
        confidence=confidence,
        verified_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(entity)

    db.flush()

    for item in evidence:

        evidence_row = EntityEvidence(
            entity_id=entity.id,
            source=item.get(
                "source",
                "unknown",
            ),
            title=item.get("title"),
            url=item.get("url"),
            snippet=item.get("snippet"),
            evidence_type=item.get(
                "evidence_type",
                "entity_resolution",
            ),
        )

        db.add(evidence_row)

    db.commit()

    db.refresh(entity)

    return entity