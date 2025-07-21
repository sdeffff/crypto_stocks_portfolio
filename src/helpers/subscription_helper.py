from fastapi import HTTPException
from src.schemas.request_types import NotifyRequest
from src.models.models import Subscritions, User
from src.database.db import session


async def addSubscription(payload: NotifyRequest, uid: int):
    user = session.query(User).filter(User.id == uid).first()
    users_subscriptions = session.query(Subscritions).filter(Subscritions.uid == uid).all()

    if (not user.premium and len(users_subscriptions) >= 4) or (user.premium and len(users_subscriptions) >= 25):
        return HTTPException(status_code=409, detail="You reached the limit for subscriptions")

    try:
        data = payload.model_dump()

        data["uid"] = uid

        subscription = (Subscritions(**data))

        session.add(subscription)
        session.commit()

        return {
            "detail": "Your subscribtion was successfully created!"
        }
    except Exception as e:
        session.rollback()

        raise HTTPException(status_code=400, detail=f"Something went wrong {e}")


def name_to_sign(name: str):
    name_sign = {
        "usd": "$",
        "eur": "€",
        "pln": "pln",
        "czk": "czk",
        "uah": "₴",
        "gbp": "£"
    }

    return name_sign[name]
