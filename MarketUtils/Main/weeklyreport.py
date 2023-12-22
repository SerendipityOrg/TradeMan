import os, sys,io, json
import json
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from io import BytesIO
import openpyxl
from openpyxl import load_workbook
import pandas as pd

# Load environment variables
DIR = os.getcwd()
active_users_json_path = os.path.join(DIR,"MarketUtils", "active_users.json")
broker_filepath = os.path.join(DIR,"MarketUtils", "broker.json")
env_path = os.path.join(DIR, '.env')
session_filepath = os.path.join(DIR,'MarketUtils', 'Telegram','+918618221715.session')

load_dotenv(env_path)
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

sys.path.append(DIR)
import MarketUtils.general_calc as general_calc
from morningmsg import get_invested_value
from Brokers.Aliceblue.alice_utils import cash_margin_available  # Specific broker utility
from Brokers.Zerodha.kite_utils import cash_balance  # Specific broker utility
from MarketUtils.Excel.strategy_calc import custom_format  # Utility for formatting Excel data
from MarketUtils.Main.firebase import process_DTD, load_excel, get_current_week

# Retrieve values from .env for Firebase and Telegram
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
database_url = os.getenv('DATABASE_URL')
storage_bucket = os.getenv('STORAGE_BUCKET')
api_id = os.getenv('TELETHON_API_ID')
api_hash = os.getenv('TELETHON_API_HASH')

# Initialize Firebase app if it hasn't been initialized yet
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': storage_bucket
    })

# Define file paths for various utilities and files
active_users_json_path = os.path.join(DIR, "MarketUtils", "active_users.json")
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")

# Function to find the start date of the current complete week
def get_current_week_range():
    """Finds and returns the start date of the current complete week."""
    today = datetime.now()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=4)
    return start_date, end_date

# Function to get the free cash/margin available for a user
def get_cashmargin_value(user_data):
    """Retrieves the cash margin available for a user based on their broker."""
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == user_data['account_name']:
            if user['broker'] == "aliceblue":
                cash_margin = cash_margin_available(user)
            elif user['broker'] == "zerodha":
                cash_margin = cash_balance(user)
            try:
                return float(cash_margin)  # Ensure cash_margin is a float
            except ValueError:
                print(f"Invalid cash margin value for {user['account_name']}: {cash_margin}")
                return 0.0  # Return a default value or handle as appropriate
    return 0.0  # If user or broker not found

# Function to send a message via Telegram
def send_telegram_message(phone_number, message):
    """Sends a message to a specified phone number via Telegram."""
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md') 

# Function to generate a formatted message for weekly reports
def generate_message(user, excel_file_name, net_pnl, cash_margin_value, trademan_account_value, trademan_invested, commission, actual_account_value, difference_value, start_date, end_date):
    """Generates and returns a formatted weekly report message."""
    message = f"Weekly Summary for {user['account_name']} ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    
    # Process the details separately
    details = process_DTD(excel_file_name)
    for detail in details:
        message += f"{detail}\n"

    message += f"\n**Net PnL: {custom_format(net_pnl)}**\n\n"
    message += f"Free Cash: {custom_format(cash_margin_value)}\n"
    message += f"Trademan Invested: {custom_format(trademan_invested)}\n"
    message += f"Trademan Account Value: {custom_format(trademan_account_value)}\n"
    message += f"Actual Account Value: {custom_format(actual_account_value)}\n"
    message += f"Difference: {custom_format(difference_value)}\n\n"

    # Only add the commission to the message if it's not zero
    if commission != 0:
        message += f"Commission: {custom_format(commission)}\n\n"

    message += "Best regards,\n**Serendipity Trading Firm**"
    return message

# Function to calculate net PnL
def calculate_net_pnl(excel_file_name):
    # Load the Excel file within the function
    df_dtd, _ = load_excel(excel_file_name)  # Only load the 'DTD' sheet

    net_pnl = 0.0  # Initialize net PnL

    if df_dtd is not None:
        # Ensure 'Amount' column is numeric
        df_dtd['Amount'] = pd.to_numeric(df_dtd['Amount'].replace('[₹,]', '', regex=True).replace('-', '-0'), errors='coerce').fillna(0)

        # Filter data for the current week
        start_week, end_week = get_current_week()
        current_week_df = df_dtd[(df_dtd['Date'].dt.date >= start_week) & (df_dtd['Date'].dt.date <= end_week)]

        # Calculate net PnL as the sum of 'Amount' column
        net_pnl = current_week_df['Amount'].sum()
        return net_pnl

# Function to calculate Trademan invested value (customize this function according to your logic)
def calculate_trademan_invested(excel_file_name):
    _, df_holdings = load_excel(excel_file_name)  # Load the 'Holdings' sheet

    total_margin_used = 0  # Initialize default value

    if df_holdings is not None:
        # Trim spaces from column names and convert them to a consistent case
        df_holdings.columns = df_holdings.columns.str.strip().str.title()

        if 'Margin Used' in df_holdings.columns:  # Check if 'Margin Used' column exists
            # Convert 'Margin Used' to numeric, replacing non-numeric with 0
            df_holdings['Margin Used'] = pd.to_numeric(df_holdings['Margin Used'].replace('[₹,]', '', regex=True), errors='coerce').fillna(0)

            # Filter rows where 'Exit Date' is NaN (i.e., no exit date)
            active_holdings = df_holdings[df_holdings['Exit Date'].isna()]

            # Sum 'Margin Used' for these active holdings
            total_margin_used = active_holdings['Margin Used'].sum()

    return total_margin_used
 
# Main function to execute the script for generating weekly reports
def main():
    """Main function to execute the script for generating weekly reports."""
    # Load broker data from JSON file
    broker_data = general_calc.read_json_file(broker_filepath)

    for user in broker_data:
        if "Active" in user['account_type']:
            # Correctly unpack the start and end dates from the tuple returned by get_current_week_range()
            start_date, end_date = get_current_week_range()
            free_cash = get_cashmargin_value(user)

            # Define the name of the Excel file in Firebase Storage
            excel_file_name = f"{user['account_name']}.xlsx"

            try:
                # Calculate Trademan invested value (move this calculation before trademan_account_value)
                trademan_invested = calculate_trademan_invested(excel_file_name)

                # Calculate net PnL
                net_pnl = calculate_net_pnl(excel_file_name)

                # Calculate commission based on net PnL
                commission = net_pnl / 2 if net_pnl > 0 else 0

                # Calculate actual account value and difference
                actual_account_value = free_cash + get_invested_value(user)
                difference_value = actual_account_value - (free_cash + trademan_invested)

                # Calculate trademan_account_value
                trademan_account_value = free_cash + trademan_invested

                # Generate and print the summary message
                message = generate_message(user, excel_file_name, net_pnl, free_cash, trademan_account_value, trademan_invested, commission, actual_account_value, difference_value, start_date, end_date)
                print(message)
        
                # Uncomment the following line to enable sending the message via Telegram
                # send_telegram_message(user['mobile_number'], message)

            except FileNotFoundError as e:
                print(f"File not found for {user['account_name']}: {e}")
            except Exception as e:
                print(f"An error occurred for {user['account_name']}: {e}")

if __name__ == "__main__":
    main()

