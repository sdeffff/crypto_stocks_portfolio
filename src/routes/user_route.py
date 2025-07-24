from dotenv import load_dotenv
from typing import List

from fastapi import APIRouter, Response, Request
from fastapi.responses import JSONResponse

from src.auth.auth_service import check_auth, get_user_by_id
from src.schemas.request_types import UserType
from src.models.models import User
from src.database.db import session

load_dotenv()

router = APIRouter()


@router.get("/",
            response_model=List[UserType],
            response_description="Endpoint to get all of the users")
async def get_all_users(res: Response, req: Request) -> List[UserType]:
    try:
        auth_data = await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        if auth_data["role"] != "admin":
            return JSONResponse(
                status_code=401,
                content={"detail": "You are not allowed to do this"}
            )
    except Exception as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    return session.query(User).all()


@router.get("/{uid}/profile",
            response_description="Profile endpoint for every user")
async def user_profile(uid: str, res: Response, req: Request):
    try:
        await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        user_data = await get_user_by_id(uid)

        res.status_code = 200

        return user_data
    except Exception as e:
        res.status_code = 401
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
