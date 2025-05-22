import os
from typing import List
from sqlalchemy.orm import sessionmaker
from database.db import db
from fastapi import FastAPI, Response

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

@app.get("/crypto/{crypto_name}", status_code=200)
async def get_crypto(crypto_name, res: Response): 
    cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

    try:
        data = cg.get_price(ids=crypto_name, vs_currencies='usd')

        price = data[f'{crypto_name}']['usd']

        formatted =f"{price:,}".replace(",", " ")

        res.status_code = 200

        return {
            "data": data,
            "price": formatted
        }
    except:
        res.status_code = 404

        return {
            "Message": "Incorrect crypto",
        }

@app.post("/auth/register")
async def register():
    pass

@app.post("/auth/login")
async def login():
    pass