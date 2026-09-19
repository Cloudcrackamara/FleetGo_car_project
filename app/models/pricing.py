# app/models/pricing.py
from decimal import Decimal

from sqlalchemy import Numeric
from sqlmodel import Column, Field, SQLModel


class Pricing(SQLModel, table=True):
    __tablename__ = "pricing"

    id: int | None = Field(default=None, primary_key=True)
    # One price row per class — unique, so PUT /pricing/{class} has
    # exactly one row to update, not "which one?"
    car_class: str = Field(unique=True, index=True)
    daily_rate: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    lateness_fee: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))