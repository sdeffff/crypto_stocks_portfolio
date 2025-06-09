import os
import httpx
from fastapi import HTTPException


def get_stocks():
    return [
        "AAPL", "NVDA",
        "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK.B", "UNH", "JNJ",
        "JPM", "XOM", "PG", "V", "MA", "HD", "LLY", "PFE", "ABBV", "PEP",
        "COST", "AVGO", "TMO", "MRK", "KO", "WMT", "BAC", "ADBE", "CVX", "CRM",
        "ACN", "INTC", "ABT", "DIS", "CMCSA", "QCOM", "MCD", "TXN", "NEE", "LIN",
        "VZ", "AMD", "AMGN", "HON", "NKE", "ORCL", "UPS", "MDT", "LOW", "PM"
    ]


async def get_stock_price(stock_name: str):
    av_api = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock_name}&interval=5min&apikey={os.getenv('ALPHA_VANTAGE_SECRET_KEY')}"

    async with httpx.AsyncClient() as client:
        response = await client.get(av_api)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Happened error with server")

    data = response.json()

    return float(data["Time Series (5min)"][data["Meta Data"]["3. Last Refreshed"]]["4. close"])
