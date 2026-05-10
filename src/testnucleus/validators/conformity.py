from __future__ import annotations
import re
from sqlalchemy import Engine
from ..models.results import CheckStatus
from ._base import q, fetch_count, fetch_column, fetch_column_non_null

ValidatorResult = tuple[CheckStatus, str, dict]

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_PHONE_RE = re.compile(r"^\+?\d{1,4}[\s.\-]?\(?\d{1,3}\)?[\s.\-]?\d{1,4}[\s.\-]?\d{1,9}$")
_URL_RE   = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def _regex_check(
    engine: Engine, table: str, field: str, pattern: re.Pattern, nullable: bool, label: str
) -> ValidatorResult:
    values  = fetch_column_non_null(engine, table, field) if nullable else fetch_column(engine, table, field)
    invalid = [v for v in values if v is not None and not pattern.match(str(v))]
    details = {"invalid_count": len(invalid), "sample": [str(v) for v in invalid[:5]]}
    if not invalid:
        return CheckStatus.PASS, f"All {label} values in {table}.{field} are valid", details
    return CheckStatus.FAIL, f"{len(invalid)} invalid {label} value(s) in {table}.{field}", details


def email_format(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    return _regex_check(engine, table, field, _EMAIL_RE, nullable, "email")


def phone_format(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    return _regex_check(engine, table, field, _PHONE_RE, nullable, "phone")


def url_format(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    return _regex_check(engine, table, field, _URL_RE, nullable, "URL")


def regex_match(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    pattern_str = params.get("pattern")
    if not pattern_str:
        return CheckStatus.ERROR, "regex_match requires a 'pattern' parameter", {}
    return _regex_check(engine, table, field, re.compile(pattern_str), nullable, f"regex({pattern_str})")


def max_length(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    max_len = int(params.get("max", 255))
    count   = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE LENGTH(CAST({q(field)} AS TEXT)) > {max_len}",
    )
    details = {"max_length": max_len, "violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} within length {max_len}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} exceed length {max_len}", details


def min_length(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    min_len = int(params.get("min", 1))
    count   = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL AND LENGTH(CAST({q(field)} AS TEXT)) < {min_len}",
    )
    details = {"min_length": min_len, "violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"All values in {table}.{field} meet minimum length {min_len}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} below minimum length {min_len}", details


def no_trailing_spaces(engine: Engine, table: str, field: str, params: dict, nullable: bool) -> ValidatorResult:
    count = fetch_count(
        engine,
        f"SELECT COUNT(*) FROM {q(table)} WHERE {q(field)} IS NOT NULL AND {q(field)} != TRIM({q(field)})",
    )
    details = {"violating_count": count}
    if count == 0:
        return CheckStatus.PASS, f"No trailing/leading spaces in {table}.{field}", details
    return CheckStatus.FAIL, f"{count} value(s) in {table}.{field} have trailing/leading spaces", details


REGISTRY: dict = {
    "email_format":       email_format,
    "phone_format":       phone_format,
    "url_format":         url_format,
    "regex_match":        regex_match,
    "max_length":         max_length,
    "min_length":         min_length,
    "no_trailing_spaces": no_trailing_spaces,
}
