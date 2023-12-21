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

# Function to find the start date of the last complete week
def get_last_week_start():
    """Finds and returns the start date of the last complete week."""
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    return last_monday

# Function to load an existing Excel file from Firebase Storage and return its data as a dictionary of pandas DataFrames
def load_existing_excel_from_firebase(excel_file_name):
    bucket = storage.bucket(storage_bucket)
    blobs = bucket.list_blobs()
    file_exists = False
    for blob in blobs:
        if blob.name == excel_file_name:
            file_exists = True
            break

    data = []  # List to store extracted data from Excel
    details_amounts = {}  # Dictionary to store the sums of amounts for each detail

    if file_exists:
        blob = bucket.blob(excel_file_name)
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)
        wb = openpyxl.load_workbook(byte_stream, data_only=True)

        if "DTD" in wb.sheetnames:
            sheet = wb["DTD"]
            column_indices = {cell.value: idx for idx, cell in enumerate(sheet[1])}

            for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
                details = row[column_indices['Details']].value
                amount_str = row[column_indices['Amount']].value

                # Skip the opening balance rows and sum the amounts for each 'Details'
                if details != "Opening Balance" and amount_str is not None:
                    # Remove currency symbols and commas, then convert to float
                    amount = float(amount_str.replace('₹', '').replace(',', '').replace('-', ''))
                    # Subtract if original amount was negative
                    if '-' in amount_str:
                        amount = -amount

                    # Sum the amounts for each 'Details'
                    if details in details_amounts:
                        details_amounts[details] += amount
                    else:
                        details_amounts[details] = amount

    # Print the total amounts for each detail
    for detail, total_amount in details_amounts.items():
        print(f"{detail}: ₹{total_amount:,.2f}")

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
def generate_message(user, net_pnl, cash_margin_value, trademan_account_value, actual_account_value, difference_value, start_date, end_date):
    """Generates and returns a formatted weekly report message."""
    message = f"Weekly Summary for {user['account_name']} ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    message += f"Net PnL: {custom_format(net_pnl)}\n"
    message += f"Free Cash: {custom_format(cash_margin_value)}\n"
    message += f"Trademan Invested: {custom_format(trademan_account_value - cash_margin_value)}\n"
    message += f"Trademan Account Value: {custom_format(trademan_account_value)}\n"
    message += f"Actual Account Value: {custom_format(actual_account_value)}\n"
    message += f"Difference: {custom_format(difference_value)}\n\n"
    message += "Best regards,\nSerendipity Trading Firm"
    return message

# Main function to execute the script for generating weekly reports
def main():
    """Main function to execute the script for generating weekly reports."""
    # Load broker data from JSON file
    broker_data = general_calc.read_json_file(broker_filepath)

    for user in broker_data:
        if "Active" in user['account_type']:
            start_date = get_last_week_start()
            end_date = start_date + timedelta(days=4)
            free_cash = get_cashmargin_value(user)

            # Define the name of the Excel file in Firebase Storage
            excel_file_name = f"{user['account_name']}.xlsx"

            try:
                # Load data from Excel file in Firebase Storage
                all_dfs = load_existing_excel_from_firebase(excel_file_name)
                if all_dfs:  # Make sure all_dfs is not empty
                    net_pnl = calculate_net_pnl(user, start_date, end_date, all_dfs)
                    # Here you can format net_pnl as needed before passing it to generate_message
                    formatted_net_pnl = custom_format(net_pnl)  # Modify this as per your formatting needs

                    # Calculate trademan_invested using all_dfs
                    trademan_invested = calculate_trademan_invested(user, all_dfs)
                    # Modify this as per your formatting needs
                    formatted_trademan_invested = custom_format(trademan_invested)

                    actual_account_value = free_cash + get_invested_value(user)
                    difference_value = actual_account_value - (free_cash + trademan_invested)

                    message = generate_message(user, formatted_net_pnl, free_cash, formatted_trademan_invested, actual_account_value, difference_value, start_date, end_date)
                    print(message)
                    # send_telegram_message(user['mobile_number'], message)  # Uncomment to enable Telegram messaging

            except FileNotFoundError as e:
                print(f"File not found for {user['account_name']}: {e}")
            except Exception as e:
                print(f"An error occurred for {user['account_name']}: {e}")

if __name__ == "__main__":
    main()
