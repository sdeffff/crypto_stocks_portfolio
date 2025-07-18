import os

from datetime import datetime, timedelta

from dotenv import load_dotenv

from pycoingecko import CoinGeckoAPI
import yfinance as yf

load_dotenv()

cg = CoinGeckoAPI(demo_api_key=os.getenv('GECKO_API_KEY'))


def get_stock_price_change(curr_price, oldest_price):
    percentage = ((curr_price * 100) / oldest_price)

    res = 100 - percentage

    return res


async def get_stock_stats(stock_name: str):
    start_date = (datetime.today() - timedelta(days=21)).strftime("%Y-%m-%d")

    df = yf.download(
        stock_name.upper(),
        start=start_date,
        auto_adjust=False,
        progress=False
    )

    closes = df['Close'].squeeze().tolist()

    data = {
        'name': stock_name.upper(),
        'current_price': closes[-1],
        'high': max(closes),
        'low': min(closes),
        'sparkline_in_7d': {
            'price': closes
        },
        'price_change_percentage_7d_in_currency': get_stock_price_change(closes[0], closes[-1]),
        'price_change_percentage_24h': get_stock_price_change(closes[0], closes[1])
    }

    return data


async def get_coin_stats(coin_name: str):
    res = cg.get_coins_markets(vs_currency="usd",
                               ids=coin_name,
                               price_change_percentage="24,7d",
                               sparkline=True)

    return res
