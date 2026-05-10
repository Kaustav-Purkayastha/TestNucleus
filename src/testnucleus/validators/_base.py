from __future__ import annotations
import re
from typing import Any

from sqlalchemy import Engine, text

_SAFE_ID = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def q(name: str) -> str:
    """Quote and validate a SQL identifier to prevent injection."""
    if not _SAFE_ID.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return f'"{name}"'


def fetch_scalar(engine: Engine, query: str, params: dict | None = None) -> Any:
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return result.scalar()


def fetch_count(engine: Engine, query: str, params: dict | None = None) -> int:
    value = fetch_scalar(engine, query, params)
    return int(value) if value is not None else 0


def fetch_column(engine: Engine, table: str, field: str) -> list[Any]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {q(field)} FROM {q(table)}"))
        return [row[0] for row in rows.fetchall()]


def fetch_column_non_null(engine: Engine, table: str, field: str) -> list[Any]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {q(field)} FROM {q(table)} WHERE {q(field)} IS NOT NULL"))
        return [row[0] for row in rows.fetchall()]
