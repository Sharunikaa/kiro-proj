"""Shared pytest fixtures for the Student Expense Tracker test suite.

Each test gets an isolated, offline SQLite database. We set
``os.environ['DATABASE_PATH']`` to a unique temp file *before* building the
FastAPI app (via ``src.main.create_app``). Routes read the path live through
``config.get_database_path()`` on every request, so a fresh app bound to a
fresh temp DB yields full isolation with no network access.

We prefer a per-test temp *file* over the shared in-memory database because the
in-memory keep-alive connection is a process-global that would otherwise leak
state across tests. A temp file is created fresh per test and discarded by the
``tmp_path`` fixture, guaranteeing isolation. A dedicated test exercises the
file-persistence requirement (FR-016) explicitly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the project root importable so ``import src.*`` resolves when pytest is
# invoked from the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_client(db_path: str) -> TestClient:
    """Build a TestClient bound to a FastAPI app using ``db_path``.

    ``DATABASE_PATH`` is set in the environment before the app is created so
    the schema bootstrap and every per-request connection target this DB.
    """
    os.environ["DATABASE_PATH"] = db_path
    # Import lazily and reload so module-level ``config.DATABASE_PATH`` (read at
    # import time) does not pin a stale path from a previous test.
    import importlib

    from src import config as config_module

    importlib.reload(config_module)
    from src import db as db_module

    importlib.reload(db_module)
    # Reset the in-memory keep-alive so no shared-cache DB leaks across tests.
    db_module._keepalive = None  # type: ignore[attr-defined]
    from src import repository as repo_module

    importlib.reload(repo_module)
    from src import service as service_module

    importlib.reload(service_module)
    from src import routes as routes_module

    importlib.reload(routes_module)
    from src import main as main_module

    importlib.reload(main_module)

    app = main_module.create_app()
    return TestClient(app)


@pytest.fixture
def db_file(tmp_path: Path) -> str:
    """Return a unique temp SQLite file path for one test."""
    return str(tmp_path / "expenses_test.db")


@pytest.fixture
def client(db_file: str):
    """A TestClient backed by an isolated temp-file SQLite DB."""
    with _build_client(db_file) as c:
        yield c


# ---- helpers -------------------------------------------------------------

VALID_EXPENSE = {
    "amount": 12.50,
    "category": "Food",
    "date": "2026-01-15",
}


def make_expense(client, **overrides):
    """POST an expense and return the parsed JSON body (asserts 201)."""
    payload = dict(VALID_EXPENSE)
    payload.update(overrides)
    resp = client.post("/expenses", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()
