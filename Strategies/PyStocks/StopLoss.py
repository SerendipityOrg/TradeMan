import strategies
import fetcher
import TA_indicators

def atr_stoploss(stock_data_monthly, atr_window=14):
    monthly_atr = TA_indicators.indicator_atr(stock_data_monthly, atr_window) 
    stop_loss = stock_data_monthly['Close'].iloc[-1]-monthly_atr.iloc[-1]  # Taking the latest ATR value as stop loss
    return stop_loss