import datetime
import pytz
from kiteconnect import KiteConnect, KiteTicker
from psycopg2 import sql
from Brokers import apikey
import psycopg2
import pandas as pd
import time
import logging

connection = psycopg2.connect(
            dbname="ohlc_token",
            user=apikey.postgres_username,
            password=apikey.postgres_pass,
            host="localhost",
            port="5432"
        )


def save_ohlc_data_to_timescaleDB(token, ohlc_data):
    global connection
    table_name = 'ohlc_' + str(token)
    header = ["date", "open", "high", "low", "close", "instrument_token"]

    with connection.cursor() as cursor:
        # Create table
        column_definitions = [
            sql.Identifier(col_name.lower()) + sql.SQL(" " + data_type)
            for col_name, data_type in zip(
                header, ["TIMESTAMPTZ", "DOUBLE PRECISION", "DOUBLE PRECISION", "DOUBLE PRECISION", "DOUBLE PRECISION", "BIGINT"]
            )
        ]
        create_table_query = (
            sql.SQL("CREATE TABLE {} (")
            .format(sql.Identifier(table_name))
            + sql.SQL(", ").join(column_definitions)
            + sql.SQL(", PRIMARY KEY (date));")
        )
        cursor.execute(create_table_query)

        # Insert data
        insert_query = sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s, %s, %s);").format(sql.Identifier(table_name))
        for index, row in ohlc_data.iterrows():
            cursor.execute(insert_query, (index, row['open'], row['high'], row['low'], row['close'], row['instrument_token']))

        try:
            connection.commit()
        except Exception:
            connection.rollback()
            logging.exception("Couldn't write ticks to db: ")


# Set your Kite API key and secret
api_key = apikey.kite_api_key
api_secret = apikey.kite_api_sec

acctkn_file = r'Brokers\acc_token.txt'
reqtkn_file = r'Brokers\req_token.txt'
kite_access_token = open(acctkn_file,'r').read()
kite_request_token = open(reqtkn_file,'r').read()

# Replace with your own list of instrument tokens
tokens = [260105]
expiry_date = '2023-05-18'
strike_prc = 18300

# Replace with your own list of holidays
holidays = ["2023-05-01"]

instruments_df = pd.read_csv(r'Brokers\instruments.csv')

instruments_df = instruments_df[
    ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size","instrument_type","expiry","strike"]
]

# from instruments dataframe, get all instruments for 'NFO' exchange, name =='NIFTY',expiry date is 4thMay2023, strike value between 17000 to 19000
nfo_ins_df = instruments_df[
    (instruments_df["exchange"] == "NFO")
    & (instruments_df["name"] == "NIFTY")
    & (instruments_df["expiry"] == expiry_date)
    & (instruments_df["strike"] == strike_prc)
]

tokens.append(nfo_ins_df['instrument_token'].values[0])
tokens.append(nfo_ins_df['instrument_token'].values[1])   

live_data = []



## Check if market is open
def is_market_open(time, holidays):
    if time.weekday() > 4 or time.strftime("%Y-%m-%d") in holidays:
        return False
    if time.time() >= datetime.time(9, 15) and time.time() <= datetime.time(15, 30):
        return True
    return False

def on_ticks(ticks,ws):
    global live_data
    print('Received ticks:', ticks)
    current_minute = datetime.datetime.now().replace(second=0, microsecond=0).astimezone().strftime('%Y-%m-%d %H:%M:%S%z')[:-2] + ":" + datetime.datetime.now().astimezone().strftime('%z')[-2:]

    for tick in ticks:
        print('Processing tick:', tick)
        token = tick['instrument_token']
        ltp = tick['last_price']

        # Check if the current_minute exists in the DataFrame's index
        if current_minute not in live_data[token].index:
            # Create a new row for the current_minute
            live_data[token].loc[current_minute] = [ltp, ltp, ltp, ltp, int(token)]

        # Update the high and low values
        live_data[token].at[current_minute, 'high'] = max(ltp, live_data[token].at[current_minute, 'high'])
        live_data[token].at[current_minute, 'low'] = min(ltp, live_data[token].at[current_minute, 'low'])

        # Update the close value
        live_data[token].at[current_minute, 'close'] = ltp
        
        for token in tokens:
            save_ohlc_data_to_timescaleDB(token,live_data[token])
          
def on_connect(ws, response):  # noqa
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(tokens)

    # Set tokens to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, tokens)


# Initialise
kws = KiteTicker(apikey.kite_api_key, kite_access_token)

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect

# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()             

connection.close()      
