import pandas as pd
import numpy as np
import json
import os,sys
import logging

from datetime import timedelta,datetime,date
from time import sleep

from kiteconnect import KiteConnect
from kiteconnect import KiteTicker

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import html, dcc
import plotly.graph_objs as go

from straddlecalculation import *
from chart import plotly_plot

from dotenv import load_dotenv

# Set up paths and import modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BROKERS_DIR = os.path.join(CURRENT_DIR, '..', '..', 'Brokers')

dotenv_path = os.path.join(BROKERS_DIR, '.env')
load_dotenv(dotenv_path)

sys.path.append(os.path.join(CURRENT_DIR, '..', '..', 'Utils'))
import general_calc as gc

sys.path.append(os.path.join(CURRENT_DIR, '..', '..', 'Utils', 'Discord'))
import discordchannels as discord_bot

sys.path.append(BROKERS_DIR)
import place_order as place_order

nifty_token = os.getenv('nifty_token')
omkar_filepath = os.getenv('omkar_json_filepath')
base_symbol = "NIFTY" 
strike_prc = None
trading_symbol = []
expiry_date,_ = gc.get_expiry_dates("NIFTY")


hist_data = {token: pd.DataFrame(columns=['date', 'instrument_token', 'open', 'high', 'low', 'close']) for token in nifty_token}
from_date =  date.today()- pd.Timedelta(days=4)
to_date = date.today()
interval = 'minute'

script_dir = os.path.dirname(os.path.abspath(__file__))
broker_filepath = os.path.join(script_dir, '..', '..', 'Utils', 'broker.json')

users_to_trade = get_amipy_users(broker_filepath)
omkar_zerodha = gc.read_json_file(omkar_filepath)

kite_access_token = omkar_zerodha['zerodha']['access_token']
kite_api_key = omkar_zerodha['zerodha']['api_key']
kite = KiteConnect(api_key=kite_api_key)
kite.set_access_token(kite_access_token)


# Define your global DataFrame
signalsdf = pd.DataFrame(columns=[
    "date", "close", "MA_open", "MA_close", "MA_high", "MA_low", "ATR", "Up", 
    "Dn", "Trend", "TrendUp", "TrendDown", "TrendSL", "EMA", "open", "high", 
    "low", "instrument_token", "LongSignal", "ShortSignal", 
    "LongCoverSignal", "ShortCoverSignal"],
    dtype=object)  # generic data type for initial creation

# Define specific data types for each column
column_types = {
    "date": "datetime64[ns]", "close": np.float64, "MA_open": np.float64, 
    "MA_close": np.float64, "MA_high": np.float64, "MA_low": np.float64, 
    "ATR": np.float64, "Up": np.float64, "Dn": np.float64, "Trend": np.float64, 
    "TrendUp": np.float64, "TrendDown": np.float64, "TrendSL": np.float64, 
    "EMA": np.float64, "open": np.float64, "high": np.float64, "low": np.float64, 
    "instrument_token": "Int64", "LongSignal": "Int64", "ShortSignal": "Int64", 
    "LongCoverSignal": "Int64", "ShortCoverSignal": "Int64"
}

# Convert column types
for column, dtype in column_types.items():
    signalsdf[column] = signalsdf[column].astype(dtype)

# Setting StrikePrc at 09.20 a.m.
def job():
    global strike_prc , nifty_token
    from_date = datetime.datetime.strptime(f'{date.today()} 09:18:59', '%Y-%m-%d %H:%M:%S')
    to_date = datetime.datetime.strptime(f'{date.today()} 09:19:59', '%Y-%m-%d %H:%M:%S')
    nifty_data = kite.historical_data(instrument_token=nifty_token,from_date=from_date,to_date=to_date,interval='minute', oi=True)[0]['close']
    strike_prc = round(nifty_data/100)*100
    return strike_prc

def get_ltp():
    global nifty_token,strike_prc
    nifty_ltp = kite.ltp('NSE:NIFTY 50')
    strike_prc = round(nifty_ltp['NSE:NIFTY 50']['last_price']/100)*100
    return strike_prc


def time_until(target_time):
    now = datetime.datetime.now()
    target_datetime = datetime.datetime.combine(now.date(), target_time)
    if now > target_datetime:
        return datetime.timedelta(0)
    return target_datetime - now

