import datetime as dt
import os,re
import sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
from MarketUtils.InstrumentBase import Instrument
import Strategies.StrategyBase as Strategy

def monitor():
    from Brokers.instrument_monitor import InstrumentMonitor
    return InstrumentMonitor()

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

def get_active_users(active_user_json_details):
    active_users = []
    for user in active_user_json_details:
        if 'Active' in user['account_type']:
            active_users.append(user)
    return active_users

# Initialize a global cache for trade IDs and exit flags
trade_cache = {}

def get_trade_id(strategy_name, trade_type):
    global trade_cache

    _, strategy_path = get_strategy_json(strategy_name)
    strategy_obj = Strategy.Strategy.read_strategy_json(strategy_path)

    if dt.datetime.now().time() < dt.datetime.strptime("11:00", "%H:%M").time():
        return "test_order"

    # If the strategy is not in the cache, initialize it
    if strategy_name not in trade_cache:
        next_trade_id = strategy_obj.get_next_trade_id()
        trade_cache[strategy_name] = {'trade_id': next_trade_id}

    current_trade_id = trade_cache[strategy_name]['trade_id']
    new_trade_id = f"{current_trade_id}_{trade_type.lower()}"

    if trade_type.lower() == 'exit':
        # Update trade ID for future orders
        next_trade_id_num = int(current_trade_id[2:]) + 1
        trade_cache[strategy_name]['trade_id'] = f"{current_trade_id[:2]}{next_trade_id_num:02}"

        # Update TodayOrders and NextTradeId, and write changes to JSON
        today_orders = strategy_obj.get_today_orders()
        today_orders.append(current_trade_id)
        strategy_obj.set_today_orders(today_orders)
        strategy_obj.set_next_trade_id(trade_cache[strategy_name]['trade_id'])
        strategy_obj.write_strategy_json(strategy_path)
    print(f"Trade ID: {new_trade_id}")
    return new_trade_id

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

def fetch_orders_json(username):
    return general_calc.read_json_file(os.path.join(DIR_PATH,'UserProfile','OrdersJson', f'{username}.json'))

def retrieve_order_id(user,strategy, trade_type, exchange_token):

    orders_json = fetch_orders_json(user)
    # Navigate through the JSON structure to retrieve the desired order_id
    strategy_orders = orders_json.get('orders', {}).get(strategy, {})
    orders = strategy_orders.get(trade_type, [])
    for order in orders:
        if order['exchange_token'] == exchange_token:
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

def calculate_target(option_ltp,price_ref):
    return option_ltp+price_ref


