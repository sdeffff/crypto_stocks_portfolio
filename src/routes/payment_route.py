import stripe
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.models.models import User

from src.database.db import session

router = APIRouter()

load_dotenv()


@router.get("/success", response_class=HTMLResponse)
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


@router.get("/fail", response_class=HTMLResponse)
async def payment_fail(req: Request):
    return "<h1>Payment was unsucessfull, try again later!</h1>"
