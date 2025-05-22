from celery import Celery
from asgiref.sync import async_to_sync

app = Celery()

app.config_from_object('src.config')

@app.task()
def send_email(recipients: list[str], subject: str, body: str):
    
    async_to_sync()