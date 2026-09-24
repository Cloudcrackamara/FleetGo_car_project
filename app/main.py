from typing import Annotated

from fastapi import Depends, FastAPI
from sqlmodel import Session, text

from app.core.config import settings
from app.core.error import register_error_handlers
from app.db.session import get_session
from app.features.auth.router import router as auth_router
from app.features.cars.router import router as cars_router
from app.features.fleet.router import router as fleet_router
from app.features.payments.router import router as payments_router
from app.features.payments.webhook_router import router as webhook_router
from app.features.rentals.router import router as rentals_router
from app.features.workshop.router import router as workshop_router
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware


app = FastAPI(title="FleetGo", version="0.1.0")

register_error_handlers(app)
app.include_router(cars_router, prefix=settings.api_prefix)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(fleet_router, prefix=settings.api_prefix)
app.include_router(payments_router, prefix=settings.api_prefix)
app.include_router(rentals_router, prefix=settings.api_prefix)
app.include_router(workshop_router, prefix=settings.api_prefix)
app.include_router(webhook_router, prefix=settings.api_prefix)


@app.get("/test-db")
def test_db(db: Annotated[Session, Depends(get_session)]):
    result = db.scalar(text("SELECT 1"))

    return {
        "status": "connected",
        "result": result,
    }
