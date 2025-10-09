"""FastAPI application entry point."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import crud, schemas
from .database import get_session, init_db

app = FastAPI(title="Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: schemas.CategoryCreate, session=Depends(get_session)
):
    try:
        category = await crud.create_category(session, payload)
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return category


@app.get("/categories", response_model=list[schemas.CategoryRead])
async def list_categories(session=Depends(get_session)):
    return await crud.list_categories(session)


@app.get("/categories/{category_id}", response_model=schemas.CategoryRead)
async def get_category(category_id: int, session=Depends(get_session)):
    category = await crud.get_category(session, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@app.patch("/categories/{category_id}", response_model=schemas.CategoryRead)
async def update_category(
    category_id: int,
    payload: schemas.CategoryUpdate,
    session=Depends(get_session),
):
    try:
        category = await crud.update_category(session, category_id, payload)
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session=Depends(get_session)):
    deleted = await crud.delete_category(session, category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/expenses", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(payload: schemas.ExpenseCreate, session=Depends(get_session)):
    return await crud.create_expense(session, payload)


DateQuery = Annotated[datetime | None, Query(description="Date au format ISO 8601")]


@app.get("/categories/{category_id}/expenses", response_model=list[schemas.ExpenseRead])
async def list_expenses(
    category_id: int,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    session=Depends(get_session),
):
    return await crud.list_expenses_by_category(
        session,
        category_id,
        start_date=start_date,
        end_date=end_date,
    )


@app.get("/expenses", response_model=list[schemas.ExpenseRead])
async def search_expenses(
    category_id: Annotated[int | None, Query()] = None,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    session=Depends(get_session),
):
    return await crud.search_expenses(
        session,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )


@app.patch("/expenses/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense(
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    session=Depends(get_session),
):
    try:
        expense = await crud.update_expense(session, expense_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, session=Depends(get_session)):
    deleted = await crud.delete_expense(session, expense_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/summary", response_model=schemas.MonthlySummary)
async def get_summary(
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    category_id: Annotated[int | None, Query()] = None,
    session=Depends(get_session),
):
    try:
        return await crud.totals_by_period(
            session,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/expenses/export")
async def export_expenses(
    format: Annotated[str, Query(pattern="^(csv|xlsx)$", description="csv ou xlsx")] = "csv",
    category_id: Annotated[int | None, Query()] = None,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    session=Depends(get_session),
):
    try:
        content, media_type, filename = await crud.export_expenses(
            session,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            export_format=format,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)

