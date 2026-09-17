from fastapi import FastAPI


app = FastAPI(
    title="FleetGo API",
    description="Car rental fleet management API",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
