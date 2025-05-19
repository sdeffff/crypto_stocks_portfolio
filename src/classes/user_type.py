from pydantic import BaseModel

class UserType(BaseModel):
    username: str
    email: str
    password: str
    country: str
    role: str