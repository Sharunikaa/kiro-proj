"""HTTP routes: the six endpoints and domain-error exception handlers.

Routes validate shape via Pydantic (automatic 422), call the service with
validated values, and serialize results via response schemas. Domain errors
are mapped to HTTP status codes:
  NotFoundError        -> 404
  DomainValidationError -> 422
"""

from __future__ import annotations

from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, Query, Response, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from . import db, service
from .errors import DomainValidationError, NotFoundError
from .schemas import ExpenseIn, ExpenseOut, MonthlySummaryOut

router = APIRouter()


def get_conn():
    """Per-request SQLite connection dependency; closed after the request."""
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseIn, conn=Depends(get_conn)) -> ExpenseOut:
    record = service.create_expense(
        conn,
        amount=payload.amount,
        category=payload.category,
        date=payload.date,
        note=payload.note,
    )
    return ExpenseOut(**record)


@router.get("/expenses/{expense_id}", response_model=ExpenseOut, status_code=status.HTTP_200_OK)
def get_expense(expense_id: int, conn=Depends(get_conn)) -> ExpenseOut:
    record = service.get_expense(conn, expense_id)
    return ExpenseOut(**record)


@router.get("/expenses", response_model=list[ExpenseOut], status_code=status.HTTP_200_OK)
def list_expenses(
    conn=Depends(get_conn),
    category: Optional[str] = Query(default=None),
    start_date: Optional[date_type] = Query(default=None),
    end_date: Optional[date_type] = Query(default=None),
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None, ge=1, le=12),
) -> list[ExpenseOut]:
    records = service.list_expenses(
        conn,
        category=category,
        start_date=start_date,
        end_date=end_date,
        year=year,
        month=month,
    )
    return [ExpenseOut(**r) for r in records]


@router.put("/expenses/{expense_id}", response_model=ExpenseOut, status_code=status.HTTP_200_OK)
def update_expense(expense_id: int, payload: ExpenseIn, conn=Depends(get_conn)) -> ExpenseOut:
    record = service.update_expense(
        conn,
        expense_id,
        amount=payload.amount,
        category=payload.category,
        date=payload.date,
        note=payload.note,
    )
    return ExpenseOut(**record)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, conn=Depends(get_conn)) -> Response:
    service.delete_expense(conn, expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary/monthly", response_model=MonthlySummaryOut, status_code=status.HTTP_200_OK)
def monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    conn=Depends(get_conn),
) -> MonthlySummaryOut:
    summary = service.monthly_summary(conn, year=year, month=month)
    return MonthlySummaryOut(**summary)


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain errors to HTTP responses with a consistent body (FR-017)."""

    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainValidationError)
    async def _domain_validation(
        request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message},
        )
