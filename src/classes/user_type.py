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


class CoinsRequest(BaseModel):
    currency: Optional[str] = None


class NotifyRequest(BaseModel):
    crypto_name: str
    value: int
