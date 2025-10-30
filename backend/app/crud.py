"""CRUD operations for categories and expenses."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
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
from .database import get_session


class CategoryNameConflictError(Exception):
    """Raised when trying to create a category with a duplicate name."""


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists."""


async def create_user(session: AsyncSession, user: schemas.UserCreate) -> models.User:
    """Create a new user."""
    # Vérifier si l'utilisateur existe déjà
    existing_user = await session.execute(
        select(models.User).where(
            (models.User.username == user.username) | (models.User.email == user.email)
        )
    )
    if existing_user.first():
        raise UserAlreadyExistsError("Username or email already exists")

    from .auth import hash_password
    hashed_password = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    # Invalider le cache pour ce nouvel utilisateur (par précaution)
    from .cache import invalidate
    invalidate(f"user:{user.username}")
    
    return db_user


async def get_user_by_username(session: AsyncSession, username: str) -> models.User | None:
    """Get a user by username with caching for better performance.
    
    Optimized to only select necessary fields for login, reducing DB load.
    """
    from .cache import get as cache_get, set as cache_set
    
    # Vérifier le cache d'abord (TTL de 5 minutes pour les données utilisateur)
    cache_key = f"user:{username}"
    cached_data = cache_get(cache_key)
    
    if cached_data:
        # Reconstruire l'objet User depuis les données en cache
        # Cela évite une requête DB si les données sont encore valides
        user = models.User(
            id=cached_data['id'],
            username=cached_data['username'],
            email=cached_data['email'],
            hashed_password=cached_data['hashed_password'],
            is_active=cached_data['is_active'],
            created_at=cached_data['created_at']
        )
        return user
    
    # Requête DB optimisée: ne sélectionner que les champs nécessaires pour le login
    # Cela réduit la quantité de données transférées depuis la DB
    result = await session.execute(
        select(
            models.User.id,
            models.User.username,
            models.User.email,
            models.User.hashed_password,
            models.User.is_active,
            models.User.created_at
        ).where(models.User.username == username)
    )
    row = result.first()
    
    if not row:
        return None
    
    # Reconstruire l'objet User depuis les résultats de la requête
    user = models.User(
        id=row.id,
        username=row.username,
        email=row.email,
        hashed_password=row.hashed_password,
        is_active=row.is_active,
        created_at=row.created_at
    )
    
    # Mettre en cache les données utilisateur (TTL de 5 minutes)
    # Les données utilisateur changent rarement, donc un cache long est acceptable
    cache_set(cache_key, {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'hashed_password': user.hashed_password,
        'is_active': user.is_active,
        'created_at': user.created_at
    }, ttl=300)  # 5 minutes
    
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> models.User | None:
    """Get a user by ID."""
    return await session.get(models.User, user_id)


async def _load_category_map(session: AsyncSession, user_id: int | None = None) -> dict[int, tuple[str, int | None]]:
    query = select(models.Category.id, models.Category.name, models.Category.parent_id)
    if user_id is not None:
        query = query.where(models.Category.user_id == user_id)
    rows = await session.execute(query)
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


