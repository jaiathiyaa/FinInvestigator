from datetime import datetime
from sqlalchemy import DateTime , String , Text
from sqlalchemy.orm import Mapped , mapped_column
from app.models.base import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id : Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    query : Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )
    