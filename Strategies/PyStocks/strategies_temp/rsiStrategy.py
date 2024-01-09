import pandas as pd
import yfinance as yf
from datetime import datetime
import fetcher

# Function to check RSI conditions and store in Excel sheet
def check_and_store_symbols(stock_symbols):
    valid_symbols = []

    for symbol in stock_symbols:
        stock_data = fetcher.get_stock_data(symbol, period="5y", duration="1d")

        if stock_data is not None and not stock_data.empty:
            # Calculating RSI for different timeframes
            monthly_rsi = stock_data['Close'].resample('M').agg(lambda x: x[-1]/x[0] if len(x) > 1 else 0).pct_change().fillna(0).rolling(window=14).apply(lambda x: x[x > 0].mean() / abs(x[x < 0].mean() if x[x < 0].mean() != 0 else 1) * 100, raw=True).fillna(0)
            weekly_rsi = stock_data['Close'].resample('W').agg(lambda x: x[-1]/x[0] if len(x) > 1 else 0).pct_change().fillna(0).rolling(window=14).apply(lambda x: x[x > 0].mean() / abs(x[x < 0].mean() if x[x < 0].mean() != 0 else 1) * 100, raw=True).fillna(0)
            daily_rsi = stock_data['Close'].pct_change().fillna(0).rolling(window=14).apply(lambda x: x[x > 0].mean() / abs(x[x < 0].mean() if x[x < 0].mean() != 0 else 1) * 100, raw=True).fillna(0)

            # Checking conditions
            if monthly_rsi.iloc[-1] > 60 and weekly_rsi.iloc[-1] > 60 and daily_rsi.iloc[-1] < 60:
                valid_symbols.append(symbol)
                valid_symbols.to_csv("strategy.csv", mode='a', header=False)

# Fetch stock symbols
stock_symbols = fetcher.get_stock_codes()
# Check RSI conditions and store valid symbols
check_and_store_symbols(stock_symbols)
