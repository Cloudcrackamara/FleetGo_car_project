from datetime import datetime

from sqlmodel import SQLModel


class WorkshopVisitCreate(SQLModel):
    comment: str | None = None


class WorkshopVisitRead(SQLModel):
    id: int
    car_id: int
    opened_at: datetime
    closed_at: datetime | None = None
    comment: str | None = None
