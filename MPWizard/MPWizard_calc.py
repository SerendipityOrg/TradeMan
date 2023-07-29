import os
import pandas as pd
from collections import namedtuple
import requests
import datetime
import json
from kiteconnect import KiteConnect

script_dir = os.path.dirname(os.path.abspath(__file__))   
parent_dir = os.path.abspath(os.path.join(script_dir, '..'))
filepath = os.path.join(parent_dir, 'Utils', 'instruments.csv')
omkar_filepath = os.path.join(parent_dir, 'Utils', 'users/omkar.json')
mpwizard_file = os.path.join(parent_dir,"MPWizard", "mpwizard(omkar).json")

with open(omkar_filepath, 'r') as file:
    brokers = json.load(file)

api_key = brokers.get('zerodha', {}).get('api_key')
access_token = brokers.get('zerodha', {}).get('access_token')

# Initialize KiteConnect
kite = KiteConnect(api_key=api_key,access_token=access_token)

Instrument = namedtuple("Instrument", ['exchange', 'token', 'symbol', 'name', 'expiry', 'lot_size'])

def get_option_tokens(base_symbol, expiry_date, option_type,strike_prc):
    instruments_df = pd.read_csv(filepath)

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

def mpwizard_discord_bot(message):
    CHANNEL_ID = "1126027722431414362" # MPWizard Discord channel
    # CHANNEL_ID = "1128567144565723147" # Test channel
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

def get_previous_dates(num_dates):
    dates = []
    current_date = datetime.date.today()

    while len(dates) < num_dates:
        current_date -= datetime.timedelta(days=1)

        if current_date.weekday() >= 5 or current_date in holidays:
            continue

        dates.append(current_date.strftime("%Y-%m-%d"))

    return dates

def get_average_range_and_update_json():
    previous_dates = get_previous_dates(5)
    tokens = [260105,256265,257801]
    for token in tokens:
        data = kite.historical_data(instrument_token=token, from_date=previous_dates[-1], to_date=previous_dates[0], interval="day")

        # Calculate range for each day and find average range
        ranges = [d['high'] - d['low'] for d in data]
        average_range = sum(ranges) / len(ranges) if ranges else None

        if average_range is not None:
            # Update ATR5D in JSON
            with open(mpwizard_file, 'r') as json_file:
                json_data = json.load(json_file)

            for index in json_data['indices']:
                if index['token'] == token:
                    index['ATR5D'] = round(average_range,2)

            with open(mpwizard_file, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)

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
    nifty_expiry = next((d for d in thursdays_2023 if d >= today), None)
    finnifty_expiry = next((d for d in tuesdays_2023 if d >= today), None)

    # Check if we found a valid expiry date for nifty and finnifty
    if nifty_expiry is None or finnifty_expiry is None:
        mpwizard_discord_bot("Please check the expiry dates")

    return nifty_expiry, finnifty_expiry

def get_high_low_range_and_update_json():
    # Get today's date
    today = datetime.date.today().strftime('%Y-%m-%d')
    tokens = [260105,256265,257801]
    for token in tokens:
        # Get data for today
        data = kite.historical_data(token, today + " 09:15:00", today + " 10:10:00", "hour")
        if data:
            high = data[0]['high']
            low = data[0]['low']
            range_ = high - low

            # Update JSON file
            with open(mpwizard_file, 'r') as json_file:
                json_data = json.load(json_file)

            for index in json_data['indices']:
                if index['token'] == token:
                    index['TriggerPoints']['IBHigh'] = high
                    index['TriggerPoints']['IBLow'] = low
                    index['IBValue'] = range_
                    ratio = range_ / index['ATR5D']
                    if ratio <= 0.3333:
                        index['IBLevel'] = "Small"
                    elif 0.3333 < ratio <= 0.6666:
                        index['IBLevel'] = "Medium"
                    else:
                        index['IBLevel'] = "Big"

            with open(mpwizard_file, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)

