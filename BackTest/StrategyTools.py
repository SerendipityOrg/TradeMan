import pandas as pd
import numpy as np

def moving_average(df, HA_MA_period):
    MA_open = pd.Series(df['open'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_open')
    MA_high = pd.Series(df['high'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_high')
    MA_low = pd.Series(df['low'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_low')
    MA_close = pd.Series(df['close'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_close')
    
    df = df.join(MA_open).join(MA_close).join(MA_high).join(MA_low)
    return df

def atr(df, period):
    true_range = pd.Series(index=df.index)
    for i in range(1, len(df)):
        high_low = df['high'][i] - df['low'][i]
        high_prev_close = abs(df['high'][i] - df['close'][i - 1])
        low_prev_close = abs(df['low'][i] - df['close'][i - 1])
        true_range[i] = max(high_low, high_prev_close, low_prev_close)
    return true_range.ewm(span=period, adjust=False).mean()


def heikin_ashi(df):
    ha_df = pd.DataFrame(index=df.index)
    
    # HaClose = (Open + High + Low + Close) / 4
    ha_df['ha_close'] = (df['MA_open'] + df['MA_high'] + df['MA_high'] + df['MA_close']) / 4
    
    # HaOpen = AMA(Ref(HaClose, -1), 0.5)
    ha_df['ha_open'] = ha_df['ha_close'].shift(1).ewm(alpha=0.5, adjust=False).mean()
    
    # HaHigh = Max(High, Max(HaClose, HaOpen))
    ha_df['ha_high'] = df['MA_high'].combine(ha_df['ha_close'], max).combine(ha_df['ha_open'], max)
    
    # HaLow = Min(Low, Min(HaClose, HaOpen))
    ha_df['ha_low'] = df['MA_close'].combine(ha_df['ha_close'], min).combine(ha_df['ha_open'], min)
    
    return ha_df

def super_trend(df, period=9, multiplier=7):
    hl2 = (df["ha_high"] + df["ha_low"]) / 2
    atr = df["ha_high"].rolling(period).apply(lambda x: np.max(x[:-1] - x[-1])) + df["ha_low"].rolling(period).apply(lambda x: np.min(x[:-1] - x[-1]))
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend = pd.Series(np.nan, index=df.index)
    in_uptrend = True
    for current in range(period, len(df)):
        previous = current - 1
        if df["ha_close"][current] > upper_band[previous]:
            supertrend[current] = upper_band[previous]
            in_uptrend = True
        elif df["ha_close"][current] < lower_band[previous]:
            supertrend[current] = lower_band[previous]
            in_uptrend = False
        else:
            supertrend[current] = supertrend[previous]
            if in_uptrend and df["ha_close"][current] < supertrend[previous]:
                supertrend[current] = lower_band[previous]
                in_uptrend = False
            elif not in_uptrend and df["ha_close"][current] > supertrend[previous]:
                supertrend[current] = upper_band[previous]
                in_uptrend = True
    return supertrend

def ema(df, column, period):
    return df[column].ewm(span=period, adjust=False).mean()


######## FOCUS HERE##############
def supertrend_new(df, period=9, multiplier=7):
    print("supertrend_new2222")
    # Calculate Average True Range (ATR)
    average_true_range = atr(df, period)
    df['ATR'] = average_true_range
    print("ATR:", df['ATR'])

    # Calculate Heikin-Ashi values
    ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_open = (df['open'].shift(1) + df['close'].shift(1)) / 2
    ha_high = df[['high', 'open', 'close']].max(axis=1)
    ha_low = df[['low', 'open', 'close']].min(axis=1)

    print("HA:", df['ha_close'],df['ha_open'],df['ha_high'],df['ha_low'])
    # Calculate Up and Dn lines
    up = (ha_high + ha_low) / 2 + multiplier * average_true_range
    dn = (ha_high + ha_low) / 2 - multiplier * average_true_range

    print("UPDN:",up, dn)
    
    # Initialize variables
    trend = np.zeros(len(df))
    trend[0] = 1
    trend_up = pd.Series(index=df.index)
    trend_down = pd.Series(index=df.index)


    for i in range(1, len(df)):
        if ha_close[i] > up[i - 1]:
            trend[i] = 1
        elif ha_close[i] < dn[i - 1]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]

        if dn[i] < dn[i - 1]:
            dn[i] = dn[i - 1]

        if up[i] > up[i - 1]:
            up[i] = up[i - 1]

        trend_up[i] = dn[i] if trend[i] > 0 else np.nan
        trend_down[i] = up[i] if trend[i] < 0 else np.nan

    print("supertrend_new4")

    # Fill NaN values
    trend_up.fillna(method='ffill', inplace=True)
    trend_down.fillna(method='ffill', inplace=True)

    print("supertrend_new5")

    # Create a new DataFrame with calculated values
    result = df.copy()
    print("result: ", result.columns)
    
    result['ATR'] = average_true_range
    result['Up'] = up
    result['Dn'] = dn
    result['Trend'] = trend
    result['TrendUp'] = trend_up
    result['TrendDown'] = trend_down
    result['TrendSL'] = np.where(result['Trend'] == 1, result['TrendUp'], result['TrendDown'])

    return result


def supertrend1(df, factor, pd):
    
    hl2 = (df['High'] + df['Low']) / 2
    df['TrendUp'] = hl2 + (factor * atr)
    df['TrendDown'] = hl2 - (factor * atr)

    result = df.copy()
    result['Trend'] = None
    result['supertrend'] = None

    for i in range(1, len(result)):
        if result['Close'][i] > result['TrendUp'][i - 1]:
            result.at[i, 'Trend'] = 1
        elif result['Close'][i] < result['TrendDown'][i - 1]:
            result.at[i, 'Trend'] = -1
        else:
            result.at[i, 'Trend'] = result.at[i - 1, 'Trend']

        if result.at[i, 'Trend'] == 1:
            result.at[i, 'supertrend'] = min(result.at[i, 'TrendUp'], result.at[i - 1, 'supertrend'])
        else:
            result.at[i, 'supertrend'] = max(result.at[i, 'TrendDown'], result.at[i - 1, 'supertrend'])

    df['supertrend'] = result['supertrend']
    return df