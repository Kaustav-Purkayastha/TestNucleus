from __future__ import annotations
from pydantic import BaseModel, model_validator
from datetime import datetime
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    PASS  = "PASS"
    FAIL  = "FAIL"
    ERROR = "ERROR"


class CheckResult(BaseModel):
    table: str
    field: str
    check_type: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = {}
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def _set_timestamp(self) -> CheckResult:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        return self


class SuiteResult(BaseModel):
    suite_name: str
    connection: str
    started_at: datetime
    completed_at: datetime | None = None
    results: list[CheckResult] = []
    table_stats: dict[str, int] = {}   # table_name -> row count

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.FAIL)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.ERROR)

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total else 0.0
