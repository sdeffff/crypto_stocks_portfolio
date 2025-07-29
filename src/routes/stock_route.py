from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, Request

from src.schemas.request_types import StatisticsResponse

from src.helpers.statistics_helper import get_stock_stats
from src.helpers.stocks_helper import get_stock_price
from src.auth.auth_service import check_tokens, check_users_auth
from src.schemas.query_types import SortByType, SortOrderType

router = APIRouter()


@router.post("/stock-list/", status_code=200,
             response_description="Get list of all stocks available")
async def get_stock_list(
    res: Response,
    req: Request,
    stock: Optional[str] = Query(None),
    sort_by: Optional[SortByType] = Query(None),
    sort_order: Optional[SortOrderType] = Query(None)
):
    try:
        is_logged_in = await check_tokens(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))
        users_data = await check_users_auth(res, req.cookies.get("access_token"), req.cookies.get("refresh_token"))

        data = await get_stock_price(stock_name=stock, sort_by=sort_by, sort_order=sort_order)

        return {
            "assetsData": data,
            "isLoggedIn": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=409, detail=f"{e}")


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
            "statsData": data,
            "isLoggedIn": is_logged_in,
            "usersData": users_data
        }
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Error with getting statistics for {stock}: {e}")
