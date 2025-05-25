from fastapi import HTTPException
from src.classes.request_types import NotifyRequest
from src.models.models import Subscritions
from src.database.db import session

# basically function to add subscription to table


async def addSubscription(payload: NotifyRequest, uid: int):
    try:
        data = payload.model_dump()

        data["uid"] = uid

        print(data)

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
