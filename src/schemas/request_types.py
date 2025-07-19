from pydantic import BaseModel
from typing import Optional, List, Literal, Union
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


class isUserLoggedInType(BaseModel):
    uid: int = 0
    username: str = ""
    role: str = ""
    pfp: str = ""


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


class CodeRequest(BaseModel):
    code: str


class SparklineIn7D(BaseModel):
    price: List[float]


class StatisticsData(BaseModel):
    name: str
    image: Optional[str] = ""
    current_price: float
    high: float
    low: float
    sparkline_in_7d: SparklineIn7D
    price_change_percentage_7d_in_currency: float
    price_change_percentage_24h: float


class StatisticsResponse(BaseModel):
    data: List[StatisticsData]
    isLoggedIn: bool
    usersData: Union[isUserLoggedInType, dict]
