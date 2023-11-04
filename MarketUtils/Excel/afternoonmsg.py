import os
import sys
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from babel.numbers import format_currency
from telethon.sync import TelegramClient
from dotenv import load_dotenv

# Setting up directory paths
DIR = os.getcwd()
sys.path.append(DIR)

# Import custom modules
import MarketUtils.general_calc as general_calc
import dtdautomation as dtd
import Streamlitapp.formats as custom_format

# Get the script directory and file paths
script_dir = os.path.dirname(os.path.realpath(__file__))
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
# excel_dir = os.path.join(DIR, "UserProfile", "excel")

ENV_PATH = os.path.join(DIR, '.env')

# Loading environment variables from .env file
load_dotenv(ENV_PATH)
excel_dir = os.getenv('onedrive_excel_folder')
print(excel_dir)
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')


# Function to load an existing Excel file and return its data as a dictionary of pandas DataFrames
def load_existing_excel(excel_path):
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    try:
        book = load_workbook(excel_path)
        return {sheet_name: pd.read_excel(excel_path, sheet_name=sheet_name) for sheet_name in book.sheetnames}
    except Exception as e:
        print(f"An error occurred while loading the Excel file: {excel_path}")
        print("Error:", e)
        return {}

def update_json_data(data, user, net_pnl, current_capital,expected_capital, broker_filepath):
    for username in data:
        if user["account_name"] == username["account_name"]:
            user_details = username
            user_details["current_capital"] = round(current_capital, 2)
            user_details["yesterday_PnL"] = round(net_pnl,2)
            user_details["expected_morning_balance"] = round(expected_capital, 2)
    general_calc.write_json_file(broker_filepath,data )

# Function to construct a PNL message for the user
def build_message(user, strategy_results, gross_pnl, total_tax, current_capital, expected_capital):
    message_parts = [
        f"Hello {user}, We hope you're enjoying a wonderful day.\n Here are your PNLs for today:\n"
    ]

    for strategy_name, values in strategy_results.items():
        # Format the pnl value using custom_format function
        formatted_pnl = format_currency(values['pnl'], 'INR', locale='en_IN')
        message_parts.append(f"{strategy_name}: {formatted_pnl}")

    message_parts.extend([
        f"\nGross PnL: {format_currency(gross_pnl, 'INR', locale='en_IN')}",
        f"Expected Tax: {format_currency(total_tax, 'INR', locale='en_IN')}",
        f"Current Capital: {format_currency(current_capital, 'INR', locale='en_IN')}",
        f"Expected Morning Balance : {format_currency(expected_capital, 'INR', locale='en_IN')}",
        "\nBest Regards,\nSerendipity Trading Firm"
    ])

    return "\n".join(message_parts).replace('\u20b9', '₹')


# Function to send a message via Telegram
def send_telegram_message(phone_number, message):
    # Define the session file path
    session_filepath = os.path.join(script_dir, "..", '..', '..', "+918618221715.session")
    
    # Create a Telegram client and send the message
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')


# The main function which processes user data and sends PNL messages
def main():
    # Load broker data from JSON file
    broker_data = general_calc.read_json_file(broker_filepath)
    
    # Filter active users
    active_users = [user for user in broker_data if "Active" in user['account_type']]
    # phone_number = user["mobile_number"]

    # Get the current date
    today = datetime.now().strftime('%Y-%m-%d')

    for user in active_users:
        excel_path = os.path.join(excel_dir, f"{user['account_name']}.xlsx")
        all_dfs = load_existing_excel(excel_path)
        
        # Update the DTD sheet in the loaded Excel file
        dtd.main()  # I'm assuming the function's name and it requires the excel path

        # Create a dictionary to store the aggregated results for each strategy
        strategy_results = {}
        
        # Initialize total_tax, total_pnl, and pnl_sum to store the cumulative values from all sheets
        total_tax = 0
        total_pnl = 0
        pnl_sum = 0

        for sheet_name, df in all_dfs.items():  
            if 'exit_time' in df.columns:
                df['entry_time'] = df['entry_time'].astype(str)
                df['exit_time'] = df['exit_time'].astype(str)

                df_today = df[df['exit_time'].str.startswith(today)]

                if not df_today.empty:
                    # Aggregate the pnl and tax values
                    pnl_sum = round(df_today['pnl'].sum(), 2)
                    tax_sum = round(df_today['tax'].sum(), 2)

                    # Accumulate the pnl_sum and tax_sum values
                    total_pnl += pnl_sum
                    total_tax += tax_sum

                    # Store the aggregated results in the strategy_results dictionary
                    strategy_results[sheet_name] = {'pnl': pnl_sum, 'tax': tax_sum}

        # Calculate gross_pnl, expected_tax, and net_pnl
        gross_pnl = total_pnl   
        expected_tax = total_tax
        net_pnl = gross_pnl - expected_tax
        current_capital = next(account["current_capital"] for account in broker_data if account["account_name"] == user["account_name"])
        expected_capital = current_capital + net_pnl if net_pnl > 0 else current_capital - abs(net_pnl)

        message = build_message(user['account_name'], strategy_results, gross_pnl, expected_tax, current_capital, expected_capital)
        update_json_data(broker_data, user, net_pnl, current_capital, expected_capital, broker_filepath)
        print(message)

        
        # Sending the message via Telegram is currently commented out, remove the comments to enable.
        # send_telegram_message(user['phone_number'], message)


# Execute the main function when the script is run
if __name__ == "__main__":
    main()
