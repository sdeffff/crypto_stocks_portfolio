from fastapi import HTTPException
import pandas as pd

import yfinance as yf

from datetime import datetime


def get_stocks():
    return [
        "AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK-B",
        "UNH", "JNJ", "JPM", "XOM", "PG", "V", "MA", "HD", "LLY", "PFE",
        "ABBV", "PEP", "COST", "AVGO", "TMO", "MRK", "KO", "WMT", "BAC",
        "ADBE", "CVX", "CRM", "ACN", "INTC", "ABT", "DIS", "CMCSA", "QCOM",
        "MCD", "TXN", "NEE", "LIN", "VZ", "AMD", "AMGN", "HON", "NKE", "ORCL",
        "UPS", "MDT", "LOW", "PM"
    ]


async def get_stock_price(stock_name: str):
    try:
        if not stock_name:
            res = []

            stocks = get_stocks()
            df = yf.download(
                tickers=stocks,
                start=datetime.today().strftime('%Y-%m-%d'),
                group_by='ticker',
                auto_adjust=False,
                progress=False
            )

            for ticker in stocks:
                try:
                    if ticker in df.columns.levels[0]:
                        data = df[ticker].iloc[-1]

                        if pd.isna(data["Volume"]):
                            continue

                        res.append({
                            "stock": ticker,
                            "date": df[ticker].index[-1].strftime('%Y-%m-%d'),
                            "open": float(data["Open"]),
                            "close": float(data["Close"]),
                            "high": float(data["High"]),
                            "low": float(data["Low"]),
                            "volume": int(data["Volume"]),
                        })
                except Exception:
                    continue

            return res
        else:
            df = yf.download(
                stock_name.upper(),
                start=datetime.today().strftime('%Y-%m-%d'),
                auto_adjust=False,
                progress=False
            )

            if df.empty:
                return [{"msg": f"No data found for {stock_name}"}]

            res = []
            latest = df.iloc[-1]

            res.append({
                "stock": stock_name.upper(),
                "date": df.index[-1].strftime('%Y-%m-%d'),
                "open": float(latest["Open"]),
                "close": float(latest["Close"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]),
            })

            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"500: Happened some error with api: {e}")
