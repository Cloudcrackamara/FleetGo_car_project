
from sqlmodel import Session

from app.features.fleet import repository
from app.models.car import Car


def get_board(db: Session) -> list[Car]:
    return repository.list_all_cars(db)