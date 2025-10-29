"""SQLAlchemy models for categories and expenses."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """User account for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relations avec les données existantes
    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    """Expense category."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    expenses: Mapped[list[Expense]] = relationship(
        "Expense", back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )
    parent: Mapped[Category | None] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
        single_parent=True,
    )
    user: Mapped[User] = relationship("User", back_populates="categories")

    __table_args__ = (
        Index('idx_categories_user_name', 'user_id', 'name'),
    )

    @property
    def full_path(self) -> str:
        """Return the category name prefixed with its ancestors."""
        parts: list[str] = []
        current: Category | None = self
        visited: set[int] = set()
        while current is not None and current.id not in visited:
            visited.add(current.id)
            parts.append(current.name)
            current = current.parent
        return " / ".join(reversed(parts)) if parts else self.name

    @full_path.setter
    def full_path(self, value: str) -> None:  # noqa: D401,D417 - placeholder setter for serialization
        # SQLAlchemy instantiates models without allowing attribute assignment on @property attributes.
        # Providing a no-op setter keeps ORM happy when we assign full_path dynamically.
        self.__dict__["_full_path_override"] = value

    @full_path.deleter
    def full_path(self) -> None:  # type: ignore[override]
        self.__dict__.pop("_full_path_override", None)


class Expense(Base):
    """Individual expense entries for a given category."""

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default='EUR')  # ISO 4217 code
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    category: Mapped[Category] = relationship(
        "Category", back_populates="expenses", lazy="selectin"
    )
    user: Mapped[User] = relationship("User", back_populates="expenses")

    __table_args__ = (
        Index('idx_expenses_user_created', 'user_id', 'created_at'),
        Index('idx_expenses_category_user', 'category_id', 'user_id'),
    )


class Translation(Base):
    """Translation strings for internationalization (i18n)."""

    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    locale: Mapped[str] = mapped_column(String(5), nullable=False)  # 'fr', 'en', 'ru'
    key: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g., 'auth.login.title'
    value: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., 'Connexion'

    __table_args__ = (
        Index('idx_translations_locale_key', 'locale', 'key'),
    )

