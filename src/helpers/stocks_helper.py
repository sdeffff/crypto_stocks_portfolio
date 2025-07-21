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


async def get_stock_price(stock_name: str, sort_by: str, sort_order: str):
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

                        stock_info = yf.Ticker(ticker=ticker)
                        info = stock_info.info

                        res.append({
                            "id": ticker,
                            'image': f"https://logo.clearbit.com/{info.get('website', ticker.lower())}",
                            "date": df[ticker].index[-1].strftime('%Y-%m-%d'),
                            "open": float(data["Open"]),
                            "current_price": float(data["Close"]),
                            "high": float(data["High"]),
                            "low": float(data["Low"]),
                            "market_cap": info.get('marketCap', 0)
                            # "price_change_percentage_24h": price_stats["price_change_percentage_24h"]
                        })
                except Exception:
                    continue

            sort_column = sort_by if sort_by else "current_price"

            res.sort(key=lambda x: x[sort_column], reverse=sort_order == "desc")

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

            stock_info = yf.Ticker(ticker=stock_name)
            info = stock_info.info

            res.append({
                "id": stock_name.upper(),
                'image': f"https://logo.clearbit.com/{info.get('website', ticker.lower())}",
                "date": df.index[-1].strftime('%Y-%m-%d'),
                "open": float(latest["Open"]),
                "current_price": float(latest["Close"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "market_cap": int(latest["Volume"]),
            })

            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"500: Happened some error with api: {e}")
