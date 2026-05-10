from __future__ import annotations
from sqlalchemy import Engine
from ..models.results import CheckStatus
from ._base import q, fetch_count

ValidatorResult = tuple[CheckStatus, str, dict]


def unique(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    total    = fetch_count(engine, f"SELECT COUNT({q(field)}) FROM {q(table)}")
    distinct = fetch_count(engine, f"SELECT COUNT(DISTINCT {q(field)}) FROM {q(table)}")
    dupes    = total - distinct
    if dupes == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} are unique", {"total": total}
    return CheckStatus.FAIL, f"{dupes} duplicate value(s) in {table}.{field}", {"duplicates": dupes, "total": total}


def duplicate_count(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    threshold = int(params.get("max_duplicates", 0))
    count = fetch_count(engine, f"SELECT COUNT(*) - COUNT(DISTINCT {q(field)}) FROM {q(table)}")
    details = {"duplicate_count": count, "threshold": threshold}
    if count <= threshold:
        return CheckStatus.PASS, f"Duplicate count {count} within threshold {threshold}", details
    return CheckStatus.FAIL, f"Duplicate count {count} exceeds threshold {threshold}", details


REGISTRY: dict = {
    "unique":           unique,
    "duplicate_count":  duplicate_count,
}
