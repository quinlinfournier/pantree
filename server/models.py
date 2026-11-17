from __future__ import annotations

from datetime import UTC, datetime, date
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )
    # author: Mapped[str] = mapped_column(String, nullable=True)
    # receipts: Mapped[list[Receipt]] = relationship(back_populates="author")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media.profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"
# TODO: Fix Receipt to match the json file import

class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    retailer: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    raw_retailer: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, unique=False, nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey(User.id), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String, unique=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    items: Mapped[list[ReceiptItem]] = relationship(back_populates="receipt", cascade="all, delete-orphan")

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_description: Mapped[str | None] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    receipt: Mapped[Receipt] = relationship(back_populates="items")