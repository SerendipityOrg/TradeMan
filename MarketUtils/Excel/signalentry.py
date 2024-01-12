import os,sys
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment,NamedStyle
from dotenv import load_dotenv
from datetime import datetime
from openpyxl.utils.dataframe import dataframe_to_rows



DIR = os.getcwd()
sys.path.append(DIR)

import MarketUtils.general_calc as general_calc
import Brokers.place_order_calc as place_order_calc
from Strategies.StrategyBase import Strategy
import DBpy.DB_utils as db_utils

ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

excel_dir = os.getenv('onedrive_excel_folder')
# excel_dir = r"/Users/amolkittur/Desktop/Dev/UserProfile/Excel"

def read_from_db(conn, strategy, date_column='exit_time'):
    """Read data from the database for a specific strategy and date."""
    today = pd.Timestamp.today().normalize()
    query = f"SELECT * FROM {strategy} WHERE strftime('%Y-%m-%d', {date_column}) = ?"
    return pd.read_sql_query(query, conn, params=(today.strftime('%Y-%m-%d'),))

def append_data_to_db(conn, data, table_name):
    """Append data to the specified table in the database."""
    new_data_df = pd.DataFrame([data])
    try:
        new_data_df.to_sql(table_name, conn, if_exists='append', index=False)
    except Exception as e:
        print(f"An error occurred while appending to the table {table_name}: {e}")


def get_list_of_strategies():
    active_users_filepath = os.path.join(DIR,"MarketUtils", "active_users.json")
    active_users = general_calc.read_json_file(active_users_filepath)
    for user in active_users:
        strategies = user["qty"]
        strategies = list(strategies.keys())
    strategies.append("AmiPy")
    return strategies

def get_sltype(strategy):
    _, strategy_path = general_calc.get_strategy_json(strategy)
    strategy_obj = Strategy.read_strategy_json(strategy_path)
    sl_type = strategy_obj.get_exit_params().get("SLType")
    return sl_type

def determine_trade_id_to_use(conn, todays_trade_ids, signal_type, strategy):
    if len(todays_trade_ids) == 1:
        return todays_trade_ids[0]
    else:
        df = read_from_db(conn, strategy)
        for trade_id in todays_trade_ids:
            trade_row = df[df['trade_id'] == trade_id]
            if not trade_row.empty and trade_row['signal'].iloc[0] == signal_type:
                return trade_id
        return None

def get_todays_trade_ids(conn, strategy):
    # Get today's date in the format used in your database
    today_str = datetime.today().strftime('%Y-%m-%d')

    # SQL query to select trades from today using the strategy name as the table name
    query = f"""
    SELECT trade_id FROM {strategy} 
    WHERE DATE(exit_time) = ?
    """
    try:
        todays_trades = pd.read_sql_query(query, conn, params=(today_str,))
        todays_trade_ids = todays_trades['trade_id'].tolist()
        return todays_trade_ids
    except Exception as e:
        print(f"An error occurred while fetching today's trade IDs for strategy '{strategy}': {e}")
        return []



def determine_trading_symbol(conn, trade_id, strategy):
    df = read_from_db(conn, strategy)
    trade_row = df[df['trade_id'] == trade_id]
    return trade_row['trading_symbol'].iloc[0]

def format_datetime_for_excel(date_time):
    # Get today's date
    today = datetime.today().date()

    # Parse the time string
    time_obj = datetime.strptime(date_time, '%H:%M:%S').time()

    # Combine date and time into a datetime object
    combined_datetime = datetime.combine(today, time_obj)

    # Format the datetime object into a string
    return combined_datetime.strftime('%Y-%m-%d %H:%M:%S')

