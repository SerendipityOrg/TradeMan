import os
import json
import sys
import io
from datetime import date
from babel.numbers import format_currency
from pya3 import Aliceblue
from kiteconnect import KiteConnect
from telethon.sync import TelegramClient

# api_id = '22941664'
# api_hash = '2ee02d39b9a6dae9434689d46e0863ca'

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))
json_dir = os.path.join(script_dir, "users")


# Change the standard output encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Load user data from the JSON file
def load_userdata():
    with open(os.path.join(script_dir, "broker.json")) as f:
        return json.load(f)

# Calculate invested value for AliceBlue user


def aliceblue_invested_value(user_data):
    alice = Aliceblue(user_data['username'], user_data['api_key'])
    session_id = alice.get_session_id()
    holdings = alice.get_holding_positions()

    if not isinstance(holdings, dict) or 'HoldingVal' not in holdings or not isinstance(holdings['HoldingVal'], list):
        raise ValueError("Unexpected format for holdings data.")

    invested_value = 0
    for stock in holdings['HoldingVal']:
        average_price = float(stock['Price'])
        quantity = float(stock['HUqty'])
        invested_value += average_price * quantity

    return invested_value

# Calculate invested value for Zerodha user


def zerodha_invested_value(broker_data, broker, user):
    user_details = broker_data[broker][user]
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    holdings = kite.holdings()
    return sum(stock['average_price'] * stock['quantity'] for stock in holdings)

# Fetch invested value based on broker type


def get_invested_value(broker_data, broker, user):
    user_details = broker_data[broker][user]
    if broker == "aliceblue":
        return aliceblue_invested_value(user_details)
    elif broker == "zerodha":
        return zerodha_invested_value(broker_data, broker, user)

# Function to format currency in custom style


def custom_format(amount):
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹ ')

# Generate a morning report message for a user


def generate_message(user, formatted_date, user_data, cash_balance, invested_value, current_capital):
    message = (
        f"Morning Report for {user} on {formatted_date}:\n\n"
        f"Yesterday's Capital: {custom_format(user_data['current_capital'])}\n"
        f"Yesterday's PnL: {custom_format(user_data['yesterday_PnL'])}\n\n"
        f"Cash Balance: {custom_format(cash_balance)}\n"
        f"Stocks Invested: {custom_format(invested_value)}\n\n"
        f"Current Capital: {custom_format(current_capital)}\n\n"
        "Best regards,\nSerendipity Trading Firm"
    )
    print(message)
    return message



# Main code execution
userdata = load_userdata()

# Initialize an empty list for the accounts to trade
user_list = []

# Go through each broker and gather users
for broker, broker_data in userdata.items():
    if 'accounts_to_trade' in broker_data:
        for account in broker_data['accounts_to_trade']:
            user_list.append((broker, account))

# Iterate through each user and generate and send report
for broker, user in user_list:
    # print(user)
    user_data = userdata[broker][user]

    # Calculate investment values
    invested_value = get_invested_value(userdata, broker, user)
    cash_balance = user_data['expected_morning_balance'] - invested_value
    current_capital = cash_balance + invested_value

    # Get current date in formatted style
    today = date.today()
    formatted_date = today.strftime("%d %b %Y")

    # Generate the message
    message = generate_message(
        user, formatted_date, user_data, cash_balance, invested_value, current_capital)

    # Print report for debugging purposes
    # print(message)

    # Load user-specific JSON data (assuming each user has a separate JSON)
    data = load_userdata()
    phone_number = data[broker][user]['mobile_number']

    # Save data to broker.json
    data_to_store = {
        'Current Capital': current_capital,
    }
    user_details = data[broker][user]
    user_details["current_capital"] = current_capital
    data[broker][user] = user_details

    # parent_file = os.path.abspath(os.path.join(script_dir, '..'))
    # filepath = os.path.join(parent_file, '+918618221715.session')
    # # # Send the report to the user via Telegram
    # # # Ensure you have `api_id` and `api_hash` defined elsewhere in your code
    # with TelegramClient(filepath, api_id, api_hash) as client:
    #     client.send_message(phone_number, message, parse_mode='md')
