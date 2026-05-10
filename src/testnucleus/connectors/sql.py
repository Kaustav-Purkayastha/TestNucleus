from __future__ import annotations
import os
import re

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

load_dotenv()

_ENV_VAR = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(connection_string: str) -> str:
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        value = os.environ.get(key)
        if value is None:
            raise ValueError(f"Environment variable '{key}' is not set (referenced in connection string)")
        return value

    return _ENV_VAR.sub(_replace, connection_string)


def get_engine(connection_string: str) -> Engine:
    """Return a SQLAlchemy Engine, resolving ${ENV_VAR} placeholders from the environment."""
    resolved = _resolve_env_vars(connection_string)
    return create_engine(resolved)
