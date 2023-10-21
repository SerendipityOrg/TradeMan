import datetime as dt
import os,re
import sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
from MarketUtils.InstrumentBase import Instrument

def get_user_details(user):
    user_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'UserProfile', 'UserJson', f'{user}.json')
    json_data = general_calc.read_json_file(user_json_path)
    return json_data, user_json_path

def get_orders_json(user):
    user_json_path = os.path.join(DIR_PATH,'UserProfile','OrdersJson', f'{user}.json')
    json_data = general_calc.read_json_file(user_json_path)
    return json_data, user_json_path

def get_strategy_json(strategy_name):
    strategy_json_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','Strategies', strategy_name,strategy_name+'.json')
    strategy_json = general_calc.read_json_file(strategy_json_path)
    return strategy_json,strategy_json_path

current_exit_signal_cache = {}

def get_trade_id(strategy, signal=None, order_details=None):
    global current_exit_signal_cache  # Use this only if the function is at the global scope

    strategy_json, strategy_json_path = get_strategy_json(strategy)

    next_trade_id_str = strategy_json["NextTradeId"]
    strategy_prefix = ''.join([i for i in next_trade_id_str if not i.isdigit()])
    next_trade_id_num = int(''.join([i for i in next_trade_id_str if i.isdigit()]))
    
    is_exit = False

    if strategy in ["AmiPy", "Overnight_Options"]:
        exit_signals = ["ShortCoverSignal", "LongCoverSignal", "Morning"]
        if signal in exit_signals:
            is_exit = True
    else:
        is_exit = order_details.get('transaction', '').lower() == 'sell' or order_details.get('transaction_type', '').lower() == 'sell'
        print('is_exit',is_exit)

    current_trade_id = strategy_prefix + str(next_trade_id_num)

    if is_exit:
        current_trade_id += "_exit"
    else:
        current_trade_id += "_entry"
    
    # Store trade_ids that are placed today in the JSON under the `today_orders` tag
    if "TodayOrders" not in strategy_json:
        strategy_json["TodayOrders"] = []

    # Check if the signal is in our cache
    if is_exit:
        if signal in current_exit_signal_cache:
            # Use the cached trade_id for the current signal
            return current_exit_signal_cache[signal]
        else:
            # Store the current trade_id in the cache for this signal
            current_exit_signal_cache[signal] = current_trade_id

        # Increment the trade_id after using it for the current exit order and update the JSON.
        strategy_json["TodayOrders"].append(strategy_prefix + str(next_trade_id_num))
        next_trade_id_num += 1
        new_trade_id = strategy_prefix + str(next_trade_id_num)
        strategy_json["NextTradeId"] = new_trade_id
        general_calc.write_json_file(strategy_json_path, strategy_json)
    print('current_trade_id',current_trade_id)
    return current_trade_id

# 1. Renamed the function to avoid clash with the logging module
def log_order(order_id, order_details):
    print("in log_order")
    # Getting the json data and path for the user
    user_data, json_path = get_orders_json(order_details['username'])

    # Creating the order_dict structure
    order_dict = {
        "order_id": order_id,
        "qty": order_details['qty'],
        "timestamp": str(dt.datetime.now()),
        "exchange_token": int(order_details['exchange_token'])
    }

    # Checking for 'signal' and 'transaction_type' and setting the trade_type accordingly
    trade_type = order_details.get('signal', order_details.get('transaction_type'))
    
    # Constructing the user_data JSON structure
    orders = user_data.setdefault('orders', {})
    strategy_orders = orders.setdefault(order_details.get("strategy"), {})
    order_type_list = strategy_orders.setdefault(trade_type, [])
    order_type_list.append(order_dict)
    general_calc.write_json_file(json_path, user_data)

def assign_user_details(username):
    user_details = general_calc.read_json_file(os.path.join(DIR_PATH,'MarketUtils','active_users.json'))
    for user in user_details:
        if user['account_name'] == username:
            user_details = user
    return user_details
    
def retrieve_order_id(user, broker,strategy, trade_type, tradingsymbol):

    user_details, _ = get_user_details(user)
    # Navigate through the JSON structure to retrieve the desired order_id
    orders_dict = user_details.get(broker, {})
    strategy_orders = orders_dict.get('orders', {}).get(strategy, {})
    orders = strategy_orders.get(trade_type, [])
    for order in orders:
        if order['tradingsymbol'] == tradingsymbol:
            return order['order_id']

    return None


def get_qty(order_details):
    userdetails = assign_user_details(order_details["username"])
    strategy = order_details["strategy"]
    if strategy not in userdetails["qty"]:
        print(f"Strategy {strategy} not found in userdetails")
        return None
    
    if strategy == "MPWizard":
        base_symbol = Instrument().get_base_symbol_by_exchange_token(order_details["exchange_token"])    
        if base_symbol is None:
            return None
        
        return userdetails["qty"]["MPWizard"].get(base_symbol)
    
    return userdetails["qty"].get(strategy)

def calculate_stoploss(order_details,ltp):#TODo split this function into two parts
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
    if transaction_type == 'BUY':
        transaction_type_sl = 'SELL'
    elif transaction_type == 'SELL':
        transaction_type_sl = 'BUY'
    return transaction_type_sl


