import requests
import datetime
from collections import namedtuple
import os
import pandas as pd
import json

def get_mpwizard_users(broker_filepath):
    with open(broker_filepath, 'r') as file:
        broker_config = json.load(file)
    accounts_to_trade = []
    zerodha_accounts = broker_config.get("zerodha", {})
    accounts_to_trade_zerodha = zerodha_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_zerodha:
        user_account = zerodha_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("MPWizard")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("zerodha", account))

    # Check Aliceblue accounts
    aliceblue_accounts = broker_config.get("aliceblue", {})
    accounts_to_trade_aliceblue = aliceblue_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_aliceblue:
        user_account = aliceblue_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("MPWizard")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("aliceblue", account))

    return accounts_to_trade

def overnight_discord_bot(message):
    # CHANNEL_ID = "1125674485744402505" # Amipy Discord channel
    CHANNEL_ID = "1128567144565723147" # Amipy Test channel
    TOKEN = "MTEyNTY3MTgxODQxMDM0ODU2Ng.GQ5DLZ.BVLPrGy0AEX9ZiZOJsB6cSxOlf8hC2vaANuilA"
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "content": message
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        raise ValueError(f"Request to discord returned an error {response.status_code}, the response is:\n{response.text}")
    return response

def get_future_expiry_date():
    holidays = [
        datetime.date(2023, 1, 26),
        datetime.date(2023, 3, 7),
        datetime.date(2023, 3, 30),
        datetime.date(2023, 4, 4),
        datetime.date(2023, 4, 7),
        datetime.date(2023, 4, 14),
        datetime.date(2023, 4, 22),
        datetime.date(2023, 5, 1),
        datetime.date(2023, 6, 28),
        datetime.date(2023, 8, 15),
        datetime.date(2023, 9, 19),
        datetime.date(2023, 10, 2),
        datetime.date(2023, 10, 24),
        datetime.date(2023, 11, 14),
        datetime.date(2023, 11, 27),
        datetime.date(2023, 12, 25)
    ]

    # Get the current date
    today = datetime.date.today()

    # Find the last day of the current month
    next_month = today.replace(day=28) + datetime.timedelta(days=4)
    last_day_of_month = next_month - datetime.timedelta(days=next_month.day)

    # Find the last Thursday of the current month
    last_thursday = last_day_of_month
    while last_thursday.weekday() != 3: # 3 corresponds to Thursday
        last_thursday -= datetime.timedelta(days=1)

    # Check if the last Thursday is a holiday
    if last_thursday in holidays:
        # Find the previous date that is not a holiday
        expiry_date = last_thursday - datetime.timedelta(days=1)
        while expiry_date in holidays:
            expiry_date -= datetime.timedelta(days=1)
            if expiry_date < today:
                overnight_discord_bot("Please check the expiry")
                print("Please check the expiry")
                return None
    else:
        expiry_date = last_thursday

    expiry_date_str = expiry_date.strftime('%Y-%m-%d')
    print(f"The expiry date is: {expiry_date_str}")
    return expiry_date_str

def get_expiry_date():
    # Initialize the list of Thursdays in 2023
    thursdays_2023 = []
    holidays = [
    datetime.date(2023, 1, 26),
    datetime.date(2023, 3, 7),
    datetime.date(2023, 3, 30),
    datetime.date(2023, 4, 4),
    datetime.date(2023, 4, 7),
    datetime.date(2023, 4, 14),
    datetime.date(2023, 4, 22),
    datetime.date(2023, 5, 1),
    datetime.date(2023, 6, 28),
    datetime.date(2023, 8, 15),
    datetime.date(2023, 9, 19),
    datetime.date(2023, 10, 2),
    datetime.date(2023, 10, 24),
    datetime.date(2023, 11, 14),
    datetime.date(2023, 11, 27),
    datetime.date(2023, 12, 25)
    ]

    # Loop through each week in 2023
    for week in range(1, 53):
        # Calculate the date of the Thursday in the given week
        thursday = datetime.datetime.strptime(f'2023-{week}-4', '%Y-%W-%w').date()
        
        # Exclude the holidays
        if thursday not in holidays:
            thursdays_2023.append(thursday)

    # Check if today is Friday
    today = datetime.date.today()
    is_friday = today.weekday() == 4

    # Check if the following Thursday is in the list thursdays_2023
    next_thursday = today + datetime.timedelta(days=(3 - today.weekday() + 7) % 7 + 1)

    if next_thursday in thursdays_2023:
        expiry_date = next_thursday.strftime('%Y-%m-%d')
        print(f"The expiry date is: {expiry_date}")
    else:
        # Check the previous day (Wednesday)
        previous_wednesday = next_thursday - datetime.timedelta(days=1)
        if previous_wednesday in thursdays_2023:
            expiry_date = previous_wednesday.strftime('%Y-%m-%d')
            print(f"The expiry date is: {expiry_date}")
        else:
            # Send a Telegram message
            overnight_discord_bot("Please check the expiry")
    return expiry_date

Instrument = namedtuple("Instrument", ['exchange', 'token', 'symbol', 'name', 'expiry', 'lot_size'])

def get_future_tokens(expiry):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instruments_df = pd.read_csv(os.path.join(script_dir, '..', '..', 'Utils', 'instruments.csv'))

    instruments_df = instruments_df[
        ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike","segment"]
    ]

    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == "NIFTY")
        & (instruments_df["expiry"] == expiry)
        & (instruments_df["instrument_type"] == "FUT")
        & (instruments_df["segment"] == "NFO-FUT")
    ]

    tokens = []
    tokens.append(int(nfo_ins_df["instrument_token"].values[0]))

    trading_symbol = []
    trading_symbol.append(nfo_ins_df["tradingsymbol"].values[0])

    trading_symbol_aliceblue = []
    for token, single_trading_symbol in zip(tokens, trading_symbol):
        trading_symbol_aliceblue.append(Instrument("NFO", token, "NIFTY", single_trading_symbol, expiry, 50))

    return tokens, trading_symbol, trading_symbol_aliceblue

def get_option_tokens(base_symbol, expiry_date, option_type,strike_prc):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instruments_df = pd.read_csv(os.path.join(script_dir, '..', '..', 'Utils', 'instruments.csv'))

    instruments_df = instruments_df[
        ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike"]
    ]
    
    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == str(base_symbol))
        & (instruments_df["expiry"] == str(expiry_date))
        & (instruments_df["strike"] == int(strike_prc))
        & (instruments_df["instrument_type"] == str(option_type))
    ]
    tokens = []  
    trading_symbol_list = []
    tokens.append(int(nfo_ins_df['instrument_token'].values[0]))  # CE token
    trading_symbol_list.append(nfo_ins_df['tradingsymbol'].values[0])  # CE trading symbol

    # Extract the token from the trading symbol
    token_CE = nfo_ins_df['tradingsymbol'].values[0]
    exchange = 'NFO'
    trading_symbol_aliceblue = []

    for token, single_trading_symbol in zip(tokens, trading_symbol_list):
        trading_symbol_aliceblue.append(Instrument(exchange, token, base_symbol, single_trading_symbol, expiry_date, 50))
    return tokens, trading_symbol_list, trading_symbol_aliceblue


