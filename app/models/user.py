from enum import Enum
from sqlmodel import Field,SQLModel

class UserRole(str,Enum):
    CUSTOMER ="customer"
    AGENT = "agent"
    MANAGER = "manager"
    
    
class UserRole(SQLModel,table=True):
    __tablename__ = "users"
    
    id:int| None =Field(default=None,primary_key=True)
    email: str = Field(unique=True,index=True)
    password_hash:str
    role:UserRole = Field(default=UserRole.CUSTOMER)