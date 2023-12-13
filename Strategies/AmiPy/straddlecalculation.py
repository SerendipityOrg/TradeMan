import pandas as pd
import os,sys
import numpy as np
import datetime
from collections import namedtuple
import requests
import json

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
print(DIR_PATH)
import MarketUtils.InstrumentBase as InstrumentBase

import Strategies.StrategyBase as StrategyBase
import Brokers.place_order_calc as place_order_calc

_,STRATEGY_PATH = place_order_calc.get_strategy_json('AmiPy')

strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)
instrument_obj = InstrumentBase.Instrument()


Heikin_Ashi_MA_period = strategy_obj.get_entry_params().get('HeikinAshiMAPeriod')
Supertrend_period = strategy_obj.get_entry_params().get('SupertrendPeriod')
Supertrend_multiplier = strategy_obj.get_entry_params().get('SupertrendMultiplier')
EMA_period = strategy_obj.get_entry_params().get('EMAPeriod')



def get_option_tokens(strike_prc):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instruments_df = pd.read_csv(os.path.join(script_dir, '..', '..', 'instruments.csv'))

    instruments_df = instruments_df[
        ["instrument_token", "exchange_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike"]
    ]

    base_symbol = strategy_obj.get_instruments()[0]
    expiry_date = instrument_obj.get_expiry_by_criteria(base_symbol,strike_prc,"CE","current_week")

    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == base_symbol)
        & (instruments_df["expiry"] == expiry_date)
        & (instruments_df["strike"] == strike_prc)
    ]

    tokens = [256265]


    tokens.append(int(nfo_ins_df['instrument_token'].values[0]))  # CE token
    tokens.append(int(nfo_ins_df['instrument_token'].values[1]))  # PE token


    return tokens


def callputmergeddf(hist_data,tokens):
    nf_hist_data = hist_data[tokens[0]]
    call_hist_data = hist_data[tokens[1]]
    put_hist_data = hist_data[tokens[2]]
    
    # Convert historical_data to pandas dataframe
    nf_df = pd.DataFrame(nf_hist_data)
    
    # add instrument token variable as column to nf_df
    nf_df['instrument_token'] = tokens[0]
    nf_call_df = pd.DataFrame(call_hist_data)
    nf_call_df['instrument_token'] = tokens[1]
    nf_put_df = pd.DataFrame(put_hist_data)
    nf_put_df['instrument_token'] = tokens[2]
    trans_df = nf_call_df.add(nf_put_df, fill_value=0)
    # Convert the index to a datetime object
    trans_df.index = pd.to_datetime(trans_df.index)

    return trans_df

