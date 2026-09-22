from sqlmodel import SQLModel

from app.models.user import UserRole


class UserCreate(SQLModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {"email": "chidi@example.com", "password": "a-strong-password"}
        }
    }


class UserLogin(SQLModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {"email": "chidi@example.com", "password": "a-strong-password"}
        }
    }


class UserRead(SQLModel):
    id: int
    email: str
    role: UserRole


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    
    
class StaffCreate(SQLModel):
    email: str
    password: str
    role: UserRole  