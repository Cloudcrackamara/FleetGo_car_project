from fastapi import FastAPI
from functools import lru_cache
from sqlalchemy import create_engine

from pydantic_settings import BaseSettings, SettingsConfigDict


app = FastAPI()
class Settings(BaseSettings):
    # Application
    app_name: str = "FleetGo API"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Password hashing
    bcrypt_rounds: int = 12

    # Payment webhook
    webhook_secret: str

    # API
    api_prefix: str = "/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
engine = create_engine(settings.database_url)


@app.get("/test-db")
def test_db():
    with engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1")
        return {"database": result.scalar()}