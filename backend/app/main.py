"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import os
import time
import logging
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
from .exceptions import (
    integrity_error_handler,
    operational_error_handler,
    value_error_handler,
    crud_error_handler,
    general_exception_handler,
)
from .health import get_health_status
from .config import config
from sqlalchemy.exc import IntegrityError, OperationalError
from pydantic import ValidationError
from fastapi import Query

# Validate environment configuration at startup
try:
    # This will raise ValueError if configuration is invalid
    config
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    import sys
    sys.exit(1)

def validate_cors_settings():
    """Valider et configurer les paramètres CORS selon l'environnement."""
    environment = config.environment
    frontend_url = config.get("FRONTEND_URL")

    if config.is_production:
        if not frontend_url:
            raise ValueError(
                "FRONTEND_URL environment variable must be set in production for CORS configuration"
            )
        # Validation basique de l'URL
        if not frontend_url.startswith(('http://', 'https://')):
            raise ValueError("FRONTEND_URL must be a valid HTTP/HTTPS URL")

        # Support multiple origins (séparées par des virgules)
        allow_origins = [url.strip() for url in frontend_url.split(',') if url.strip()]
        print(f"🔒 Production CORS: Allowing origins {', '.join(allow_origins)}")
    else:
        # Développement: utiliser l'URL du frontend ou localhost:3000 par défaut
        # On ne peut pas utiliser "*" avec allow_credentials=True
        if not frontend_url:
            frontend_url = "http://localhost:3000"
            print(f"⚠️  WARNING: FRONTEND_URL not set. Using default: {frontend_url}")
        else:
            print(f"🔓 Development CORS: Allowing origin {frontend_url}")
        
        # Toujours spécifier explicitement l'origine en développement pour permettre credentials
        allow_origins = [frontend_url]

    return environment, allow_origins

# Configuration validée de l'environnement et CORS
ENVIRONMENT, ALLOWED_ORIGINS = validate_cors_settings()

