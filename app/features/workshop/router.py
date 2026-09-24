from fastapi import APIRouter, Body, status

from app.core.dependencies import DbSession, require_role
from app.features.cars import schemas as car_schemas
from app.features.workshop import schemas, service

router = APIRouter(tags=["Workshop"])


@router.post(
    "/cars/{car_id}/workshop",
    response_model=car_schemas.CarRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_role("manager")],
)
def send_car_to_workshop(
    car_id: int,
    payload: schemas.WorkshopVisitCreate | None = Body(default=None),
    db: DbSession = None,
):
    return service.send_to_workshop(
        db,
        car_id,
        comment=(payload.comment if payload else None),
    )


@router.post(
    "/cars/{car_id}/back-in-service",
    response_model=car_schemas.CarRead,
    dependencies=[require_role("manager")],
)
def return_car_from_workshop(
    car_id: int,
    payload: schemas.WorkshopVisitCreate | None = Body(default=None),
    db: DbSession = None,
):
    return service.return_from_workshop(
        db,
        car_id,
        comment=(payload.comment if payload else None),
    )
