"""Application configuration.

Reads settings from environment variables with safe local defaults.
No hardcoded secrets (coding-standards: config via environment).
"""

from __future__ import annotations

import os

# Default to a local SQLite file alongside the project workspace. Overridable
# via the DATABASE_PATH environment variable (FR-016).
DEFAULT_DATABASE_PATH = "expenses.db"


def get_database_path() -> str:
    """Return the SQLite database file path from the environment or default."""
    return os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)


# Convenience module-level value for callers that read it once at import time.
DATABASE_PATH: str = get_database_path()
