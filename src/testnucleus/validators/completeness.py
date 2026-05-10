from __future__ import annotations
from sqlalchemy import Engine
from ..models.results import CheckStatus
from ._base import q, fetch_count

ValidatorResult = tuple[CheckStatus, str, dict]


def not_null(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    count = fetch_count(engine, f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NULL")
    if count == 0:
        return CheckStatus.PASS, f"No NULL values in {table}.{field}", {}
    return CheckStatus.FAIL, f"{count} NULL value(s) found in {table}.{field}", {"null_count": count}


def not_empty(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NULL OR TRIM(CAST({q(field)} AS TEXT)) = ''",
    )
    if count == 0:
        return CheckStatus.PASS, f"No NULL or empty values in {table}.{field}", {}
    return CheckStatus.FAIL, f"{count} NULL/empty value(s) in {table}.{field}", {"empty_count": count}


def completeness_rate(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    threshold = float(params.get("threshold", 95.0))
    non_null = fetch_count(engine, f"SELECT COUNT({q(field)}) FROM {q(table)}")
    total    = fetch_count(engine, f"SELECT COUNT(*) FROM {q(table)}")
    rate     = (non_null / total * 100) if total > 0 else 0.0
    details  = {"rate": round(rate, 2), "threshold": threshold, "non_null": non_null, "total": total}
    if rate >= threshold:
        return CheckStatus.PASS, f"Completeness {rate:.1f}% meets threshold {threshold}%", details
    return CheckStatus.FAIL, f"Completeness {rate:.1f}% below threshold {threshold}%", details


REGISTRY: dict = {
    "not_null":           not_null,
    "not_empty":          not_empty,
    "completeness_rate":  completeness_rate,
}
