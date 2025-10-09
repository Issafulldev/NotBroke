"""SQLAlchemy models for categories and expenses."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    """Expense category."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

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
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    category: Mapped[Category] = relationship(
        "Category", back_populates="expenses", lazy="selectin"
    )

