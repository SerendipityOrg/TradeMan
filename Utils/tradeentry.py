import pandas as pd
import json
from openpyxl import load_workbook
import os
from telethon.sync import TelegramClient

api_id = '22941664'
api_hash = '2ee02d39b9a6dae9434689d46e0863ca'

def process_mpwizard_trades(mpwizard_trades):
    if not mpwizard_trades:
        print("No MPWizard trades found.")
        return []
        
    result = []
    # Extracting trade details
    for i in range(len(mpwizard_trades["BUY"])):
        buy_trade = mpwizard_trades["BUY"][i]
        sell_trade = mpwizard_trades["SELL"][i]
        trade_data = {
            "Strategy": "MPWizard",
            "Index": buy_trade["tradingsymbol"][:-12],
            "Strike Prc": buy_trade["tradingsymbol"][-7:-2],
            "Date": pd.to_datetime(buy_trade["timestamp"]).date(),
            "Entry Time": pd.to_datetime(buy_trade["timestamp"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(sell_trade["timestamp"]).strftime('%H:%M'),
            "Entry Price": buy_trade["avg_prc"],
            "Exit Price": sell_trade["avg_prc"],
            "Trade points": float(sell_trade["avg_prc"]) - float(buy_trade["avg_prc"]),
            "Qty": buy_trade["qty"],
            "PnL": (float(sell_trade["avg_prc"]) - float(buy_trade["avg_prc"])) * int(buy_trade["qty"]) 
        }
        result.append(trade_data)
    return result

def process_short_trades(short_signals, short_cover_signals):
    if len(short_signals) != len(short_cover_signals):
        print("Mismatch in the number of ShortSignal and ShortCoverSignal trades.")
        return []

    result = []
    for i in range(0, len(short_signals), 4):  # Process each group of 4 trades together
        short_signal_group = short_signals[i:i+4]
        short_cover_signal_group = short_cover_signals[i:i+4]

        hedge_price = sum(float(trade["avg_prc"]) for trade in short_signal_group if trade["trade_type"] == "HedgeOrder") - \
                      sum(float(trade["avg_prc"]) for trade in short_cover_signal_group if trade["trade_type"] == "HedgeOrder")

        entry_price = sum(float(trade["avg_prc"]) for trade in short_signal_group)
        exit_price = sum(float(trade["avg_prc"]) for trade in short_cover_signal_group)
        trade_points = (entry_price - exit_price) + hedge_price
        trade_data = {
            "Strategy": "Nifty Straddle",
            "Index": "NIFTY",
            "Trade Type": "Short",
            "Strike Prc": short_signal_group[0]["strike_price"],
            "Date": pd.to_datetime(short_signal_group[0]["timestamp"]).date(),
            "Entry Time": pd.to_datetime(short_signal_group[0]["timestamp"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(short_cover_signal_group[0]["timestamp"]).strftime('%H:%M'),
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Hedge Price": hedge_price,
            "Trade points": exit_price - entry_price - hedge_price,
            "Qty": short_signal_group[0]["qty"],
            "PnL": trade_points * int(short_signal_group[0]["qty"])            
        }
        result.append(trade_data)
    return result

def process_long_trades(long_signals, long_cover_signals):
    if len(long_signals) != len(long_cover_signals):
        print("Mismatch in the number of LongSignal and LongCoverSignal trades.")
        return []

    result = []
    for i in range(0, len(long_signals), 2):  # Process each pair of trades together
        long_signal_pair = long_signals[i:i+2]
        long_cover_signal_pair = long_cover_signals[i:i+2]

        entry_price = sum(float(trade["avg_prc"]) for trade in long_signal_pair)
        exit_price = sum(float(trade["avg_prc"]) for trade in long_cover_signal_pair)

        trade_data = {
            "Strategy": "Amipy",
            "Index": "NIFTY",
            "Trade Type": "Long",
            "Strike Prc": long_signal_pair[0]["strike_price"],
            "Date": pd.to_datetime(long_signal_pair[0]["timestamp"]).date(),
            "Entry Time": pd.to_datetime(long_signal_pair[0]["timestamp"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(long_cover_signal_pair[0]["timestamp"]).strftime('%H:%M'),
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Trade points": exit_price - entry_price,
            "Qty": long_signal_pair[0]["qty"],
            "Hedge Price": float('nan'),
            "PnL": (exit_price - entry_price) * int(long_signal_pair[0]["qty"]) 
        }
        result.append(trade_data)
    return result


script_dir = os.path.dirname(os.path.realpath(__file__))
broker_filepath = os.path.join(script_dir, "broker.json")
json_dir = os.path.join(script_dir, "users")
excel_dir = os.path.join(script_dir, "excel")

with open(broker_filepath) as file:
    data = json.load(file)

# Initialize an empty list for the accounts to trade
user_list = []

# Go through each broker
for broker, broker_data in data.items():
    # Check if 'accounts_to_trade' is in the broker data
    if 'accounts_to_trade' in broker_data:
        # Add each account to the list
        for account in broker_data['accounts_to_trade']:
            user_list.append((broker, account))

for broker, user in user_list:
    # Load the JSON data
    with open(os.path.join(json_dir, f"{user}.json")) as file:
        user_data = json.load(file)

    phone_number = data[broker][user]["mobile_number"]

    # Default values
    amipy_df = pd.DataFrame()
    amipy_pnl = 0

    if "MPWizard" in user_data[broker]["orders"]:
        # Process the MPWizard trades
        mpwizard_data = process_mpwizard_trades(user_data[broker]["orders"]["MPWizard"])
        mpwizard_df = pd.DataFrame(mpwizard_data)
        mpwizard_pnl = round(mpwizard_df["PnL"].sum(),1)

    if "Amipy" in user_data[broker]["orders"]:
        amipy_data_short = []
        amipy_data_long = []
        if "ShortSignal" in user_data[broker]["orders"]["Amipy"]:
            # Process the AmiPy ShortSignal and ShortCoverSignal trades
            amipy_data_short = process_short_trades(user_data[broker]["orders"]["Amipy"]["ShortSignal"], 
                                                    user_data[broker]["orders"]["Amipy"]["ShortCoverSignal"])
        if "LongSignal" in user_data[broker]["orders"]["Amipy"]:
            # Process the AmiPy LongSignal and LongCoverSignal trades
            amipy_data_long = process_long_trades(user_data[broker]["orders"]["Amipy"]["LongSignal"], 
                                                user_data[broker]["orders"]["Amipy"]["LongCoverSignal"])

        # Combine short and long trades into a single DataFrame
        amipy_data = amipy_data_short + amipy_data_long
        if amipy_data:
            amipy_df = pd.DataFrame(amipy_data)
            amipy_pnl = round(amipy_df["PnL"].sum(), 1)

    # Read existing data from Excel file into separate DataFrames
    mpwizard_existing_df = pd.read_excel(os.path.join(excel_dir, f"{user}.xlsx"), sheet_name="MPWizard")
    amipy_existing_df = pd.read_excel(os.path.join(excel_dir, f"{user}.xlsx"), sheet_name="AmiPy")

    # Append new data
    mpwizard_final_df = pd.concat([mpwizard_existing_df, mpwizard_df])
    amipy_final_df = pd.concat([amipy_existing_df, amipy_df])

    message_parts = [f"Hello {user}, here are your PNLs for today:\n"]

    if "MPWizard" in user_data[broker]["orders"]:
        message_parts.append(f"MPWizard: {mpwizard_pnl}")

    if "Amipy" in user_data[broker]["orders"]:
        message_parts.append(f"AmiPy: {amipy_pnl}")

    message_parts.append(f"\nTotal: {mpwizard_pnl + amipy_pnl}")

    message = "\n".join(message_parts)

    # # Send the message
    with TelegramClient('anon', api_id, api_hash) as client:
        client.send_message(phone_number, message)

    # Create a new Excel file to store the updated data
    with pd.ExcelWriter(os.path.join(excel_dir, f"{user}_new.xlsx"), engine='openpyxl') as writer:
        # Write each DataFrame to a specific sheet
        mpwizard_final_df.to_excel(writer, sheet_name='MPWizard', index=False)
        amipy_final_df.to_excel(writer, sheet_name='AmiPy', index=False)

    # Delete the old file and rename the new one
    os.remove(os.path.join(excel_dir, f"{user}.xlsx"))
    os.rename(os.path.join(excel_dir, f"{user}_new.xlsx"), os.path.join(excel_dir, f"{user}.xlsx"))