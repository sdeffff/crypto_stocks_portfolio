import os
import pandas as pd
from typing import List, Optional
from sqlalchemy.orm import sessionmaker
from database.db import db
from fastapi import FastAPI, Response

from models.models import User

from classes.user_type import UserType

from pycoingecko import CoinGeckoAPI

app = FastAPI()

SessionLocal = sessionmaker(db)
session = SessionLocal()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))

@app.get("/")
def home():
    return {"Data": "test"}

@app.get("/users", response_model=List[UserType])
def get_all_users() -> List[UserType]:
    return session.query(User).all()

@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}

"""API to get cryptocurrency in currency we want"""
@app.get("/crypto/currency/{crypto_name}/{currency}", status_code=200)
async def get_crypto_price(crypto_name, currency, res: Response): 
    try:
        data = cg.get_price(ids=str.lower(crypto_name), 
                            vs_currencies=str.lower(currency), 
                            include_market_cap=True,
                            include_24hr_change=True)

        price = data[f'{crypto_name}'][currency]

        formatted = f"{price:,}".replace(",", " ")

        res.status_code = 200 

        return {
            "data": data,
            "price": formatted
        }
    except:
        res.status_code = 404

        return {
            "Message": "Provided incorrect currency or crypto",
        }

@app.get("/crypto/coin-list", status_code=200)
def get_coin_list(res: Response):
    try:
        data = cg.get_coins_list()
        coinDataFrame = pd.DataFrame.from_dict(data).sort_values('id').reset_index(drop=True)

        return coinDataFrame.to_dict(orient="records")
    except Exception as e:
        print(f"Error: {e}")
        res.status_code = 404