import os, sys
import json
from datetime import datetime
from telethon.sync import TelegramClient
from dotenv import load_dotenv

# Define constants and load environment variables
DIR = os.getcwd()
sys.path.append(DIR)

from MarketUtils.Main.afternoonmsg import main
import MarketUtils.general_calc as general_calc
from MarketUtils.Main.weeklyreport import calculate_commission_and_drawdown, read_base_capital
from MarketUtils.Excel.strategy_calc import custom_format

ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Retrieve API details and Omkar's number from the environment variables
api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')
phone_number = os.getenv('phone_number') 

def send_telegram_message(phone_number, message):
    session_filepath = os.path.join(DIR, "MarketUtils", "Telegram", "session_file.session")  # Update with actual session file path
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')

# Function to create the report message
def create_report_message(broker_data, base_capital, custom_format):
    today = datetime.now().strftime('%d %b %Y')
    report_parts = [f"PnL for Today ({today})"]

    # Loop through each user in the broker data
    for user in broker_data:
        # Add the user's account name
        report_parts.append(f"{user['account_name']}")
        strategy_results = user.get('strategy_results', {})

        # Add the details for each trade
        for trade_id, values in strategy_results.items():
            pnl_formatted = custom_format(values['pnl'])
            report_parts.append(f"{trade_id}: {pnl_formatted}")

        # Calculate the actual account value
        current_capital = user.get('current_capital', 0)

        # Calculate commission and drawdown
        commission, drawdown = calculate_commission_and_drawdown(user, current_capital, base_capital)

        # Check if drawdown is 0 and use commission
        adjustment = drawdown if drawdown != 0 else commission

        # Calculate and format Base Capital
        base_capital_value = current_capital - adjustment
        base_capital_formatted = custom_format(base_capital_value)

        # Format the drawdown value
        drawdown_formatted = custom_format(abs(drawdown))

        # Add the summary for the user
        gross_pnl_formatted = custom_format(user.get('gross_pnl', 0))
        net_pnl = user.get('gross_pnl', 0) - user.get('expected_tax', 0)
        net_pnl_formatted = custom_format(net_pnl)
        current_capital_formatted = custom_format(current_capital)

        # Append all details to the report
        report_parts.extend([
            f"\nGross PnL: {gross_pnl_formatted}",
            f"Net PnL : {net_pnl_formatted}",
            f"Current Capital: {current_capital_formatted}",
            f"Drawdown: {drawdown_formatted}",
            f"Base Capital: {base_capital_formatted}\n",
        ])

    return "\n".join(report_parts)

# Main function to generate and send the report
def main():
    # Load the broker data from a JSON file created by afternoon.py
    broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")  # Update with the actual path to broker data
    broker_data = general_calc.read_json_file(broker_filepath)
    
    # Load base capital data
    base_capital = read_base_capital(os.path.join(DIR, 'MarketUtils', 'Main', 'basecapital.txt'))

    # Create the report message
    report_message = create_report_message(broker_data, base_capital, custom_format)
    print(report_message)

    # # Send the report message 
    # send_telegram_message(phone_number, report_message)

# Execute the main function
if __name__ == "__main__":
    main()