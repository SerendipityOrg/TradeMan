import os,sys
import datetime as dt
import pandas as pd
import psycopg2
from kiteconnect import KiteConnect
from collections import namedtuple
from datetime import timedelta

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Strategies.StrategyBase as StrategyBase
import MarketUtils.general_calc as general_calc
import MarketUtils.InstrumentBase as InstrumentBase
from Brokers.BrokerUtils import Broker

_,strategy_path = general_calc.get_strategy_json("AmiPy")
strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
instru_obj = InstrumentBase.Instrument()


kite = KiteConnect(api_key=Broker.get_primary_account()[0])
kite.set_access_token(access_token=Broker.get_primary_account()[1])

def get_csv_kite():
    instrument_dump = kite.instruments()
    instrument_df = pd.DataFrame(instrument_dump)
    instrument_df.to_csv(r'instruments.csv')
    print("Download Complete!")

get_csv_kite()

holidays = [dt.date(2023, i, j) for i, j in [
    (1, 26), (3, 7), (3, 30), (4, 4), (4, 7), (4, 14),
    (4, 22), (5, 1), (6, 28), (8, 15), (9, 19), (10, 2),
    (10, 24), (11, 14), (11, 27), (12, 25)]
]


def connect_to_db(base_symbol):
    print(f"Connecting to database {base_symbol.lower()}...")
    return psycopg2.connect(
        dbname=base_symbol.lower(),
        user="postgres",
        password="K@nnada0",
        host="localhost",
        port="5432"
    )

def store_data_in_postgres(trading_symbol_list, all_data, cursor):
    table_name =trading_symbol_list[0]
        
    if " " or "(" or")" in table_name:
        table_name = table_name.replace(" ", "").replace("(", "").replace(")", "")

    print(f"Storing data in table {table_name}...")
    # table_name = trading_symbol_list[0].replace("-", "_").lower()
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (date TIMESTAMP, open REAL, high REAL, low REAL, close REAL, volume INT);"
    cursor.execute(create_table_query)
    
    for record in all_data:
        date = record['date'].strftime('%Y-%m-%d %H:%M:%S')
        open_price = record['open']
        high = record['high']
        low = record['low']
        close_price = record['close']
        volume = record['volume']
        
        insert_query = f"INSERT INTO {table_name} (date, open, high, low, close, volume) VALUES ('{date}', {open_price}, {high}, {low}, {close_price}, {volume});"
        try:
            cursor.execute(insert_query)
        except Exception as e:
            print(f"Error while inserting record {table_name}: {e}")
    
    cursor.connection.commit()

def fetch_token_and_name(base_symbol,strike_prc,option_type,expiry_date):
    exchange_token = instru_obj.get_exchange_token_by_criteria(base_symbol,int(strike_prc),option_type,expiry_date)
    token = instru_obj.get_token_by_exchange_token(exchange_token)
    name = instru_obj.get_trading_symbol_by_exchange_token(exchange_token)
    return token,name

def fetch_and_store_historical_data(token,base_symbol, start_date, end_date,cursor):
    strike_prc = strategy_obj.calculate_current_atm_strike_prc(base_symbol)
    strike_step = strategy_obj.get_strike_step(base_symbol)
    upper_strikes = [(strike_prc  + i*strike_step) for i in range(1, 9)]
    lower_strikes = [(strike_prc  - i*strike_step) for i in range(1, 9)]
    all_strikes = lower_strikes + [strike_prc] + upper_strikes

    option_expiry = instru_obj.get_expiry_by_criteria(base_symbol,int(strike_prc),"CE")
    future_expiry = instru_obj.get_expiry_by_criteria(base_symbol,0,"FUT","current_month")


    data = kite.historical_data(instrument_token=token, from_date=start_date, to_date=end_date, interval="minute", continuous=False)
    store_data_in_postgres(base_symbol, data, cursor)
    
    future_token,future_symbol = fetch_token_and_name(base_symbol,0,"FUT",future_expiry)
    data = kite.historical_data(instrument_token=future_token, from_date=start_date, to_date=end_date, interval="minute", continuous=False)
    store_data_in_postgres(future_symbol, data, cursor)

    for strike in all_strikes:
        print(strike)
        for option_type in ["CE", "PE"]:
            token, name = fetch_token_and_name(base_symbol,int(strike),option_type,option_expiry)     
            data = kite.historical_data(instrument_token=token, from_date=start_date, to_date=end_date, interval="minute", continuous=False)
            # Store the data for this trading_symbol
            store_data_in_postgres(name, data, cursor)

def main():
    today = dt.datetime.today()
    day = today.weekday()
    today_expiry_symbol,today_expiry_token = strategy_obj.determine_expiry_index(day)
    base_symbols = [(today_expiry_symbol, today_expiry_token)]


    tomorrow = today + dt.timedelta(days=1)

    if day == 4:  # If today is Friday
        tomorrow += dt.timedelta(days=2)
        next_day = 0
    else:
        next_day = day + 1

    if tomorrow.date() in holidays:
        next_expiry_symbol, next_expiry_token= strategy_obj.determine_expiry_index(next_day)
        base_symbols.append((next_expiry_symbol, next_expiry_token))
    
    for base_symbol,expiry_token in base_symbols:
        conn = connect_to_db(base_symbol)
        cursor = conn.cursor()
        
        start_date = (dt.datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = dt.datetime.now().strftime('%Y-%m-%d')
        fetch_and_store_historical_data(expiry_token, base_symbol,start_date, end_date, cursor)

        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()