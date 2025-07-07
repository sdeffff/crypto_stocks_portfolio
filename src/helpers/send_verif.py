import random

from fastapi.responses import Response
from fastapi.requests import Request
from src.celery_worker import send_email
from src.models.models import Verifications, User

from src.database.db import session


def send_verification_email(email: str, res: Response):
    code = random.randint(1000, 9999)

    verification_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 500px; margin: auto; background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h2 style="color: #2ecc71;">Crypto&Stocks Tracker</h2>
                <p>Hello,</p>
                <p>Thank you for registering on our platform.</p>
                <p>Please confirm your email by entering the following verification code:</p>
                <p style="font-size: 24px; font-weight: bold; color: #3498db; letter-spacing: 4px; text-align: center;">{code}</p>
                <p>If you didn't request this, you can safely ignore this email.</p>
                <p style="margin-top: 20px;">— The Crypto&Stocks Tracker Team</p>
                </div>
            </body>
        </html>
    """

    send_email.delay([email],
                     "Email verification on Crypto&Stocks Tracker",
                     verification_content)

    verification = (Verifications(email=email, code=code))

    session.add(verification)
    session.commit()

    res.set_cookie(
        key="user_email",
        value=email,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=5 * 60
    )


def check_code(req: Request, code: str):
    user_email = req.cookies.get("user_email")

    if not user_email:
        return False

    verif, user = (
        session.query(Verifications, User)
        .join(User, User.email == Verifications.email)
        .filter(Verifications.email == user_email)
        .first()
    )

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
