"""CRUD operations for categories and expenses."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
import csv
import io
from enum import Enum
from typing import Literal

from openpyxl import Workbook

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import selectinload

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas


class CategoryNameConflictError(Exception):
    """Raised when trying to create a category with a duplicate name."""


async def _load_category_map(session: AsyncSession) -> dict[int, tuple[str, int | None]]:
    rows = await session.execute(
        select(models.Category.id, models.Category.name, models.Category.parent_id)
    )
    return {row.id: (row.name, row.parent_id) for row in rows.all()}


def _build_category_path_from_map(
    category_id: int | None, category_map: dict[int, tuple[str, int | None]]
) -> str:
    if category_id is None:
        return "Non classé"

    parts: list[str] = []
    current_id: int | None = category_id
    visited: set[int] = set()

    while current_id is not None and current_id not in visited:
        visited.add(current_id)
        entry = category_map.get(current_id)
        if entry is None:
            break
        name, parent_id = entry
        parts.append(name)
        current_id = parent_id

    return " / ".join(reversed(parts)) if parts else "Non classé"


async def create_category(session: AsyncSession, category: schemas.CategoryCreate) -> models.Category:
    data = category.model_dump()
    if data.get("parent_id") is not None and data["parent_id"] == data.get("id"):
        data["parent_id"] = None
    db_category = models.Category(**data)
    session.add(db_category)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - depends on DB backend
        raise CategoryNameConflictError("Category name already exists") from exc
    await session.refresh(db_category)
    await session.refresh(db_category, attribute_names=["parent"])
    category_map = await _load_category_map(session)
    setattr(
        db_category,
        "full_path",
        _build_category_path_from_map(db_category.id, category_map),
    )
    return db_category


async def list_categories(session: AsyncSession) -> Sequence[models.Category]:
    result = await session.execute(
        select(models.Category)
        .options(
            selectinload(models.Category.parent),
            selectinload(models.Category.children),
        )
        .order_by(models.Category.name)
    )
    categories = result.scalars().unique().all()
    category_map = {category.id: (category.name, category.parent_id) for category in categories}
    for category in categories:
        setattr(
            category,
            "full_path",
            _build_category_path_from_map(category.id, category_map),
        )

    # Retourner un arbre (racines uniquement), avec children peuplés
    id_to_node = {c.id: c for c in categories}
    roots: list[models.Category] = []
    for c in categories:
        if c.parent_id and c.parent_id in id_to_node:
            # la relation children est déjà chargée via selectinload, mais on s'assure
            parent = id_to_node[c.parent_id]
            if c not in parent.children:
                parent.children.append(c)
        else:
            roots.append(c)
    return roots


def _build_category_path(category: models.Category) -> str:
    parts = [category.name]
    current = category.parent
    while current is not None:
        parts.append(current.name)
        current = current.parent
    return " / ".join(reversed(parts))


async def get_category(session: AsyncSession, category_id: int) -> models.Category | None:
    result = await session.execute(
        select(models.Category)
        .options(
            selectinload(models.Category.parent),
        )
        .where(models.Category.id == category_id)
    )
    category = result.scalars().first()
    if category is None:
        return None

    category_map = await _load_category_map(session)
    setattr(
        category,
        "full_path",
        _build_category_path_from_map(category.id, category_map),
    )
    return category


async def update_category(
    session: AsyncSession, category_id: int, payload: schemas.CategoryUpdate
) -> models.Category | None:
    category = await session.get(models.Category, category_id)
    if category is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    if "parent_id" in data and data["parent_id"] == category_id:
        data["parent_id"] = None
    for field, value in data.items():
        setattr(category, field, value)

    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - depends on DB backend
        raise CategoryNameConflictError("Category name already exists") from exc

    await session.refresh(category)
    await session.refresh(category, attribute_names=["parent"])
    category_map = await _load_category_map(session)
    setattr(
        category,
        "full_path",
        _build_category_path_from_map(category.id, category_map),
    )
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    category = await session.get(models.Category, category_id)
    if category is None:
        return False
    await session.delete(category)
    return True


async def create_expense(session: AsyncSession, expense: schemas.ExpenseCreate) -> models.Expense:
    payload = expense.model_dump(exclude_none=True)
    if "created_at" in payload and payload["created_at"] is None:
        payload.pop("created_at")
    db_expense = models.Expense(**payload)
    session.add(db_expense)
    await session.flush()
    await session.refresh(db_expense)
    await session.refresh(db_expense, attribute_names=["category"])
    category_map = await _load_category_map(session)
    setattr(
        db_expense,
        "category_path",
        _build_category_path_from_map(db_expense.category_id, category_map),
    )
    return db_expense


async def list_expenses_by_category(
    session: AsyncSession,
    category_id: int,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Sequence[models.Expense]:
    query = (
        select(models.Expense)
        .options(
            selectinload(models.Expense.category).selectinload(models.Category.parent),
        )
        .where(models.Expense.category_id == category_id)
    )

    if start_date is not None:
        query = query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        query = query.where(models.Expense.created_at <= end_date)

    result = await session.execute(query.order_by(models.Expense.created_at.desc()))
    expenses = result.scalars().all()
    category_map = await _load_category_map(session)
    for expense in expenses:
        setattr(
            expense,
            "category_path",
            _build_category_path_from_map(expense.category_id, category_map),
        )
    return expenses


async def search_expenses(
    session: AsyncSession,
    *,
    category_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> Sequence[models.Expense]:
    query = (
        select(models.Expense)
        .options(
            selectinload(models.Expense.category).selectinload(models.Category.parent),
        )
        .order_by(models.Expense.created_at.desc())
    )

    if category_id is not None:
        query = query.where(models.Expense.category_id == category_id)
    if start_date is not None:
        query = query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        query = query.where(models.Expense.created_at <= end_date)

    result = await session.execute(query)
    expenses = result.scalars().all()
    category_map = await _load_category_map(session)
    for expense in expenses:
        setattr(
            expense,
            "category_path",
            _build_category_path_from_map(expense.category_id, category_map),
        )
    return expenses


async def get_expense(session: AsyncSession, expense_id: int) -> models.Expense | None:
    return await session.get(models.Expense, expense_id)


async def update_expense(
    session: AsyncSession, expense_id: int, payload: schemas.ExpenseUpdate
) -> models.Expense | None:
    expense = await session.get(models.Expense, expense_id)
    if expense is None:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data and data["category_id"] is not None:
        category = await session.get(models.Category, data["category_id"])
        if category is None:
            raise ValueError("Category not found")

    if data.get("created_at") is None:
        data.pop("created_at", None)

    for field, value in data.items():
        setattr(expense, field, value)

    await session.flush()
    await session.refresh(expense)
    await session.refresh(expense, attribute_names=["category"])
    category_map = await _load_category_map(session)
    setattr(
        expense,
        "category_path",
        _build_category_path_from_map(expense.category_id, category_map),
    )
    return expense


async def delete_expense(session: AsyncSession, expense_id: int) -> bool:
    expense = await session.get(models.Expense, expense_id)
    if expense is None:
        return False
    await session.delete(expense)
    return True


def _resolve_date_range(
    start_date: datetime | None, end_date: datetime | None
) -> tuple[datetime, datetime]:
    now = datetime.utcnow()

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date must be before end_date")

    if start_date is None and end_date is None:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif start_date is None:
        start_date = end_date
    elif end_date is None:
        end_date = start_date

    return start_date, end_date


async def totals_by_period(
    session: AsyncSession,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
) -> schemas.MonthlySummary:
    start_date, end_date = _resolve_date_range(start_date, end_date)

    total_case = case(
        (
            and_(
                models.Expense.created_at >= start_date,
                models.Expense.created_at <= end_date,
            ),
            models.Expense.amount,
        ),
        else_=0.0,
    )

    query = (
        select(
            models.Category.id,
            func.coalesce(func.sum(total_case), 0.0),
        )
        .outerjoin(models.Expense, models.Expense.category_id == models.Category.id)
        .group_by(models.Category.id)
        .order_by(models.Category.name)
    )

    if category_id is not None:
        query = query.where(models.Category.id == category_id)

    result = await session.execute(query)
    totals = result.all()
    category_map = await _load_category_map(session)

    category_totals = {
        _build_category_path_from_map(category_id, category_map): float(total)
        for category_id, total in totals
    }
    overall_total = float(sum(category_totals.values()))

    if start_date.date() == end_date.date():
        period_label = start_date.strftime("%Y-%m-%d")
    else:
        period_label = f"{start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}"

    return schemas.MonthlySummary(
        month=period_label,
        total=overall_total,
        category_totals=category_totals,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
    )


async def export_expenses(
    session: AsyncSession,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
    export_format: Literal["csv", "xlsx"] = "csv",
) -> tuple[bytes, str, str]:
    start_date, end_date = _resolve_date_range(start_date, end_date)

    expenses = await search_expenses(
        session,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )

    category_map = await _load_category_map(session)

    grouped: dict[str, list[models.Expense]] = {}
    for expense in expenses:
        path = _build_category_path_from_map(expense.category_id, category_map)
        grouped.setdefault(path, []).append(expense)

    category_totals = {name: float(sum(exp.amount for exp in items)) for name, items in grouped.items()}
    overall_total = float(sum(category_totals.values()))

    headers = ["Catégorie", "ID", "Montant", "Note", "Date"]

    if export_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Résumé"])
        for name, total in category_totals.items():
            writer.writerow([name, f"{total:.2f} €"])
        writer.writerow(["Total", f"{overall_total:.2f} €"])
        writer.writerow([])
        writer.writerow(headers)
        for name, items in grouped.items():
            for expense in items:
                writer.writerow(
                    [
                        name,
                        expense.id,
                        f"{expense.amount:.2f}",
                        expense.note or "",
                        expense.created_at.isoformat() if expense.created_at else "",
                    ]
                )
        content = buffer.getvalue().encode("utf-8")
        filename = "expenses.csv"
        media_type = "text/csv"
    else:
        workbook = Workbook()
        summary_sheet = workbook.active
        summary_sheet.title = "Résumé"
        summary_sheet.append(["Catégorie", "Total (€)"])
        for name, total in category_totals.items():
            summary_sheet.append([name, float(total)])
        summary_sheet.append(["Total", overall_total])

        detail_sheet = workbook.create_sheet("Détails")
        detail_sheet.append(headers)
        for name, items in grouped.items():
            for expense in items:
                detail_sheet.append(
                    [
                        name,
                        expense.id,
                        float(expense.amount),
                        expense.note or "",
                        expense.created_at.isoformat() if expense.created_at else "",
                    ]
                )

        bytes_buffer = io.BytesIO()
        workbook.save(bytes_buffer)
        content = bytes_buffer.getvalue()
        filename = "expenses.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return content, media_type, filename

