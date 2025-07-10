from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.schemas.request_types import StatisticsResponse

from src.helpers.statistics_helper import get_stock_stats
from src.helpers.stocks_helper import get_stock_price

router = APIRouter()


@router.get("/stock-list/", status_code=200,
            response_model=List[dict],
            response_description="Get list of all stocks available")
async def get_stock_list(
    stock_name: Optional[str] = Query("", min_length=0)
) -> List[str]:
    try:
        return await get_stock_price(stock_name=stock_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

# Get statistics for stocks


@router.get("/statistics/", status_code=200,
            response_model=StatisticsResponse,
            response_description="Get statistics for the stock")
async def get_stock_statistics(
    stock_name: str = Query("", min_length=0),
):
    try:
        data = await get_stock_stats(stock_name)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with getting statistics for {stock_name}: {e}")
