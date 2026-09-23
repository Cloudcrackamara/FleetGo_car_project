"""Password hashing (bcrypt) and JWT helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import hashlib
import hmac as hmac_module


from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str, role: str, expires_minutes: int | None = None
) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": subject, "role": role, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    
    expected = hmac_module.new(
        settings.webhook_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    try:
        return hmac_module.compare_digest(expected, signature)
    except (ValueError, TypeError):
        return False