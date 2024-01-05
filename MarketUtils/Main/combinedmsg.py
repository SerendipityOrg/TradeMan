import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from firebase_admin import db, credentials, storage
import firebase_admin
from babel.numbers import format_currency
import pandas as pd
from telethon.sync import TelegramClient
import requests
from io import BytesIO

# Define constants and load environment variables
DIR = os.getcwd()
sys.path.append(DIR)  # Add the current directory to the system path

# Import custom utility modules
import MarketUtils.general_calc as general_calc
from MarketUtils.Main.weeklyreport import calculate_commission_and_drawdown, read_base_capital
from MarketUtils.Excel.strategy_calc import custom_format
import MarketUtils.Firebase.firebase_utils as firebase_utils

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

def update_json_data(data, user, net_pnl, current_capital,expected_capital, broker_filepath):
    for username in data:
        if user["account_name"] == username["account_name"]:
            user_details = username
            user_details["current_capital"] = round(current_capital, 2)
            user_details["yesterday_PnL"] = round(net_pnl,2)
            user_details["expected_morning_balance"] = round(expected_capital, 2)
    general_calc.write_json_file(broker_filepath,data )

# Function to send a message via Telegram
def send_telegram_message(phone_number, message):
    # Define the session file path
    session_filepath = os.path.join(DIR, "MarketUtils", "Telegram", "+918618221715.session")
    
    # Create a Telegram client and send the message
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')

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

# Function to construct a PNL message for the user
def build_message(user, strategy_results, gross_pnl, total_tax, current_capital, expected_capital):
    message_parts = [
        f"Hello {user}, We hope you're enjoying a wonderful day.\n Here are your PNLs for today:\n"
    ]

       # Iterating over each trade_id and its results
    for trade_id, values in strategy_results.items():
        formatted_pnl = format_currency(values['pnl'], 'INR', locale='en_IN')
        # Using trade_id in the message instead of the strategy name
        message_parts.append(f"{trade_id}: {formatted_pnl}")

    message_parts.extend([
        f"\nGross PnL: {format_currency(gross_pnl, 'INR', locale='en_IN')}",
        f"Expected Tax: {format_currency(total_tax, 'INR', locale='en_IN')}",
        f"Current Capital: {format_currency(current_capital, 'INR', locale='en_IN')}",
        f"Expected Morning Balance : {format_currency(expected_capital, 'INR', locale='en_IN')}",
        "\nBest Regards,\nSerendipity Trading Firm"
    ])

    return "\n".join(message_parts).replace('\u20b9', '₹')
# Main function to generate and send the report
def main():
    today = datetime.now().strftime('%Y-%m-%d')
    combined_report = f"PnL for Today ({today})\n"

    broker_data = general_calc.read_json_file(broker_filepath)

        # Filter active users
    active_users = [user for user in broker_data if "Active" in user['account_type']]

    for user in active_users:
        mobile_number = user["mobile_number"]

    for user in broker_data:
        if "Active" in user['account_type']:
            excel_file_name = f"{user['account_name']}.xlsx"
            xls, sheet_names = firebase_utils.load_excel(excel_file_name)

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
                current_capital = user.get('current_capital', 0)
                expected_capital = current_capital + net_pnl

                # Call the build_message function to create a personalized message
                message = build_message(user['account_name'], strategy_results, total_pnl, total_tax, current_capital, expected_capital)
                print(message)
                send_telegram_message(user['mobile_number'], message)
                update_json_data(broker_data, user, net_pnl, current_capital, expected_capital, broker_filepath)

                base_capital = read_base_capital(os.path.join(DIR, 'MarketUtils', 'Main', 'basecapital.txt'))
                report_message = create_report_message(user, base_capital, strategy_results, custom_format)
                combined_report += report_message + "\n"

    print(combined_report)
    send_discord_message(combined_report)

if __name__ == "__main__":
    main()
