import os

from typing import List

from datetime import datetime, timedelta

from dotenv import load_dotenv

from pycoingecko import CoinGeckoAPI
import yfinance as yf

load_dotenv()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))


def get_stock_price_change(curr_price, oldest_price):
    if oldest_price == 0:
        return 0    
    percentage = ((curr_price - oldest_price) / oldest_price) * 100
    return percentage


async def get_stock_stats(stock_names: List[str]):
    start_date = (datetime.today() - timedelta(days=21)).strftime("%Y-%m-%d")

    res = []

    for stock in stock_names:
        df = yf.download(
            stock.upper(),
            start=start_date,
            auto_adjust=False,
            progress=False
        )

        closes = df['Close'].squeeze().tolist()

        stock_info = yf.Ticker(stock.upper())
        info = stock_info.info

        data = {
            'name': stock.upper(),
            'image': f"https://logo.clearbit.com/{info.get('website', stock.lower())}",
            'current_price': closes[-1],
            'high': max(closes),
            'low': min(closes),
            'sparkline_in_7d': {
                'price': closes
            },
            'price_change_percentage_7d_in_currency': get_stock_price_change(closes[0], closes[-1]),
            'price_change_percentage_24h': get_stock_price_change(closes[-2], closes[-1])
        }

        res.append(data)

    return res


async def get_coin_stats(coin_name: str):
    res = cg.get_coins_markets(vs_currency="usd",
                               ids=coin_name,
                               price_change_percentage="24,7d",
                               sparkline=True)

    return res
