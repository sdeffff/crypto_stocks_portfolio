from dotenv import load_dotenv

from fastapi import HTTPException
from pycoingecko import CoinGeckoAPI

from classes.request_types import CoinsRequest

load_dotenv()

cg = CoinGeckoAPI()

#Function to get coin list for subscriptions
async def get_coin_list(payload: CoinsRequest):
    try:
        result = cg.get_coins_markets(vs_currency=payload.currency or "usd", page=1)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Heppened smth wrong with api")