import json

from sqlmodel import Session

from app.core.redis_client import redis_client
from app.features.fleet import repository
from app.models.car import Car

FLEET_BOARD_CACHE_KEY = "fleet:board"
FLEET_BOARD_CACHE_TTL = 30


def get_board(db: Session) -> list[Car] | list[dict]:
    cached = redis_client.get(FLEET_BOARD_CACHE_KEY)
    if cached is not None:
        return json.loads(cached)

    cars = repository.list_all_cars(db)

    serialized = json.dumps([car.model_dump(mode="json") for car in cars])
    redis_client.setex(FLEET_BOARD_CACHE_KEY, FLEET_BOARD_CACHE_TTL, serialized)

    return cars