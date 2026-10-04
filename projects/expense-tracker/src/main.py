"""FastAPI application factory.

Creates the app, registers routes and domain-error handlers, and initializes
the SQLite schema via a lifespan handler (FR-016).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .routes import register_exception_handlers, router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the file-backed schema on normal `uvicorn` startup.

    Per-request connections additionally ensure the schema themselves (see
    db.get_connection), so correctness also holds under TestClient and with
    in-memory SQLite where startup events may not fire or are not shared.
    """
    db.init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Student Expense Tracker",
        version="1.0.0",
        description="A simple expense tracking API for students.",
        lifespan=lifespan,
    )

    app.include_router(router)
    register_exception_handlers(app)

    return app


app = create_app()
