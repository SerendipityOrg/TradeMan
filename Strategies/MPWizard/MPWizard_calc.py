import os
import sys
import ast
import pandas as pd
import datetime as dt
from kiteconnect import KiteConnect
from dotenv import load_dotenv

# Define constants and paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(CURRENT_DIR, '..', '..', 'MarketUtils')
sys.path.append(UTILS_DIR)
import general_calc as gc

env_file_path = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', 'Brokers', '.env'))
load_dotenv(env_file_path)

indices_tokens = ast.literal_eval(os.getenv('indices_tokens'))
file_path = os.getenv('omkar_json_filepath')
atr_days = int(os.getenv('atr_days'))
start_time = os.getenv('data_fetch_start')
end_time = os.getenv('data_fetch_end')

mpwizard_file = os.path.abspath(os.path.join(CURRENT_DIR, "MPWizard.json"))

kite_cred = gc.read_json_file(file_path)
api_key = kite_cred.get('zerodha', {}).get('api_key')
access_token = kite_cred.get('zerodha', {}).get('access_token')

# Initialize KiteConnect
kite = KiteConnect(api_key=api_key, access_token=access_token)

def get_average_range_and_update_json(days=atr_days):
    """
    Calculate and update the average range in the JSON file.
    """
    previous_dates = gc.get_previous_dates(days)
    for token in indices_tokens:
        data = kite.historical_data(instrument_token=token, from_date=previous_dates[-1], to_date=previous_dates[0], interval="day")
        ranges = [d['high'] - d['low'] for d in data]
        average_range = sum(ranges) / len(ranges) if ranges else None

        if average_range:
            json_data = gc.read_json_file(mpwizard_file)
            for index in json_data['indices']:
                if index['token'] == token:
                    index['ATR5D'] = round(average_range, 2)
            gc.write_json_file(mpwizard_file, json_data)

def get_high_low_range_and_update_json():
    """
    Calculate and update the high-low range in the JSON file.
    """
    today = dt.date.today().strftime('%Y-%m-%d')
    for token in indices_tokens:
        data = kite.historical_data(token, today + " 09:15:00", today + " 10:15:00", "hour")
        if data:
            high, low = data[0]['high'], data[0]['low']
            range_ = high - low

            json_data = gc.read_json_file(mpwizard_file)
            for index in json_data['indices']:
                if index['token'] == token:
                    index['TriggerPoints']['IBHigh'] = high
                    index['TriggerPoints']['IBLow'] = low
                    index['IBValue'] = range_
                    ratio = range_ / index['ATR5D']
                    index['IBLevel'] = determine_ib_level(ratio)

            gc.write_json_file(mpwizard_file, json_data)


def determine_ib_level(ratio):
    """
    Determine the IB Level based on the given ratio.
    """
    if ratio <= 0.3333:
        return "Small"
    elif 0.3333 < ratio <= 0.6666:
        return "Medium"
    else:
        return "Big"


def get_weekday_price_ref(base_symbol):
    """Get the price reference for the current weekday."""
    data = gc.read_json_file(mpwizard_file)
    today = dt.date.today().strftime('%A')[:3]
    for index_data in data["indices"]:
        # index_name = index_data["name"]
        if index_data["name"] == base_symbol:
            return index_data["WeekdayPrcRef"].get(today)
        