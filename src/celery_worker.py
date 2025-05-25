import sys
import os
import asyncio
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from celery import Celery
from celery.schedules import crontab
from src.mail import mail, create_message
from src.database.db import session
from src.models.models import Subscritions, User
from src.helpers.subscription_helper import name_to_sign

load_dotenv()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

sys.path.insert(0, os.path.dirname((os.path.abspath(__file__))))

# Create Celery app
app = Celery(
    'crypto-tracker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
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

# Fatching subscriptions from database

# Fetch data from database - get all of the subscriptions of the user
# Fetch data from coin market to compare it if something is okay - send email to user


@app.task
def check_if_notify():
    sub = session.query(Subscritions).all()

    for i in range(len(sub)):
        current_user = session.query(User).filter(User.id == sub[i].uid).first()

        coin_data = cg.get_price(ids=sub[i].crypto_name, vs_currencies=sub[i].currency, include_market_cap=True)

        if sub[i].operator == "more":
            if sub[i].value < coin_data[sub[i].crypto_name][sub[i].currency]:
                send_email.delay([current_user.email],
                                 f"{(sub[i].crypto_name).upper()} is higher than {sub[i].value}{name_to_sign(sub[i].currency) or sub[i].currency}! 📈",
                                 f"The value of {sub[i].crypto_name} has risen above {sub[i].value}{name_to_sign(sub[i].currency) or sub[i].currency}! Current Price - {coin_data[sub[i].crypto_name][sub[i].currency]}{name_to_sign(sub[i].currency) or sub[i].currency} 📊")

                session.delete(sub[i])
                session.commit()

        if sub[i].operator == "less":
            if sub[i].value > coin_data[sub[i].crypto_name][sub[i].currency]:
                send_email.delay([current_user.email],
                                 f"{(sub[i].crypto_name).upper()} is less than {sub[i].value}{name_to_sign(sub[i].currency) or sub[i].currency}! 📉",
                                 f"The value of {sub[i].crypto_name} has fallen below {sub[i].value}{name_to_sign(sub[i].currency) or sub[i].currency}! Current Price - {coin_data[sub[i].crypto_name][sub[i].currency]}{name_to_sign(sub[i].currency) or sub[i].currency} 📊")

                session.delete(sub[i])
                session.commit()


app.conf.beat_schedule = {
    'check-alerts-every-minute': {
        'task': 'src.celery_worker.check_if_notify',
        'schedule': 60.0
    }
}

if __name__ == '__main__':
    app.start()
