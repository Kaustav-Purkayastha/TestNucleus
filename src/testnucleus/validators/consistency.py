from __future__ import annotations
from sqlalchemy import Engine, text
from ..models.results import CheckStatus
from ._base import q, fetch_count

ValidatorResult = tuple[CheckStatus, str, dict]


def referential_integrity(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    ref_table = params.get("ref_table")
    ref_field = params.get("ref_field")
    if not ref_table or not ref_field:
        return CheckStatus.ERROR, "referential_integrity requires 'ref_table' and 'ref_field' params", {}
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} t "
        f"WHERE t.{q(field)} IS NOT NULL "
        f"AND t.{q(field)} NOT IN (SELECT {q(ref_field)} FROM {q(ref_table)})",
    )
    details = {"ref_table": ref_table, "ref_field": ref_field, "orphan_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All {table}.{field} values exist in {ref_table}.{ref_field}", details
    return CheckStatus.FAIL, f"{count} orphaned value(s) in {table}.{field} (not found in {ref_table}.{ref_field})", details


def no_cross_table_duplicates(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    other_table = params.get("other_table")
    other_field = params.get("other_field", field)
    if not other_table:
        return CheckStatus.ERROR, "no_cross_table_duplicates requires an 'other_table' param", {}
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} t1 "
        f"INNER JOIN {q(other_table)} t2 ON t1.{q(field)} = t2.{q(other_field)}",
    )
    details = {"other_table": other_table, "other_field": other_field, "overlap_count": count}
    if count == 0:
        return (
            CheckStatus.PASS,
            f"No overlapping values between {table}.{field} and {other_table}.{other_field}",
            details,
        )
    return (
        CheckStatus.FAIL,
        f"{count} overlapping value(s) between {table}.{field} and {other_table}.{other_field}",
        details,
    )


REGISTRY: dict = {
    "referential_integrity":       referential_integrity,
    "no_cross_table_duplicates":   no_cross_table_duplicates,
}
