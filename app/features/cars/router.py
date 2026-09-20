from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import DbSession, require_role
from app.features.cars import schemas, service


router = APIRouter(tags=["cars"])


@router.post(
    "/cars",
    response_model=schemas.CarRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_role("manager")],
)
def create_car(
    payload: schemas.CarCreate,
    db: DbSession,
):
    return service.create_car(
        db,
        plate_no=payload.plate_no,
        car_class=payload.car_class,
    )


@router.get(
    "/cars",
    response_model=list[schemas.CarRead],
)
def search_cars(
    db: DbSession,
    query: Annotated[
        schemas.CarAvailabilityQuery,
        Depends(),
    ],
):
    return service.search_available_cars(
        db,
        car_class=query.car_class,
        start=query.start,
        end=query.end,
    )


@router.put(
    "/pricing/{car_class}",
    response_model=schemas.PricingRead,
    dependencies=[require_role("manager")],
)
def update_pricing(
    car_class: str,
    payload: schemas.PricingUpdate,
    db: DbSession,
):
    return service.set_pricing(
        db,
        car_class,
        daily_rate=payload.daily_rate,
        lateness_fee=payload.lateness_fee,
    )