"""One-command bootstrap for the first manager account.

Every subsequent agent/manager gets created properly through
POST /api/v1/auth/staff (manager-only) — this script exists purely
to solve the chicken-and-egg problem of who creates the very first
manager, since that endpoint requires a manager token to call.

Run once:
    docker compose exec api uv run python -m app.db.seed

Safe to run more than once — it checks for an existing email before
inserting, so it won't create duplicates on a second run.
"""

from sqlmodel import Session, select

from app.core.security import hash_password
from app.db.session import engine
from app.models.user import User, UserRole


def main() -> None:
    with Session(engine) as db:
        existing = db.exec(
            select(User).where(User.email == "amarachi@gmail.com")
        ).first()
        if existing:
            print("manager@fleetgo.test already exists — nothing to do")
            return

        manager = User(
            email="amarachi@gmail.com",
            password_hash=hash_password("comebookaride4U"),
            role=UserRole.MANAGER,
        )
        db.add(manager)
        db.commit()
        print("seeded first manager account: amarachi@gmail.com")


if __name__ == "__main__":
    main()
    
    