def handle_strategy_sl(main_conn, signals_conn, strategy, strategy_path):
    print(f"Processing strategy {strategy}")
    strategy_obj = Strategy.read_strategy_json(strategy_path)
    signal_entry = strategy_obj.get_signal_entry()
    todays_trade_ids = get_todays_trade_ids(main_conn, strategy)

    for signal_type, details in signal_entry.items():
        if 'cover' in signal_type.lower():
            # Extract details from strategy JSON
            trade_entry_time = details.get("TradeEntryTime")
            trade_exit_time = details.get("TradeExitTime")
            trade_entry_price = details.get("TradeEntryPrice")
            trade_exit_price = details.get("TradeExitPrice")

            # Initialize variables
            hedge_points = 0.00
            trade_points = 0
            signal = ""

            if signal_type == "ShortCoverSignal":
                hedge_points = calculate_hedge_points(main_conn, strategy)
                trade_points = (trade_entry_price - trade_exit_price) + hedge_points
                signal = "Short"
            elif signal_type == "LongCoverSignal":
                trade_points = (trade_exit_price - trade_entry_price)
                signal = "Long"

            trade_id_to_use = determine_trade_id_to_use(main_conn, todays_trade_ids, signal, strategy)
            if not trade_id_to_use:
                print(f"No trade ID found for {signal_type} in strategy {strategy}")
                continue

            trade_data = {
                "trade_id": trade_id_to_use,
                "trading_symbol": determine_trading_symbol(main_conn, trade_id_to_use, strategy),
                "signal": signal,
                "entry_time": format_datetime_for_excel(trade_entry_time),
                "exit_time": format_datetime_for_excel(trade_exit_time),
                "entry_price": round(trade_entry_price, 2),
                "exit_price": round(trade_exit_price, 2),
                "hedge_points": round(hedge_points, 2), 
                "trade_points": round(trade_points, 2),
            }

            append_data_to_db(signals_conn, trade_data, strategy)



def handle_other_sl_types(main_conn, signals_conn, strategy):
    print(f"Processing strategy {strategy}")
    todays_trade_ids = get_todays_trade_ids(main_conn, strategy)

    for trade_id in todays_trade_ids:
        trade_row = read_from_db(main_conn, strategy)

        if not trade_row.empty:
            trade_entry_price = trade_row['entry_price'].iloc[0]
            trade_exit_price = trade_row['exit_price'].iloc[0]
            hedge_entry_price = trade_row['hedge_entry_price'].iloc[0]
            hedge_exit_price = trade_row['hedge_exit_price'].iloc[0]
            hedge_points = hedge_exit_price - hedge_entry_price
            trade_points = (trade_entry_price - trade_exit_price) + hedge_points

            entry_time_datetime = pd.to_datetime(trade_row['entry_time'].iloc[0])
            exit_time_datetime = pd.to_datetime(trade_row['exit_time'].iloc[0])

            trade_data = {
                "trade_id": trade_id,
                "trading_symbol": determine_trading_symbol(main_conn, trade_id, strategy),
                "signal": trade_row['signal'].iloc[0],
                "entry_time": entry_time_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "exit_time": exit_time_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "entry_price": round(trade_entry_price, 2),
                "exit_price": round(trade_exit_price, 2),
                "hedge_points": round(hedge_points, 2), 
                "trade_points": round(trade_points, 2),
            }

            append_data_to_db(signals_conn, trade_data, strategy)


def calculate_hedge_points(conn, strategy):
    # Fetch today's trade IDs
    todays_trades = get_todays_trade_ids(conn, strategy)

    # Initialize hedge_points
    total_hedge_points = 0

    # Calculate hedge points for each trade
    for trade_id in todays_trades:
        # Fetch trade details from the database
        trade_row = read_from_db(conn, strategy)

        if not trade_row.empty:
            # Extract hedge entry and exit prices
            hedge_entry_price = trade_row['hedge_entry_price'].iloc[0]
            hedge_exit_price = trade_row['hedge_exit_price'].iloc[0]

            # Calculate hedge points for the trade
            hedge_points = hedge_exit_price - hedge_entry_price
            total_hedge_points += hedge_points

    return total_hedge_points


def main():
    strategies = get_list_of_strategies()
    print(strategies)#excel_dir

    main_db_path = os.path.join(excel_dir, "vimala.db")  # Path to the omkar.db file
    signals_db_path = os.path.join(excel_dir, "Signals.db")

    main_conn = db_utils.get_db_connection(main_db_path)
    signals_conn = db_utils.get_db_connection(signals_db_path)

    for strategy in strategies:
        sl_type = get_sltype(strategy)
        _, strategy_path = general_calc.get_strategy_json(strategy)

        if sl_type == "StrategySL":
            handle_strategy_sl(main_conn,signals_conn, strategy, strategy_path)
        else:
            handle_other_sl_types(main_conn,signals_conn, strategy)

    main_conn.close()
    signals_conn.close()


main()