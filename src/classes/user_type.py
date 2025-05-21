from pydantic import BaseModel
from typing import Optional


class UserType(BaseModel):
    username: str
    email: str
    password: str
    country: str
    role: Optional[str] = "user"


class LoginType(BaseModel):
    email: str
    password: str