# check if the time is greater than 09:20 a.m. to run job() or else wait for 09:20 a.m
current_time = datetime.datetime.now().time()
target_time = datetime.time(9, 19)

if current_time > target_time:
    print('Running job()...')
    job()
else:
    # Wait until 09:19
    print('Waiting for 09:19 AM...')
    sleep(time_until(target_time).seconds)
    get_ltp()

print("Today's Strike Price:",strike_prc)

# holidays = ['2023-05-01', '2023-06-16','2023-06-29']  # Add all trading holidays here

trading_tokens,zerodha_list,alice_list = get_option_tokens(base_symbol,str(expiry_date),strike_prc)

for token in trading_tokens:
    # hist_data[token] = read_data_from_timescaleDB(token)
    hist_data[token] =  pd.DataFrame(kite.historical_data(token, from_date, to_date, interval))
    hist_data[token]['date'] = pd.to_datetime(hist_data[token]['date'])
    hist_data[token].set_index('date', inplace=True)
    hist_data[token].sort_index(inplace=True)
    hist_data[token]['instrument_token'] = token
    hist_data[token]= hist_data[token].drop(['volume'], axis=1)
  
with open('Strategies/Amipy/AmiPy.json' , 'r') as f:
    parameters = json.load(f)

entry = parameters['Nifty'][0]['entry_time']
last = parameters['Nifty'][0]['last_buy_time']
sqroff = parameters['Nifty'][0]['sqroff_time']


long_indices = []
longcover_indices = []
short_indices = []
shortcover_indices = []
last_signal_minute = None
trade_state_df = pd.DataFrame(columns=['in_trade', 'strike_price', 'trade_type', 'trade_points', 'TrendSL', 'close', 'TradeEntryPrice', 'SL_points'])

# Time params ### TTTT
entry_time = pd.Timestamp(entry).time()
last_buy_time = pd.Timestamp(last).time()
sqroff_time = pd.Timestamp(sqroff).time()


