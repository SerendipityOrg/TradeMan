import pandas as pd
import yfinance as yf
import fetcher
import TA_indicators

selected_stocks=[]
def strategy_VolumeBreakout(stockSymbols, period='2d', duration='1d', volume_change_threshold=3):
    global selected_stocks
    selected_stocks=[]
    for symbol in stockSymbols:
        stock_data = fetcher.get_stock_data(symbol, period, duration)
        if stock_data is not None and len(stock_data) >= 2:
            volume_changes = stock_data['Volume'].pct_change(periods=1).iloc[-2:]  # Calculate volume changes for last 2 days
            avg_volume_change = volume_changes.mean()
            
            if avg_volume_change > volume_change_threshold:
                
                # Calculate the ratio of All-Time High to Last Traded Price
                all_time_high = stock_data['High'].max()
                last_traded_price = stock_data['Close'].iloc[-1]
                ratio_ATH_LTP = all_time_high / last_traded_price
                
                selected_stocks.append([symbol, ratio_ATH_LTP])

                # Save sorted stocks to a CSV file
                #df_selected_stocks.to_csv("significant_volume_changes.csv", mode='w', header=False)
                #print(f"Stock symbol {symbol} has a volume change more than 3x:\n{stock_data}\n")
    return selected_stocks
    
def strategy_golden_crossover(stock_symbols, period='1y', duration='1d'):
    global selected_stocks
    selected_stocks = []
    for symbol in stock_symbols:
        stock_data = fetcher.get_stock_data(symbol, period, duration)
        if stock_data is not None and len(stock_data) >= 26:  # Ensure sufficient data for EMA calculation
            stock_data['EMA5'] = TA_indicators.indicator_5EMA(stock_data)
            stock_data['EMA13'] = TA_indicators.indicator_13EMA(stock_data)
            stock_data['EMA26'] = TA_indicators.indicator_26EMA(stock_data)

            # Check for Golden Crossover
            if stock_data['EMA5'].iloc[-2] < stock_data['EMA13'].iloc[-2] and \
               stock_data['EMA13'].iloc[-2] < stock_data['EMA26'].iloc[-2]:
                if stock_data['EMA5'].iloc[-1] > stock_data['EMA13'].iloc[-1] and \
                stock_data['EMA13'].iloc[-1] > stock_data['EMA26'].iloc[-1]:
                    # Calculate the ratio of All-Time High to Last Traded Price
                    all_time_high = stock_data['High'].max()
                    last_traded_price = stock_data['Close'].iloc[-1]
                    ratio_ATH_LTP = all_time_high / last_traded_price
                    selected_stocks.append([symbol, ratio_ATH_LTP])
    return selected_stocks                
   
def strategy_above_50EMA(stock_data):
    if stock_data is not None and not stock_data.empty:
        stock_data['EMA_50'] = TA_indicators.indicator_50EMA(stock_data)
        stock_data['Above_50_EMA'] = stock_data['Close'] > stock_data['EMA_50']
        return stock_data
    else:
        return None
    
def strategy_momentum(stock_symbols):
    global selected_stocks
    selected_stocks = []
    for symbol in stock_symbols:
        try:
            stock_data = fetcher.get_stock_data(symbol, period="2y", duration="1d")
        except:
            pass
        if stock_data is not None and not stock_data.empty:
            # Calculate RSI
            rsi_length_input = 14
            rsi_source_input = 'Close'
            rsi_values = TA_indicators.indicator_RSI(stock_data, rsi_length_input, rsi_source_input)
            
            # Calculate Bollinger Bands
            bb_window = 20
            stock_data = TA_indicators.indicator_bollinger_bands(stock_data, bb_window)
            
            # Check if LTP is above 50 EMA
            stock_data = strategy_above_50EMA(stock_data)

            macd, signal_line = TA_indicators.indicator_MACD(stock_data)
            
            # Apply momentum Strategy conditions
            if rsi_values.iloc[-1] > 50 and stock_data['Above_50_EMA'].iloc[-1]:
                if stock_data['Upper_band'].iloc[-1] < stock_data['Close'].iloc[-1]:
                    if macd.iloc[-1] > signal_line.iloc[-1]:  # Condition 4
                        all_time_high = stock_data['High'].max()
                        last_traded_price = stock_data['Close'].iloc[-1]
                        ratio_ATH_LTP = all_time_high / last_traded_price
                        selected_stocks.append([symbol, ratio_ATH_LTP])
                        #df_selected_stocks = pd.DataFrame(selected_stocks, columns=['Symbol', 'Stoploss'])
                        #df_selected_stocks.to_csv("Momentum.csv", mode='w', header=False)         
    return selected_stocks
    
