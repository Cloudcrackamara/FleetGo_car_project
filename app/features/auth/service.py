
from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.features.auth import repository
from app.models.user import User, UserRole


def register(
    db: Session, *, email: str, password: str, role: UserRole = UserRole.CUSTOMER
) -> User:
    if repository.get_by_email(db, email):
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"a user with email {email} already exists"
        )
    user = repository.create(
        db, User(email=email, password_hash=hash_password(password), role=role)
    )
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, *, email: str, password: str) -> str:
    user = repository.get_by_email(db, email)
    # Same generic message whether the email doesn't exist or the
    # password is wrong — a login endpoint shouldn't leak which
    # emails are registered.
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")
    return create_access_token(subject=str(user.id), role=user.role.value)