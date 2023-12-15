import os
import sys
import json
import pandas as pd
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
excel_dir = os.getenv('onedrive_excel_folder')
excel_dir = os.path.normpath(excel_dir)  # Normalize the file path to handle any special characters

active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")

# Add the script directory to the system path for importing other modules
sys.path.append(DIR)
import MarketUtils.general_calc as general_calc

# Function to load an Excel sheet
def load_excel_sheet(excel_file_name, sheet_name):
    """Loads a specified sheet from an Excel file into a DataFrame."""
    excel_path = os.path.join(excel_dir, excel_file_name)
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        # Check if 'Date' column exists
        if 'Date' not in df.columns:
            print(f"'Date' column not found in the Excel file: {excel_file_name}")
            return pd.DataFrame()
        # Convert 'Date' column to datetime format
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y', errors='coerce')
        return df
    except FileNotFoundError:
        print(f"Excel file not found: {excel_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return pd.DataFrame()

# Function to calculate Profit and Loss (PnL)
def calculate_pnl(data, start_date, end_date):
    """Calculates PnL between two dates in the DataFrame."""
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    return filtered_data['Running Balance'].sum()

# Function to calculate cash balance
def calculate_cash_balance(user, invested_value):
    """Calculates the cash balance for a user."""
    return user['expected_morning_balance'] - invested_value

# Function to generate the weekly report message
def generate_message(pnl, cash_balance, next_week_capital, invested_value, start_date, end_date):
    """Formats the weekly report message."""
    message = f"Weekly Summary ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    message += f"PnL: ₹{pnl}\n\n"
    message += f"Cash Balance+stocks: ₹{cash_balance} + ₹{invested_value}\n"
    message += f"Next Week Starting Capital with stocks: ₹{next_week_capital}\n\n"
    message += "Best regards,\nYour Trading Firm"
    return message

# Function to send Telegram messages to users
def send_telegram_messages(broker_data, session_filepath):
    """Sends investment status messages to users via Telegram."""
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        for user in broker_data:
            if "Active" in user['account_type']:
                invested_value = get_invested_value(user)
                cash_balance = calculate_cash_balance(user, invested_value)
                current_capital = cash_balance + invested_value
                formatted_date = datetime.today().strftime("%d %b %Y")
                message = telegram_message(user, formatted_date, cash_balance, invested_value, current_capital)
                user['current_capital'] = current_capital
                phone_number = user['mobile_number']
                # Send the message to the user's phone number
                # client.send_message(phone_number, message)
                print(message)  # For testing purposes

# Function to format the Telegram message
def telegram_message(user, date, cash_balance, invested_value, current_capital):
    """Formats a message for sending to a user via Telegram."""
    message = f"Hello {user['name']},\n\n"
    message += f"Date: {date}\n"
    message += f"Cash Balance: ₹{cash_balance}\n"
    message += f"Invested Value: ₹{invested_value}\n"
    message += f"Current Capital: ₹{current_capital}\n\n"
    message += "Please review your investment status.\n"
    message += "Best regards,\nYour Trading Firm"
    return message

# Functions to calculate the invested value from different brokers
def aliceblue_invested_value(user_data):
    """Calculates the invested value for a user with Aliceblue broker."""
    alice = Aliceblue(user_data['username'], user_data['api_key'], session_id=user_data['session_id'])
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
    """Calculates the invested value for a user with Zerodha broker."""
    user_details = broker_data
    kite = KiteConnect(api_key=user_details['api_key'])                                                                                                                                                                                                                                                                                                         
    kite.set_access_token(user_details['access_token'])
    holdings = kite.holdings()
    return sum(stock['average_price'] * stock['quantity'] for stock in holdings)

# Function to fetch the invested value based on broker type
def get_invested_value(user_data):
    """Fetches the invested value based on the broker type of the user."""
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == user_data['account_name']:
            if user['broker'] == "aliceblue":
                return aliceblue_invested_value(user)
            elif user['broker'] == "zerodha":
                return zerodha_invested_value(user)

# Main function to execute the script
def main():
    """Main function to execute the script."""
    with open(active_users_json_path, 'r') as file:
        users = json.load(file)

    for user in users:
        excel_file_name = f"{user['account_name']}.xlsx"
        dtd_data = load_excel_sheet(excel_file_name, 'DTD')
        
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday() + 1)
        end_date = start_date + timedelta(days=5)
        pnl = calculate_pnl(dtd_data, start_date, end_date)
        invested_value = get_invested_value(user)
        cash_balance = calculate_cash_balance(user, invested_value)
        next_week_capital = cash_balance + invested_value
        report = generate_message(pnl, cash_balance, next_week_capital, invested_value, start_date, end_date)
        print(report)  # Replace this with your method of sending the report

# Retrieve API credentials for Telegram from environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

if __name__ == "__main__":
    main()