def strategy_mean_reversion(stock_symbols):
    global selected_stocks
    selected_stocks = []
    for symbol in stock_symbols:
        try:
            stock_data = fetcher.get_stock_data(symbol, period="2y", duration="1d")#for 15 min duration = 15m period = 50d, for hourly duration = 1h period = 1y
            stock_data_weekly = fetcher.get_stock_data(symbol, period="2y", duration="1wk")
        except:
            pass
        if stock_data is not None and not stock_data.empty:
            # Calculate RSI
            rsi_length_input = 14
            rsi_source_input = 'Close'
            rsi_values = TA_indicators.indicator_RSI(stock_data, rsi_length_input, rsi_source_input)
            # Calculate Bollinger Bands
            bb_window = 20
            stock_data = TA_indicators.indicator_bollinger_bands(stock_data, bb_window)
            stock_data_weekly = TA_indicators.indicator_bollinger_bands(stock_data_weekly, bb_window)
            # Check if LTP is above 50 EMA
            stock_data = strategy_above_50EMA(stock_data)
            # Apply Mean Reversion Strategy conditions
            if rsi_values.iloc[-1] < 40 and stock_data['Above_50_EMA'].iloc[-1]:
                if stock_data_weekly['MA'].iloc[-1] < stock_data_weekly['Close'].iloc[-1]:
                    if stock_data['Lower_band'].iloc[-2] < stock_data['Lower_band'].iloc[-3]:
                        if stock_data['Lower_band'].iloc[-1] > stock_data['Lower_band'].iloc[-2]:
                            all_time_high = stock_data['High'].max()
                            last_traded_price = stock_data['Close'].iloc[-1]
                            ratio_ATH_LTP = all_time_high / last_traded_price
                            selected_stocks.append([symbol, ratio_ATH_LTP])
                            #df_selected_stocks = pd.DataFrame(selected_stocks, columns=['Symbol'])
                            #df_selected_stocks.to_csv("MeanReversion.csv", mode='w', header=False)
    return selected_stocks
            
def strategy_EMA_BB_Confluence(stock_symbols):
    global selected_stocks
    selected_stocks =[]
    for symbol in stock_symbols:
        try:
            stock_data = fetcher.get_stock_data(symbol, period='1y', duration='1d')
            bb_window = 20
            stock_data = TA_indicators.indicator_bollinger_bands(stock_data, bb_window)
            stock_data['EMA_50'] = TA_indicators.indicator_50EMA(stock_data)
            if stock_data['EMA_50'].iloc[-1] <= stock_data['Lower_band'].iloc[-1]:
                if stock_data['Close'].iloc[-1] < stock_data['MA'].iloc[-1]:
                    if stock_data['Lower_band'].iloc[-2] < stock_data['Lower_band'].iloc[-3]:
                        if stock_data['Lower_band'].iloc[-1] > stock_data['Lower_band'].iloc[-2]:
                            bollinger_close_to_ema = abs(stock_data['Lower_band'].iloc[-1] - stock_data['EMA_50'].iloc[-1]) < 0.05 * stock_data['Close'].iloc[-1]
                            if bollinger_close_to_ema:
                                all_time_high = stock_data['High'].max()
                                last_traded_price = stock_data['Close'].iloc[-1]
                                ratio_ATH_LTP = all_time_high / last_traded_price
                                selected_stocks.append([symbol, ratio_ATH_LTP])
                                #df_selected_stocks = pd.DataFrame(selected_stocks, columns=['Symbol'])
                                #df_selected_stocks.to_csv("selected stocks.csv", mode='w', header=False)
                                break
        except:
            pass
    return selected_stocks