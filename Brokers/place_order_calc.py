from enum import Enum
import datetime as dt
import os,re
import sys,math
import pandas as pd
import json
from dotenv import load_dotenv

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)
excel_dir = os.getenv('onedrive_excel_folder')

import MarketUtils.general_calc as general_calc
from MarketUtils.InstrumentBase import Instrument
import Strategies.StrategyBase as StrategyBase
from MarketUtils.Excel.strategy_calc import load_existing_excel
import Brokers.telegram_order_calc as telegram_order_calc

active_users_json_path = os.path.join(DIR_PATH,"MarketUtils", "active_users.json")
trade_state_path = os.path.join(DIR_PATH, 'trade_id_state.json')

class TradeType(Enum):
    ENTRY = 'entry'
    EXIT = 'exit'

class StrategyPrefix(Enum):
    AmiPy = "AP"
    MPWizard = "MP"
    ExpiryTrader = "ET"
    OvernightFutures = "OF"
    Extra = "EXTRA"
    Stock = "STOCK"

    @staticmethod
    def get_strategy_by_prefix(prefix):
        for strategy in StrategyPrefix:
            if strategy.value == prefix:
                return strategy.name
        return None

def monitor():
    from Brokers.instrument_monitor import InstrumentMonitor
    return InstrumentMonitor()



def get_trade_id(strategy_name, trade_type: TradeType):
    """
    Generate a trade ID based on the given strategy name and trade type.

    Args:
        strategy_name (str): The name of the strategy.
        trade_type (TradeType): The type of the trade (entry or exit).

    Returns:
        str: The generated trade ID.
    """
    # Load the last state from JSON
    def load_last_state():
        try:
            trade_state_json = general_calc.read_json_file(trade_state_path)
            return trade_state_json
        except FileNotFoundError:
            return {}

    # Save the current state to JSON
    def save_current_state(state):
        general_calc.write_json_file(trade_state_path, state)

    # Initialize or load the trade ID state
    trade_id_state = load_last_state()

    # Load strategy object
    _, strategy_path = general_calc.get_strategy_json(strategy_name)
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

    # Resolve strategy name to prefix
    strategy_prefix = StrategyPrefix[strategy_name].value

    # Initialize strategy in state if not present
    if strategy_prefix not in trade_id_state:
        trade_id_state[strategy_prefix] = 1

    # Generate trade ID for entry
    if trade_type == TradeType.ENTRY.value:
        current_id = trade_id_state[strategy_prefix]
        trade_id_state[strategy_prefix] += 1
        trade_id = f"{strategy_prefix}{current_id}_entry"
        next_trade_id = f"{strategy_prefix}{trade_id_state[strategy_prefix]}"
        # Save new trade ID in strategy JSON
        strategy_obj.set_next_trade_id(next_trade_id)
        strategy_obj.write_strategy_json(strategy_path)

    # Use the same ID for exit
    elif trade_type == TradeType.EXIT.value:
        current_id = trade_id_state[strategy_prefix] - 1
        trade_id = f"{strategy_prefix}{current_id}_exit"

    # Add trade_id to today's orders after completion
    base_trade_id = f"{strategy_prefix}{current_id}"
    today_orders = strategy_obj.get_today_orders()
    if base_trade_id not in today_orders:
        today_orders.append(base_trade_id)
        strategy_obj.set_today_orders(today_orders)
        strategy_obj.write_strategy_json(strategy_path)

    # Save state after each ID generation
    save_current_state(trade_id_state)
    print(f"Generated trade ID: {trade_id}")
    return trade_id

def retrieve_order_id(user, strategy, trade_type, exchange_token):
    orders_json,_ = general_calc.get_orders_json(user)
    # Navigate through the JSON structure to retrieve the desired order_id
    strategy_orders = orders_json.get('orders', {}).get(strategy, {})
    orders = strategy_orders.get(trade_type, [])
    for order in orders:
        if order['exchange_token'] == exchange_token:
            return order['order_id']
    return None

def fetch_qty_from_excel(account_name, strategy, trade_id):
    excel_path = os.path.join(excel_dir, f"{account_name}.xlsx") 
    trade_df = load_existing_excel(excel_path).get(strategy, pd.DataFrame())
    trade_id = trade_id.split("_")[0]
    trade_index = trade_df.index[trade_df['trade_id'] == trade_id].tolist()
    if trade_index:
        row_index = trade_index[0]
        trade_data = trade_df.loc[row_index]
        return trade_data['qty']
    else:
        print(f"Trade ID {trade_id} not found in excel")

