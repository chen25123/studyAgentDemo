from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from llm.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models — used by Alembic migrations."""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)
