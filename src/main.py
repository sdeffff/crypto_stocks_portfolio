import os
import jwt
import pandas as pd

from datetime import timedelta
from typing import List, Optional
from database.db import session
from fastapi import FastAPI, Response, HTTPException, Cookie

from models.models import User

from classes.user_type import UserType, LoginType

from pycoingecko import CoinGeckoAPI

from auth.auth_service import register_user, check_if_user_exists, create_token, get_user_by_id
from helpers.pwd_helper import hashPwd, comparePwds

app = FastAPI()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))


@app.get("/")
def home():
    return {"Data": "test"}


@app.get("/users", response_model=List[UserType])
def get_all_users() -> List[UserType]:
    return session.query(User).all()


"""API to get cryptocurrency in currency we want"""


@app.get("/crypto/currency/{crypto_name}/{currency}", status_code=200)
async def get_crypto_price(crypto_name, currency, res: Response):
    try:
        data = cg.get_price(ids=str.lower(crypto_name),
                            vs_currencies=str.lower(currency),
                            include_market_cap=True,
                            include_24hr_change=True)

        price = data[f'{crypto_name}'][currency]

        formatted = f"{price:,}".replace(",", " ")

        res.status_code = 200

        return {
            "data": data,
            "price": formatted
        }
    except BaseException:
        raise HTTPException(status_code=404, detail="Provided incorrect crypto currency or currency")


@app.get("/crypto/coin-list", status_code=200)
def get_coin_list(res: Response):
    try:
        data = cg.get_coins_list()
        coinDataFrame = pd.DataFrame.from_dict(data).sort_values('id').reset_index(drop=True)

        return coinDataFrame.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Happened some error with getting coins data {e}")


@app.post("/auth/register", status_code=200)
async def register(user_data: UserType, res: Response):
    if await check_if_user_exists(session, user_data.email):
        raise HTTPException(status_code=400, detail="User with such email already exists")

    try:
        hashedPwd = (await hashPwd(user_data.password)).decode('utf-8')

        user_data.password = hashedPwd

        await register_user(user_data=user_data)

        res.status_code = 201

        return {
            "Message": "Registered succesfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with registration: {e}")


@app.post("/auth/login", status_code=200)
async def login(data: LoginType, res: Response):
    if not (await check_if_user_exists(session, data.email)):
        raise HTTPException(status_code=400, detail="There is no user with suh email")

    try:
        user = session.query(User).filter(User.email == data.email).first()

        doesMatch = await comparePwds(data.password, user.password)

        if not doesMatch:
            raise HTTPException(status_code=409, detail="Incorrect password for provided email")

        payload = {
            "uid": user.id,
            "role": user.role
        }

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

        return {
            "Message": "Logged in succesfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with login: {e}")


@app.get("/users/{uid}/profile")
async def user_profile(uid: str, res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    if not access_token and not refresh_token:
        raise HTTPException(status_code=403, detail="You must be authenticated")

    if access_token:
        auth_data = jwt.decode(access_token, os.getenv("ACCESS_TOKEN_SECRET"), "HS256")

        user_data = await get_user_by_id(uid)

        res.status_code = 200

        return user_data
    elif refresh_token:
        auth_data = jwt.decode(refresh_token, os.getenv("REFRESH_TOKEN_SECRET"), "HS256")

        payload = {
            "uid": auth_data["uid"],
            "role": auth_data["role"]
        }

        user_data = await get_user_by_id(uid)

        refreshed_access_token = await create_token(payload, timedelta(minutes=15), os.getenv("ACCESS_TOKEN_SECRET"))

        res.set_cookie(
            key="access_token",
            value=refreshed_access_token,
            httponly=True,
            secure=os.getenv("PROD") == "production",
            samesite="lax",
            max_age=15 * 60
        )

        res.status_code = 200

        return user_data
    else:
        raise HTTPException(status_code=403, detail="You must be authenticated")
