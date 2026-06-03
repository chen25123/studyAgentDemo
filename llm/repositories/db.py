from collections.abc import Iterator
from contextlib import contextmanager

from pymysql.connections import Connection
from sqlalchemy.engine import Engine

from llm.repositories.database import engine


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine."""
    return engine


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Create a raw DB-API connection from the SQLAlchemy engine.

    This keeps existing repository code working while the project moves toward
    SQLAlchemy sessions and migrations.
    """
    connection = engine.raw_connection()
    try:
        yield connection
    finally:
        connection.close()
