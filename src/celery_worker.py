from src.mail import mail, create_message
import asyncio
from celery import Celery
import sys
import os

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

#Fatching subscriptions from database
@app.task
def check_if_notify():
    pass


if __name__ == '__main__':
    app.start()
