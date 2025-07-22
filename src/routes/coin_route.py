import os
import pandas as pd

from typing import List, Optional
from dotenv import load_dotenv

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pycoingecko import CoinGeckoAPI

from src.schemas.request_types import CoinsRequest, StatisticsResponse
from src.helpers.statistics_helper import get_coin_stats
from src.auth.auth_service import check_tokens, check_users_auth

load_dotenv()

router = APIRouter()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))


@router.post("/crypto-list",
             status_code=200,
             response_description="List of all available crypto currencies")
async def get_coin_list(
    res: Response,
    req: Request,
    payload: CoinsRequest, page: int = Query(1, ge=1),
    crypto: List[str] = Query(default=[]),
    sort_by: Optional[str] = Query("", min_length=0),
    sort_order: Optional[str] = Query("", min_length=0)
):
    try:
        is_logged_in = await check_tokens(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))
        users_data = await check_users_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

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

        return {
            "assetsData": sorted_df.head(payload.limit).to_dict(orient="records"),
            "isLoggedIn": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Happened some error with getting coins data: {e}")


@router.get("/statistics/",
            status_code=200,
            response_model=StatisticsResponse,
            response_description="Get statistics for crypto coin")
async def get_coin_statistics(
    res: Response,
    req: Request,
    crypto: str = Query("", min_length=0),
):
    try:
        is_logged_in = await check_tokens(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))
        users_data = await check_users_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        if crypto == "":
            raise HTTPException(status_code=409, detail="You cannot use empty string as crypto!")

        data = await get_coin_stats(crypto)

        res = pd.DataFrame(data)[["name", "image", "current_price", "high_24h", "low_24h", "sparkline_in_7d", "price_change_percentage_24h", "price_change_percentage_7d_in_currency"]].rename(columns={"high_24h": "high", "low_24h": "low"})

        return {
            "statsData": [res.to_dict(orient="records")[0]],
            "isLoggedIn": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Error with getting statistics for {crypto}: {e}")
