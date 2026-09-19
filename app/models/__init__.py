#This makes alembic discover all models

from app.models.user import UserRole


__all__ = [
    "UserRole",
]