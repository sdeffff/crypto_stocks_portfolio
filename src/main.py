import os
import pandas as pd
import stripe
import httpx

from dotenv import load_dotenv
from datetime import timedelta
from typing import Optional
from fastapi import FastAPI, Response, Request, HTTPException, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from pycoingecko import CoinGeckoAPI

from src.database.db import session
from src.models.models import User, Subscritions, Notifications
from src.classes.request_types import UserType, LoginType, CoinsRequest, NotifyRequest, StockRequest
from src.auth.auth_service import register_user, check_if_user_exists, create_token, get_user_by_id, check_auth
from src.helpers.pwd_helper import hashPwd, comparePwds
from src.celery_worker import send_email
from src.helpers.subscription_helper import addSubscription
from src.helpers.stocks_helper import get_stocks, get_stock_price

load_dotenv()

app = FastAPI()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@app.get("/")
def home():
    return {"Data": "test"}


@app.post("/test-email/")
async def send_user_email(payload: NotifyRequest, res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    auth_data = await check_auth(res, access_token, refresh_token)

    if auth_data:
        print(auth_data)

        try:
            send_email.delay([auth_data["email"]], "sample email", f"Notify the user with email: {auth_data["email"]} when {payload.crypto_name} is going to be {payload.state} than {payload.value} {payload.currency}")

            res.status_code = 201

            return {"Message": f"Email was sent successfully to your email: {auth_data['email']}"}
        except Exception as e:
            res.status_code = 500

            return HTTPException(status_code=500, detail=f"Failed to send email: {e}")
    else:
        return HTTPException(status_code=401, detail="You have to be authenticated")


@app.get("/users")
async def get_all_users(res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    try:
        auth_data = await check_auth(res, access_token, refresh_token)

        if auth_data["role"] != "admin":
            res.status_code = 401

            return HTTPException(status_code=401, detail="You are not allowed to do this")
    except Exception:
        return HTTPException(status_code=401, detail="You are not authenticated!")

    return session.query(User).all()


@app.post("/auth/register", status_code=200)
async def register(user_data: UserType, res: Response):
    if await check_if_user_exists(session, user_data.email):
        raise HTTPException(status_code=400, detail="User with such email already exists")

    try:
        hashedPwd = (await hashPwd(user_data.password)).decode('utf-8')

        user_data.password = hashedPwd

        user_data.pfp = f"https://eu.ui-avatars.com/api/?name={user_data.username}"

        await register_user(user_data=user_data)

        res.status_code = 201

        return {
            "Message": "Registered succesfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with registration: {e}")


@app.post("/auth/login", status_code=200)
async def login(data: LoginType, res: Response):
    try:
        user = session.query(User).filter(User.email == data.email).first()

        doesMatch = await comparePwds(data.password, user.password)

        if not doesMatch:
            raise HTTPException(status_code=409, detail="Incorrect password for provided email")

        payload = {
            "uid": user.id,
            "role": user.role,
            "email": user.email
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
    try:
        await check_auth(res, access_token, refresh_token)

        user_data = await get_user_by_id(uid)

        res.status_code = 200

        return user_data
    except BaseException:
        return HTTPException(status_code=401, detail="You must be authenticated")


"""API to get cryptocurrency in currency we want"""


@app.get("/crypto/currency/{crypto_name}/{currency}", status_code=200)
async def get_crypto_price(crypto_name, currency, res: Response):
    try:
        data = cg.get_price(ids=str.lower(crypto_name),
                            vs_currencies=str.lower(currency),
                            include_market_cap=True,
                            include_24hr_change=True,
                            include_price_change_percentage_24h=True)

        price = data[f'{crypto_name}'][currency]

        formatted = f"{price:,}".replace(",", " ")

        res.status_code = 200

        return {
            "data": data,
            "price": formatted
        }
    except BaseException:
        raise HTTPException(status_code=404, detail="Provided incorrect crypto currency or currency")


@app.post("/crypto/coin-list", status_code=200)
async def get_coin_list(payload: CoinsRequest):
    try:
        data = cg.get_coins_markets(vs_currency=payload.currency or "usd", page=1)

        df = None

        if payload.names:
            df = pd.DataFrame(data)[["id", "image", "current_price"]]
        else:
            df = pd.DataFrame(data)[["id", "symbol", "image", "current_price", "market_cap", "market_cap_rank", "price_change_percentage_24h"]]

        return df.sort_values(by="current_price", ascending=False).head(payload.limit).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with getting coins data: {e}")


@app.post("/stocks/stock-list", status_code=200)
async def get_stock_list(payload: StockRequest, req: Request):
    try:
        if payload.stock_name == "":
            return get_stocks()
        else:
            av_api = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={payload.stock_name}&apikey={os.getenv('ALPHA_VANTAGE_SECRET_KEY')}"

            async with httpx.AsyncClient() as client:
                response = await client.get(av_api)

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Happened error with server")

            result = [item["1. symbol"] for item in response.json()["bestMatches"]]

            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with api: {e}")


@app.get("/stocks/{stock_name}", status_code=200)
async def get_stock_by_name(stock_name: str):
    try:
        result = await get_stock_price(stock_name=stock_name)

        return float(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with api: {e}")

# Notify me when stock/crpyto 'crypto_name/stock_name' is going to be less/greater than 'value' 'currency'


@app.post("/alert/")
async def notify_user(payload: NotifyRequest, res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    try:
        auth_data = await check_auth(res, access_token, refresh_token)

        res.status_code = 201

        return await addSubscription(payload, auth_data["uid"])
    except Exception as e:
        res.status_code = 401

        return HTTPException(status_code=401, detail=f"You are not authenticated: {e}")


@app.get("/subscriptions/{uid}")
async def get_subscriptions(uid: str, res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    try:
        auth_data = await check_auth(res, access_token, refresh_token)

        if int(auth_data["uid"]) != int(uid):
            res.status_code = 409
            return HTTPException(status_code=409, detail="You are not allowed to see others subscriptions")

        return session.query(Subscritions).filter(Subscritions.uid == uid).all()
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Happened smth wrong with getting subscriptions: {e}")


@app.get("/notifications/{uid}")
async def get_notifications(uid: str, res: Response, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    try:
        auth_data = await check_auth(res, access_token, refresh_token)

        if int(auth_data["uid"]) != int(uid):
            res.status_code = 409
            return HTTPException(status_code=409, detail="You are not allowed to see others notifications")

        return session.query(Notifications).filter(Notifications.uid == uid).all()
    except Exception:
        return HTTPException(status_code=401, detail="You must be authenticated!")


@app.post("/buy-premium/", response_class=RedirectResponse)
async def buy_premium(res: Response, req: Request, access_token: Optional[str] = Cookie(None), refresh_token: Optional[str] = Cookie(None)):
    try:
        auth_data = await check_auth(res, access_token, refresh_token)

        user = session.query(User).filter(User.id == int(auth_data["uid"])).first()

        if user.premium:
            raise HTTPException(status_code=409, detail="You are already premium user!")

        base_url = str(req.base_url).rstrip("/")
        success_url = f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        fail_url = f"{base_url}/payment/fail"

        try:
            checkout = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': 1499,
                        'product_data': {
                            'name': "Premium account for Crypto tracker"
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                billing_address_collection='required',
                success_url=success_url,
                cancel_url=fail_url,
                customer_email=auth_data["email"]
            )

            return RedirectResponse(checkout.url, status_code=200)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Happened some error with checkout session: {e}")
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"{e}")


@app.get("/payment/success", response_class=HTMLResponse)
async def payment_success(req: Request):
    session_id = req.query_params.get("session_id")

    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
        users_email = stripe_session.get("customer_email")

        user = session.query(User).filter(User.email == users_email).first()

        if user:
            user.premium = True
            session.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened error with payment: {e}")

    return "<h1>Payment Successful! You're now a premium user 🎉</h1>"


@app.get("/payment/fail", response_class=HTMLResponse)
async def payment_fail(req: Request):
    return "<h1>Payment was unsucessfull, try again later!</h1>"
