"""SQLite connection factory and schema bootstrap.

Owns connection creation and `init_db` (table + indexes). Uses the stdlib
`sqlite3` driver. Connections use a Row factory so repository code can map
rows to dicts cleanly.
"""

from __future__ import annotations

import sqlite3

from . import config

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amount     TEXT    NOT NULL,                 -- canonical "0.00" string, > 0
    category   TEXT    NOT NULL,                 -- trimmed, non-empty
    date       TEXT    NOT NULL,                 -- ISO 'YYYY-MM-DD'
    note       TEXT,                             -- nullable, <= 500 chars
    created_at TEXT    NOT NULL                  -- ISO-8601 timestamp
);
"""

CREATE_INDEX_DATE_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);"
)
CREATE_INDEX_CATEGORY_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);"
)


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the expenses table and indexes on `conn` if absent (idempotent).

    Called on every new connection so correctness holds for both file-backed
    and in-memory databases — where each raw connection is otherwise a distinct
    empty database and a one-time init would not be visible to request
    connections. All statements use IF NOT EXISTS, so this is safe to run
    repeatedly.
    """
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_INDEX_DATE_SQL)
    conn.execute(CREATE_INDEX_CATEGORY_SQL)
    conn.commit()


# A shared in-memory database identifier. When DATABASE_PATH is ":memory:",
# each raw sqlite3 ":memory:" connection would be a *separate* empty database,
# so data written by one request would be invisible to the next. Using a
# named shared-cache in-memory URI lets every per-request connection attach to
# the same in-memory DB. One keep-alive connection is held open for the process
# lifetime so the shared in-memory database is not torn down between requests.
_SHARED_MEMORY_URI = "file:expense_tracker_mem?mode=memory&cache=shared"
_keepalive: sqlite3.Connection | None = None


def _resolve(path: str) -> tuple[str, bool]:
    """Map a configured path to (sqlite target, uri_flag).

    ":memory:" is translated to a shared-cache in-memory URI so connections
    share one database; file paths pass through unchanged.
    """
    if path == ":memory:":
        return _SHARED_MEMORY_URI, True
    return path, False


def get_connection(database_path: str | None = None) -> sqlite3.Connection:
    """Create a short-lived SQLite connection with the schema ensured.

    `check_same_thread=False` permits use across the ASGI worker threads; each
    request should still use its own connection and close it. `ensure_schema`
    runs before returning so every connection — file or in-memory — has the
    required table and indexes. In-memory paths are routed through a shared
    in-memory database (see `_resolve`) with a keep-alive connection so data
    persists across the separate per-request connections.
    """
    global _keepalive
    raw_path = database_path if database_path is not None else config.get_database_path()
    target, uri = _resolve(raw_path)

    if uri and _keepalive is None:
        # Hold the shared in-memory DB open for the process lifetime.
        _keepalive = sqlite3.connect(target, check_same_thread=False, uri=True)
        _keepalive.row_factory = sqlite3.Row

    conn = sqlite3.connect(target, check_same_thread=False, uri=uri)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def init_db(database_path: str | None = None) -> None:
    """Create the expenses table and supporting indexes if absent (FR-016).

    Delegates to `ensure_schema`; retained so normal `uvicorn` runs still
    initialize the file-backed DB at startup via the app lifespan handler.
    """
    conn = get_connection(database_path)
    try:
        ensure_schema(conn)
    finally:
        conn.close()


def init_db(database_path: str | None = None) -> None:
    """Create the expenses table and supporting indexes if absent (FR-016).

    Delegates to `ensure_schema`; retained so normal `uvicorn` runs still
    initialize the file-backed DB at startup via the app lifespan handler.
    """
    conn = get_connection(database_path)
    try:
        ensure_schema(conn)
    finally:
        conn.close()
