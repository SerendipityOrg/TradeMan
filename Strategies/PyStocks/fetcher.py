import pandas as pd
import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()

def get_stock_codes():
    url = os.getenv('tickers_url')
    return list(pd.read_csv(url)['SYMBOL'].values)

def get_stock_data(stockCode, period, duration):
    try:
        append_exchange = ".NS"
        data = yf.download(
            tickers=stockCode + append_exchange,
            period=period,
            interval=duration)
        return data
    except Exception as e:
        print(f"Error fetching data for {stockCode}: {e}")
        return None