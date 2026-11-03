import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "database" / "schema_sqlite.sql"

# app.db creates its global engine at import time. Point it at a throwaway
# database so tests can never touch the real milktea.db, and so TestClient
# can use the normal dependency wiring.
_BOOTSTRAP_DIR = Path(tempfile.mkdtemp(prefix="milktea-test-bootstrap-"))
_BOOTSTRAP_DB = _BOOTSTRAP_DIR / "bootstrap.db"


def _init_schema(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


_init_schema(_BOOTSTRAP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_BOOTSTRAP_DB.as_posix()}"


def _make_session_factory(path: Path):
    engine = create_engine(
        f"sqlite:///{path.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "milktea-test.db"
    _init_schema(path)
    return path


@pytest.fixture()
def session_factory(db_path: Path):
    engine, factory = _make_session_factory(db_path)
    yield factory
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session
