import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pya3 import Aliceblue
from kiteconnect import KiteConnect
# Import TelegramClient from telethon
from telethon import TelegramClient

# Load environment variables
DIR = os.getcwd()
active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")
env_path = os.path.join(DIR, '.env')
load_dotenv(env_path)

# Retrieve API credentials from environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

# Add the script directory to the system path
sys.path.append(DIR)
import MarketUtils.general_calc as general_calc

# Function definitions:

# Function to load an Excel sheet
def load_excel_sheet(excel_path, sheet_name):
    """Loads a sheet from an Excel file into a DataFrame."""
    try:
        return pd.read_excel(excel_path, sheet_name=sheet_name)
    except FileNotFoundError:
        print(f"Excel file not found: {excel_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return pd.DataFrame()

# Function to calculate PnL
def calculate_pnl(data, start_date, end_date):
    """Calculates PnL between two dates in the DataFrame."""
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    return filtered_data['Running Balance'].sum()

# Function to calculate cash balance
def calculate_cash_balance(user, invested_value):
    """Calculates the cash balance for a user."""
    return user['expected_morning_balance'] - invested_value

# Function to generate the report message
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
                # Calculate investment values for active users
                invested_value = get_invested_value(user)

                cash_balance = user['expected_morning_balance'] - invested_value
                current_capital = cash_balance + invested_value

                # Formatting date and message
                formatted_date = datetime.today().strftime("%d %b %Y")
                message = telegram_message(user, formatted_date, cash_balance, invested_value, current_capital)

                user['current_capital'] = current_capital
                phone_number = user['mobile_number']

                # Send the message to the user's phone number (implement the sending logic as needed)
                # client.send_message(phone_number, message)
                print(message)  # For testing purposes


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
        
# Main function to execute the script
def main():
    # Read active users from the JSON file
    with open(active_users_json_path, 'r') as file:
        users = json.load(file)

    # Process each user
    for user in users:
        # Load the DTD sheet from the Excel file
        excel_path = f"{user['account_name']}.xlsx"
        dtd_data = load_excel_sheet(excel_path, 'DTD')

        # Calculate PnL
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday() + 1)
        end_date = start_date + timedelta(days=5)
        pnl = calculate_pnl(dtd_data, start_date, end_date)

        # Get invested value using the imported function
        invested_value = get_invested_value(user)

        # Calculate cash balance
        cash_balance = calculate_cash_balance(user, invested_value)

        # Calculate next week's capital, including invested value
        next_week_capital = cash_balance + invested_value

        # Generate and print/send the report
        report = generate_message(pnl, cash_balance, next_week_capital, invested_value, start_date, end_date)
        print(report)  # Replace this with your method of sending the report (e.g., email, Telegram)

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
