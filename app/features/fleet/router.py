
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.dependencies import DbSession, require_role
from app.events.broadcaster import fleet_broadcaster
from app.features.fleet import schemas, service

router = APIRouter(prefix="/fleet", tags=["Reports"])


@router.get(
    "/board",
    response_model=list[schemas.FleetBoardRow],
    dependencies=[require_role("manager")],
)
def get_fleet_board(db: DbSession):
    return service.get_board(db)


# GET /fleet/stream (SSE) is NOT built yet — deliberately. It needs to
# push real state changes, and nothing publishes those until
# lifecycle.py (Rentals) exists and calls a broadcaster on every
# accepted move. Building this now would be an endpoint with nothing
# to say. Comes back once Rentals is done.

@router.get("/stream", dependencies=[require_role("manager")])
async def fleet_stream():
    return StreamingResponse(
        fleet_broadcaster.subscribe(), media_type="text/event-stream"
    )