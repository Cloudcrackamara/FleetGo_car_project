from app.features.auth.service import register
from app.models.user import User


def test_register_creates_user_and_returns_email(db):
    user = register(db, email="new-user@example.com", password="StrongPass123!")

    assert user.email == "new-user@example.com"
    assert user.id is not None
    assert db.get(User, user.id).email == "new-user@example.com"
