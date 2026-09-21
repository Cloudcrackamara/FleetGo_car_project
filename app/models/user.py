from enum import StrEnum

from sqlmodel import Field, SQLModel


class UserRole(StrEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    MANAGER = "manager"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.CUSTOMER)