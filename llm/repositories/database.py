from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from llm.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_session() -> Iterator[Session]:
    """Yield a database session and always close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
