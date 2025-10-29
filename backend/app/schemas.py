"""Pydantic schemas for request and response models."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Generic, TypeVar
import re

from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str | None, Field(default=None, max_length=500)] = None


class CategoryCreate(CategoryBase):
    parent_id: Annotated[int | None, Field(default=None, ge=1)] = None


class CategoryUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)] = None
    description: Annotated[str | None, Field(default=None, max_length=500)] = None
    parent_id: Annotated[int | None, Field(default=None, ge=1)] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:  # noqa: D417
        if value is not None and not value.strip():
            msg = "Category name cannot be empty"
            raise ValueError(msg)
        return value


class CategoryRead(CategoryBase):
    id: int
    parent_id: int | None = None
    full_path: str
    children: list["CategoryRead"] = []

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    amount: Annotated[float, Field(gt=0, description="Expense amount must be greater than zero")]
    currency: Annotated[str, Field(default='EUR', min_length=3, max_length=3, description="ISO 4217 currency code (e.g., EUR, USD, GBP)")]
    note: Annotated[str | None, Field(default=None, max_length=500)] = None
    created_at: Annotated[datetime | None, Field(default=None)] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:  # noqa: D417
        if value <= 0:
            msg = "Expense amount must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, value: str | None) -> str:  # noqa: D417
        """Validate ISO 4217 currency code."""
        # Handle None or empty values (for existing records that might not have currency)
        if not value or value == '':
            return 'EUR'
        
        # Ensure it's a string and uppercase
        value_str = str(value).strip().upper()
        
        if not value_str.isalpha() or len(value_str) != 3:
            msg = "Currency must be a valid 3-letter ISO 4217 code (e.g., EUR, USD, GBP)"
            raise ValueError(msg)
        # Liste des devises courantes acceptées
        valid_currencies = {
            'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB', 'TRY',
            'CNY', 'INR', 'BRL', 'ZAR', 'MXN', 'SGD', 'HKD', 'KRW'
        }
        if value_str not in valid_currencies:
            msg = f"Currency '{value_str}' is not supported. Supported currencies: {', '.join(sorted(valid_currencies))}"
            raise ValueError(msg)
        return value_str


class ExpenseCreate(ExpenseBase):
    category_id: int


class ExpenseRead(ExpenseBase):
    id: int
    category_id: int
    category_path: str | None = None
    created_at: datetime
    currency: str  # Explicitly include, inherited from ExpenseBase with validation

    class Config:
        from_attributes = True


class ExpenseUpdate(BaseModel):
    amount: Annotated[float | None, Field(default=None, gt=0)] = None
    currency: Annotated[str | None, Field(default=None, min_length=3, max_length=3)] = None
    note: Annotated[str | None, Field(default=None, max_length=500)] = None
    created_at: Annotated[datetime | None, Field(default=None)] = None
    category_id: int | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float | None) -> float | None:  # noqa: D417
        if value is not None and value <= 0:
            msg = "Expense amount must be greater than zero"
            raise ValueError(msg)
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:  # noqa: D417
        """Validate ISO 4217 currency code."""
        if value is None:
            return value
        if not value.isupper() or not value.isalpha() or len(value) != 3:
            msg = "Currency must be a valid 3-letter ISO 4217 code (e.g., EUR, USD, GBP)"
            raise ValueError(msg)
        valid_currencies = {
            'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB', 'TRY',
            'CNY', 'INR', 'BRL', 'ZAR', 'MXN', 'SGD', 'HKD', 'KRW'
        }
        if value not in valid_currencies:
            msg = f"Currency '{value}' is not supported. Supported currencies: {', '.join(sorted(valid_currencies))}"
            raise ValueError(msg)
        return value


class MonthlySummary(BaseModel):
    month: str
    total: float
    category_totals: dict[str, float]
    start_date: datetime | None = None
    end_date: datetime | None = None
    category_id: int | None = None


class UserBase(BaseModel):
    username: Annotated[str, Field(
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Username: 3-50 chars, alphanumeric with _ and - only"
    )]
    email: Annotated[str, Field(
        max_length=100,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="Valid email address"
    )]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=128, description="Password: 8-128 chars")]

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:  # noqa: D417
        """Ensure password has minimum complexity."""
        if not any(c.isupper() for c in v):
            msg = "Password must contain at least one uppercase letter"
            raise ValueError(msg)
        if not any(c.islower() for c in v):
            msg = "Password must contain at least one lowercase letter"
            raise ValueError(msg)
        if not any(c.isdigit() for c in v):
            msg = "Password must contain at least one digit"
            raise ValueError(msg)
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            msg = "Password must contain at least one special character (!@#$%^&*...)"
            raise ValueError(msg)
        return v


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class LoginResponse(Token):
    user: UserRead


T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta


class PaginatedCategories(PaginatedResponse[CategoryRead]):
    pass


class PaginatedExpenses(PaginatedResponse["ExpenseRead"]):
    pass


class TranslationBase(BaseModel):
    locale: Annotated[str, Field(min_length=2, max_length=5, pattern=r'^[a-z]{2}(-[A-Z]{2})?$')]
    key: Annotated[str, Field(min_length=1, max_length=200)]
    value: Annotated[str, Field(min_length=1)]


class TranslationCreate(TranslationBase):
    pass


class TranslationRead(TranslationBase):
    id: int

    class Config:
        from_attributes = True


class TranslationsResponse(BaseModel):
    """Response with all translations for a locale as a dictionary."""
    locale: str
    translations: dict[str, str]  # e.g., {'auth.login.title': 'Connexion', ...}

