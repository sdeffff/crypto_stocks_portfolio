import os
import pandas as pd
import stripe
import httpx

from dotenv import load_dotenv
from datetime import timedelta
from fastapi import FastAPI, Response, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pycoingecko import CoinGeckoAPI
from typing import List, Optional

from src.database.db import session
from src.models.models import User, Subscritions, Notifications
from src.schemas.request_types import UserType, LoginType, CoinsRequest, NotifyRequest, StockRequest, CodeRequest
from src.auth.auth_service import register_user, user_exists, create_token, get_user_by_id, check_auth

from src.helpers.pwd_helper import hashPwd, comparePwds
from src.helpers.subscription_helper import addSubscription
from src.helpers.stocks_helper import get_stocks, get_stock_price
from src.helpers.send_verif import send_verification_email, check_code, check_verified


# TODO - imprve sqlalchemy queries, if they a potential issues
# TODO - change stocks functionality - from alpha vantage to yahoo finance

load_dotenv()

app = FastAPI()

allowed_origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@app.get("/users",
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


@app.get("/users/{uid}/profile",
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


@app.post("/auth/register", status_code=200)
async def register(user_data: UserType, res: Response):
    if await user_exists(session, user_data.email):
        raise HTTPException(status_code=404, detail="User with such email already exists")

    try:
        hashedPwd = (await hashPwd(user_data.password)).decode('utf-8')

        user_data.password = hashedPwd

        user_data.pfp = f"https://eu.ui-avatars.com/api/?name={user_data.username}"

        await register_user(user_data=user_data)

        res.status_code = 201

        send_verification_email(user_data.email, res)

        return "Verification email was sent tou your email address"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with registration: {e}")


@app.post("/auth/login", status_code=200)
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
            "email": user.email
        }

        res = JSONResponse(
            status_code=200,
            content={
                "message": "Logged in successfully",
                "uid": user.id
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
        raise HTTPException(status_code=500, detail=f"Happened some error with login: {e}")


@app.post("/email-verification")
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


@app.post("/crypto/coin-list",
          status_code=200,
          response_description="List of all available crypto currencies")
async def get_coin_list(
    payload: CoinsRequest, page: int = Query(1, ge=1),
    crypto: List[str] = Query(default=[]),
    sort_by: Optional[str] = Query("", min_length=0),
    sort_order: Optional[str] = Query("", min_length=0)
):
    try:
        data = cg.get_coins_markets(vs_currency=payload.currency or "usd", page=(page if page else 1))

        df = None

        if payload.names:
            df = pd.DataFrame(data)[["id", "image", "current_price"]]
        else:
            df = pd.DataFrame(data)[["id", "symbol", "image", "current_price", "market_cap", "market_cap_rank", "price_change_percentage_24h"]]

        if crypto:
            filtered_df = df[df.id.isin([c.lower() for c in crypto])]
        else:
            filtered_df = df

        sort_column = sort_by if sort_by else "current_price"
        sorted_df = filtered_df.sort_values(by=sort_column, ascending=(True if sort_order == "asc" else False))

        return sorted_df.head(payload.limit).to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with getting coins data: {e}")


@app.post("/stocks/stock-list", status_code=200,
          response_model=List[str],
          response_description="Get list of all stocks available")
async def get_stock_list(payload: StockRequest) -> List[str]:
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


@app.get("/stocks/{stock_name}",
         status_code=200,
         response_model=float,
         response_description="Get stock price by name")
async def get_stock_by_name(stock_name: str) -> float:
    try:
        result = await get_stock_price(stock_name=stock_name)

        return float(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with api: {e}")

# Notify me when stock/crpyto 'crypto_name/stock_name' is going to be less/greater than 'value' 'currency'


@app.post("/alert/",
          status_code=201,
          response_description="Add a subscription to check crypto/stock price")
async def notify_user(payload: NotifyRequest, res: Response, req: Request):
    try:
        auth_data = await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        res.status_code = 201

        return await addSubscription(payload, auth_data["uid"])
    except Exception as e:
        res.status_code = 401

        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


@app.get("/subscriptions/{uid}",
         response_model=List[NotifyRequest],
         response_description="Get list of  all of the users subscribtions")
async def get_subscriptions(uid: str, res: Response, req: Request) -> List[NotifyRequest]:
    try:
        auth_data = await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        if int(auth_data["uid"]) != int(uid):
            res.status_code = 409
            return JSONResponse(status_code=409, content={"detail": "You are not allowed to see others subscriptions"})

        return session.query(Subscritions).filter(Subscritions.uid == uid).all()
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": e})


@app.get("/notifications/{uid}",
         response_model=List[NotifyRequest],
         response_description="Get list of all notifications that were sent to the user")
async def get_notifications(uid: str, res: Response, req: Request) -> List[NotifyRequest]:
    try:
        auth_data = await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        if int(auth_data["uid"]) != int(uid):
            res.status_code = 409
            return JSONResponse(status_code=409, content={"detail": "You are not allowed to see others notifications"})

        return session.query(Notifications).filter(Notifications.uid == uid).all()
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": e})


@app.post("/buy-premium/", response_class=RedirectResponse)
async def buy_premium(res: Response, req: Request):
    try:
        auth_data = await check_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

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
