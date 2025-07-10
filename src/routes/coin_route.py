import os
import pandas as pd

from typing import List, Optional
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Query
from pycoingecko import CoinGeckoAPI

from src.schemas.request_types import CoinsRequest
from src.helpers.statistics_helper import get_coin_stats

load_dotenv()

router = APIRouter()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))


@router.post("/coin-list",
             status_code=200,
             response_description="List of all available crypto currencies")
async def get_coin_list(
    payload: CoinsRequest, page: int = Query(1, ge=1),
    crypto: List[str] = Query(default=[]),
    sort_by: Optional[str] = Query("", min_length=0),
    sort_order: Optional[str] = Query("", min_length=0)
):
    try:
        data = cg.get_coins_markets(vs_currency=payload.currency or "usd", page=(page if page else 1))

        df = None

        if payload.names:
            df = pd.DataFrame(data)[["id", "image", "current_price"]]
        else:
            df = pd.DataFrame(data)[["id", "symbol", "image", "current_price", "market_cap", "market_cap_rank", "price_change_percentage_24h"]]

        if crypto:
            filtered_df = df[df.id.isin([c.lower() for c in crypto])]
        else:
            filtered_df = df

        sort_column = sort_by if sort_by else "current_price"
        sorted_df = filtered_df.sort_values(by=sort_column, ascending=(True if sort_order == "asc" else False)).dropna()

        return sorted_df.head(payload.limit).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Happened some error with getting coins data: {e}")

# Get statistics for coins


@router.get("/statistics/",
            status_code=200,
            response_description="Get statistics for crypto coin")
async def get_coin_statistics(
    coin_name: str = Query("", min_length=0),
):
    try:
        data = await get_coin_stats(coin_name)

        res = pd.DataFrame(data)[["name", "image", "current_price", "high_24h", "low_24h", "sparkline_in_7d", "price_change_percentage_7d_in_currency"]].rename(columns={"high_24h": "high", "low_24h": "low"})

        return res.to_dict(orient="records")[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with getting statistics for {coin_name}: {e}")
