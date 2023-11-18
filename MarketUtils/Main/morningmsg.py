import os,json,sys,io
from dotenv import load_dotenv
from datetime import date
from babel.numbers import format_currency
from pya3 import Aliceblue
from kiteconnect import KiteConnect
from telethon.sync import TelegramClient

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

# Change the standard output encoding to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def aliceblue_invested_value(user_data):
    
    alice = Aliceblue(user_data['username'], user_data['api_key'])
    session_id = alice.get_session_id()
    holdings = alice.get_holding_positions()

    invested_value = 0
    if holdings.get("stat") == "Not_Ok":
        invested_value = 0
    else:
        for stock in holdings['HoldingVal']:
            average_price = float(stock['Price'])
            quantity = float(stock['HUqty'])
            invested_value += average_price * quantity

    return invested_value


def zerodha_invested_value(broker_data):
    user_details = broker_data
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    holdings = kite.holdings()
    return sum(stock['average_price'] * stock['quantity'] for stock in holdings)

# Fetch invested value based on broker type


def get_invested_value(broker_data, broker, user):
    user_details = broker_data
    if broker == "aliceblue":
        return aliceblue_invested_value(user_details)
    elif broker == "zerodha":
        return zerodha_invested_value(user_details)

# Function to format currency in custom style


def custom_format(amount):
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹ ')

# Generate a morning report message for a user


def generate_message(user, formatted_date, user_data, cash_balance, invested_value, current_capital):
    # Base message
    message = (
        f"Morning Report for {user['account_name']} on {formatted_date}:\n\n"
        f"Yesterday's Capital: {custom_format(user_data['current_capital'])}\n"
        f"Yesterday's PnL: {custom_format(user_data['yesterday_PnL'])}\n\n"
        f"Cash Balance: {custom_format(cash_balance)}\n"
    )

    # Conditionally add the Stocks Invested line5
    if invested_value and invested_value > 0:
        message += f"Stocks Invested: {custom_format(invested_value)}\n\n"

    # Continue with the rest of the message
    message += (
        f"Current Capital: {custom_format(current_capital)}\n\n"
        "Best regards,\nSerendipity Trading Firm"
    )

    return message


broker_data = general_calc.read_json_file(broker_filepath)
updated_users = []

for user in broker_data:
    # Check if the account type is Active
    if "Active" in user['account_type']:
        # Calculate investment values
        user_data = user
        invested_value = get_invested_value(user, user_data['broker'], user)
        for client in broker_data:
            if user_data['account_name'] == client['account_name']:
                user_data['expected_morning_balance'] = client['expected_morning_balance']
                user_data['yesterday_PnL'] = client['yesterday_PnL']
                user_data['current_capital'] = client['current_capital']
                user_data['mobile_number'] = client['mobile_number']

        cash_balance = user_data['expected_morning_balance'] - invested_value
        current_capital = cash_balance + invested_value
        formatted_date = date.today().strftime("%d %b %Y")
        message = generate_message(user, formatted_date, user_data, cash_balance, invested_value, current_capital)

        user_data['current_capital'] = current_capital
        phone_number = user_data['mobile_number']
        print(message)
    updated_users.append(user_data)

    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')



general_calc.write_json_file(broker_filepath, updated_users)