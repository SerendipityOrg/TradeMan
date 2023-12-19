import os
import sys
import datetime as dt
from dotenv import load_dotenv

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

import MarketUtils.general_calc as general_calc
import Brokers.BrokerUtils.Broker as Broker
import Brokers.Zerodha.kite_utils as kite_utils
import Strategies.StrategyBase as StrategyBase
import MarketUtils.Calculations.qty_calc as qty_calc

_,STRATEGY_PATH = general_calc.get_strategy_json('MPWizard')
strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)

api_key, access_token = Broker.get_primary_account()

def calculate_average_range(historical_data):
    """
    Calculate the average range (High - Low) from the historical data.
    """
    total_range = 0
    for day_data in historical_data:
        total_range += day_data['high'] - day_data['low']
    return total_range / len(historical_data)

def get_average_range_and_update_json(days):
    """
    Calculate and update the average range in the JSON file.
    """
    kite = kite_utils.create_kite_obj(api_key=api_key, access_token=access_token)
    previous_dates = general_calc.get_previous_dates(days)
    indices_tokens = strategy_obj.get_general_params().get('IndicesTokens')
    instruments = strategy_obj.get_instruments()
    
    for instrument in instruments:
        # Fetch the instrument token
        instrument_token = indices_tokens.get(instrument, None)
        if instrument_token is None:
            print(f"Instrument token for {instrument} not found.")
            continue
        
        # Fetch historical data for the instrument
        historical_data = kite.historical_data(instrument_token, from_date = previous_dates[-1], to_date=previous_dates[0], interval = 'day')
        
        # Calculate the average range
        average_range = calculate_average_range(historical_data)

        # Update the JSON file with the average range
        entry_params = strategy_obj.get_entry_params()
        entry_params[instrument]['ATR5D'] = round(average_range, 2)
        strategy_obj.write_strategy_json(STRATEGY_PATH)

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

def get_high_low_range_and_update_json():
    """
    Calculate and update the high-low range in the JSON file.
    """
    # today = dt.date.today().strftime('%Y-%m-%d')
    kite = kite_utils.create_kite_obj(api_key=api_key, access_token=access_token)
    today = dt.datetime.now().date()
    start_time = dt.datetime.combine(today, dt.time(9, 15))
    end_time = dt.datetime.combine(today, dt.time(10, 30))
    indices_tokens = strategy_obj.get_general_params().get('IndicesTokens')
    instruments = strategy_obj.get_instruments()

    for instrument in instruments:

        # Fetch the instrument token
        instrument_token = indices_tokens.get(instrument, None)
        if instrument_token is None:
            print(f"Instrument token for {indices_tokens} not found.")
            continue

        data = kite.historical_data(instrument_token, start_time, end_time, 'hour')
        if data:
            high, low = data[0]['high'], data[0]['low']
            range_ = high - low

            entry_params = strategy_obj.get_entry_params()
            entry_params[instrument]['TriggerPoints']['IBHigh'] = high
            entry_params[instrument]['TriggerPoints']['IBLow'] = low
            entry_params[instrument]['IBValue'] = range_
            entry_params[instrument]['IBLevel'] = determine_ib_level(range_ / entry_params[instrument]['ATR5D'])
            entry_params[instrument]["PriceRef"] = qty_calc.get_price_reference('MPWizard',instrument)
            strategy_obj.write_strategy_json(STRATEGY_PATH)

def calculate_option_type(ib_level,cross_type,trade_view):
    if ib_level == 'Big':
        return 'PE' if cross_type == 'UpCross' else 'CE'
    elif ib_level == 'Small':
        return 'PE' if cross_type == 'DownCross' else 'CE'
    elif ib_level == 'Medium':
        return 'PE' if trade_view == 'Bearish' else 'CE'
    else:
        print(f"Unknown IB Level: {ib_level}")
    return None