import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from firebase_admin import db, credentials, storage
import firebase_admin
import pandas as pd
import requests
from io import BytesIO

# Define constants and load environment variables
DIR = os.getcwd()
sys.path.append(DIR)  # Add the current directory to the system path

# Import custom utility modules
import MarketUtils.general_calc as general_calc
from MarketUtils.Main.weeklyreport import calculate_commission_and_drawdown, read_base_capital
from MarketUtils.Excel.strategy_calc import custom_format

# Load environment variables from the .env file
ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Retrieve API details and contact number from the environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')
# Retrieve your Discord webhook URL from the environment variables
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")

# Retrieve Firebase configuration from .env
firebase_credentials_path = os.getenv('firebase_credentials_path')
database_url = os.getenv('database_url')
storage_bucket = os.getenv('storage_bucket')

# Initialize the Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': storage_bucket
    })

# Function to load an existing Excel file from Firebase Storage
def load_excel(excel_file_name):
    # Connect to the Firebase bucket
    bucket = storage.bucket(storage_bucket)
    blob = bucket.blob(excel_file_name)

    # Download the file if it exists in Firebase and return its content as a Pandas DataFrame
    if blob.exists():
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)
        # Load the Excel file into a Pandas DataFrame
        xls = pd.ExcelFile(byte_stream)
        # Return the ExcelFile object and the sheet names
        return xls, xls.sheet_names
    else:
        print(f"The file {excel_file_name} does not exist in Firebase Storage.")
        return None, None
    #     return pd.read_excel(byte_stream)
    # else:
    #     print(f"The file {excel_file_name} does not exist in Firebase Storage.")
    #     return None

# Function to send a message via Discord using a webhook
def send_discord_message(message: str):
    # Discord's character limit per message
    char_limit = 2000

    # Split the message into parts if it's too long
    parts = [message[i:i + char_limit] for i in range(0, len(message), char_limit)]

    for part in parts:
        data = {"content": part}
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Part of the message sent successfully")
        else:
            print(f"Failed to send message part: {response.status_code}, {response.text}")

# Function to create the report message for each user
def create_report_message(user, base_capital, strategy_results, custom_format):
    # Format the date and start the report
    # today = datetime.now().strftime('%d %b %Y')
    report_parts = [f"\n**{user['account_name']}**"]

    # Add the details for each trade
    for trade_id, values in strategy_results.items():
        pnl_formatted = custom_format(values['pnl'])
        report_parts.append(f"{trade_id}: {pnl_formatted}")

    # Calculate financial metrics
    current_capital = user.get('current_capital', 0)
    commission, drawdown = calculate_commission_and_drawdown(user, current_capital, base_capital)
    adjustment = drawdown if drawdown != 0 else commission
    base_capital_value = current_capital - adjustment

    # Format the financial values
    base_capital_formatted = custom_format(base_capital_value)
    drawdown_formatted = custom_format(abs(drawdown))
    gross_pnl_formatted = custom_format(user.get('gross_pnl', 0))
    net_pnl = user.get('gross_pnl', 0) - user.get('expected_tax', 0)
    net_pnl_formatted = custom_format(net_pnl)
    current_capital_formatted = custom_format(current_capital)

    # Append all details to the report
    report_parts.extend([
        f"\nGross PnL: {gross_pnl_formatted}",
        f"**Net PnL : {net_pnl_formatted}**",
        f"**Current Capital: {current_capital_formatted}**",
        f"Drawdown: {drawdown_formatted}",
        f"**Base Capital: {base_capital_formatted}\n**",
    ])

    return "\n".join(report_parts)

# Main function to generate and send the report
def main():
    # Get yesterday's date to title the report
    today = datetime.now().strftime('%Y-%m-%d')
    combined_report = f"PnL for Today ({today})\n"

    # Load broker data from the JSON file
    broker_data = general_calc.read_json_file(broker_filepath)

    # Process data for each user in the broker data
    for user in broker_data:
        if "Active" in user['account_type']:
            excel_file_name = f"{user['account_name']}.xlsx"
            xls, sheet_names = load_excel(excel_file_name)

            if xls is not None:
                strategy_results = {}
                total_tax = 0
                total_pnl = 0

                for sheet_name in sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    if 'exit_time' in df.columns and 'trade_id' in df.columns:
                        df['exit_time'] = pd.to_datetime(df['exit_time']).dt.strftime('%Y-%m-%d')
                        df_yesterday = df[df['exit_time'] == today]

                        if not df_yesterday.empty:
                            tax_sum = round(df_yesterday['tax'].sum(), 2)
                            total_tax += tax_sum

                            for index, trade in df_yesterday.iterrows():
                                trade_id = trade['trade_id']
                                pnl = trade['pnl']
                                if trade_id not in strategy_results:
                                    strategy_results[trade_id] = {'pnl': 0, 'tax': tax_sum}
                                strategy_results[trade_id]['pnl'] += pnl
                                total_pnl += pnl

                user['strategy_results'] = strategy_results
                user['gross_pnl'] = total_pnl
                user['expected_tax'] = total_tax
                net_pnl = total_pnl - total_tax
                user['net_pnl'] = net_pnl

                base_capital = read_base_capital(os.path.join(DIR, 'MarketUtils', 'Main', 'basecapital.txt'))
                report_message = create_report_message(user, base_capital, strategy_results, custom_format)
                combined_report += report_message + "\n"

    # Print the combined report to the console
    print(combined_report)

    #   # Send the report to Discord
    send_discord_message(combined_report)

if __name__ == "__main__":
    main()
