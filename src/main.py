import os
from typing import List
from sqlalchemy.orm import sessionmaker
from database.db import db
from fastapi import FastAPI

from models.models import User

from classes.user_type import UserType

from pycoingecko import CoinGeckoAPI

app = FastAPI()

SessionLocal = sessionmaker(db)
session = SessionLocal()

@app.get("/")
def home():
    return {"Data": "test"}

@app.get("/users", response_model=List[UserType])
def get_all_users() -> List[UserType]:
    return session.query(User).all()

@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}

@app.get("/crypto/{crypto_name}")
async def get_crypto(crypto_name): 
    cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

    data = cg.get_price(ids='bitcoin', vs_currencies='usd')

    price = data['bitcoin']['usd']

    formatted =f"{price:,}".replace(",", " ")

    return {
        "data": data,
    }