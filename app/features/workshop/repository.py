from sqlmodel import Session, select

from app.models.workshop_visit import WorkshopVisit


def get_open_for_car(db: Session, car_id: int) -> WorkshopVisit | None:
    return db.exec(
        select(WorkshopVisit)
        .where(WorkshopVisit.car_id == car_id, WorkshopVisit.closed_at.is_(None))
        .order_by(WorkshopVisit.opened_at.desc())
    ).first()


def create(db: Session, visit: WorkshopVisit) -> WorkshopVisit:
    db.add(visit)
    db.flush()
    return visit


def close(db: Session, visit: WorkshopVisit, *, closed_at=None) -> WorkshopVisit:
    visit.closed_at = closed_at
    db.add(visit)
    db.flush()
    return visit 
