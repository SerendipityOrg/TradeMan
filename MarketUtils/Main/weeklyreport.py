import os
import sys
import json
from datetime import datetime, timedelta
from babel.numbers import format_currency
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from pya3 import Aliceblue
from kiteconnect import KiteConnect

# Set up the working directory and load environment variables
DIR = os.getcwd()
ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Define file paths
active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
starting_capital_path = os.path.join(DIR, "MarketUtils", "weekstartingcapital.txt")

# Extend the system path for importing modules from the script directory
sys.path.append(DIR)
from MarketUtils.Main.morningmsg import get_invested_value  # Import function without printing

# Function to format currency in a custom style
def custom_format(amount):
    """Formats a numeric amount into a currency format."""
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹ ')

def aliceblue_cash_value(user_data):
    
    alice = Aliceblue(user_data['username'], user_data['api_key'],session_id=user_data['session_id'])

    # Fetching the margin or funds details, the method name might differ based on the API
    balance_details = alice.get_balance()  # This method might have a different name

      # Search for 'coverOrderMarginPrsnt' in the balance_details
    for item in balance_details:
        if isinstance(item, dict) and 'coverOrderMarginPrsnt' in item:
            cover_order_margin_present = item.get('coverOrderMarginPrsnt', 0)
            print("Cover order margin present:", cover_order_margin_present)
            return cover_order_margin_present

    # Default return if 'coverOrderMarginPrsnt' is not found
    return 0

# Function to calculate the cash balance for a user
def calculate_cash_balance(user, invested_value):
    """Calculates and returns the cash balance for a user."""
    return user['expected_morning_balance'] - invested_value

# Function to read the starting capital from a file for a specific user
def get_starting_capital(user_account_name):
    """Reads and returns the starting capital for a specific user from a file."""
    with open(starting_capital_path, 'r', encoding='utf-8') as file:
        for line in file:
            if user_account_name in line:
                capital_str = line.split(':')[1].split('date')[0].strip()
                capital_str = capital_str.replace('₹', '').replace(',', '')
                return float(capital_str)
    return 0.0

# Function to read the current capital for a specific user from a file
def get_current_capital(user_account_name):
    """Reads and returns the current capital for a specific user from a file."""
    with open(broker_filepath, 'r') as file:
        broker_data = json.load(file)
    for account in broker_data:
        if account.get("account_name") == user_account_name:
            return account.get("current_capital", 0.0)
    return 0.0

# Function to calculate the profit and loss
def calculate_pnl(starting_capital, current_capital):
    """Calculates and returns the Profit and Loss (PnL)."""
    return  current_capital - starting_capital 

# Function to generate a formatted message for weekly reports
def generate_message(user, pnl, cash_balance, next_week_capital, invested_value, start_date, end_date):
    """Generates and returns a formatted weekly report message."""
    message = f"Weekly Summary for {user['account_name']} ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    message += f"PnL: {custom_format(pnl)}\n\n"
    message += f"Cash Balance + stocks: {custom_format(cash_balance)} + {custom_format(invested_value)}\n"
    message += f"Next Week Starting Capital with stocks: {custom_format(next_week_capital)}\n\n"
    message += "Best regards,\nSerendipity Trading Firm"
    return message

# Function to find the start date of the last complete week
def get_last_week_start():
    """Finds and returns the start date of the last complete week."""
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    return last_monday

# Function to save the next week's capital for each user to a file
def save_next_week_capital(next_week_capitals):
    """Saves the next week's capital for each user to a file."""
    with open(starting_capital_path, 'w', encoding='utf-8') as file:
        date_string = datetime.now().strftime("%d-%b-%y")
        for user_name, capital in next_week_capitals.items():
            file.write(f"{user_name} : {custom_format(capital)} date: {date_string}\n")

# Function to send a message via Telegram
def send_telegram_message(phone_number, message):
    """Sends a message to a specified phone number via Telegram."""
    session_filepath = os.path.join(DIR, "MarketUtils", "Telegram", "+918618221715.session")
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')

# Main function to execute the script
def main():
    """Main function to execute the script for generating weekly reports."""
    with open(active_users_json_path, 'r') as file:
        users = json.load(file)

    next_week_capitals = {}

    for user in users:
        user_name = user['account_name']
        starting_capital = get_starting_capital(user_name)
        current_capital = get_current_capital(user_name)
        invested_value = get_invested_value(user)
        cash_balance = calculate_cash_balance(user, invested_value)
        pnl = calculate_pnl(starting_capital, current_capital)
        next_week_capital = cash_balance + invested_value
        next_week_capitals[user_name] = next_week_capital

        start_date = get_last_week_start()
        end_date = start_date + timedelta(days=4)
        message = generate_message(user, pnl, cash_balance, next_week_capital, invested_value, start_date, end_date)
        # print(message)

        # Uncomment the line below to enable sending the message via Telegram
        # send_telegram_message(user['mobile_number'], message)

    # save_next_week_capital(next_week_capitals) 

# Retrieve API credentials for Telegram from environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

if __name__ == "__main__":
    main()
