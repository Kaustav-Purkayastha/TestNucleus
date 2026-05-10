from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Any


class CheckConfig(BaseModel):
    type: str
    params: dict[str, Any] = {}
    nullable: bool = False  # if True, NULL rows are skipped for this check


class FieldTestConfig(BaseModel):
    table: str
    field: str
    checks: list[CheckConfig]


class SuiteConfig(BaseModel):
    suite_name: str
    connection: str
    description: str = ""
    tests: list[FieldTestConfig]

    @field_validator("connection")
    @classmethod
    def connection_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("connection string cannot be empty")
        return v
