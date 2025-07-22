from datetime import timedelta
import os

from dotenv import load_dotenv

from fastapi import APIRouter, Response, Request, HTTPException
from fastapi.responses import JSONResponse

from src.models.models import User
from src.schemas.request_types import UserType, LoginType, CodeRequest

from src.auth.auth_service import register_user, user_exists
from src.helpers.pwd_helper import comparePwds, hashPwd
from src.helpers.send_verif import send_verification_email, check_verified, check_code
from src.auth.auth_service import create_token, clear_tokens

from src.database.db import session

load_dotenv()

router = APIRouter()


@router.post("/register", status_code=201)
async def register(
    user_data: UserType,
    res: Response
):
    if await user_exists(session, user_data.email):
        raise HTTPException(status_code=406, detail="User with such email already exists")

    try:
        hashedPwd = (await hashPwd(user_data.password)).decode('utf-8')

        user_data.password = hashedPwd

        user_data.pfp = f"https://eu.ui-avatars.com/api/?name={user_data.username}"

        await register_user(user_data=user_data)

        res.status_code = 201

        send_verification_email(user_data.email, res)

        return JSONResponse(
            status_code=201,
            content="Verification code was sent to your email!"
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Happened some error with registration: {e}")


@router.post("/email-verification", status_code=202)
async def verify_email(code: CodeRequest, req: Request, res: Response):
    try:
        verif_status = check_code(req, code.code)
    except Exception as e:
        raise HTTPException(detail=f"Happened some error with code: {e}", status_code=404)

    if verif_status:
        res.status_code = 200

        req.cookies.clear()

        return "Your email was successfully confirmed, thanks!"
    else:
        res.status_code = 400

        return "Code you provided is incorrect, try again!"


@router.post("/login", status_code=202)
async def login(data: LoginType):
    if not check_verified(data.email):
        raise HTTPException(status_code=403, detail="You didn't verify your email")

    try:
        user = session.query(User).filter(User.email == data.email).first()

        doesMatch = await comparePwds(data.password, user.password)

        if not doesMatch:
            raise HTTPException(status_code=409, detail="Incorrect password for provided email")

        payload = {
            "uid": user.id,
            "role": user.role,
            "pfp": user.pfp,
            "username": user.username
        }

        res = JSONResponse(
            status_code=200,
            content={
                "message": "Logged in successfully",
                "usersData": payload
            }
        )

        access_token = await create_token(payload, timedelta(minutes=15), os.getenv("ACCESS_TOKEN_SECRET"))
        refresh_token = await create_token(payload, timedelta(days=1), os.getenv("REFRESH_TOKEN_SECRET"))

        res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=os.getenv("PROD") == "production",
            samesite="lax",
            max_age=15 * 60
        )

        res.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=os.getenv("PROD") == "production",
            samesite="lax",
            max_age=24 * 60 * 60
        )

        return res
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Happened some error with login: {e}")


@router.delete("/logout", status_code=200)
async def logout(res: Response):
    clear_tokens(res)

    return JSONResponse(
        status_code=200,
        content={"message": "Successfully logged out"}
    )