def genSignals(resultdf):
    counter = 0
    signals = []
    trade_no = 1
    current_position = None
    global last_signal_minute, trading_tokens,trade_state_df, strike_prc
    trade_state = {'in_trade': False, 'strike_price':strike_prc, 'trade_type': None, 'trade_points': 0, 'TrendSL': 0, 'close': 0, 'TradeEntryPrice': 0, 'SL_points': 0}
    
    # trade_state_path = os.path.join("LiveCSV","trade_state.csv")
    script_dir = os.path.dirname(os.path.realpath(__file__))
    trade_state_path = os.path.join(script_dir, "LiveCSV","trade_state.csv")

    long_indices = []
    longcover_indices = []
    short_indices = []
    shortcover_indices = []
    
    def long(df, i):
        return (df.loc[df.index[i], "Trend"] == 1) & (df.loc[df.index[i], "close"] > df.loc[df.index[i], "EMA"]) & (df.index[i].time() > entry_time) & (df.index[i].time() < sqroff_time) & (df.index[i].time() < last_buy_time)

    def short(df, i):
        return (df.loc[df.index[i], "Trend"] == -1) & (df.loc[df.index[i], "close"] < df.loc[df.index[i], "EMA"]) & (df.index[i].time() > entry_time) & (df.index[i].time() < sqroff_time) & (df.index[i].time() < last_buy_time)

    def longcover(df, i):
        current_minute = df.index[i].floor('T')
        return (current_minute not in longcover_indices) and ((df.loc[df.index[i], "Trend"] == -1) or (df.index[i].time() > sqroff_time))

    def shortcover(df, i):
        current_minute = df.index[i].floor('T')
        return (current_minute not in shortcover_indices) and ((df.loc[df.index[i], "Trend"] == 1) or (df.index[i].time() > sqroff_time))

    
    cover_position_check = None
    
    for i in range(1, len(resultdf)):
        current_time = resultdf.index[i]
        current_minute = current_time.floor('T')
        current_close = resultdf.loc[current_time, 'close']
        trend_sl = resultdf.loc[current_time, 'TrendSL']
        
        if current_time.date() != datetime.datetime.today().date():
            continue
                
        if current_position is None:
            cover_position_check = None
            if long(resultdf, i):
                counter += 1
                current_position = 'Long'
                long_indices.append(resultdf.index[i])
                                
                trade_state['in_trade'] = True
                trade_state['strike_price'] = strike_prc
                trade_state['trade_type'] = 'Long'
                trade_state['trade_points'] = current_close - resultdf['close'].iloc[-1]
                trade_state['TrendSL'] = trend_sl
                trade_state['close'] = resultdf['close'].iloc[-1]
                trade_state['TradeEntryPrice'] = current_close
                trade_state['SL_points'] = resultdf['close'].iloc[-1] - trend_sl
                
            elif short(resultdf, i):
                current_position = 'Short'
                short_indices.append(resultdf.index[i])
                
                trade_state['in_trade'] = True
                trade_state['strike_price'] = strike_prc
                trade_state['trade_type'] = 'Short'
                trade_state['trade_points'] = current_close - resultdf['close'].iloc[-1]
                trade_state['TrendSL'] = trend_sl
                trade_state['close'] = resultdf['close'].iloc[-1]
                trade_state['TradeEntryPrice'] = current_close
                trade_state['SL_points'] = trend_sl - resultdf['close'].iloc[-1]
                
        else:
            if current_position == 'Long' and longcover(resultdf, i):
                if cover_position_check != 'LongCover':
                    longcover_indices.append(resultdf.index[i])
                    cover_position_check = 'LongCover'
                trade_no += 1
                trade_state['in_trade'] = False
                trade_state['strike_price'] = 0
                trade_state['trade_type'] = None
                trade_state['trade_points'] = 0
                trade_state['TrendSL'] = 0
                trade_state['SL_points'] = 0
                trade_state['TradeEntryPrice'] = 0


            elif current_position == 'Short' and shortcover(resultdf, i):
                if cover_position_check != 'ShortCover':
                    shortcover_indices.append(resultdf.index[i])
                    cover_position_check = 'ShortCover'

                trade_no += 1
                trade_state['in_trade'] = False
                trade_state['strike_price'] = 0
                trade_state['trade_type'] = None
                trade_state['trade_points'] = 0
                trade_state['TrendSL'] = 0
                trade_state['SL_points'] = 0
                trade_state['TradeEntryPrice'] = 0
            
        
        trade_state_df = pd.DataFrame([trade_state])  # convert dictionary to DataFrame
        trade_state_df.to_csv(trade_state_path, index=False)  # write DataFrame to CSV

        resultdf['LongSignal'] = 0
        resultdf['ShortSignal'] = 0
        resultdf['LongCoverSignal'] = 0
        resultdf['ShortCoverSignal'] = 0

        resultdf.loc[long_indices, 'LongSignal'] = 1
        resultdf.loc[short_indices, 'ShortSignal'] = 1
        resultdf.loc[longcover_indices, 'LongCoverSignal'] = 1
        resultdf.loc[shortcover_indices, 'ShortCoverSignal'] = 1
    
    # genSignals_path = os.path.join("LiveCSV", "amipy_genSignals.csv")
    script_dir = os.path.dirname(os.path.realpath(__file__))
    genSignals_path = os.path.join(script_dir, "LiveCSV", "amipy_genSignals.csv")
    resultdf.to_csv(genSignals_path, index=True)

    return resultdf, trade_state

signals = []

