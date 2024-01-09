import pandas as pd
def strategy_VolumeBreakout(stockSymbols, period='2d', duration='1d', volume_change_threshold=3):
    selected_stocks = []
    
    for symbol in stockSymbols:
        stock_data = fetcher.get_stock_data(symbol, period, duration)
        stock_data_monthly = fetcher.get_stock_data(symbol, period="2y", duration="1mo")
        
        if stock_data is not None and len(stock_data) >= 2:
            volume_changes = stock_data['Volume'].pct_change(periods=1).iloc[-2:]  # Calculate volume changes for last 2 days
            avg_volume_change = volume_changes.mean()
            
            if avg_volume_change > volume_change_threshold:
                stoploss = StopLoss.atr_stoploss(stock_data_monthly, atr_window=14)
                
                # Calculate the ratio of All-Time High to Last Traded Price
                all_time_high = stock_data['High'].max()
                last_traded_price = stock_data['Close'].iloc[-1]
                ratio_ATH_LTP = all_time_high / last_traded_price
                
                selected_stocks.append([symbol, stoploss, ratio_ATH_LTP])

    # Create DataFrame from selected stocks and sort by ratio of ATH and LTP
    df_selected_stocks = pd.DataFrame(selected_stocks, columns=['Symbol', 'Stoploss', 'Ratio_ATH_LTP'])
    df_selected_stocks = df_selected_stocks.sort_values(by='Ratio_ATH_LTP', ascending=True)
    
    # Save sorted stocks to a CSV file
    df_selected_stocks.to_csv("significant_volume_changes.csv", mode='a', header=False)
    
    return df_selected_stocks

# Example usage
stock_symbols = ['AAPL', 'GOOGL', 'MSFT']  # Replace with your desired stock symbols
result = strategy_VolumeBreakout(stock_symbols)
print(result)
