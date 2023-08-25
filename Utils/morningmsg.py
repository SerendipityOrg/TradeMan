import os
import json
from datetime import date
from babel.numbers import format_currency
from pya3 import Aliceblue
from kiteconnect import KiteConnect

script_dir = os.path.dirname(os.path.realpath(__file__))

# Load user data from the JSON file


def load_userdata():
    with open(os.path.join(script_dir, "broker.json")) as f:
        return json.load(f)

# Calculate invested value for AliceBlue user using the loop format


def aliceblue_invested_value(broker_data, broker, user):
    alice = Aliceblue(user_id=broker_data[broker][user]['username'],
                      api_key=broker_data[broker][user]['api_key'])

    print(alice.get_session_id())  # Get Session ID
    # Fetch holding positions using the given loop method
    holdings = alice.get_holding_positions().get('HoldingVal', [])

# Calculate invested value for Zerodha user


def zerodha_invested_value(broker_data, broker, user):
    user_details = broker_data[broker][user]
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    holdings = kite.holdings()
    return sum(stock['average_price'] * stock['quantity'] for stock in holdings)

# Fetch invested value based on broker type


def get_invested_value(broker_data, broker, user):
    if broker == "aliceblue":
        return aliceblue_invested_value(broker_data, broker, user)
    elif broker == "zerodha":
        return zerodha_invested_value(broker_data, broker, user)

# Generate morning report message for a user


def report_msg(broker_data, broker, user):
    user_data = broker_data[broker][user]
    today = date.today()
    formatted_date = today.strftime("%d %b %Y")
    invested_value = get_invested_value(broker_data, broker, user)
    cash_balance = user_data['expected_morning_balance'] - invested_value
    current_capital = cash_balance + invested_value

    def custom_format(amount):
        formatted = format_currency(amount, 'INR', locale='en_IN')
        return formatted.replace('₹', 'Rs')

    return (f"Report for {user} on {formatted_date}:\n"
            f"Morning Report:\n"
            f"Yesterday's Capital: {custom_format(user_data['current_capital'])}\n"
            f"Yesterday's PnL: {custom_format(user_data['yesterday_PnL'])}\n"
            f"Cash Balance: {custom_format(cash_balance)}\n"
            f"Stocks Invested: {custom_format(invested_value)}\n\n"
            f"Current Capital: {custom_format(current_capital)}\n\n"
            "Best regards,\nSerendipity Trading Firm")


# Main code execution
userdata = load_userdata()
for broker, data in userdata.items():
    for user in data['accounts_to_trade']:
        print(report_msg(userdata, broker, user))