def updateSignalDf(last_signal,users_to_trade):
    print("updateSignalDf")
    global signalsdf, signals

    # trade_sig_path = os.path.join("LiveCSV", "amiNF_trd_sig_liv.csv")
    script_dir = os.path.dirname(os.path.realpath(__file__))
    trade_sig_path = os.path.join(script_dir, "LiveCSV", "amiNF_trd_sig_liv.csv")

    trade_no = 1
    current_close = last_signal['close']
    trade_date = last_signal.name.date()
    trade_time = last_signal.name.time()

    allsignals = ['LongSignal', 'ShortSignal', 'LongCoverSignal', 'ShortCoverSignal']
    trade_type = None  # initialize trade_type variable
    for generated_signal in allsignals:
        if last_signal[generated_signal] == 1:
            trade_type = generated_signal  # update trade_type when a signal is generated
            print(f"{trade_type} is generated")

    if trade_type == 'LongSignal' or trade_type == 'ShortSignal':
        signal = {
            'Strike_Price': strike_prc,
            'Trade_No': trade_no,
            'Trade_Type': trade_type,
            'Date': str(trade_date),
            'TradeEntryTime': str(trade_time),
            'TradeEntryPrice': current_close,
        }
        signals.append(signal)
        signals_df = pd.DataFrame(signal, index=[0])
        signals_df.to_csv(trade_sig_path, index=True)
        if 'SignalEntry' not in params['Nifty'][0]:
            params['Nifty'][0]['SignalEntry'] = {}
        params['Nifty'][0]['SignalEntry'][trade_type] = signal
        with open('AmiPy.json' , 'w') as f:
            json.dump(params, f, indent=4)
        if trade_type == 'LongSignal':
            order_details_opt = {
                "strike_prc": strike_prc,
                "transcation":"BUY",
            }
            for zerodha,alice in zip(zerodha_list,alice_list):
                place_order.place_order_for_broker("AmiPy",order_details_opt,trading_symbol=(zerodha,alice))
        elif trade_type == 'ShortSignal':
            for zerodha,alice in zip(zerodha_list,alice_list):
                # Extract the strike price from the token
                token_strike_price = int(zerodha[-7:-2])
                # Compare with strike_prc
                if token_strike_price == strike_prc:
                    transcation_type = 'SELL'
                else:
                    transcation_type = 'BUY'
                # Call your place_order function here
                place_order.place_order_for_broker("AmiPy", {"strike_prc": strike_prc, "transcation": transcation_type}, trading_symbol=(zerodha,alice))

    elif trade_type == 'LongCoverSignal' or trade_type == 'ShortCoverSignal':
        signal = signals.pop()  # Retrieve the last signal
        signal.update({
            'TradeExitTime': str(trade_time),
            'TradeExitPrice': current_close,
        })
        signal['NetTradePoints'] = signal['TradeExitPrice'] - signal['TradeEntryPrice']
        signals_df = pd.DataFrame(signal, index=[0])
        signals_df.to_csv(trade_sig_path, index=True)
        params['Nifty'][0]['SignalEntry'][trade_type] = signal
        #update the json file
        with open('AmiPy.json' , 'w') as f:
            json.dump(params, f, indent=4)
        if trade_type == 'LongCoverSignal':
            order_details_opt = {
                "strike_prc": strike_prc,
                "transcation":"SELL",
            }
            for zerodha,alice in zip(zerodha_list,alice_list):
                place_order.place_order_for_broker("AmiPy",order_details_opt,tradingsymbol=(zerodha,alice))
        elif trade_type == 'ShortCoverSignal':
            for zerodha,alice in zip(zerodha_list,alice_list):
                # Extract the strike price from the token
                token_strike_price = int(zerodha[-7:-2])

                # Compare with strike_prc
                if token_strike_price == strike_prc:
                    transcation_type = 'BUY'
                else:
                    transcation_type = 'SELL'
                
                # Call your place_order function here
                place_order.place_order_for_broker("AmiPy", {"strike_prc": strike_prc, "transcation": transcation_type}, tradingsymbol=(zerodha,alice))

    try:
        if trade_type is not None:  # check that a signal was generated
            signal_prc = str(last_signal['close'])
            message = f"Signal: {trade_type}\nStrikePrc: {strike_prc} \nDate: {trade_date}\nTime: {trade_time}\nClose: {signal_prc}"
            print(message)
            discord_bot.discord_bot(message, "AmiPy")
    except Exception as e:
        print(f"Error in sending telegram message: {e}")

last_signal_t = None