def moving_average(df, HA_MA_period=Heikin_Ashi_MA_period):
    MA_open = pd.Series(df['open'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_open')
    MA_high = pd.Series(df['high'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_high')
    MA_low = pd.Series(df['low'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_low')
    MA_close = pd.Series(df['close'].rolling(HA_MA_period, min_periods=HA_MA_period).mean(), name='MA_close')
    
    df = df.join(MA_open).join(MA_close).join(MA_high).join(MA_low)
    return df

def HeikinAshi(ma_df):
    ha_df = pd.DataFrame(index=ma_df.index)

    # HaClose = (Open + High + Low + Close) / 4
    ha_df['ha_close'] = (ma_df['MA_open'] + ma_df['MA_high'] + ma_df['MA_high'] + ma_df['MA_close']) / 4

    # HaOpen = AMA(Ref(HaClose, -1), 0.5)
    ha_df['ha_open'] = ha_df['ha_close'].shift(1).ewm(alpha=0.5, adjust=False).mean()

    # HaHigh = Max(High, Max(HaClose, HaOpen))
    ha_df['ha_high'] = ma_df['MA_high'].combine(ha_df['ha_close'], max).combine(ha_df['ha_open'], max)

    # HaLow = Min(Low, Min(HaClose, HaOpen))
    ha_df['ha_low'] = ma_df['MA_close'].combine(ha_df['ha_close'], min).combine(ha_df['ha_open'], min)

    ma_df = pd.concat([ma_df, ha_df], axis=1)

def atr(df, period):
    true_range = pd.Series(index=df.index,dtype='float64')
    for i in range(1, len(df)):
        high_low = df['high'][i] - df['low'][i]
        high_prev_close = abs(df['high'][i] - df['close'][i - 1])
        low_prev_close = abs(df['low'][i] - df['close'][i - 1])
        true_range[i] = max(high_low, high_prev_close, low_prev_close)
    return true_range.ewm(span=period, adjust=False).mean()

def supertrend(ma_df):

    # Calculate Average True Range (ATR)
    average_true_range = atr(ma_df, Supertrend_period)
    ma_df['ATR'] = average_true_range

    # Calculate Heikin-Ashi values
    ha_close = (ma_df['open'] + ma_df['high'] + ma_df['low'] + ma_df['close']) / 4
    ha_open = (ma_df['open'].shift(1) + ma_df['close'].shift(1)) / 2
    ha_high = ma_df[['high', 'open', 'close']].max(axis=1)
    ha_low = ma_df[['low', 'open', 'close']].min(axis=1)

    # Calculate Up and Dn lines
    up = (ha_high + ha_low) / 2 + Supertrend_multiplier * average_true_range
    dn = (ha_high + ha_low) / 2 - Supertrend_multiplier * average_true_range

    # Initialize variables
    trend = np.zeros(len(ma_df))
    trend[0] = 1
    trend_up = pd.Series(index=ma_df.index,dtype='float64')
    trend_down = pd.Series(index=ma_df.index,dtype='float64')

    change_of_trend = 0
    flag = flagh = 0

    # calulating change of trend
    for i in range(1, len(ma_df)):
        change_of_trend = 0
        
        if ha_close[i] > up[i - 1]:
            trend[i] = 1
            if trend[i-1] == -1:
                change_of_trend = 1
        elif ha_close[i] < dn[i - 1]:
            trend[i] = -1
            if trend[i-1] == 1:
                change_of_trend = 1
        else:
            trend[i] = trend[i - 1]

        if trend[i] < 0 and trend[i-1] > 0:
            flag = 1
        else:
            flag = 0

        if trend[i] > 0 and trend[i-1] < 0:
            flagh = 1
        else:
            flagh = 0

        if trend[i] > 0 and dn[i] < dn[i - 1]:
            dn[i] = dn[i - 1]

        if trend[i] < 0 and up[i] > up[i - 1]:
            up[i] = up[i - 1]

        if flag == 1:
            up[i] = (ha_high[i] + ha_low[i]) / 2 + Supertrend_multiplier * average_true_range[i]

        if flagh == 1:
            dn[i] = (ha_high[i] + ha_low[i]) / 2 - Supertrend_multiplier * average_true_range[i]

        trend_up[i] = dn[i] if trend[i] > 0 else np.nan
        trend_down[i] = up[i] if trend[i] < 0 else np.nan

        if change_of_trend == 1:
            if trend[i] == 1:
                trend_up[i - 1] = trend_down[i - 1]
            elif trend[i] == -1:
                trend_down[i - 1] = trend_up[i - 1]

    # Create a new DataFrame with calculated values
    result = ma_df.copy()

    result['ATR'] = average_true_range
    result["EMA"] = result["close"].ewm(span=EMA_period, adjust=False).mean()
    result['Up'] = up
    result['Dn'] = dn
    result['Trend'] = trend
    result['TrendUp'] = trend_up
    result['TrendDown'] = trend_down
    result['TrendSL'] = np.where(result['Trend'] == 1, result['TrendUp'], result['TrendDown'])
    
    # Reorder the columns of result
    # Assuming 'df' is your DataFrame
    columns_order = ['close', 'MA_open', 'MA_close', 'MA_high', 'MA_low','ATR','Up', 'Dn', 'Trend', 'TrendUp',
                    'TrendDown', 'TrendSL','EMA','open', 'high', 'low', 'instrument_token']

    # Reorder the columns
    result = result[columns_order]

    script_dir = os.path.dirname(os.path.realpath(__file__))
    supertrend_path = os.path.join(script_dir,"LiveCSV","amipy_supertrend.csv")

    # supertrend_path = os.path.join("Amipy/LiveCSV", "amipy_supertrend.csv")
    result.to_csv(supertrend_path, index=True)
    
    return result