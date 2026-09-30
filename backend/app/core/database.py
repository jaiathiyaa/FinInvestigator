from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import setting

engine = create_engine(
    setting.database_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)