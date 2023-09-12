from remove import StrategyTools
from kiteconnect import KiteConnect
import pandas as pd

import pytz

# Fixed params 
name = "NIFTY"

# Weekly params
expiry = '4May2023'
expiry1 = "2023-05-04"

# Time params
entry_time = pd.Timestamp("09:21:00").time()
last_buy_time = pd.Timestamp("14:50:00").time()
sqroff_time = pd.Timestamp("15:10:00").time() 

# Historical Data Params
interval = "5minute"         # Choose the time interval: "1minute", "5minute", "15minute", "30minute", "60minute", "day", "week", or "month"
from_date = "2023-04-25"     # Start date for historical data
to_date = "2023-04-28"       # End date for historical data

# Supertrend params
Heikin_Ashi_MA_period = 13
Supertrend_period = 9
Supertrend_multiplier = 7
EMA_period = 256

# init
nifty_token = 256265
ce_instr_token = 14755842
pe_instr_token = 14756098

import pytz


def process_live_kite_ticker(nf_live_df, call_live_df, put_live_df):
    
    print('Processing live 1min OHLC...')

    merged_df = pd.merge(call_live_df, put_live_df, on='date', suffixes=('_call', '_put'))

    # Sum the 'open', 'high', 'low', and 'close' values for call and put dataframes
    merged_df['open'] = merged_df['open_call'] + merged_df['open_put']
    merged_df['high'] = merged_df['high_call'] + merged_df['high_put']
    merged_df['low'] = merged_df['low_call'] + merged_df['low_put']
    merged_df['close'] = merged_df['close_call'] + merged_df['close_put']
    # merged_df['date'] = pd.to_datetime(merged_df['date'])


    # Merge the resulting dataframe with nf_live_df on 'date'
    #trans_df = pd.merge(merged_df, nf_live_df.add_prefix('nf_'), on='date')

    #Convert 'date' column to Kolkata timezone
    
    #merged_df.set_index('date', inplace=True)
    #merged_df['date'] = merged_df['date'].dt.tz_convert(pytz.timezone('Asia/Kolkata'))

    merged_df.to_csv(f'ce_pe_df.csv', index=True)
    return merged_df



def get_nf_hist_data(kite, from_date, to_date, interval):
    print('Better resampling')
    print('Getting historical data for Nifty...')
    nf_hist_data = kite.historical_data(nifty_token, from_date, to_date, interval)
    call_hist_data = kite.historical_data(ce_instr_token, from_date, to_date, interval)
    put_hist_data = kite.historical_data(pe_instr_token, from_date, to_date, interval)
    
    # Convert historical_data to pandas dataframe
    nf_df = pd.DataFrame(nf_hist_data)
    nf_df = nf_df.set_index('date')

    # add instrument token variable as column to nf_df
    nf_df['instrument_token'] = nifty_token

    nf_call_df = pd.DataFrame(call_hist_data)
    nf_call_df = nf_call_df.set_index('date')
    nf_call_df['instrument_token'] = ce_instr_token

    nf_put_df = pd.DataFrame(put_hist_data)
    nf_put_df = nf_put_df.set_index('date')
    nf_put_df['instrument_token'] = pe_instr_token
    nf_call_df.head()

    trans_df = nf_call_df.add(nf_put_df, fill_value=0)

    # combine combined_df and nf_df renaming columns of nf_df to 'nf_' + column name
    trans_df = pd.concat([trans_df, nf_df.add_prefix('nf_')], axis=1)
    
    # Resample the DataFrame at 1-minute intervals
    resampled_df = trans_df.resample("1T").asfreq()
    resampled_df = resampled_df.interpolate(method="time")
    
    resampled_df.to_csv(f'nf_hist_df.csv', index=True)
    
    

    return resampled_df

