from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, Request

from src.schemas.request_types import StatisticsResponse

from src.helpers.statistics_helper import get_stock_stats
from src.helpers.stocks_helper import get_stock_price
from src.auth.auth_service import check_tokens, check_users_auth

router = APIRouter()


@router.post("/stock-list/", status_code=200,
             response_description="Get list of all stocks available")
async def get_stock_list(
    res: Response,
    req: Request,
    stock: Optional[str] = Query("", min_length=0),
    sort_by: Optional[str] = Query("", min_length=0),
    sort_order: Optional[str] = Query("", min_length=0)
):
    try:
        is_logged_in = await check_tokens(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))
        users_data = await check_users_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        data = await get_stock_price(stock_name=stock, sort_by=sort_by, sort_order=sort_order)

        return {
            "data": data,
            "isLoggedin": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

# Get statistics for stocks


@router.get("/statistics/", status_code=200,
            response_model=StatisticsResponse,
            response_description="Get statistics for the stock")
async def get_stock_statistics(
    res: Response,
    req: Request,
    stock: List[str] = Query(default=[]),
):
    try:
        is_logged_in = await check_tokens(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))
        users_data = await check_users_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        data = await get_stock_stats(stock)

        return {
            "data": data,
            "isLoggedIn": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with getting statistics for {stock}: {e}")
