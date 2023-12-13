import os, sys
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Setting up directory paths
DIR = os.getcwd()
sys.path.append(DIR)

# Import custom modules
import MarketUtils.general_calc as general_calc
import MarketUtils.Main.dtdautomation as dtd

# Get the script directory and file paths
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
ENV_PATH = os.path.join(DIR, '.env')

# Loading environment variables from .env file
load_dotenv(ENV_PATH)
import MarketUtils.general_calc as general_calc
from morningmsg import aliceblue_invested_value, zerodha_invested_value

# Assuming aliceblue_invested_value, zerodha_invested_value and other necessary functions 
# are defined in the user's environment similar to morningmsg.py

# Function to load an existing Excel file and return its data as a pandas DataFrame
def load_excel_sheet(excel_path, sheet_name):
    """Loads a specified sheet from an Excel file into a pandas DataFrame."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    try:
        return pd.read_excel(excel_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"An error occurred while loading the Excel file: {excel_path}")
        print("Error:", e)
        return pd.DataFrame()

# Function to calculate PnL for the specified period
def calculate_pnl(data, start_date, end_date):
    """Calculates the PnL for a given period in the provided DataFrame."""
    filtered_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
    return filtered_data['Running Balance'].sum()

# Function to calculate cash balance
def calculate_cash_balance(user, broker_data):
    """Calculates the cash balance for the user."""
    # Fetch the invested value based on broker type
    invested_value = get_invested_value(user, broker_data)
    cash_balance = user['expected_morning_balance'] - invested_value
    return cash_balance

# Function to get the invested value based on broker type
def get_invested_value(user, broker_data):
    if user['broker'] == 'aliceblue':
        return aliceblue_invested_value(user)
    elif user['broker'] == 'zerodha':
        return zerodha_invested_value(user)
    else:
        return 0  # Default value for other brokers or if not specified

# Function to format and send the weekly report
def send_weekly_report(user, pnl, cash_balance, next_week_capital):
    """Formats and prints the weekly report message."""
    today = datetime.now()
    start_date = today - timedelta(days=today.weekday() + 1) # Last Monday
    end_date = start_date + timedelta(days=5) # Last Saturday

    message = f"Weekly Summary ( {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')})\n\n"
    message += f"PnL : ₹ {pnl}\n\n"
    message += f"Cash Balance: ₹ {cash_balance}\n"
    message += f"Next Week Starting Capital with Stocks : ₹ {next_week_capital}\n\n"
    message += "Best regards,\nSerendipity Trading Firm"
    
    print(message)  # Replace this with your method to send the message (e.g., email, Telegram)

# Main function to execute the script
def main():
    """Main function to execute the script."""
    DIR = os.getcwd()
    broker_filepath = os.path.join(DIR, "MarketUtils", "active_broker.json")

    # Read active_users.json
    with open('active_users.json', 'r') as file:
        users = json.load(file)

    # Load broker data
    broker_data = general_calc.read_json_file(broker_filepath)

    for user in users:
        account_name = user['account_name']
        excel_path = f"{account_name}.xlsx"

        # Load the DTD sheet from the Excel file
        dtd_data = load_excel_sheet(excel_path, 'DTD')

        # Calculate the PnL for the last week
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday() + 1) # Last Monday
        end_date = start_date + timedelta(days=5) # Last Saturday
        pnl = calculate_pnl(dtd_data, start_date, end_date)

        # Calculate cash balance
        cash_balance = calculate_cash_balance(user, broker_data)

        # Next week starting capital with stocks (placeholder, replace with actual calculation)
        next_week_capital = cash_balance  # Placeholder, replace with actual calculation

        # Send the weekly report
        send_weekly_report(user, pnl, cash_balance, next_week_capital)

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
