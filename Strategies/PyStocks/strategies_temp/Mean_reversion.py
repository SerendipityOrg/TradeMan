import pandas as pd
import yfinance as yf
import fetcher
import TA_indicators
import strategies

# Fetch stock symbols
stock_symbols = fetcher.get_stock_codes()
# Apply Mean Reversion Strategy and store selected stocks
strategies.strategy_mean_reversion(stock_symbols)

