import pandas as pd
import yfinance as yf
import fetcher
import TA_indicators
import strategies
              
# Fetch stock symbols
stock_symbols = fetcher.get_stock_codes()
# Apply Momentum Strategy and store selected stocks
strategies.strategy_momentum(stock_symbols)

