from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StockEntity(Base):
    __tablename__ = "stock_entities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # What the user originally typed
    user_input: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # Canonical company information
    canonical_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    exchange: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    finance_query: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    resolution_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    evidence: Mapped[list["EntityEvidence"]] = relationship(
        "EntityEvidence",
        back_populates="entity",
        cascade="all, delete-orphan",
    )


class EntityEvidence(Base):
    __tablename__ = "entity_evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    entity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "stock_entities.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    entity: Mapped["StockEntity"] = relationship(
        "StockEntity",
        back_populates="evidence",
    )