app = FastAPI(
    title="Expense Tracker API",
    docs_url="/docs" if not config.is_production else None,
    redoc_url="/redoc" if not config.is_production else None,
    version="1.0.0",
    description="""
    A modern expense management API built with FastAPI.
    
    ## Features
    
    * **Authentication**: JWT-based authentication with secure httpOnly cookies
    * **Categories**: Hierarchical category management with parent-child relationships
    * **Expenses**: Track expenses with amounts, notes, and categorization
    * **Summaries**: Monthly summaries with totals by category and period
    * **Export**: Export expenses to CSV or XLSX formats
    * **Internationalization**: Multi-language support (FR, EN, RU)
    
    ## Security
    
    * Rate limiting on sensitive endpoints
    * Input validation with Pydantic
    * Security headers (CORS, CSP, HSTS)
    * Audit logging for security events
    
    ## Authentication
    
    All endpoints except `/auth/register` and `/auth/login` require authentication.
    Include the JWT token in the Authorization header or use httpOnly cookies.
    """,
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "NotBroke API Support",
        "url": "https://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Register exception handlers
# Note: HTTPException handler must be registered BEFORE other handlers
# because HTTPException is a subclass of Exception
from .exceptions import http_exception_handler
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(crud.CategoryNameConflictError, crud_error_handler)
app.add_exception_handler(crud.UserAlreadyExistsError, crud_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

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


@app.get("/health", response_model=None, tags=["Health"])
async def health_check(include_details: bool = Query(False, description="Include detailed system information")):
    """
    Health check endpoint.
    
    Returns the health status of the API and database.
    Use `?include_details=true` for detailed system information.
    """
    return await get_health_status(include_details=include_details)


@app.get("/", include_in_schema=False)
async def root_healthcheck() -> dict[str, str]:
    """Simple healthcheck endpoint for Render probes (redirects to /health)."""
    return {"status": "ok", "health_endpoint": "/health"}

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

# Middleware de timing pour mesurer les performances
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Ajoute un header X-Process-Time pour mesurer le temps de traitement des requêtes."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response

# Middleware de timeout pour éviter les requêtes qui traînent
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Timeout middleware avec timeout adaptatif selon l'endpoint."""
    # Timeout plus court pour les endpoints d'authentification (10s)
    # Timeout standard pour les autres endpoints (30s)
    timeout = 10.0 if request.url.path.startswith("/auth") else 30.0
    
    try:
        return await asyncio.wait_for(call_next(request), timeout=timeout)
    except asyncio.TimeoutError:
        return JSONResponse(
            {"detail": f"Request timeout after {timeout}s"}, 
            status_code=408
        )


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
    # Seed translations on startup (only if they don't exist yet)
    # Cela évite les insertions répétées à chaque redémarrage
    from .database import AsyncSessionLocal
    session = AsyncSessionLocal()
    try:
        # Vérifier si les traductions existent déjà (une seule requête rapide)
        existing_fr = await crud.get_translations_by_locale(session, 'fr')
        if not existing_fr:
            print("🌱 Seeding translations...")
            await crud.seed_translations(session)
            await session.commit()
            print("✅ Translations seeded successfully")
        else:
            print("✅ Translations already exist, skipping seed")
    except Exception as e:
        await session.rollback()
        print(f"⚠️  Error seeding translations: {e}")
    finally:
        await session.close()


# Routes d'authentification
# Logger pour les endpoints critiques
logger = logging.getLogger(__name__)


@app.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user: schemas.UserCreate, session=Depends(get_session)):
    start_time = time.time()
    
    # Rate limit: 3 registrations per minute
    client_ip = request.client.host if request.client else None
    if not check_rate_limit("/auth/register", client_ip, 3):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Please try again later.")
    
    try:
        db_user = await crud.create_user(session, user)
        process_time = time.time() - start_time
        log_security_event("USER_REGISTERED", db_user.id, {"username": user.username})
        
        # Log performance pour monitoring
        logger.info(
            f"User registration successful for '{user.username}' - "
            f"Process time: {process_time:.4f}s"
        )
        
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
    start_time = time.time()
    
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
        secure=config.is_production,
        samesite="none" if config.is_production else "lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    process_time = time.time() - start_time
    log_security_event("LOGIN_SUCCESS", user.id, {"username": user.username})
    
    # Log performance pour monitoring
    logger.info(
        f"Login successful for user '{user.username}' - "
        f"Process time: {process_time:.4f}s"
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.post("/auth/logout")
async def logout(request: Request, response: Response, current_user=Depends(get_current_user)):
    """Logout endpoint that clears the httpOnly cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=config.is_production,
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
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"POST /categories - user_id={current_user.id}, name='{payload.name}', parent_id={payload.parent_id}")
    
    try:
        category = await crud.create_category(session, payload, current_user.id)
        log_security_event("CATEGORY_CREATED", current_user.id, {"category_id": category.id, "name": category.name})
        logger.info(f"Category created successfully: id={category.id}, name='{category.name}'")
        cache_invalidate(f"categories:{current_user.id}")
        cache_invalidate(f"summary:{current_user.id}")
        return category
    except crud.CategoryNameConflictError as exc:
        logger.warning(f"Category creation failed: {exc} for user_id={current_user.id}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error creating category: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while creating the category"
        ) from exc


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


def get_cors_headers(request: Request) -> dict[str, str]:
    """Get CORS headers for a request."""
    origin = request.headers.get("origin")
    normalized_origin = origin.rstrip("/") if origin else None
    normalized_allowed = [o.rstrip("/") for o in ALLOWED_ORIGINS]

    headers = {
        "Access-Control-Allow-Credentials": "true",
    }

    # Vérifier si l'origine est autorisée
    if normalized_origin and normalized_origin in normalized_allowed:
        headers["Access-Control-Allow-Origin"] = origin
    elif ALLOWED_ORIGINS:
        # Utiliser la première origine autorisée si l'origine de la requête ne correspond pas
        headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGINS[0]
    
    return headers


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
        # Ajouter headers CORS même en cas d'erreur
        cors_headers = get_cors_headers(request)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
            headers=cors_headers
        ) from exc
    except Exception as exc:
        # Catch toutes les autres exceptions et ajouter headers CORS
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error exporting expenses: {exc}", exc_info=True)
        cors_headers = get_cors_headers(request)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while exporting expenses",
            headers=cors_headers
        ) from exc

    # Ajouter headers CORS pour que le téléchargement fonctionne
    cors_headers = get_cors_headers(request)
    headers = {
        **cors_headers,
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

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

