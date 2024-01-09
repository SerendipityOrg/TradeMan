import fetcher
import strategies

# Fetch stock symbols
stock_symbols = fetcher.get_stock_codes()#function to fetch Stock

# Apply Golden Crossover strategy and store selected stocks in CSV
strategies.golden_crossover_strategy(stock_symbols)
