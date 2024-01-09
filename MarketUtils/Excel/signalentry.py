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

ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

excel_dir = os.getenv('onedrive_excel_folder')
# excel_dir = r"/Users/amolkittur/Desktop/Dev/UserProfile/Excel"

def append_data_to_excel(data, sheet_name):
    excel_path = os.path.join(excel_dir, "Signals.xlsx")
    book = load_workbook(excel_path)
    sheet = book[sheet_name] if sheet_name in book.sheetnames else book.create_sheet(sheet_name)

    # Convert data to DataFrame for easy manipulation
    new_data_df = pd.DataFrame([data])

    # Find the first empty row to start appending data
    first_empty_row = sheet.max_row + 1 if sheet.max_row > 1 else 2

    # Append new data
    for r_idx, row in enumerate(dataframe_to_rows(new_data_df, index=False, header=False), first_empty_row):
        for c_idx, value in enumerate(row, 1):
            sheet.cell(row=r_idx, column=c_idx, value=value)

    # Apply formatting to new rows only
    number_style = NamedStyle(name='number_style', number_format='0.00')
    center_alignment = Alignment(horizontal='center')
    rounded_columns = ['entry_price', 'exit_price', 'hedge_entry_price', 'hedge_exit_price', 'trade_points']

    if 'number_style' not in book.named_styles:
        book.add_named_style(number_style)

    for row in sheet.iter_rows(min_row=first_empty_row, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
        for cell in row:
            cell.alignment = center_alignment
            if sheet.cell(row=1, column=cell.col_idx).value in rounded_columns:
                cell.number_format = number_style.number_format

    # Save the workbook with the new data and styles
    book.save(excel_path)
    book.close()

def get_list_of_strategies():
    active_users_filepath = os.path.join(DIR,"MarketUtils", "active_users.json")
    active_users = general_calc.read_json_file(active_users_filepath)
    for user in active_users:
        strategies = user["qty"]
        strategies = list(strategies.keys())
    strategies.append("AmiPy")
    strategies.remove("PreviousOvernightFutures")
    return strategies

def get_sltype(strategy):
    _, strategy_path = place_order_calc.get_strategy_json(strategy)
    strategy_obj = Strategy.read_strategy_json(strategy_path)
    sl_type = strategy_obj.get_exit_params().get("SLType")
    return sl_type

def get_todays_trade_ids(strategy):
        # Load the respective sheet from 'omkar.xlsx'
    omkar_file_path = os.path.join(excel_dir, "omkar.xlsx")
    df = pd.read_excel(omkar_file_path, sheet_name=strategy)
    # Filter the DataFrame for rows where the exit_time is today's date
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    today = pd.Timestamp.today().normalize()
    todays_trades = df[df['exit_time'].dt.normalize() == today]
    todays_trade_ids = todays_trades['trade_id'].tolist()
    return todays_trade_ids

def determine_trade_id_to_use(todays_trade_ids, signal_type, strategy):
    if len(todays_trade_ids) == 1:
        return todays_trade_ids[0]
    else:
        omkar_file_path = os.path.join(excel_dir, "omkar.xlsx")
        df = pd.read_excel(omkar_file_path, sheet_name=strategy)

        for trade_id in todays_trade_ids:
            trade_row = df[df['trade_id'] == trade_id]
            if not trade_row.empty and trade_row['signal'].iloc[0] == signal_type:
                return trade_id

        # If no matching trade_id is found, you might want to handle this case
        return None

def format_datetime_for_excel(date_time):
    # Get today's date
    today = datetime.today().date()

    # Parse the time string
    time_obj = datetime.strptime(date_time, '%H:%M:%S').time()

    # Combine date and time into a datetime object
    combined_datetime = datetime.combine(today, time_obj)

    # Format the datetime object into a string
    return combined_datetime.strftime('%Y-%m-%d %H:%M:%S')

def determine_trading_symbol(trade_id,strategy):
    omkar_file_path = os.path.join(excel_dir, "omkar.xlsx")
    df = pd.read_excel(omkar_file_path, sheet_name=strategy)
    trade_row = df[df['trade_id'] == trade_id]
    return trade_row['trading_symbol'].iloc[0]

def handle_strategy_sl(strategy, strategy_path):
    # Read the strategy JSON to get SignalEntry details
    strategy_obj = Strategy.read_strategy_json(strategy_path)
    signal_entry = strategy_obj.get_signal_entry()
    todays_trade_ids = get_todays_trade_ids(strategy)
    trade_date = datetime.today()

    # Process each signal in SignalEntry
    for signal_type, details in signal_entry.items():
        # Process only signals with 'cover' in their type
        if 'cover' in signal_type.lower():
            trade_entry_time = details.get("TradeEntryTime")
            trade_exit_time = details.get("TradeExitTime")            
            trade_entry_price = details.get("TradeEntryPrice")
            trade_exit_price = details.get("TradeExitPrice")

            # Calculate trade points based on Trade_Type
            trade_points = 0
            if signal_type == "ShortCoverSignal":
                hedge_points = calculate_hedge_points(strategy)
                trade_points = (trade_entry_price - trade_exit_price) + hedge_points
                signal = "Short"
                trade_id_to_use = determine_trade_id_to_use(todays_trade_ids, signal, strategy)
            elif signal_type == "LongCoverSignal":
                # Note: For LongCoverSignal, there might be specific logic
                trade_points = (trade_exit_price - trade_entry_price)
                hedge_points = 0.00
                signal = "Long"
                trade_id_to_use = determine_trade_id_to_use(todays_trade_ids, signal, strategy)

    trade_data = {
            "trade_id": trade_id_to_use,
            "trading_symbol": determine_trading_symbol(trade_id_to_use,strategy),
            "signal": signal,
            "entry_time": format_datetime_for_excel(trade_entry_time),
            "exit_time": format_datetime_for_excel(trade_exit_time),
            "entry_price": round(trade_entry_price, 2),
            "exit_price": round(trade_exit_price, 2),
            "hedge_points": round(hedge_points,2), 
            "trade_points": round(trade_points, 2),
        }
    append_data_to_excel(trade_data,strategy)

def handle_other_sl_types(strategy):
    # Fetch today's trade IDs from 'omkar.xlsx'
    todays_trade_ids = get_todays_trade_ids(strategy)

    # Load the respective sheet from 'omkar.xlsx' for additional trade details
    omkar_file_path = os.path.join(excel_dir, "omkar.xlsx")
    df = pd.read_excel(omkar_file_path, sheet_name=strategy)


    # Process each trade for today
    for trade_id in todays_trade_ids:
        trade_row = df[df['trade_id'] == trade_id]
        if not trade_row.empty:
            trade_entry_price = trade_row['entry_price'].iloc[0]
            trade_exit_price = trade_row['exit_price'].iloc[0]

            # Calculate hedge points
            hedge_entry_price = trade_row['hedge_entry_price'].iloc[0]
            hedge_exit_price = trade_row['hedge_exit_price'].iloc[0]
            hedge_points = hedge_exit_price - hedge_entry_price
            trade_points = (trade_entry_price - trade_exit_price) + hedge_points

        entry_time_datetime = pd.to_datetime(trade_row['entry_time'].iloc[0])
        exit_time_datetime = pd.to_datetime(trade_row['exit_time'].iloc[0])

        trade_data = {
                "trade_id": trade_id,
                "trading_symbol": determine_trading_symbol(trade_id,strategy),
                "signal": trade_row['signal'].iloc[0],
                "entry_time": entry_time_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "exit_time": exit_time_datetime,
                "entry_price": round(trade_entry_price, 2),
                "exit_price": round(trade_exit_price, 2),
                "hedge_points": round(hedge_points,2), 
                "trade_points": round(trade_points, 2),
            }
        append_data_to_excel(trade_data,strategy)

def calculate_hedge_points(strategy):
    todays_trades = get_todays_trade_ids(strategy)
    
    omkar_file_path = os.path.join(excel_dir, "omkar.xlsx")
    df = pd.read_excel(omkar_file_path, sheet_name=strategy)

    # Calculate hedge points for each trade
    for trade_id in todays_trades:
        trade_row = df[df['trade_id'] == trade_id]
        if not trade_row.empty:
            hedge_entry_price = trade_row['hedge_entry_price'].iloc[0]
            hedge_exit_price = trade_row['hedge_exit_price'].iloc[0]
            hedge_points= hedge_exit_price - hedge_entry_price

    return hedge_points

def main():
    strategies = get_list_of_strategies()
    print(strategies)
    for strategy in strategies:
        sl_type = get_sltype(strategy)
        _, strategy_path = place_order_calc.get_strategy_json(strategy)
        if sl_type == "StrategySL":
            handle_strategy_sl(strategy, strategy_path)
        else:
            handle_other_sl_types(strategy)

main()