from pydantic import BaseModel
from typing import Optional
from datetime import datetime

"""Models/Classes to identify types of data in endpoints"""


class UserType(BaseModel):
    username: str
    email: str
    password: str
    country: str
    role: Optional[str] = "user"
    pfp: Optional[str] = ""


class UserProfileType(BaseModel):
    id: int
    username: str
    email: str
    country: str
    role: str


class LoginType(BaseModel):
    email: str
    password: str


class CoinsRequest(BaseModel):
    currency: Optional[str] = None
    limit: Optional[int] = 50
    names: Optional[bool] = False


class NotifyRequest(BaseModel):
    check_type: str
    what_to_check: str
    operator: str
    value: int
    currency: str


class NotifyModel(BaseModel):
    check_type: str
    what_to_check: str
    operator: str
    value: int
    currency: str
    created_at: datetime


class StockRequest(BaseModel):
    stock_name: Optional[str] = ""


class CodeRequest(BaseModel):
    code: str
