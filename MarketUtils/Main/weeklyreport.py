import os
import sys
import json
import pandas as pd
from babel.numbers import format_currency
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pya3 import Aliceblue
from kiteconnect import KiteConnect
from telethon import TelegramClient

# Set the current working directory and load environment variables
DIR = os.getcwd()
ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Retrieve and normalize the directory path for Excel files
# excel_dir = os.getenv('onedrive_excel_folder')
# excel_dir = os.path.normpath(excel_dir) 
excel_dir = r"C:\Users\vanis\OneDrive\Desktop\TradeMan\UserProfile\excel" 

active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")

# Add the script directory to the system path for importing other modules
sys.path.append(DIR)
import MarketUtils.general_calc as general_calc
# from MarketUtils.Main.morningmsg import get_invested_value

def custom_format(amount):
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹ ')

def read_week_starting_capital(file_path):
    start_capital = {}
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split('date:')
                if len(parts) == 2:
                    user_balance_part = parts[0].strip()
                    user_parts = user_balance_part.split(':')
                    date_str = parts[1].strip()
                    if len(user_parts) == 2:
                        user = user_parts[0].strip()
                        balance_str = user_parts[1].strip().replace('₹', '').replace(',', '').strip()
                        start_capital[user] = {
                            'balance': float(balance_str),
                            'date': pd.to_datetime(date_str, format='%d-%b-%y')  # Assuming the date is in '04-Nov-23' format
                        }
    except FileNotFoundError:
        print("useropeningbalance.txt not found.")
    return start_capital

# # Function to load an Excel sheet
# def load_excel_sheet(excel_file_name, sheet_name):
#     """Loads a specified sheet from an Excel file into a DataFrame."""
#     excel_path = os.path.join(excel_dir, excel_file_name)
#     try:
#         df = pd.read_excel(excel_path, sheet_name=sheet_name)
#         if 'Date' not in df.columns:
#             print(f"'Date' column not found in the Excel file: {excel_file_name}")
#             return pd.DataFrame()
#         df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y', errors='coerce')
#         return df
#     except FileNotFoundError:
#         print(f"Excel file not found: {excel_path}")
#         return pd.DataFrame()
#     except Exception as e:
#         print(f"Error loading Excel file: {e}")
#         return pd.DataFrame()

def write_next_week_capital(capital_file_path, users_capital):
    """Writes next week's capital to a file."""
    with open(capital_file_path, 'w') as file:
        for user, capital in users_capital.items():
            date_str = datetime.now().strftime("%d-%b-%y")
            file.write(f"{user} : {custom_format(capital)} date: {date_str}\n")

def calculate_pnl_and_update_capital(users, capital_file_path):
    """Calculates PnL and updates the capital file."""
    starting_capitals = read_week_starting_capital(capital_file_path)
    next_week_capitals = {}
    for user in users:
        current_capital = user['current_capital']  # Assuming this field exists in your user data
        starting_capital = starting_capitals.get(user['account_name'], 0)
        pnl = starting_capital - current_capital
        next_week_capitals[user['account_name']] = current_capital
        print(f"PnL for {user['account_name']}: {custom_format(pnl)}")
    write_next_week_capital(capital_file_path, next_week_capitals)


# Function to calculate cash balance
def calculate_cash_balance(user, invested_value):
    """Calculates the cash balance for a user."""
    return user['expected_morning_balance'] - invested_value

# Function to generate the weekly report message
def generate_message(user, pnl, cash_balance, next_week_capital, invested_value, start_date, end_date):
    """Formats and generates the weekly report message."""
    message = f"Weekly Summary for {user['account_name']} ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    message += f"PnL: {pnl}\n\n"
    message += f"Cash Balance + stocks: {cash_balance} + {invested_value}\n"
    message += f"Next Week Starting Capital with stocks: {next_week_capital}\n\n"
    message += "Best regards,\nSerendipity Trading Firm"
    return message


def aliceblue_invested_value(user_data):
    
    alice = Aliceblue(user_data['username'], user_data['api_key'],session_id=user_data['session_id'])
    holdings = alice.get_holding_positions()

    invested_value = 0
    if holdings.get("stat") == "Not_Ok":
        invested_value = 0
    else:
        for stock in holdings['HoldingVal']:
            average_price = float(stock['Price'])
            quantity = float(stock['HUqty'])
            invested_value += average_price * quantity

    return invested_value

def zerodha_invested_value(broker_data):
    user_details = broker_data
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    holdings = kite.holdings()
    return sum(stock['average_price'] * stock['quantity'] for stock in holdings)

# Fetch invested value based on broker type
def get_invested_value(user_data):
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == user_data['account_name'] and user['broker'] == "aliceblue":
            return aliceblue_invested_value(user)
        elif user['account_name'] == user_data['account_name'] and user['broker'] == "zerodha":
            return zerodha_invested_value(user)

# Function to find the start date of the last complete week (Monday to Friday)
def get_last_week_start():
    """Finds the start date of the last complete week."""
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    return last_monday

# Function to get last week's Running Balance
def get_last_week_running_balance(data):
    """Gets the last week's Running Balance from the DataFrame."""
    if data.empty:
        print("Dataframe is empty. Cannot calculate last week's running balance.")
        return None
    start_date = get_last_week_start()
    end_date = start_date + timedelta(days=4)  # Up to Friday

    week_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    if not week_data.empty:
        last_week_balance = week_data.iloc[-1]['Running Balance']  # Access the last row's running balance
        return last_week_balance
    else:
        print("No data found for last week.")
        return None


# Main function to execute the script
def main():
    capital_file_path = os.path.join(DIR, "weekstartingcapital.txt")
    with open(active_users_json_path, 'r') as file:
        users = json.load(file)

    for user in users:
        excel_file_name = f"{user['account_name']}.xlsx"
        
        # Load specific sheet (DTD) and perform calculations
        # dtd_data = load_excel_sheet(excel_file_name, 'DTD')

        # Other calculations and message generation
        start_date = get_last_week_start()
        end_date = start_date + timedelta(days=4)
        pnl = calculate_pnl_and_update_capital(start_date, end_date)
        invested_value = get_invested_value(user)
        cash_balance = calculate_cash_balance(user, invested_value)
        next_week_capital = cash_balance + invested_value
        message = generate_message(user, pnl, cash_balance, next_week_capital, invested_value, start_date, end_date)
        print(message)

    # Update the starting capital for the next week
    calculate_pnl_and_update_capital(users, capital_file_path)

# Retrieve API credentials for Telegram from environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

strating_capital = read_week_starting_capital(os.path.join(DIR, 'MarketUtils', 'Main', 'weekstartingcapital.txt'))

if __name__ == "__main__":
    main()