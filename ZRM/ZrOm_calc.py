import os
import pandas as pd
from collections import namedtuple
import json
import requests
import datetime

Instrument = namedtuple("Instrument", ['exchange', 'token', 'symbol', 'name', 'expiry', 'lot_size'])

def get_option_tokens(base_symbol, expiry_date, strike_prc, option_type):
    #get out of the folder and then go to Utils folder and fetch the instruments.csv file
    instrument_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Utils", "instruments.csv")
    instruments_df = pd.read_csv(instrument_path)

    instruments_df = instruments_df[
        ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike"]
    ]
    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == base_symbol)
        & (instruments_df["expiry"] == expiry_date)
        & (instruments_df["strike"] == strike_prc)
        & (instruments_df["instrument_type"] == option_type)
    ]
    tokens = []
    trading_symbol_list = []

    tokens.append(int(nfo_ins_df['instrument_token'].values[0]))  # CE token

    trading_symbol_list.append(nfo_ins_df['tradingsymbol'].values[0])  # CE trading symbol

    # Extract the token from the trading symbol
    token_CE = nfo_ins_df['tradingsymbol'].values[0]

    print("Trading symbol: ",trading_symbol_list)
    exchange = 'NFO'

    trading_symbol_aliceblue = []
    for token, single_trading_symbol in zip(tokens, trading_symbol_list):
        trading_symbol_aliceblue.append(Instrument(exchange, token, base_symbol, single_trading_symbol, expiry_date, 50))

    return tokens, trading_symbol_list, trading_symbol_aliceblue

def get_zrm_users(broker_filepath):
    with open(broker_filepath, 'r') as file:
        broker_config = json.load(file)
    accounts_to_trade = []
    zerodha_accounts = broker_config.get("zerodha", {})
    accounts_to_trade_zerodha = zerodha_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_zerodha:
        user_account = zerodha_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("ZRM")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("zerodha", account))

    # Check Aliceblue accounts
    aliceblue_accounts = broker_config.get("aliceblue", {})
    accounts_to_trade_aliceblue = aliceblue_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_aliceblue:
        user_account = aliceblue_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("ZRM")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("aliceblue", account))

    return accounts_to_trade

def zrm_discord_bot(message):
    # CHANNEL_ID = "1129673128864391178" # MPWizard Discord channel
    CHANNEL_ID = "1128567144565723147" # Test channel
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

def get_expiry_dates():
    # Initialize the list of Thursdays and Tuesdays in 2023
    thursdays_2023 = []
    tuesdays_2023 = []

    # Loop through each week in 2023
    for week in range(1, 53):
        # Calculate the date of the Thursday and Tuesday in the given week
        thursday = datetime.datetime.strptime(f'2023-{week}-4', '%Y-%W-%w').date()
        tuesday = datetime.datetime.strptime(f'2023-{week}-2', '%Y-%W-%w').date()

        # Exclude the holidays
        if thursday not in holidays:
            thursdays_2023.append(thursday)
        if tuesday not in holidays:
            tuesdays_2023.append(tuesday)

    # Get the current date
    today = datetime.date.today()

    # Find the next non-holiday Thursday and Tuesday
    nifty_expiry = next((d for d in thursdays_2023 if d > today), None)
    finnifty_expiry = next((d for d in tuesdays_2023 if d > today), None)

    # Check if we found a valid expiry date for nifty and finnifty
    if nifty_expiry is None or finnifty_expiry is None:
        zrm_discord_bot("Please check the expiry dates")

    return nifty_expiry, finnifty_expiry