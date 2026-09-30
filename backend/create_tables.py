from app.core.database import engine
from app.models import Base

# Import models so SQLAlchemy knows about them.
from app.models.entity import (
    StockEntity,
    EntityEvidence,
)


def main():
    Base.metadata.create_all(
        bind=engine
    )

    print("Database tables created successfully.")


if __name__ == "__main__":
    main()