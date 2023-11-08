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

def get_active_users(broker_json_details):
    active_users = []
    for user in broker_json_details:
        if 'Active' in user['account_type']:
            active_users.append(user)
    return active_users

def increment_trade_id(trade_id):
    # This function separates the prefix and the number, increments the number, and then rejoins them.
    match = re.match(r"([a-zA-Z]+)(\d+)", trade_id)
    prefix = match.group(1)
    number = int(match.group(2))
    incremented_number = number + 1
    return f"{prefix}{incremented_number}"

# Initialize a global cache for trade IDs and exit flags
trade_cache = {}

def get_trade_id(strategy_name, trade_type):
    global trade_cache

    _, strategy_path = get_strategy_json(strategy_name)
    strategy_obj = Strategy.Strategy.read_strategy_json(strategy_path)

    if dt.datetime.now().time() < dt.datetime.strptime("09:00", "%H:%M").time():
        return "test_order"
# Check if a new day has started and reset the cache if it has
    if strategy_name not in trade_cache :
        next_trade_id = strategy_obj.get_next_trade_id()
        trade_cache[strategy_name] = {
            'initial_trade_id': next_trade_id,
            'trade_id': next_trade_id,
            'exit_made': False
        }
    
    current_trade_id = trade_cache[strategy_name]['trade_id']
    today_orders = strategy_obj.get_today_orders()

    # Append the current_trade_id to today_orders after an entry
    if trade_type.lower() == 'entry':
        # If the last action was an exit, use a new trade ID
        if trade_cache[strategy_name]['exit_made']:
            current_trade_id = increment_trade_id(current_trade_id)
            trade_cache[strategy_name]['trade_id'] = current_trade_id  # Update trade_id in the cache
            trade_cache[strategy_name]['exit_made'] = False  # Reset exit flag for new entry
            strategy_obj.set_next_trade_id(current_trade_id)  # Save new trade ID for strategy
            strategy_obj.write_strategy_json(strategy_path)

        new_trade_id = f"{current_trade_id}_entry"
        if new_trade_id not in today_orders:
            today_orders.append(current_trade_id)  # Append the new trade ID with entry tag
            strategy_obj.set_today_orders(today_orders)
            strategy_obj.write_strategy_json(strategy_path)

    # Process exit
    elif trade_type.lower() == 'exit':
        new_trade_id = f"{current_trade_id}_exit"
        if not trade_cache[strategy_name]['exit_made']:
            # Mark exit as made
            trade_cache[strategy_name]['exit_made'] = True
            # No need to increment the trade_id here, it should be incremented at the next entry

        if current_trade_id not in today_orders:
            today_orders.append(current_trade_id)  # Append the new trade ID with exit tag
            strategy_obj.set_today_orders(today_orders)
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
        "exchange_token": int(order_details['exchange_token']),
        "trade_id" : order_details['trade_id']
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

    if strategy == 'OvernightFutures' and "exit" in order_details["trade_id"]:
        return userdetails["qty"].get("PreviousOvernightFutures")
        
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
    if transaction_type == 'BUY' or transaction_type == 'B':
        transaction_type_sl = 'SELL'
    elif transaction_type == 'SELL' or transaction_type == 'S':
        transaction_type_sl = 'BUY'
    return transaction_type_sl


def calculate_target(option_ltp,price_ref,strategy):
    if strategy == 'MPWizard':
        target = option_ltp+(price_ref/2)
    return target

def get_strategy_name(trade_id):
    # Define the mapping between trade_id prefix and strategy name
    strategy_map = {
        'AP': 'AmiPy',
        'MP': 'MPWizard',
        'ET': 'ExpiryTrader' 
    }
    
    # Extract the prefix from the trade_id
    prefix = trade_id[:2]  # assuming all prefixes are two characters long
    
    # Return the strategy name based on the prefix, or a default value if not found
    return strategy_map.get(prefix, "Unknown Strategy")

def get_exit_trade_id(trade_id):
    # Replace '_entry' with '_exit' in the trade_id
    if '_entry' in trade_id:
        return trade_id.replace('_entry', '_exit')
    else:
        return trade_id

def create_sweep_order_details(user,order_details):
    strategy_name = get_strategy_name(order_details['trade_id'])
    transaction_type_sl = calculate_transaction_type_sl(order_details['transaction_type'])
    trade_id_sl = get_exit_trade_id(order_details['trade_id'])
    sweep_orders_dict = {
            'username': user['username'],
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