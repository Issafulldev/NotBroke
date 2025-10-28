"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from functools import wraps
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware

from . import crud, schemas
from .database import get_session, init_db
from .auth import create_access_token, get_current_user, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from .logging_config import log_security_event
from .cache import get as cache_get, set as cache_set, invalidate as cache_invalidate
from .rate_limit import check_rate_limit

def validate_cors_settings():
    """Valider et configurer les paramètres CORS selon l'environnement."""
    environment = os.getenv("ENVIRONMENT", "development")
    frontend_url = os.getenv("FRONTEND_URL")

    if environment == "production":
        if not frontend_url:
            raise ValueError(
                "FRONTEND_URL environment variable must be set in production for CORS configuration"
            )
        # Validation basique de l'URL
        if not frontend_url.startswith(('http://', 'https://')):
            raise ValueError("FRONTEND_URL must be a valid HTTP/HTTPS URL")

        allow_origins = [frontend_url]
        print(f"🔒 Production CORS: Allowing origin {frontend_url}")
    else:
        # Développement: origines permissives avec avertissement
        allow_origins = ["*"]
        if not frontend_url:
            print("⚠️  WARNING: FRONTEND_URL not set. Using permissive CORS for development.")
        else:
            print(f"🔓 Development CORS: Allowing all origins (configured for {frontend_url})")

    return environment, allow_origins

# Configuration validée de l'environnement et CORS
ENVIRONMENT, ALLOWED_ORIGINS = validate_cors_settings()

app = FastAPI(
    title="Expense Tracker API",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
)

# Compression des réponses pour réduire la bande passante
app.add_middleware(GZipMiddleware, minimum_size=500)

# Configuration CORS sécurisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],  # 🔐 Specific headers instead of wildcard with credentials
)


@app.get("/", include_in_schema=False)
async def root_healthcheck() -> dict[str, str]:
    """Simple healthcheck endpoint for Render probes."""
    return {"status": "ok"}

# Middleware de sécurité - Headers de sécurité
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response

# Middleware de timeout pour éviter les requêtes qui traînent
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=30.0)
    except asyncio.TimeoutError:
        return JSONResponse({"detail": "Request timeout"}, status_code=408)


# Rate limiting decorator
def rate_limit(requests_per_minute: int):
    """Decorator to apply rate limiting to endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            client_ip = request.client.host if request.client else None
            endpoint = request.url.path
            
            if not check_rate_limit(endpoint, client_ip, requests_per_minute):
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                )
            
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    # Seed translations on startup
    from .database import AsyncSessionLocal
    session = AsyncSessionLocal()
    try:
        await crud.seed_translations(session)
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"Error seeding translations: {e}")
    finally:
        await session.close()


# Routes d'authentification
@app.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user: schemas.UserCreate, session=Depends(get_session)):
    # Rate limit: 3 registrations per minute
    client_ip = request.client.host if request.client else None
    if not check_rate_limit("/auth/register", client_ip, 3):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Please try again later.")
    
    try:
        db_user = await crud.create_user(session, user)
        log_security_event("USER_REGISTERED", db_user.id, {"username": user.username})
        return db_user
    except crud.UserAlreadyExistsError as exc:
        log_security_event("REGISTRATION_FAILED", None, {"reason": "user_exists", "username": user.username})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/auth/login", response_model=schemas.LoginResponse)
async def login(
    request: Request,
    user_credentials: schemas.UserLogin,
    response: Response,
    session=Depends(get_session)
):
    client_ip = request.client.host if request.client else None
    if not check_rate_limit("/auth/login", client_ip, 5):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")

    user = await crud.get_user_by_username(session, user_credentials.username)
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        log_security_event(
            "LOGIN_FAILED",
            None,
            {"username": user_credentials.username, "ip": client_ip or "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="none" if ENVIRONMENT == "production" else "lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    log_security_event("LOGIN_SUCCESS", user.id, {"username": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.post("/auth/logout")
async def logout(request: Request, response: Response, current_user=Depends(get_current_user)):
    """Logout endpoint that clears the httpOnly cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
    )
    log_security_event("LOGOUT", current_user.id, {"username": current_user.username})
    return {"message": "Successfully logged out"}


