from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.features.auth import schemas, service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=schemas.UserRead)
def register(payload: schemas.UserCreate, db: DbSession):
    return service.register(db, email=payload.email, password=payload.password)


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: DbSession):
    token = service.login(db, email=payload.email, password=payload.password)
    return schemas.TokenResponse(access_token=token)
