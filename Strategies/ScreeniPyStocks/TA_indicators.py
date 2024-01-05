import pandas as pd
import yfinance as yf
import fetcher

def indicator_5EMA(stock_data):
    return stock_data['Close'].ewm(span=5, min_periods=0, adjust=False).mean()

def indicator_13EMA(stock_data):
    return stock_data['Close'].ewm(span=13, min_periods=0, adjust=False).mean()

def indicator_26EMA(stock_data):
    return stock_data['Close'].ewm(span=26, min_periods=0, adjust=False).mean()

def indicator_50EMA(stock_data):
    return stock_data['Close'].ewm(span=50, min_periods=0, adjust=False).mean()
    
def indicator_RSI(data, rsi_length, rsi_source):
    try:
        delta = data[rsi_source].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=rsi_length).mean()
        avg_loss = loss.rolling(window=rsi_length).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        pass

def indicator_bollinger_bands(data, window):
    data['MA'] = data['Close'].rolling(window=window).mean()
    data['Std_dev'] = data['Close'].rolling(window=window).std()
    data['Upper_band'] = data['MA'] + (data['Std_dev'] * 2)
    data['Lower_band'] = data['MA'] - (data['Std_dev'] * 2)
    return data

def indicator_MACD(data, fast_length=12, slow_length=26, signal_length=9):
    data['EMA_fast'] = data['Close'].ewm(span=fast_length, adjust=False).mean()
    data['EMA_slow'] = data['Close'].ewm(span=slow_length, adjust=False).mean()
    data['MACD'] = data['EMA_fast'] - data['EMA_slow']
    data['Signal_line'] = data['MACD'].ewm(span=signal_length, adjust=False).mean()
    return data['MACD'], data['Signal_line']

def indicator_atr(stock_data, window):
    stock_data['HL'] = stock_data['High'] - stock_data['Low']
    stock_data['HC'] = abs(stock_data['High'] - stock_data['Close'].shift())
    stock_data['LC'] = abs(stock_data['Low'] - stock_data['Close'].shift())
    stock_data['TR'] = stock_data[['HL', 'HC', 'LC']].max(axis=1)
    stock_data['ATR'] = stock_data['TR'].rolling(window=window).mean()
    return stock_data['ATR']