from __future__ import annotations
from datetime import datetime
from sqlalchemy import Engine, text
from ..models.results import CheckStatus
from ._base import q, fetch_count, fetch_column, fetch_column_non_null

ValidatorResult = tuple[CheckStatus, str, dict]


def min_value(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    min_val = params.get("min", 0)
    count   = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL AND {q(field)} < {min_val}",
    )
    details = {"min": min_val, "violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} >= {min_val}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} below minimum {min_val}", details


def max_value(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    max_val = params.get("max")
    if max_val is None:
        return CheckStatus.ERROR, "max_value requires a 'max' parameter", {}
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL AND {q(field)} > {max_val}",
    )
    details = {"max": max_val, "violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} <= {max_val}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} above maximum {max_val}", details


def between(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    min_val = params.get("min")
    max_val = params.get("max")
    if min_val is None or max_val is None:
        return CheckStatus.ERROR, "between requires 'min' and 'max' parameters", {}
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL "
        f"AND ({q(field)} < {min_val} OR {q(field)} > {max_val})",
    )
    details = {"min": min_val, "max": max_val, "violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} between {min_val} and {max_val}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} outside range [{min_val}, {max_val}]", details


def not_negative(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    return min_value(engine, table, field, {"min": 0}, nullable)


def date_format(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    fmt    = params.get("format", "%Y-%m-%d")
    values = fetch_column_non_null(engine, table, field) if nullable else fetch_column(engine, table, field)
    invalid = []
    for v in values:
        if v is None:
            continue
        try:
            datetime.strptime(str(v), fmt)
        except ValueError:
            invalid.append(str(v))
    details = {"format": fmt, "invalid_count": len(invalid), "sample": invalid[:5]}
    if not invalid:
        return CheckStatus.PASS, f"All dates in {table}.{field} match format '{fmt}'", details
    return CheckStatus.FAIL, f"{len(invalid)} invalid date(s) in {table}.{field} for format '{fmt}'", details


def in_set(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    allowed = params.get("values", [])
    if not allowed:
        return CheckStatus.ERROR, "in_set requires a 'values' list parameter", {}
    placeholders = ", ".join([f":v{i}" for i in range(len(allowed))])
    bind_params  = {f"v{i}": v for i, v in enumerate(allowed)}
    with engine.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL AND {q(field)} NOT IN ({placeholders})"),
            bind_params,
        ).scalar() or 0
    details = {"allowed_values": allowed, "violating_count": int(count)}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} are within the allowed set", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} outside allowed set", details


REGISTRY: dict = {
    "min_value":    min_value,
    "max_value":    max_value,
    "between":      between,
    "not_negative": not_negative,
    "date_format":  date_format,
    "in_set":       in_set,
}