def get_qty(order_details):
    userdetails = general_calc.assign_user_details(order_details["account_name"])
    strategy = order_details["strategy"]
    qty = None

    if strategy in userdetails.get("qty", {}):
        if order_details.get('strategy_mode') == "MultipleInstruments":
            base_symbol = Instrument().get_base_symbol_by_exchange_token(order_details["exchange_token"])
            qty = userdetails["qty"].get(strategy, {}).get(base_symbol) 
        elif order_details.get('strategy_mode') == 'CarryForward' and "exit" in order_details["trade_id"]:
            qty = fetch_qty_from_excel(order_details["account_name"], strategy, order_details["trade_id"])
        else:
            qty = userdetails.get("qty", {}).get(strategy)

    return qty

def calculate_stoploss(order_details,ltp):
    if 'stoploss_mutiplier' in order_details:
        stoploss = calculate_multipler_stoploss(order_details,ltp)
    elif 'price_ref' in order_details:
        stoploss = calculate_priceref_stoploss(order_details,ltp)
    else:
        raise ValueError("Invalid stoploss calculation in order_details")
    return stoploss

def calculate_multipler_stoploss(order_details,ltp):
    if order_details.get('transaction_type') == 'BUY':
        stoploss = round(float(ltp - (ltp * order_details.get('stoploss_mutiplier'))),1)
    elif order_details.get('transaction_type') == 'SELL':
        stoploss = round(float(ltp + (ltp * order_details.get('stoploss_mutiplier'))),1)

    if stoploss < 0:
        return 1
    
    return stoploss

def calculate_priceref_stoploss(order_details,ltp):
    if order_details.get('transaction_type') == 'BUY':
        stoploss = round(float(ltp - order_details.get('price_ref')),1)
    elif order_details.get('transaction_type') == 'SELL':
        stoploss = round(float(ltp + order_details.get('price_ref')),1)

    if stoploss < 0:
        return 1
    
    return stoploss

def calculate_trigger_price(transaction_type,stoploss):
    if transaction_type == 'BUY':
        trigger_price = round(float(stoploss + 1),1)
    elif transaction_type == 'SELL':
        trigger_price = round(float(stoploss - 1),1)
    return trigger_price

def calculate_transaction_type_sl(transaction_type):
    if transaction_type == 'BUY' or transaction_type == 'B':
        transaction_type_sl = 'SELL'
    elif transaction_type == 'SELL' or transaction_type == 'S':
        transaction_type_sl = 'BUY'
    return transaction_type_sl

def calculate_target(option_ltp,price_ref,strategy):
    return option_ltp+(price_ref/2)

def calculate_strategy_name(trade_id):
    trade_id = trade_id.split("_")[0]
    match = re.match(r'^[A-Za-z]+', trade_id).group()

    # If not a direct match, extract prefix and look up strategy
    strategy_name = StrategyPrefix.get_strategy_by_prefix(match)
    
    # Return the strategy name based on the prefix
    return strategy_name if strategy_name else None

def get_exit_trade_id(trade_id):
    # Replace '_entry' with '_exit' in the trade_id
    if '_entry' in trade_id:
        return trade_id.replace('_entry', '_exit')
    else:
        return trade_id

def create_sweep_order_details(user,order_details):
    strategy_name = calculate_strategy_name(order_details['trade_id'])
    transaction_type_sl = calculate_transaction_type_sl(order_details['transaction_type'])
    trade_id_sl = get_exit_trade_id(order_details['trade_id'])
    sweep_orders_dict = {
            'account_name': user['account_name'],
            'broker' : user['broker'],
            'strategy': strategy_name,
            'transaction_type': transaction_type_sl,
            'exchange_token': order_details['exchange_token'],
            'qty': order_details['qty'],
            'order_type': 'Market',
            'product_type': 'MIS',
            'trade_id': trade_id_sl         
        }
    return sweep_orders_dict

def create_telegram_order_details(details):
    base_symbol = telegram_order_calc.extract_base_symbol(details)
    strategy_name, strategy_obj = telegram_order_calc.get_strategy_object(details)
    strike_prc = telegram_order_calc.calculate_strike_price(details, strategy_obj, base_symbol)
    exchange_token = telegram_order_calc.get_exchange_token(details, base_symbol, strike_prc)
    order_details = telegram_order_calc.prepare_order_details(details, strategy_name, base_symbol, exchange_token, strategy_obj)
    telegram_order_calc.place_orders_for_users(details, order_details)