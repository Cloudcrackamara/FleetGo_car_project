from fastapi import APIRouter, status

from app.core.dependencies import DbSession, require_role
from app.features.auth import schemas, service

router = APIRouter(tags=["Auth"])


@router.post("/auth/register", response_model=schemas.UserRead)
def register(payload: schemas.UserCreate, db: DbSession):
    return service.register(db, email=payload.email, password=payload.password)


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: DbSession):
    token = service.login(db, email=payload.email, password=payload.password)
    return schemas.TokenResponse(access_token=token)

@router.post(
    "/staff", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED,
    dependencies=[require_role("manager")],
)
def create_staff(payload: schemas.StaffCreate, db: DbSession):
    return service.create_staff(db, email=payload.email, password=payload.password, role=payload.role)
