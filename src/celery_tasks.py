from celery import Celery, shared_task
from asgiref.sync import async_to_sync

from mail import mail, create_message

app = Celery()

app.config_from_object('src.config')

@shared_task()
def send_email(recipients: list[str], subject: str, body: str):
    message = create_message(recipients, subject, body)    

    async_to_sync(mail.send_message)(message)