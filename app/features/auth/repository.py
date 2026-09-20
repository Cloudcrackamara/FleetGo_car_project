# app/features/auth/repository.py
"""Every database query for User, in one place. Nothing outside this
file runs a query against the users table. Returns rows or None —
never raises HTTP errors, never commits (that's the service's job).
"""

from sqlmodel import Session, select

from app.models.user import User


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.exec(select(User).where(User.email == email)).first()


def create(db: Session, user: User) -> User:
    db.add(user)
    db.flush()  # assigns user.id without committing — service commits
    return user
