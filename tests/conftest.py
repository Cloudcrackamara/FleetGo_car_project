
"""Test fixtures. A TEST database, never the real one.

Each test runs inside a transaction that's rolled back afterward —
so tests can't leak data into each other or into your real dev DB.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.db.session import get_session
from app.main import app


@pytest.fixture(scope="session")
def engine():
    url = settings.test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    if url == settings.database_url:
        pytest.fail("TEST_DATABASE_URL must not point at the real database")
    admin_url = url.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, pool_pre_ping=True)
    with admin_engine.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        db_name = url.rsplit("/", 1)[1]
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        ).scalar()
        if exists is None:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()
    eng = create_engine(url, pool_pre_ping=True)
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def session(db) -> Session:
    return db


@pytest.fixture
def client(db) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
