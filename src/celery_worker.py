import sys
import os
import asyncio

from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from celery import Celery
from celery.schedules import crontab
from src.mail import mail, create_message
from src.database.db import session
from src.models.models import Subscritions, User, Notifications
from src.helpers.subscription_helper import name_to_sign
from src.helpers.stocks_helper import get_stock_price

load_dotenv()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

sys.path.insert(0, os.path.dirname((os.path.abspath(__file__))))

# Create Celery app
app = Celery(
    'crypto-tracker',
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)


@app.task
def send_email(recipients: list[str], subject: str, body: str):
    try:
        message = create_message(recipients, subject, body)
        asyncio.run(mail.send_message(message))
        return "Email sent successfully"
    except Exception as e:
        raise e


def add_notif(sub: Subscritions):
    notif = Notifications(
        check_type=sub.check_type,
        uid=sub.uid,
        what_to_check=sub.what_to_check,
        operator=sub.operator,
        value=sub.value,
        currency=sub.currency
    )

    session.add(notif)
    session.delete(sub)
    session.commit()


"""Helper function to check if threshold was reached"""


def check_operators(operator: str, threshold: float, current: float) -> bool:
    return (operator == "greater" and current > threshold) or (operator == "less" and current < threshold)


"""Function to send email to user"""


def send_formatted_email(user: User, sub: Subscritions, current_value: float):
    symbol = "📈" if sub.operator == "greater" else "📉"

    send_email.delay([user.email],
                     f"{(sub.what_to_check).upper()} is {sub.operator} than {sub.value}{name_to_sign(sub.currency) or sub.currency}{symbol}!",
                     f"The value of {sub.what_to_check} is now {current_value}{name_to_sign(sub.currency) or sub.currency}, is higher than your threshhold of {sub.value}{name_to_sign(sub.currency) or sub.currency}.`📊")

    add_notif(sub)

"""Main method, which decides what to send, subscription type"""


def check_subscriptions(sub: Subscritions, user: User):
    if sub.check_type == "stock":
        current_price = asyncio.run(get_stock_price(sub.what_to_check))
    elif sub.check_type == "crypto":
        price_data = cg.get_price(ids=sub.what_to_check, vs_currencies=sub.currency, include_market_cap=True)
        current_price = price_data[sub.what_to_check][sub.currency]
    else:
        return

    if check_operators(sub.operator, sub.value, current_price):
        send_formatted_email(user, sub, current_price)


@app.task
def check_if_notify():
    subs = session.query(Subscritions).all()

    for sub in subs:
        current_user = session.query(User).filter(User.id == sub.uid).first()

        check_subscriptions(sub, current_user)


app.conf.beat_schedule = {
    'check-alerts': {
        'task': 'src.celery_worker.check_if_notify',
        'schedule': 300.0
    }
}

if __name__ == '__main__':
    app.start()