def pd_cruncher(resampled_df):
    ma_df = StrategyTools.moving_average(resampled_df, Heikin_Ashi_MA_period)
    
    ha_df = StrategyTools.heikin_ashi(ma_df)
    ma_df = pd.concat([ma_df, ha_df], axis=1)
    
    # remove 'nf_volume', 'volume','nf_instrument_token', column from ma_df
    ma_df = ma_df.drop(['volume','nf_instrument_token','nf_volume'], axis=1)
    
    
    print('Calculating Supertrend...')
    supertrend_df = StrategyTools.supertrend_new(ma_df, period=7, multiplier=9)
    ma_df = ma_df.merge(supertrend_df, left_index=True, right_index=True)
    
    ma_df["ema"] = StrategyTools.ema(ma_df, "close", EMA_period)
    
    # print ma_df to csv including index
    ma_df.to_csv(r'ma_df_st.csv', index=True)
    
    return ma_df

def pd_liv_cruncher(resampled_df):
    
    print('Crunching live 1min OHLC...')
    
    resampled_df = resampled_df.drop(['instrument_token_call','instrument_token_put'], axis=1)
    ma_df = StrategyTools.moving_average(resampled_df, Heikin_Ashi_MA_period)
    
    ha_df = StrategyTools.heikin_ashi(ma_df)
    ma_df = pd.concat([ma_df, ha_df], axis=1)     
    
    print('Calculating Supertrend...')
    supertrend_df = StrategyTools.supertrend_new(ma_df, period=7, multiplier=9)
    ma_df = ma_df.merge(supertrend_df, left_index=True, right_index=True)
    
    ma_df["ema"] = StrategyTools.ema(ma_df, "close", EMA_period)
    
    # print ma_df to csv including index
    ma_df.to_csv(r'ma_df_st1.csv', index=True)
    
    return ma_df

def generate_trade_signals(df):
    signals = []
    trade_no = 1
    current_position = None
    
    def long(df, i):
        return (df.loc[df.index[i], "supertrend"] == 1) & (df.loc[df.index[i], "close"] > df.loc[df.index[i], "ema"]) & (df.index[i].time() > entry_time) & (df.index[i].time() < sqroff_time) & (df.index[i].time() < last_buy_time)

    def longcover(df, i):
        return (df.loc[df.index[i], "supertrend"] == -1) | (df.index[i].time() > sqroff_time)

    def short(df, i):
        return (df.loc[df.index[i], "supertrend"] == -1) & (df.loc[df.index[i], "close"] < df.loc[df.index[i], "ema"]) & (df.index[i].time() > entry_time) & (df.index[i].time() < sqroff_time) & (df.index[i].time() < last_buy_time)

    def shortcover(df, i):
        return (df.loc[df.index[i], "supertrend"] == 1) | (df.index[i].time() > sqroff_time)

    for i in range(1, len(df)):
        current_time = df.index[i]
        current_close = df.loc[current_time, 'close']

        if current_position is None:
            if long(df, i):
                current_position = 'Long'
                signal = {
                    'Trade_No': trade_no,
                    'Trade_Type': current_position,
                    'Date': current_time.date(),
                    'TradeEntryTime': current_time.time(),
                    'TradeEntryPrice': current_close,
                }
                signals.append(signal)

            elif short(df, i):
                current_position = 'Short'
                signal = {
                    'Trade_No': trade_no,
                    'Trade_Type': current_position,
                    'Date': current_time.date(),
                    'TradeEntryTime': current_time.time(),
                    'TradeEntryPrice': current_close,
                }
                signals.append(signal)

        else:
            if current_position == 'Long' and longcover(df, i):
                current_position = None
                last_signal = signals[-1]
                last_signal.update({
                    'TradeExitTime': current_time.time(),
                    'TradeExitPrice': current_close,
                })
                last_signal['NetTradePoints'] = last_signal['TradeExitPrice'] - last_signal['TradeEntryPrice']
                trade_no += 1

            elif current_position == 'Short' and shortcover(df, i):
                current_position = None
                last_signal = signals[-1]
                last_signal.update({
                    'TradeExitTime': current_time.time(),
                    'TradeExitPrice': current_close,
                })
                last_signal['NetTradePoints'] = last_signal['TradeEntryPrice'] - last_signal['TradeExitPrice']
                trade_no += 1

    signals_df = pd.DataFrame(signals)
    signals_df.to_csv('amiNF_trd_sig_liv.csv', index=True)

    return signals_df
