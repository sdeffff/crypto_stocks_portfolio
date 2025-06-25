import random
import os

from fastapi.responses import Response
from fastapi.requests import Request
from src.celery_worker import send_email
from src.models.models import Verifications, User

from src.database.db import session


def send_verification_email(email: str, res: Response):
    code = random.randint(1000, 9999)

    send_email.delay([email],
                     "Email verification on Crypto&Stocks Tracker",
                     f"Hello, you have registered to our platform confirm your email by entering the following code: {code}")

    verification = (Verifications(email=email, code=code))

    session.add(verification)
    session.commit()

    res.set_cookie(
        key="user_email",
        value=email,
        httponly=True,
        secure=os.getenv("PROD") == "production",
        samesite="lax",
        max_age=5 * 60
    )


def check_code(req: Request, code: str):
    user_email = req.cookies.get("user_email")

    if not user_email:
        return False

    verif = session.query(Verifications).filter(Verifications.email == user_email).first()
    user = session.query(User).filter(User.email == verif.email).first()

    if verif and code == verif.code and user:
        user.verified = True
        session.delete(verif)

        session.commit()

        return True
    else:
        return False


def check_verified(email: str):
    current_user = session.query(User).filter(User.email == email).first()

    if current_user.verified:
        return True
    else:
        return False