async def create_category(session: AsyncSession, category: schemas.CategoryCreate, user_id: int) -> models.Category:
    """Create a new category for a user.
    
    Ensures category name uniqueness per user (not globally).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    data = category.model_dump()
    if data.get("parent_id") is not None and data["parent_id"] == data.get("id"):
        data["parent_id"] = None
    
    # Normaliser parent_id : convertir 0, "0", ou valeurs invalides en None
    # Cela peut arriver si le frontend envoie des valeurs invalides
    parent_id_raw = data.get("parent_id")
    if parent_id_raw is None or parent_id_raw == 0 or parent_id_raw == "0" or parent_id_raw == "":
        parent_id = None
        data["parent_id"] = None
    else:
        try:
            parent_id = int(parent_id_raw)
            data["parent_id"] = parent_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid parent_id value: {parent_id_raw}, setting to None")
            parent_id = None
            data["parent_id"] = None
    category_name = data["name"].strip().lower()  # Normaliser le nom (supprimer les espaces, minuscules)
    original_name = data["name"].strip()  # Garder le nom original pour l'affichage
    
    logger.info(f"Creating category: user_id={user_id}, name='{original_name}', parent_id={parent_id}")
    
    try:
        # IMPORTANT: Vérifier d'abord s'il existe vraiment des catégories pour cet utilisateur
        # Cela aide à déboguer les problèmes sur Render/PostgreSQL
        all_user_categories_query = select(models.Category).where(
            models.Category.user_id == user_id
        )
        all_user_categories_result = await session.execute(all_user_categories_query)
        all_user_categories = all_user_categories_result.scalars().all()
        
        logger.info(f"Total categories for user_id={user_id}: {len(all_user_categories)}")
        if all_user_categories:
            # Convertir les objets en tuples simples pour éviter les problèmes de sérialisation dans les logs
            try:
                categories_info = [(c.id, c.name, c.parent_id, c.user_id) for c in all_user_categories]
                logger.info(f"All user categories: {categories_info}")
            except Exception as log_err:
                logger.warning(f"Could not log categories details: {log_err}")
        
        # Récupérer les catégories de l'utilisateur avec le même parent_id
        # Utiliser une approche plus explicite pour PostgreSQL
        if parent_id is None:
            # Pour parent_id NULL, utiliser IS NULL explicitement
            existing_query = select(models.Category).where(
                models.Category.user_id == user_id,
                models.Category.parent_id.is_(None)
            )
        else:
            # Pour parent_id spécifique, utiliser l'égalité
            existing_query = select(models.Category).where(
                models.Category.user_id == user_id,
                models.Category.parent_id == parent_id
            )
        
        existing_categories_result = await session.execute(existing_query)
        all_existing = existing_categories_result.scalars().all()
        
        logger.info(f"Found {len(all_existing)} existing categories for user_id={user_id} with parent_id={parent_id}")
        
        # Log toutes les catégories trouvées pour débogage
        if all_existing:
            # Convertir les objets en tuples simples pour éviter les problèmes de sérialisation dans les logs
            try:
                existing_info = [(c.id, c.name, c.parent_id, c.user_id) for c in all_existing]
                logger.info(f"Existing categories with same parent_id: {existing_info}")
            except Exception as log_err:
                logger.warning(f"Could not log existing categories details: {log_err}")
        
        # Vérifier manuellement si une catégorie avec le même nom (normalisé) existe
        # DOUBLE CHECK: Vérifier aussi que le user_id correspond bien
        for existing in all_existing:
            # Sécurité supplémentaire : vérifier que le user_id correspond
            if existing.user_id != user_id:
                logger.error(f"CRITICAL: Found category with wrong user_id! category_id={existing.id}, category_user_id={existing.user_id}, expected_user_id={user_id}")
                continue  # Ignorer cette catégorie car elle ne devrait pas être là
            
            existing_name_normalized = existing.name.strip().lower()
            logger.debug(f"Comparing: '{existing_name_normalized}' == '{category_name}' for category_id={existing.id}")
            if existing_name_normalized == category_name:
                logger.warning(
                    f"Category conflict detected: user_id={user_id}, name='{original_name}', "
                    f"existing_id={existing.id}, existing_name='{existing.name}', "
                    f"existing_parent_id={existing.parent_id}, existing_user_id={existing.user_id}"
                )
                raise CategoryNameConflictError(
                    f"Category name '{original_name}' already exists"
                )
        
        logger.info(f"No conflict found for user_id={user_id}, name='{original_name}', proceeding with creation")
    except CategoryNameConflictError:
        # Re-raise les erreurs de conflit directement
        raise
    except Exception as check_err:
        # Log mais continuer - la vérification a échoué mais on peut quand même essayer de créer
        logger.error(f"Error during category check: {check_err}", exc_info=True)
        # Ne pas bloquer la création si la vérification échoue
        # On fait confiance à la contrainte d'intégrité de la DB
    
    # Utiliser le nom normalisé (mais garder la casse originale)
    data["name"] = original_name
    db_category = models.Category(**data, user_id=user_id)
    
    # IMPORTANT: S'assurer que user_id est bien défini avant l'ajout
    # Double vérification pour éviter les problèmes sur Render/PostgreSQL
    if db_category.user_id != user_id:
        logger.error(f"CRITICAL: Category user_id mismatch! Got {db_category.user_id}, expected {user_id}")
        db_category.user_id = user_id
    
    session.add(db_category)
    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - depends on DB backend
        # Fallback si la vérification explicite n'a pas fonctionné
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        logger.error(f"IntegrityError during category creation: {error_msg}", exc_info=True)
        
        # Vérifier une dernière fois si la catégorie existe vraiment
        # Cela peut arriver en cas de race condition sur Render avec plusieurs instances
        # Utiliser une comparaison simple sans func.lower pour éviter les problèmes de compatibilité
        try:
            final_check_query = select(models.Category).where(
                models.Category.user_id == user_id
            )
            if parent_id is None:
                final_check_query = final_check_query.where(models.Category.parent_id.is_(None))
            else:
                final_check_query = final_check_query.where(models.Category.parent_id == parent_id)
            
            final_check_result = await session.execute(final_check_query)
            final_check_categories = final_check_result.scalars().all()
            
            # Comparer manuellement en Python
            for check_cat in final_check_categories:
                if check_cat.name.strip().lower() == category_name:
                    raise CategoryNameConflictError(
                        f"Category name '{original_name}' already exists (detected during insert)"
                    )
        except CategoryNameConflictError:
            raise
        except Exception as check_exc:
            logger.error(f"Error during final check: {check_exc}", exc_info=True)
        
        # Si on arrive ici, l'erreur d'intégrité vient d'autre chose
        raise CategoryNameConflictError("Category name already exists") from exc
    
    try:
        await session.refresh(db_category)
        await session.refresh(db_category, attribute_names=["parent"])
        category_map = await _load_category_map(session, user_id)
        setattr(
            db_category,
            "full_path",
            _build_category_path_from_map(db_category.id, category_map),
        )
    except Exception as refresh_err:
        logger.error(f"Error refreshing category or building full_path: {refresh_err}", exc_info=True)
        # On continue quand même - la catégorie a été créée, même si le full_path n'est pas défini
        # On construit un chemin simple pour éviter une erreur
        try:
            setattr(db_category, "full_path", original_name)
        except Exception:
            pass  # Si même ça échoue, on continue sans full_path
    
    return db_category


async def list_categories(
    session: AsyncSession,
    user_id: int,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[models.Category], int, bool, bool]:
    result = await session.execute(
        select(models.Category)
        .options(
            selectinload(models.Category.parent),
            selectinload(models.Category.children),
        )
        .where(models.Category.user_id == user_id)
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

    id_to_node = {c.id: c for c in categories}
    roots: list[models.Category] = []
    for c in categories:
        if c.parent_id and c.parent_id in id_to_node:
            parent = id_to_node[c.parent_id]
            if c not in parent.children:
                parent.children.append(c)
        else:
            roots.append(c)

    total = len(categories)
    return roots, total, False, False


def _build_category_path(category: models.Category) -> str:
    parts = [category.name]
    current = category.parent
    while current is not None:
        parts.append(current.name)
        current = current.parent
    return " / ".join(reversed(parts))


async def get_category(session: AsyncSession, category_id: int, user_id: int) -> models.Category | None:
    result = await session.execute(
        select(models.Category)
        .options(
            selectinload(models.Category.parent),
        )
        .where(models.Category.id == category_id, models.Category.user_id == user_id)
    )
    category = result.scalars().first()
    if category is None:
        return None

    category_map = await _load_category_map(session, user_id)
    setattr(
        category,
        "full_path",
        _build_category_path_from_map(category.id, category_map),
    )
    return category


async def update_category(
    session: AsyncSession, category_id: int, payload: schemas.CategoryUpdate, user_id: int
) -> models.Category | None:
    """Update a category, ensuring name uniqueness per user."""
    category = await session.get(models.Category, category_id)
    if category is None or category.user_id != user_id:
        return None

    data = payload.model_dump(exclude_unset=True)
    if "parent_id" in data and data["parent_id"] == category_id:
        data["parent_id"] = None
    
    # Si le nom est modifié, vérifier qu'aucune autre catégorie n'a déjà ce nom pour cet utilisateur
    if "name" in data:
        # Vérifier qu'une autre catégorie (différente de celle-ci) avec le même nom n'existe pas
        new_parent_id = data.get("parent_id", category.parent_id)
        existing_query = select(models.Category).where(
            models.Category.user_id == user_id,
            models.Category.name == data["name"],
            models.Category.id != category_id  # Exclure la catégorie actuelle
        )
        # Comparer parent_id correctement (NULL-safe)
        if new_parent_id is None:
            existing_query = existing_query.where(models.Category.parent_id.is_(None))
        else:
            existing_query = existing_query.where(models.Category.parent_id == new_parent_id)
        
        existing_category = await session.execute(existing_query)
        if existing_category.first():
            raise CategoryNameConflictError(
                f"Category name '{data['name']}' already exists"
            )
    
    for field, value in data.items():
        setattr(category, field, value)

    try:
        await session.flush()
    except IntegrityError as exc:  # pragma: no cover - depends on DB backend
        raise CategoryNameConflictError("Category name already exists") from exc

    await session.refresh(category)
    await session.refresh(category, attribute_names=["parent"])
    category_map = await _load_category_map(session, user_id)
    setattr(
        category,
        "full_path",
        _build_category_path_from_map(category.id, category_map),
    )
    return category


async def delete_category(session: AsyncSession, category_id: int, user_id: int) -> bool:
    category = await session.get(models.Category, category_id)
    if category is None or category.user_id != user_id:
        return False
    await session.delete(category)
    return True


async def create_expense(session: AsyncSession, expense: schemas.ExpenseCreate, user_id: int) -> models.Expense:
    payload = expense.model_dump(exclude_none=True)
    if "created_at" in payload and payload["created_at"] is None:
        payload.pop("created_at")
    db_expense = models.Expense(**payload, user_id=user_id)
    session.add(db_expense)
    await session.flush()
    await session.refresh(db_expense)
    await session.refresh(db_expense, attribute_names=["category"])
    category_map = await _load_category_map(session, user_id)
    setattr(
        db_expense,
        "category_path",
        _build_category_path_from_map(db_expense.category_id, category_map),
    )
    return db_expense


async def list_expenses_by_category(
    session: AsyncSession,
    category_id: int,
    user_id: int,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[models.Expense], int, bool, bool]:
    query = (
        select(models.Expense)
        .options(
            selectinload(models.Expense.category).selectinload(models.Category.parent),
        )
        .where(models.Expense.category_id == category_id, models.Expense.user_id == user_id)
    )

    if start_date is not None:
        query = query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        query = query.where(models.Expense.created_at < end_date + timedelta(days=1))

    count_query = select(func.count()).select_from(models.Expense).where(
        models.Expense.category_id == category_id,
        models.Expense.user_id == user_id,
    )

    if start_date is not None:
        count_query = count_query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        count_query = count_query.where(models.Expense.created_at < end_date + timedelta(days=1))

    total = await session.scalar(count_query) or 0

    offset = (page - 1) * per_page
    result = await session.execute(query.order_by(models.Expense.created_at.desc()).offset(offset).limit(per_page))
    expenses = result.scalars().all()
    category_map = await _load_category_map(session, user_id)
    for expense in expenses:
        setattr(
            expense,
            "category_path",
            _build_category_path_from_map(expense.category_id, category_map),
        )

    has_next = total > page * per_page
    has_previous = page > 1

    return expenses, total, has_next, has_previous


async def search_expenses(
    session: AsyncSession,
    user_id: int,
    *,
    category_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[models.Expense], int, bool, bool]:
    query = (
        select(models.Expense)
        .options(
            selectinload(models.Expense.category).selectinload(models.Category.parent),
        )
        .where(models.Expense.user_id == user_id)
        .order_by(models.Expense.created_at.desc())
    )

    if category_id is not None:
        query = query.where(models.Expense.category_id == category_id)
    if start_date is not None:
        query = query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        query = query.where(models.Expense.created_at < end_date + timedelta(days=1))

    count_query = select(func.count()).select_from(models.Expense).where(models.Expense.user_id == user_id)
    if category_id is not None:
        count_query = count_query.where(models.Expense.category_id == category_id)
    if start_date is not None:
        count_query = count_query.where(models.Expense.created_at >= start_date)
    if end_date is not None:
        count_query = count_query.where(models.Expense.created_at < end_date + timedelta(days=1))

    total = await session.scalar(count_query) or 0

    offset = (page - 1) * per_page
    result = await session.execute(query.offset(offset).limit(per_page))
    expenses = result.scalars().all()
    category_map = await _load_category_map(session, user_id)
    for expense in expenses:
        setattr(
            expense,
            "category_path",
            _build_category_path_from_map(expense.category_id, category_map),
        )

    has_next = total > page * per_page
    has_previous = page > 1

    return expenses, total, has_next, has_previous


async def get_expense(session: AsyncSession, expense_id: int, user_id: int) -> models.Expense | None:
    result = await session.execute(
        select(models.Expense).where(models.Expense.id == expense_id, models.Expense.user_id == user_id)
    )
    return result.scalars().first()


async def update_expense(
    session: AsyncSession, expense_id: int, payload: schemas.ExpenseUpdate, user_id: int
) -> models.Expense | None:
    expense = await session.get(models.Expense, expense_id)
    if expense is None or expense.user_id != user_id:
        return None

    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data and data["category_id"] is not None:
        category = await session.get(models.Category, data["category_id"])
        if category is None or category.user_id != user_id:
            raise ValueError("Category not found")

    if data.get("created_at") is None:
        data.pop("created_at", None)

    for field, value in data.items():
        setattr(expense, field, value)

    await session.flush()
    await session.refresh(expense)
    await session.refresh(expense, attribute_names=["category"])
    category_map = await _load_category_map(session, user_id)
    setattr(
        expense,
        "category_path",
        _build_category_path_from_map(expense.category_id, category_map),
    )
    return expense


async def delete_expense(session: AsyncSession, expense_id: int, user_id: int) -> bool:
    expense = await session.get(models.Expense, expense_id)
    if expense is None or expense.user_id != user_id:
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
    user_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
) -> schemas.MonthlySummary:
    start_date, end_date = _resolve_date_range(start_date, end_date)

    total_case = case(
        (
            and_(
                models.Expense.created_at >= start_date,
                models.Expense.created_at < end_date + timedelta(days=1),
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
        .where(models.Category.user_id == user_id)
        .group_by(models.Category.id)
        .order_by(models.Category.name)
    )

    if category_id is not None:
        query = query.where(models.Category.id == category_id)

    result = await session.execute(query)
    totals = result.all()
    category_map = await _load_category_map(session, user_id)

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
    user_id: int,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category_id: int | None = None,
    export_format: Literal["csv", "xlsx"] = "csv",
) -> tuple[bytes, str, str]:
    start_date, end_date = _resolve_date_range(start_date, end_date)

    # search_expenses retourne un tuple (expenses, total, has_next, has_previous)
    # On ne prend que la liste des expenses pour l'export
    expenses, _, _, _ = await search_expenses(
        session,
        user_id=user_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        page=1,
        per_page=10000,  # Nombre élevé pour récupérer toutes les dépenses
    )

    category_map = await _load_category_map(session, user_id)

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


async def paginate_query(
    session: AsyncSession,
    query,
    *,
    page: int,
    per_page: int,
) -> tuple[list, int, bool, bool]:
    total_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(total_query)

    offset = (page - 1) * per_page
    result = await session.execute(query.offset(offset).limit(per_page))
    items = result.scalars().unique().all()

    has_next = total > page * per_page
    has_previous = page > 1

    return items, total, has_next, has_previous


# ============================================================================
# TRANSLATIONS (i18n)
# ============================================================================

async def get_translations_by_locale(session: AsyncSession, locale: str) -> dict[str, str]:
    """Get all translations for a given locale as a dictionary."""
    result = await session.execute(
        select(models.Translation).where(models.Translation.locale == locale)
    )
    translations = result.scalars().all()
    return {t.key: t.value for t in translations}


async def create_translation(
    session: AsyncSession, translation: schemas.TranslationCreate
) -> models.Translation:
    """Create a new translation."""
    db_translation = models.Translation(
        locale=translation.locale,
        key=translation.key,
        value=translation.value,
    )
    session.add(db_translation)
    await session.flush()
    return db_translation


async def upsert_translation(
    session: AsyncSession, locale: str, key: str, value: str
) -> models.Translation:
    """Create or update a translation."""
    result = await session.execute(
        select(models.Translation).where(
            (models.Translation.locale == locale) & (models.Translation.key == key)
        )
    )
    translation = result.scalar_one_or_none()

    if translation:
        translation.value = value
    else:
        translation = models.Translation(locale=locale, key=key, value=value)
        session.add(translation)

    await session.flush()
    return translation


async def seed_translations(session: AsyncSession) -> None:
    """Seed the database with default translations."""
    translations_data = [
        # ========== FRENCH ==========
        ("fr", "common.appName", "NotBroke"),
        ("fr", "common.tagline", "Gérez vos dépenses en toute simplicité"),
        ("fr", "auth.login.title", "Connexion"),
        ("fr", "auth.login.subtitle", "Connectez-vous à votre compte NotBroke"),
        ("fr", "auth.login.username", "Nom d'utilisateur"),
        ("fr", "auth.login.usernamePlaceholder", "Nom d'utilisateur"),
        ("fr", "auth.login.password", "Mot de passe"),
        ("fr", "auth.login.passwordPlaceholder", "••••••••"),
        ("fr", "auth.login.button", "Se connecter"),
        ("fr", "auth.login.connecting", "Connexion..."),
        ("fr", "auth.login.noAccount", "Pas encore de compte ?"),
        ("fr", "auth.login.register", "S'inscrire"),
        ("fr", "auth.login.errors.invalidCredentials", "Nom d'utilisateur ou mot de passe incorrect"),
        ("fr", "auth.register.title", "Inscription"),
        ("fr", "auth.register.subtitle", "Créez votre compte pour commencer"),
        ("fr", "auth.register.username", "Nom d'utilisateur"),
        ("fr", "auth.register.usernamePlaceholder", "Nom d'utilisateur"),
        ("fr", "auth.register.usernameHelp", "3-50 caractères, alphanumériques"),
        ("fr", "auth.register.email", "Email"),
        ("fr", "auth.register.emailPlaceholder", "votre@email.com"),
        ("fr", "auth.register.password", "Mot de passe"),
        ("fr", "auth.register.passwordPlaceholder", "••••••••"),
        ("fr", "auth.register.passwordHelp", "Minimum 8 caractères avec majuscule, minuscule, chiffre et caractère spécial"),
        ("fr", "auth.register.passwordChecklistTitle", "Votre mot de passe doit contenir :"),
        ("fr", "auth.register.passwordRequirementLength", "Au moins 8 caractères"),
        ("fr", "auth.register.passwordRequirementUppercase", "Au moins une lettre majuscule"),
        ("fr", "auth.register.passwordRequirementLowercase", "Au moins une lettre minuscule"),
        ("fr", "auth.register.passwordRequirementDigit", "Au moins un chiffre"),
        ("fr", "auth.register.passwordRequirementSpecial", "Au moins un caractère spécial (!@#$% etc.)"),
        ("fr", "auth.register.confirmPassword", "Confirmer le mot de passe"),
        ("fr", "auth.register.confirmPasswordPlaceholder", "••••••••"),
        ("fr", "auth.register.button", "S'inscrire"),
        ("fr", "auth.register.registering", "Inscription en cours..."),
        ("fr", "auth.register.passwordMismatch", "Les mots de passe ne correspondent pas"),
        ("fr", "auth.register.passwordInvalid", "Votre mot de passe ne respecte pas les exigences de sécurité"),
        ("fr", "auth.register.noAccount", "Vous avez déjà un compte ?"),
        ("fr", "auth.register.login", "Se connecter"),
        ("fr", "dashboard.title", "NotBroke"),
        ("fr", "dashboard.subtitle", "Gérer vos catégories et dépenses"),
        ("fr", "dashboard.tabs.create", "Création"),
        ("fr", "dashboard.tabs.search", "Recherche"),
        ("fr", "dashboard.tabs.export", "Export"),
        ("fr", "dashboard.hint.export", "Utilisez les mêmes filtres que dans la recherche"),
        ("fr", "categories.title", "Catégories"),
        ("fr", "categories.addButton", "Ajouter une catégorie"),
        ("fr", "categories.editButton", "Éditer"),
        ("fr", "categories.deleteButton", "Supprimer"),
        ("fr", "categories.name", "Nom"),
        ("fr", "categories.description", "Description"),
        ("fr", "categories.noDescription", "Pas de description"),
        ("fr", "categories.parent", "Catégorie parente"),
        ("fr", "categories.cancel", "Annuler"),
        ("fr", "categories.save", "Enregistrer"),
        ("fr", "expenses.title", "Dépenses"),
        ("fr", "expenses.addButton", "Ajouter une dépense"),
        ("fr", "expenses.editButton", "Éditer une dépense"),
        ("fr", "expenses.deleteButton", "Supprimer"),
        ("fr", "expenses.amount", "Montant (€)"),
        ("fr", "expenses.amountRequired", "Le montant est obligatoire"),
        ("fr", "expenses.amountPositive", "Le montant doit être positif"),
        ("fr", "expenses.date", "Date"),
        ("fr", "expenses.dateRequired", "La date est obligatoire"),
        ("fr", "expenses.category", "Catégorie"),
        ("fr", "expenses.categoryPlaceholder", "Sélectionner une catégorie"),
        ("fr", "expenses.description", "Description"),
        ("fr", "expenses.descriptionPlaceholder", "Description"),
        ("fr", "expenses.save", "Enregistrer"),
        ("fr", "expenses.saving", "Enregistrement..."),
        ("fr", "expenses.create", "Créer la dépense"),
        ("fr", "expenses.cancel", "Annuler"),
        ("fr", "expenses.addSubtitle", "Ajoutez une nouvelle dépense à votre budget"),
        ("fr", "expenses.editSubtitle", "Modifiez les détails de cette dépense"),
        ("fr", "expenses.noExpenses", "Aucune dépense"),
        ("fr", "search.startDate", "Date de début"),
        ("fr", "search.endDate", "Date de fin"),
        ("fr", "search.category", "Catégorie"),
        ("fr", "search.selectCategories", "Sélectionner les catégories"),
        ("fr", "search.button", "Rechercher"),
        ("fr", "search.reset", "Réinitialiser"),
        ("fr", "search.results", "Résultats de la recherche"),
        ("fr", "search.noResults", "Aucun résultat trouvé"),
        ("fr", "export.title", "Export des données"),
        ("fr", "export.format", "Format"),
        ("fr", "export.csv", "CSV"),
        ("fr", "export.xlsx", "Excel"),
        ("fr", "export.startDate", "Date de début"),
        ("fr", "export.endDate", "Date de fin"),
        ("fr", "export.category", "Catégorie (optionnel)"),
        ("fr", "export.button", "Télécharger"),
        ("fr", "export.selectPeriod", "Veuillez sélectionner une période"),
        ("fr", "export.invalidDates", "La date de fin doit être postérieure à la date de début"),
        ("fr", "export.error", "Erreur lors de l'export des données"),
        ("fr", "summary.title", "Résumé mensuel"),
        ("fr", "summary.total", "Total"),
        ("fr", "summary.byCategory", "Par catégorie"),
        ("fr", "summary.month", "Mois"),
        ("fr", "summary.noData", "Aucune données"),
        ("fr", "summary.statistics", "Statistiques"),
        ("fr", "summary.categoriesUsed", "Catégories utilisées"),
        ("fr", "summary.averagePerCategory", "Moyenne par catégorie"),
        ("fr", "summary.percentOfTotal", "du total"),
        ("fr", "user.login", "Connexion"),
        ("fr", "user.logout", "Déconnexion"),
        ("fr", "user.profile", "Profil"),
        ("fr", "errors.rateLimitRegister", "Trop de tentatives d'inscription. Réessayez plus tard."),
        ("fr", "errors.rateLimitLogin", "Trop de tentatives de connexion. Réessayez plus tard."),
        ("fr", "errors.rateLimitGeneral", "Trop de requêtes. Réessayez plus tard."),
        ("fr", "errors.invalidCredentials", "Nom d'utilisateur ou mot de passe incorrect"),
        ("fr", "errors.userAlreadyExists", "Cet utilisateur existe déjà"),
        ("fr", "errors.invalidEmail", "L'adresse email est invalide"),
        ("fr", "errors.categoryNotFound", "Catégorie non trouvée"),
        ("fr", "errors.expenseNotFound", "Dépense non trouvée"),
        ("fr", "errors.couldNotValidateCredentials", "Impossible de valider les identifiants"),
        ("fr", "errors.invalidLocale", "Locale non valide"),
        ("fr", "errors.failedFetchTranslations", "Impossible de récupérer les traductions"),
        ("fr", "errors.validationFailed", "Validation échouée"),
        ("fr", "errors.passwordUppercase", "Le mot de passe doit contenir au moins une lettre majuscule"),
        ("fr", "errors.passwordLowercase", "Le mot de passe doit contenir au moins une lettre minuscule"),
        ("fr", "errors.passwordDigit", "Le mot de passe doit contenir au moins un chiffre"),
        ("fr", "errors.passwordSpecial", "Le mot de passe doit contenir au moins un caractère spécial"),
        ("fr", "errors.passwordLength", "Le mot de passe doit contenir au moins 8 caractères"),
        
        # ========== ENGLISH ==========
        ("en", "common.appName", "NotBroke"),
        ("en", "common.tagline", "Manage your expenses with ease"),
        ("en", "auth.login.title", "Login"),
        ("en", "auth.login.subtitle", "Sign in to your NotBroke account"),
        ("en", "auth.login.username", "Username"),
        ("en", "auth.login.usernamePlaceholder", "Username"),
        ("en", "auth.login.password", "Password"),
        ("en", "auth.login.passwordPlaceholder", "••••••••"),
        ("en", "auth.login.button", "Sign in"),
        ("en", "auth.login.connecting", "Signing in..."),
        ("en", "auth.login.noAccount", "Don't have an account?"),
        ("en", "auth.login.register", "Sign up"),
        ("en", "auth.login.errors.invalidCredentials", "Incorrect username or password"),
        ("en", "auth.register.title", "Sign up"),
        ("en", "auth.register.subtitle", "Create your account to get started"),
        ("en", "auth.register.username", "Username"),
        ("en", "auth.register.usernamePlaceholder", "Username"),
        ("en", "auth.register.usernameHelp", "3-50 characters, alphanumeric"),
        ("en", "auth.register.email", "Email"),
        ("en", "auth.register.emailPlaceholder", "your@email.com"),
        ("en", "auth.register.password", "Password"),
        ("en", "auth.register.passwordPlaceholder", "••••••••"),
        ("en", "auth.register.passwordHelp", "Minimum 8 characters with uppercase, lowercase, digit and special character"),
        ("en", "auth.register.passwordChecklistTitle", "Your password must include:"),
        ("en", "auth.register.passwordRequirementLength", "At least 8 characters"),
        ("en", "auth.register.passwordRequirementUppercase", "At least one uppercase letter"),
        ("en", "auth.register.passwordRequirementLowercase", "At least one lowercase letter"),
        ("en", "auth.register.passwordRequirementDigit", "At least one digit"),
        ("en", "auth.register.passwordRequirementSpecial", "At least one special character (!@#$% etc.)"),
        ("en", "auth.register.confirmPassword", "Confirm password"),
        ("en", "auth.register.confirmPasswordPlaceholder", "••••••••"),
        ("en", "auth.register.button", "Sign up"),
        ("en", "auth.register.registering", "Signing up..."),
        ("en", "auth.register.passwordMismatch", "Passwords do not match"),
        ("en", "auth.register.passwordInvalid", "Your password does not meet the security requirements"),
        ("en", "auth.register.noAccount", "Already have an account?"),
        ("en", "auth.register.login", "Sign in"),
        ("en", "dashboard.title", "NotBroke"),
        ("en", "dashboard.subtitle", "Manage your categories and expenses"),
        ("en", "dashboard.tabs.create", "Create"),
        ("en", "dashboard.tabs.search", "Search"),
        ("en", "dashboard.tabs.export", "Export"),
        ("en", "dashboard.hint.export", "Use the same filters as in search"),
        ("en", "categories.title", "Categories"),
        ("en", "categories.addButton", "Add a category"),
        ("en", "categories.editButton", "Edit"),
        ("en", "categories.deleteButton", "Delete"),
        ("en", "categories.name", "Name"),
        ("en", "categories.description", "Description"),
        ("en", "categories.noDescription", "No description"),
        ("en", "categories.parent", "Parent category"),
        ("en", "categories.cancel", "Cancel"),
        ("en", "categories.save", "Save"),
        ("en", "expenses.title", "Expenses"),
        ("en", "expenses.addButton", "Add an expense"),
        ("en", "expenses.editButton", "Edit expense"),
        ("en", "expenses.deleteButton", "Delete"),
        ("en", "expenses.amount", "Amount (€)"),
        ("en", "expenses.amountRequired", "Amount is required"),
        ("en", "expenses.amountPositive", "Amount must be positive"),
        ("en", "expenses.date", "Date"),
        ("en", "expenses.dateRequired", "Date is required"),
        ("en", "expenses.category", "Category"),
        ("en", "expenses.categoryPlaceholder", "Select a category"),
        ("en", "expenses.description", "Description"),
        ("en", "expenses.descriptionPlaceholder", "Description"),
        ("en", "expenses.save", "Save"),
        ("en", "expenses.saving", "Saving..."),
        ("en", "expenses.create", "Create expense"),
        ("en", "expenses.cancel", "Cancel"),
        ("en", "expenses.addSubtitle", "Add a new expense to your budget"),
        ("en", "expenses.editSubtitle", "Modify this expense details"),
        ("en", "expenses.noExpenses", "No expenses"),
        ("en", "search.startDate", "Start date"),
        ("en", "search.endDate", "End date"),
        ("en", "search.category", "Category"),
        ("en", "search.selectCategories", "Select categories"),
        ("en", "search.button", "Search"),
        ("en", "search.reset", "Reset"),
        ("en", "search.results", "Search results"),
        ("en", "search.noResults", "No results found"),
        ("en", "export.title", "Export data"),
        ("en", "export.format", "Format"),
        ("en", "export.csv", "CSV"),
        ("en", "export.xlsx", "Excel"),
        ("en", "export.startDate", "Start date"),
        ("en", "export.endDate", "End date"),
        ("en", "export.category", "Category (optional)"),
        ("en", "export.button", "Download"),
        ("en", "export.selectPeriod", "Please select a period"),
        ("en", "export.invalidDates", "End date must be after start date"),
        ("en", "export.error", "Error exporting data"),
        ("en", "summary.title", "Monthly summary"),
        ("en", "summary.total", "Total"),
        ("en", "summary.byCategory", "By category"),
        ("en", "summary.month", "Month"),
        ("en", "summary.noData", "No data"),
        ("en", "summary.statistics", "Statistics"),
        ("en", "summary.categoriesUsed", "Categories used"),
        ("en", "summary.averagePerCategory", "Average per category"),
        ("en", "summary.percentOfTotal", "of total"),
        ("en", "user.login", "Login"),
        ("en", "user.logout", "Logout"),
        ("en", "user.profile", "Profile"),
        ("en", "errors.rateLimitRegister", "Too many registration attempts. Please try again later."),
        ("en", "errors.rateLimitLogin", "Too many login attempts. Please try again later."),
        ("en", "errors.rateLimitGeneral", "Too many requests. Please try again later."),
        ("en", "errors.invalidCredentials", "Incorrect username or password"),
        ("en", "errors.userAlreadyExists", "This user already exists"),
        ("en", "errors.invalidEmail", "The email address is invalid"),
        ("en", "errors.categoryNotFound", "Category not found"),
        ("en", "errors.expenseNotFound", "Expense not found"),
        ("en", "errors.couldNotValidateCredentials", "Could not validate credentials"),
        ("en", "errors.invalidLocale", "Invalid locale"),
        ("en", "errors.failedFetchTranslations", "Failed to fetch translations"),
        ("en", "errors.validationFailed", "Validation failed"),
        ("en", "errors.passwordUppercase", "Password must contain at least one uppercase letter"),
        ("en", "errors.passwordLowercase", "Password must contain at least one lowercase letter"),
        ("en", "errors.passwordDigit", "Password must contain at least one digit"),
        ("en", "errors.passwordSpecial", "Password must contain at least one special character"),
        ("en", "errors.passwordLength", "Password must contain at least 8 characters"),
        
        # ========== RUSSIAN ==========
        ("ru", "common.appName", "NotBroke"),
        ("ru", "common.tagline", "Управляйте расходами легко"),
        ("ru", "auth.login.title", "Вход"),
        ("ru", "auth.login.subtitle", "Войдите в свой аккаунт NotBroke"),
        ("ru", "auth.login.username", "Имя пользователя"),
        ("ru", "auth.login.usernamePlaceholder", "Имя пользователя"),
        ("ru", "auth.login.password", "Пароль"),
        ("ru", "auth.login.passwordPlaceholder", "••••••••"),
        ("ru", "auth.login.button", "Войти"),
        ("ru", "auth.login.connecting", "Вход..."),
        ("ru", "auth.login.noAccount", "Нет аккаунта?"),
        ("ru", "auth.login.register", "Зарегистрироваться"),
        ("ru", "auth.login.errors.invalidCredentials", "Неверное имя пользователя или пароль"),
        ("ru", "auth.register.title", "Регистрация"),
        ("ru", "auth.register.subtitle", "Создайте аккаунт для начала"),
        ("ru", "auth.register.username", "Имя пользователя"),
        ("ru", "auth.register.usernamePlaceholder", "Имя пользователя"),
        ("ru", "auth.register.usernameHelp", "3-50 символов, буквы и цифры"),
        ("ru", "auth.register.email", "Email"),
        ("ru", "auth.register.emailPlaceholder", "ваш@email.com"),
        ("ru", "auth.register.password", "Пароль"),
        ("ru", "auth.register.passwordPlaceholder", "••••••••"),
        ("ru", "auth.register.passwordHelp", "Минимум 8 символов с заглавной, строчной буквой, цифрой и спецсимволом"),
        ("ru", "auth.register.passwordChecklistTitle", "Пароль должен содержать:"),
        ("ru", "auth.register.passwordRequirementLength", "Не менее 8 символов"),
        ("ru", "auth.register.passwordRequirementUppercase", "Как минимум одну заглавную букву"),
        ("ru", "auth.register.passwordRequirementLowercase", "Как минимум одну строчную букву"),
        ("ru", "auth.register.passwordRequirementDigit", "Как минимум одну цифру"),
        ("ru", "auth.register.passwordRequirementSpecial", "Как минимум один специальный символ (!@#$% и т.д.)"),
        ("ru", "auth.register.confirmPassword", "Подтверждение пароля"),
        ("ru", "auth.register.confirmPasswordPlaceholder", "••••••••"),
        ("ru", "auth.register.button", "Зарегистрироваться"),
        ("ru", "auth.register.registering", "Регистрация..."),
        ("ru", "auth.register.passwordMismatch", "Пароли не совпадают"),
        ("ru", "auth.register.passwordInvalid", "Пароль не соответствует требованиям безопасности"),
        ("ru", "auth.register.noAccount", "Уже есть аккаунт?"),
        ("ru", "auth.register.login", "Войти"),
        ("ru", "dashboard.title", "NotBroke"),
        ("ru", "dashboard.subtitle", "Управляйте категориями и расходами"),
        ("ru", "dashboard.tabs.create", "Создание"),
        ("ru", "dashboard.tabs.search", "Поиск"),
        ("ru", "dashboard.tabs.export", "Экспорт"),
        ("ru", "dashboard.hint.export", "Используйте те же фильтры, что и в поиске"),
        ("ru", "categories.title", "Категории"),
        ("ru", "categories.addButton", "Добавить категорию"),
        ("ru", "categories.editButton", "Редактировать"),
        ("ru", "categories.deleteButton", "Удалить"),
        ("ru", "categories.name", "Название"),
        ("ru", "categories.description", "Описание"),
        ("ru", "categories.noDescription", "Нет описания"),
        ("ru", "categories.parent", "Родительская категория"),
        ("ru", "categories.cancel", "Отмена"),
        ("ru", "categories.save", "Сохранить"),
        ("ru", "expenses.title", "Расходы"),
        ("ru", "expenses.addButton", "Добавить расход"),
        ("ru", "expenses.editButton", "Редактировать расход"),
        ("ru", "expenses.deleteButton", "Удалить"),
        ("ru", "expenses.amount", "Сумма (€)"),
        ("ru", "expenses.amountRequired", "Сумма обязательна"),
        ("ru", "expenses.amountPositive", "Сумма должна быть положительной"),
        ("ru", "expenses.date", "Дата"),
        ("ru", "expenses.dateRequired", "Дата обязательна"),
        ("ru", "expenses.category", "Категория"),
        ("ru", "expenses.categoryPlaceholder", "Выберите категорию"),
        ("ru", "expenses.description", "Описание"),
        ("ru", "expenses.descriptionPlaceholder", "Описание"),
        ("ru", "expenses.save", "Сохранить"),
        ("ru", "expenses.saving", "Сохранение..."),
        ("ru", "expenses.create", "Создать расход"),
        ("ru", "expenses.cancel", "Отмена"),
        ("ru", "expenses.addSubtitle", "Добавьте новый расход в ваш бюджет"),
        ("ru", "expenses.editSubtitle", "Измените детали этого расхода"),
        ("ru", "expenses.noExpenses", "Нет расходов"),
        ("ru", "search.startDate", "Дата начала"),
        ("ru", "search.endDate", "Дата окончания"),
        ("ru", "search.category", "Категория"),
        ("ru", "search.selectCategories", "Выбрать категории"),
        ("ru", "search.button", "Поиск"),
        ("ru", "search.reset", "Сброс"),
        ("ru", "search.results", "Результаты поиска"),
        ("ru", "search.noResults", "Результаты не найдены"),
        ("ru", "export.title", "Экспорт данных"),
        ("ru", "export.format", "Формат"),
        ("ru", "export.csv", "CSV"),
        ("ru", "export.xlsx", "Excel"),
        ("ru", "export.startDate", "Дата начала"),
        ("ru", "export.endDate", "Дата окончания"),
        ("ru", "export.category", "Категория (опционально)"),
        ("ru", "export.button", "Загрузить"),
        ("ru", "export.selectPeriod", "Пожалуйста, выберите период"),
        ("ru", "export.invalidDates", "Дата окончания должна быть позже даты начала"),
        ("ru", "export.error", "Ошибка при экспорте данных"),
        ("ru", "summary.title", "Ежемесячный отчет"),
        ("ru", "summary.total", "Итого"),
        ("ru", "summary.byCategory", "По категориям"),
        ("ru", "summary.month", "Месяц"),
        ("ru", "summary.noData", "Нет данных"),
        ("ru", "summary.statistics", "Статистика"),
        ("ru", "summary.categoriesUsed", "Используемые категории"),
        ("ru", "summary.averagePerCategory", "Средняя по категориям"),
        ("ru", "summary.percentOfTotal", "от всего"),
        ("ru", "user.login", "Вход"),
        ("ru", "user.logout", "Выход"),
        ("ru", "user.profile", "Профиль"),
        ("ru", "errors.rateLimitRegister", "Слишком много попыток регистрации. Повторите попытку позже."),
        ("ru", "errors.rateLimitLogin", "Слишком много попыток входа. Повторите попытку позже."),
        ("ru", "errors.rateLimitGeneral", "Слишком много запросов. Повторите попытку позже."),
        ("ru", "errors.invalidCredentials", "Неверное имя пользователя или пароль"),
        ("ru", "errors.userAlreadyExists", "Этот пользователь уже существует"),
        ("ru", "errors.invalidEmail", "Адрес электронной почты недействителен"),
        ("ru", "errors.categoryNotFound", "Категория не найдена"),
        ("ru", "errors.expenseNotFound", "Расход не найден"),
        ("ru", "errors.couldNotValidateCredentials", "Не удалось проверить учетные данные"),
        ("ru", "errors.invalidLocale", "Неверная локаль"),
        ("ru", "errors.failedFetchTranslations", "Не удалось получить переводы"),
        ("ru", "errors.validationFailed", "Ошибка валидации"),
        ("ru", "errors.passwordUppercase", "Пароль должен содержать как минимум одну заглавную букву"),
        ("ru", "errors.passwordLowercase", "Пароль должен содержать как минимум одну строчную букву"),
        ("ru", "errors.passwordDigit", "Пароль должен содержать как минимум одну цифру"),
        ("ru", "errors.passwordSpecial", "Пароль должен содержать как минимум один специальный символ"),
        ("ru", "errors.passwordLength", "Пароль должен содержать не менее 8 символов"),
    ]

    for locale, key, value in translations_data:
        await upsert_translation(session, locale, key, value)

