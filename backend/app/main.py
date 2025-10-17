"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from . import crud, schemas
from .database import get_session, init_db
from .auth import create_access_token, get_current_user, verify_password

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

# Configuration CORS sécurisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Middleware de timeout pour éviter les requêtes qui traînent
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=30.0)
    except asyncio.TimeoutError:
        return JSONResponse({"detail": "Request timeout"}, status_code=408)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


# Routes d'authentification
@app.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, session=Depends(get_session)):
    try:
        db_user = await crud.create_user(session, user)
        return db_user
    except crud.UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/auth/login", response_model=schemas.Token)
async def login(
    user_credentials: schemas.UserLogin,
    response: Response,
    session=Depends(get_session)
):
    user = await crud.get_user_by_username(session, user_credentials.username)
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    # Définir le cookie httpOnly avec le token JWT
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=ENVIRONMENT == "production",  # Secure seulement en production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convertir en secondes
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(response: Response):
    """Logout endpoint that clears the httpOnly cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
    )
    return {"message": "Successfully logged out"}


@app.post("/categories", response_model=schemas.CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: schemas.CategoryCreate,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    try:
        category = await crud.create_category(session, payload, current_user.id)
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return category


@app.get("/categories", response_model=list[schemas.CategoryRead])
async def list_categories(
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    return await crud.list_categories(session, current_user.id)


@app.get("/categories/{category_id}", response_model=schemas.CategoryRead)
async def get_category(
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
    category_id: int,
    payload: schemas.CategoryUpdate,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        category = await crud.update_category(session, category_id, payload, current_user.id)
    except crud.CategoryNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    deleted = await crud.delete_category(session, category_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/expenses", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: schemas.ExpenseCreate,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    return await crud.create_expense(session, payload, current_user.id)


DateQuery = Annotated[datetime | None, Query(description="Date au format ISO 8601")]


@app.get("/categories/{category_id}/expenses", response_model=list[schemas.ExpenseRead])
async def list_expenses(
    category_id: int,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    return await crud.list_expenses_by_category(
        session,
        category_id,
        current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@app.get("/expenses", response_model=list[schemas.ExpenseRead])
async def search_expenses(
    category_id: Annotated[int | None, Query()] = None,
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    return await crud.search_expenses(
        session,
        current_user.id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
    )


@app.patch("/expenses/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense(
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        expense = await crud.update_expense(session, expense_id, payload, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    current_user = Depends(get_current_user),
    session=Depends(get_session)
):
    deleted = await crud.delete_expense(session, expense_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/summary", response_model=schemas.MonthlySummary)
async def get_summary(
    start_date: DateQuery = None,
    end_date: DateQuery = None,
    category_id: Annotated[int | None, Query()] = None,
    current_user = Depends(get_current_user),
    session=Depends(get_session),
):
    try:
        return await crud.totals_by_period(
            session,
            current_user.id,
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
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)

