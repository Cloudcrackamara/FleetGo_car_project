from fastapi import FastAPI, Depends
from sqlmodel import Session, text

from app.db.session import get_session


app = FastAPI()



@app.get("/test-db")
def test_db(db: Session = Depends(get_session)):
    result = db.scalar(text("SELECT 1"))
    
    return {
        "status": "connected",
        "result": result
    }