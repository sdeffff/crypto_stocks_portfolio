import jwt
import os
import dotenv
from datetime import datetime, timedelta
from fastapi import HTTPException, Response
from src.database.db import session
from sqlalchemy.orm import Session
from typing import Optional

from src.classes.request_types import UserType

from src.models.models import User

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


async def check_auth(res: Response, access_token: Optional[str], refresh_token: Optional[str]):
    try:
        if access_token:
            return jwt.decode(access_token, os.getenv("ACCESS_TOKEN_SECRET"), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        # Access token expired, attempt refresh token
        pass
    except jwt.InvalidTokenError:
        # Access token invalid, try refresh
        pass

    if not refresh_token:
        raise HTTPException(status_code=403, detail="Access token expired or invalid, and no refresh token provided.")

    try:
        auth_data = jwt.decode(refresh_token, os.getenv("REFRESH_TOKEN_SECRET"), algorithms=["HS256"])

        payload = {
            "uid": auth_data["uid"],
            "role": auth_data["role"],
            "email": auth_data["email"]
        }

        new_access_token = await create_token(payload, timedelta(minutes=15), os.getenv("ACCESS_TOKEN_SECRET"))

        res.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=os.getenv("PROD") == "production",
            samesite="lax",
            max_age=15 * 60
        )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
