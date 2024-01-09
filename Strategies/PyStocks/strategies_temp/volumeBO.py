import fetcher
import strategies

stockSymbols = fetcher.get_stock_codes()# Fetch stock symbols
strategies.strategy_VolumeBreakout(stockSymbols)#apply VOlume BO Strategy

