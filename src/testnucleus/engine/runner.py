from __future__ import annotations
from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import text

from ..connectors.sql import get_engine
from ..models.config import SuiteConfig
from ..models.results import SuiteResult, CheckResult, CheckStatus
from ..validators import run_check
from ..validators._base import q


def load_config(path: str | Path) -> SuiteConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return SuiteConfig.model_validate(data)


def run_suite(config_path: str | Path) -> SuiteResult:
    config = load_config(config_path)
    engine = get_engine(config.connection)

    # Collect row counts for every table referenced in the config
    table_names = list(dict.fromkeys(ft.table for ft in config.tests))
    table_stats: dict[str, int] = {}
    with engine.connect() as conn:
        for table in table_names:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {q(table)}")).scalar() or 0
                table_stats[table] = int(count)
            except Exception:
                table_stats[table] = 0

    suite_result = SuiteResult(
        suite_name=config.suite_name,
        connection=config.connection,
        started_at=datetime.now(),
        table_stats=table_stats,
    )

    for field_test in config.tests:
        for check in field_test.checks:
            try:
                status, message, details = run_check(
                    engine,
                    field_test.table,
                    field_test.field,
                    check.type,
                    check.params,
                    check.nullable,
                )
            except SQLAlchemyError as exc:
                status  = CheckStatus.ERROR
                message = f"Database error: {exc}"
                details = {}
            except Exception as exc:
                status  = CheckStatus.ERROR
                message = f"Unexpected error: {exc}"
                details = {}

            suite_result.results.append(
                CheckResult(
                    table=field_test.table,
                    field=field_test.field,
                    check_type=check.type,
                    status=status,
                    message=message,
                    details=details,
                )
            )

    suite_result.completed_at = datetime.now()
    engine.dispose()
    return suite_result
