from app.core.security import hash_password
from app.features.auth.service import login, register
from app.models.user import User


def test_register_creates_user_and_returns_email(db):
    user = register(
        db,
        email="new-user@example.com",
        password="StrongPass123!",
    )

    assert user.email == "new-user@example.com"
    assert user.id is not None
    assert db.get(User, user.id).email == "new-user@example.com"


def test_register_sends_welcome_email(db, monkeypatch):
    captured = {}

    def fake_send_email(**kwargs):
        captured.update(kwargs)
        return {"status": "sent"}

    monkeypatch.setattr(
        "app.integrations.notifications.send_email", fake_send_email
    )

    register(db, email="welcome-user@example.com", password="StrongPass123!")

    assert captured["to_email"] == "welcome-user@example.com"
    assert "Welcome to FleetGo" in captured["subject"]


def test_login_sends_security_email(db, monkeypatch):
    captured = {}

    def fake_send_email(**kwargs):
        captured.update(kwargs)
        return {"status": "sent"}

    user = User(
        email="login-user@example.com",
        password_hash=hash_password("StrongPass123!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    monkeypatch.setattr(
        "app.integrations.notifications.send_email", fake_send_email
    )

    login(db, email="login-user@example.com", password="StrongPass123!")

    assert captured["to_email"] == "login-user@example.com"
    assert "login alert" in captured["subject"].lower()
