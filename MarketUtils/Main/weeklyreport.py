import os
import sys
import json
from firebase_admin import db
from firebase_admin import credentials
import firebase_admin
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon.sync import TelegramClient

# Set up the working directory and load environment variables
DIR = os.getcwd()
ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Retrieve values from .env for Firebase
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
database_url = os.getenv('DATABASE_URL')

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
    })

# Define file paths
active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
starting_capital_path = os.path.join(DIR, "MarketUtils", "weekstartingcapital.txt")

# Extend the system path for importing modules from the script directory
sys.path.append(DIR)
import MarketUtils.general_calc as general_calc
from Brokers.Aliceblue.alice_utils import cash_margin_available
from Brokers.Zerodha.kite_utils import cash_balance
from MarketUtils.Excel.strategy_calc import custom_format
from MarketUtils.Main.morningmsg import get_invested_value 

def get_cashmargin_value(user_data):#TODO get the values from excel
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == user_data['account_name'] and user['broker'] == "aliceblue":
            return cash_margin_available(user)
        elif user['account_name'] == user_data['account_name'] and user['broker'] == "zerodha":
            return cash_balance(user)
    
# Function to calculate the cash balance for a user
def calculate_cash_balance(user, invested_value, get_cashmargin_value):
    """Calculates and returns the cash balance for a user"""
    cash_margin_value = get_cashmargin_value(user)
    # Convert cash_margin_value to float
    cash_margin_value = float(cash_margin_value)
    return cash_margin_value - invested_value

# Function to get starting capital from Firebase
def get_starting_capital(mobile_number):
    """Reads and returns the starting capital for a specific user from Firebase based on mobile number."""
    ref = db.reference('/clients')
    clients = ref.get()

    # Format mobile_number to match the Firebase format
    mobile_number_formatted = mobile_number[3:] if mobile_number.startswith('+91') else mobile_number

    if clients:
        for username, client_data in clients.items():
            if client_data.get('phone number') == mobile_number_formatted:
                return client_data.get('Weekly Saturday Capital', 0.0)
    return 0.0

# Function to read the current capital for a specific user from a file
def get_current_capital(username):
    """Reads and returns the current capital for a specific user from a file."""
    with open(broker_filepath, 'r') as file:
        broker_data = json.load(file)
    for account in broker_data:
        if account.get("account_name") == username:
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
    """Saves the next week's capital for each user to the 'clients' node in Firebase."""
    ref = db.reference('/clients')  # Reference to the 'clients' node
    date_string = datetime.now().strftime("%d-%b-%y")

    for user_name, capital in next_week_capitals.items():
        # Update the 'Weekly Saturday Capital' for each client
        client_ref = ref.child(user_name)
        client_data = client_ref.get() or {}
        client_data['Weekly Saturday Capital'] = custom_format(capital)
        client_data['Updated Date'] = date_string
        client_ref.set(client_data)

    print("Next week's capitals updated in Firebase.")

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
        cash_balance = calculate_cash_balance(user, invested_value, get_cashmargin_value)
        pnl = calculate_pnl(starting_capital, current_capital)
        next_week_capital = cash_balance + invested_value
        next_week_capitals[user_name] = next_week_capital

        start_date = get_last_week_start()
        end_date = start_date + timedelta(days=4)
        message = generate_message(user, pnl, cash_balance, next_week_capital, invested_value, start_date, end_date)
        print(message)

        # Uncomment the line below to enable sending the message via Telegram
        # send_telegram_message(user['mobile_number'], message)

    # save_next_week_capital(next_week_capitals) 

# Retrieve API credentials for Telegram from environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

if __name__ == "__main__":
    main()