@app.get("/auth/me", response_model=schemas.UserRead)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@app.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request,
    payload: schemas.CategoryCreate,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    try:
        category = await crud.create_category(session, payload, current_user.id)
        log_security_event("CATEGORY_CREATED", current_user.id, {"category_id": category.id, "name": category.name})
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    cache_invalidate(f"categories:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return category


@app.get("/categories", response_model=schemas.PaginatedCategories)
async def list_categories(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    cache_key = f"categories:{current_user.id}:{page}:{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return schemas.PaginatedCategories.model_validate(cached)

    categories, total, has_next, has_previous = await crud.list_categories(
        session,
        current_user.id,
        page=page,
        per_page=per_page,
    )
    response_data = schemas.PaginatedCategories(
        items=categories,
        meta=schemas.PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            has_next=has_next,
            has_previous=has_previous,
        ),
    )
    cache_set(cache_key, response_data.model_dump(), ttl=60)
    return response_data


@app.get("/categories/{category_id}", response_model=schemas.CategoryRead)
async def get_category(
    request: Request,
    category_id: int,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    category = await crud.get_category(session, category_id, current_user.id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@app.patch("/categories/{category_id}", response_model=schemas.CategoryRead)
async def update_category(
    request: Request,
    category_id: int,
    payload: schemas.CategoryUpdate,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        category = await crud.update_category(session, category_id, payload, current_user.id)
        log_security_event("CATEGORY_UPDATED", current_user.id, {"category_id": category_id})
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    cache_invalidate(f"categories:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    request: Request,
    category_id: int,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    deleted = await crud.delete_category(session, category_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    log_security_event("CATEGORY_DELETED", current_user.id, {"category_id": category_id})
    cache_invalidate(f"categories:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/expenses", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    request: Request,
    payload: schemas.ExpenseCreate,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    expense = await crud.create_expense(session, payload, current_user.id)
    cache_invalidate(f"expenses:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return expense
    cache_invalidate(f"expenses:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")


DateQuery = Annotated[datetime | None, Query(description="Date au format ISO 8601")]


@app.get("/categories/{category_id}/expenses", response_model=schemas.PaginatedExpenses)
async def list_expenses(
    request: Request,
    category_id: int,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    expenses, total, has_next, has_previous = await crud.list_expenses_by_category(
        session,
        category_id,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return schemas.PaginatedExpenses(
        items=expenses,
        meta=schemas.PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            has_next=has_next,
            has_previous=has_previous,
        ),
    )


@app.get("/expenses", response_model=schemas.PaginatedExpenses)
async def search_expenses(
    request: Request,
    category_id: Annotated[int | None, Query()] = None,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    cache_key = f"expenses:{current_user.id}:{category_id}:{start_date}:{end_date}:{page}:{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return schemas.PaginatedExpenses.model_validate(cached)

    expenses, total, has_next, has_previous = await crud.search_expenses(
        session,
        current_user.id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    response_data = schemas.PaginatedExpenses(
        items=expenses,
        meta=schemas.PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            has_next=has_next,
            has_previous=has_previous,
        ),
    )
    cache_set(cache_key, response_data.model_dump(), ttl=30)
    return response_data


@app.patch("/expenses/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense(
    request: Request,
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        expense = await crud.update_expense(session, expense_id, payload, current_user.id)
        log_security_event("EXPENSE_UPDATED", current_user.id, {"expense_id": expense_id})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    cache_invalidate(f"expenses:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    request: Request,
    expense_id: int,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    deleted = await crud.delete_expense(session, expense_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    log_security_event("EXPENSE_DELETED", current_user.id, {"expense_id": expense_id})
    cache_invalidate(f"expenses:{current_user.id}")
    cache_invalidate(f"summary:{current_user.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/summary", response_model=schemas.MonthlySummary)
async def get_summary(
    request: Request,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    category_id: Annotated[int | None, Query()] = None,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    cache_key = f"summary:{current_user.id}:{start_date}:{end_date}:{category_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        summary = await crud.totals_by_period(
            session,
            current_user.id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
        )
        cache_set(cache_key, summary, ttl=60)
        return summary
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/expenses/export")
async def export_expenses(
    request: Request,
    format: Annotated[str, Query(pattern="^(csv|xlsx)$", description="csv ou xlsx")] = "csv",
    category_id: Annotated[int | None, Query()] = None,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        content, media_type, filename = await crud.export_expenses(
            session,
            current_user.id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            export_format=format,  # type: ignore[arg-type]
        )
        log_security_event("EXPENSES_EXPORTED", current_user.id, {"format": format})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # 🆕 NOUVEAU: Ajouter headers CORS pour que le téléchargement fonctionne
    origin = request.headers.get("origin")
    normalized_origin = origin.rstrip("/") if origin else None
    normalized_allowed = [o.rstrip("/") for o in ALLOWED_ORIGINS if o != "*"]

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    if "*" in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin or "*"
    elif normalized_origin and normalized_origin in normalized_allowed:
        headers["Access-Control-Allow-Origin"] = origin

    return Response(content=content, media_type=media_type, headers=headers)


# ============================================================================
# TRANSLATIONS (i18n)
# ============================================================================

@app.get("/translations/{locale}", response_model=schemas.TranslationsResponse)
async def get_translations(
    request: Request,
    locale: str,
    session=Depends(get_session)
):
    """
    Get all translations for a given locale.
    
    Returns a dictionary of all translations keyed by their translation key.
    Example: {'auth.login.title': 'Connexion', 'auth.login.button': 'Se connecter', ...}
    """
    # Validate locale
    valid_locales = ['fr', 'en', 'ru']
    if locale not in valid_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid locale. Supported: {', '.join(valid_locales)}"
        )
    
    try:
        translations = await crud.get_translations_by_locale(session, locale)
        response = JSONResponse(
            content={"locale": locale, "translations": translations},
            status_code=200
        )
        
        # 🆕 NOUVEAU: Ajouter des headers de cache HTTP
        # Cacher pendant 30 jours (2592000 secondes)
        response.headers["Cache-Control"] = "public, max-age=2592000"
        # Permettre aussi au navigateur de réutiliser même après expiration si pas de connexion
        response.headers["Vary"] = "Accept-Encoding"
        
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch translations: {str(exc)}"
        ) from exc

