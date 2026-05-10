from __future__ import annotations
from . import completeness, conformity, consistency, uniqueness, validity
from ..models.results import CheckStatus

_MODULES = [completeness, conformity, consistency, uniqueness, validity]

REGISTRY: dict = {}
for _mod in _MODULES:
    REGISTRY.update(_mod.REGISTRY)


def run_check(
    engine,
    table: str,
    field: str,
    check_type: str,
    params: dict,
    nullable: bool,
) -> tuple[CheckStatus, str, dict]:
    validator = REGISTRY.get(check_type)
    if validator is None:
        return CheckStatus.ERROR, f"Unknown check type: '{check_type}'. Run 'testnucleus list-checks' to see available checks.", {}
    return validator(engine, table, field, params, nullable)


__all__ = ["REGISTRY", "run_check"]
