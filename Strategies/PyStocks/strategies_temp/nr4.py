import pandas as pd
import yfinance as yf
import fetcher
import strategies

# Fetch stock symbols
stock_symbols = fetcher.get_stock_codes()

# Apply NR4 strategy and store selected stocks in Excel
strategies.strategy_nr4(stock_symbols)
