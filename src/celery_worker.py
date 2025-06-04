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

def add_notif(sub: Subscritions, check_type, uid, what_to_check, operator, value, currency):
    notif = (Notifications(
        check_type=check_type,
        uid=uid,
        what_to_check=what_to_check,
        operator=operator,
        value=value,
        currency=currency
    ))

    session.add(notif)

    session.delete(sub)
    session.commit()

def check_crypto(data, current_user: User, sub: Subscritions):
    if sub.operator == "greater":
        if sub.value < data[sub.what_to_check][sub.currency]:
            send_email.delay([current_user.email],
                                f"{(sub.what_to_check).upper()} is higher than {sub.value}{name_to_sign(sub.currency) or sub.currency}! 📈",
                                f"The value of {sub.what_to_check} has risen above {sub.value}{name_to_sign(sub.currency) or sub.currency}! Current Price - {data[sub.what_to_check][sub.currency]}{name_to_sign(sub.currency) or sub.currency} 📊")

    if sub.operator == "less":
        if sub.value > data[sub.what_to_check][sub.currency]:
            send_email.delay([current_user.email],
                                f"{(sub.what_to_check).upper()} is less than {sub.value}{name_to_sign(sub.currency) or sub.currency}! 📉",
                                f"The value of {sub.what_to_check} has fallen below {sub.value}{name_to_sign(sub.currency) or sub.currency}! Current Price - {data[sub.what_to_check][sub.currency]}{name_to_sign(sub.currency) or sub.currency} 📊")

def check_stock(stock_price: int, current_user: User, sub: Subscritions):
    if sub.operator == "greater":
        if sub.value < stock_price:
            send_email.delay([current_user.email],
                                f"{(sub.what_to_check).upper()} is higher than {sub.value}{name_to_sign(sub.currency) or sub.currency}! 📈",
                                f"The value of {sub.what_to_check} has risen above {sub.value}{name_to_sign(sub.currency) or sub.currency}! Current Price - {stock_price}{name_to_sign(sub.currency) or sub.currency} 📊")

    if sub.operator == "less":
        if sub.value > stock_price:
            send_email.delay([current_user.email],
                                f"{(sub.what_to_check).upper()} is less than {sub.value}{name_to_sign(sub.currency) or sub.currency}! 📉",
                                f"The value of {sub.what_to_check} has risen above {sub.value}{name_to_sign(sub.currency) or sub.currency}! Current Price - {stock_price}{name_to_sign(sub.currency) or sub.currency} 📊")


@app.task
def check_if_notify():
    sub = session.query(Subscritions).all()

    for i in range(len(sub)):
        current_user = session.query(User).filter(User.id == sub[i].uid).first()

        if sub[i].check_type == "stock":
            stock_price = asyncio.run(get_stock_price(sub[i].what_to_check))

            check_stock(float(stock_price), current_user, sub[i])

            add_notif(sub[i], sub[i].check_type, sub[i].uid, sub[i].what_to_check, sub[i].operator, sub[i].value, sub[i].currency)

        if sub[i].check_type == "crypto":
            data = cg.get_price(ids=sub[i].what_to_check, vs_currencies=sub[i].currency, include_market_cap=True)

            check_crypto(data, current_user, sub[i])

            add_notif(sub[i], sub[i].check_type, sub[i].uid, sub[i].what_to_check, sub[i].operator, sub[i].value, sub[i].currency)

app.conf.beat_schedule = {
    'check-alerts': {
        'task': 'src.celery_worker.check_if_notify',
        'schedule': 300.0
    }
}

if __name__ == '__main__':
    app.start()
