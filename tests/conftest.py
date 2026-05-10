import sqlite3
import pytest
from sqlalchemy import create_engine, Engine


@pytest.fixture(scope="session")
def sample_engine(tmp_path_factory) -> Engine:
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            email TEXT,
            age   INTEGER,
            name  TEXT,
            score DECIMAL(5,2)
        );
        INSERT INTO users VALUES (1, 'alice@example.com',  30, 'Alice',   95.5);
        INSERT INTO users VALUES (2, 'bob@example.com',    -5, 'Bob  ',   80.0);
        INSERT INTO users VALUES (3, NULL,                 25, 'Charlie', 70.0);
        INSERT INTO users VALUES (4, 'invalid-email',      40, 'Dave',    60.0);
        INSERT INTO users VALUES (5, 'alice@example.com',  28, 'Eve',     55.0);
    """)
    conn.commit()
    conn.close()
    return create_engine(f"sqlite:///{db_path}")
