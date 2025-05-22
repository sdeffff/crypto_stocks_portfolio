import jwt
import dotenv
from datetime import datetime, timedelta
from fastapi import HTTPException
from database.db import session
from sqlalchemy.orm import Session

from classes.user_type import UserType

from models.models import User

dotenv.load_dotenv()


async def create_token(payload: dict, exp: timedelta, secret: str):
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.now() + exp
    return jwt.encode(payload_copy, secret, algorithm="HS256")


async def check_if_user_exists(session: Session, email: str) -> bool:
    user = session.query(User).filter(User.email == email).first()

    return True if user else False


async def register_user(user_data: UserType):
    try:
        new_user = (User(**user_data.model_dump()))

        session.add(new_user)
        session.commit()

        session.refresh(new_user)
    except BaseException:
        session.rollback()
        raise HTTPException(status_code=500, detail="Database error")


async def get_user_by_id(uid: str):
    uid = int(uid)

    result = session.query(User.id, User.email, User.username, User.country, User.role).filter(User.id == uid).first()

    return {
        "id": result[0],
        "email": result[1],
        "username": result[2],
        "country": result[3],
        "role": result[4],
    }
