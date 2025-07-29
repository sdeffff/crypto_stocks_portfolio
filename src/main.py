import os
import stripe

from dotenv import load_dotenv
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pycoingecko import CoinGeckoAPI
from typing import List

from src.database.db import session
from src.models.models import User, Subscritions, Notifications
from src.schemas.request_types import NotifyRequest
from src.auth.auth_service import check_auth

from src.helpers.subscription_helper import addSubscription

from src.routes import auth_route, stock_route, payment_route, user_route, crypto_route

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

app.include_router(auth_route.router, prefix="/auth")
app.include_router(crypto_route.router, prefix="/crypto")
app.include_router(stock_route.router, prefix="/stock")
app.include_router(payment_route.router, prefix="/payment")
app.include_router(user_route.router, prefix="/users")


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
         status_code=200,
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
         status_code=200,
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


@app.post("/buy-premium/",
          status_code=201,
          response_class=RedirectResponse)
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