def on_ticks(ws, ticks):
    global hist_data,signalsdf,last_signal_t 
    # print('Received ticks:', ticks)
    current_minute = datetime.datetime.now().replace(second=0, microsecond=0).astimezone().strftime('%Y-%m-%d %H:%M:%S%z')[:-2] + ":" + datetime.datetime.now().astimezone().strftime('%z')[-2:]

    for tick in ticks:
        # print('Processing tick:', tick)
        token = tick['instrument_token']
        ltp = tick['last_price']

        # Check if the current_minute exists in the DataFrame's index
        if current_minute not in hist_data[token].index:
            # print("New minute")
            # Create a new row for the current_minute
            hist_data[token].loc[current_minute] = [ltp, ltp, ltp, ltp, int(token)]

        # Update the high and low values
        # print("Updating high and low")
        hist_data[token].at[current_minute, 'high'] = max(ltp, hist_data[token].at[current_minute, 'high'])
        hist_data[token].at[current_minute, 'low'] = min(ltp, hist_data[token].at[current_minute, 'low'])

        # Update the close value
        hist_data[token].at[current_minute, 'close'] = ltp
        
        hist_data[token]
        
    resampleddf = callputmergeddf(hist_data,trading_tokens)
    # resampleddf.to_csv(f'resample_ohlc_{trading_tokens[0]}.csv', index=True)
    ma_df = moving_average(resampleddf)
    # ma_df.to_csv(f'Dataframescsv/amipy_madf.csv', index=True)
    resultdf = supertrend(ma_df)
    # resultdf.to_csv(f'Dataframescsv/amipy_resultdf.csv', index=True)
    signalsdf, trade_state = genSignals(resultdf)

    current_time = datetime.datetime.now()
    
    time_diff = (current_time - last_signal_t) if last_signal_t is not None else timedelta(minutes=1)

    if time_diff >= timedelta(minutes=1):

        last_signal_t = current_time
    
        new_signal = signalsdf[['LongSignal', 'ShortSignal', 'LongCoverSignal', 'ShortCoverSignal']].iloc[-1].any()
        if new_signal:
            last_signal = signalsdf.iloc[-1]
            updateSignalDf(last_signal, users_to_trade)

    # updateSignalDf(signalsdf, trade_state)

def on_connect(ws, response):  # noqa
    global trading_tokens
    # Callback on successful connect.
    ws.subscribe(trading_tokens)

    # Set trading_tokens to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, trading_tokens)

# Initialise
kws = KiteTicker(kite_api_key, kite_access_token)
# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect(threaded=True)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout
app.layout = html.Div(
    [
        dbc.Row([
            dbc.Col(html.H4(id='strike-price', className="text-center"), width=12),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='live-graph', animate=True), width=12),
        ]),
        dcc.Interval(
            id='graph-update',
            interval=1*1000,)  # in milliseconds
    ]
)

# Define callback to update chart and trade state
@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph_scatter(n):
    if trade_state_df.empty:
        trade_state = {
            'in_trade': 0,
            'strike_price': 0,
            'trade_type': 'neutral',
            'trade_points': 0,
            'TrendSL': 0,
            'close': 0,
            'TradeEntryPrice': 0,
            'SL_points': 0,
        }
    else:
        # Call your genSignals function here to get the latest trade_state
        trade_state = trade_state_df.iloc[-1].to_dict()
    # trade_state = trade_state_df.iloc[-1].to_dict()

    # Format the trade_state as a string
    trade_state_text = f"In Trade: {trade_state['in_trade']}\n" \
                       f"Trade Points: {trade_state['trade_points']:.2f}\n" \
                       f"TrendSL: {trade_state['TrendSL']:.2f}\n" \
                       f"TradeEntryPrice: {trade_state['TradeEntryPrice']:.2f}\n" \
                       f"SL Points: {trade_state['SL_points']:.2f}"
    

    strike_price_text = f"Strike Price: {trade_state['strike_price']:.2f}"
    close_text = f"{trade_state['close']:.2f}"
    # Update the plot
    fig = plotly_plot(signalsdf)
    fig.update_xaxes(
        tickformat="%H:%M:%S",  # Change this if you have a different time format
        dtick=3600000  # 1 hour in milliseconds
    )

    # Add trade state and strike price as annotations
    fig.add_annotation(
        x=0,
        y=0,
        xref="paper",
        yref="y",
        text=trade_state_text,
        showarrow=False,
        bgcolor='green' if trade_state['trade_type'] == 'Long' else 'red' if trade_state['trade_type'] == 'Short' else 'grey',
        font=dict(color='white'),
        align='left',
        borderpad=4,
        xanchor='left',
        yanchor='bottom'
    )

    fig.add_annotation(
        x=0.5,
        y=1,
        xref="paper",
        yref="paper",
        text=strike_price_text,
        showarrow=False,
        bgcolor='white',
        font=dict(color='black'),
        align='center',
        borderpad=4,
        xanchor='center',
        yanchor='top'
    )

    fig.add_annotation(
        x=1.02,
        y=trade_state['close'],  # Slightly higher position for 'Close'
        xref="paper",
        yref="y",
        text=close_text,
        showarrow=False,
        bgcolor='white',
        font=dict(color='black', size=14),  # Increased font size
        align='right',
        borderpad=4,
        xanchor='center',
        yanchor='top'
    )

    return fig

# Run app
if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port="8050", debug=True, use_reloader=False)

print("Waiting for ticks...")
