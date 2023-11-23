import datetime as dt
import os,re
import sys,math
import pandas as pd
import json

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import Brokers.place_order_calc as place_order_calc
from MarketUtils.InstrumentBase import Instrument
import Strategies.StrategyBase as Strategy

active_users_json_path = os.path.join(DIR_PATH,"MarketUtils", "active_users.json")
fno_info_path = os.path.join(DIR_PATH, 'fno_info.csv')

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
    try:
        strategy_json = general_calc.read_json_file(strategy_json_path)
    except (FileNotFoundError, IOError, json.JSONDecodeError):
        # Handle exceptions and use an empty dictionary if the file doesn't exist or an error occurs
        strategy_json = {}
    return strategy_json, strategy_json_path

def get_active_users(broker_json_details):
    active_users = []
    for user in broker_json_details:
        if 'Active' in user['account_type']:
            active_users.append(user)
    return active_users


# Mapping of strategy names to prefixes
strategy_prefix_map = {
    'AmiPy': 'AP',
    'MPWizard': 'MP',
    'ExpiryTrader': 'ET',
    'OvernightFutures': 'OF'
}

# # Load the last state from JSON
def load_last_state():
    try:
        with open('trade_id_state.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# # Save the current state to JSON
def save_current_state(state):
    with open('trade_id_state.json', 'w') as file:
        json.dump(state, file)

# # Initialize or load the trade ID state
trade_id_state = load_last_state()

def get_trade_id(strategy_name, trade_type):
    global trade_id_state

    # Load strategy object
    _, strategy_path = get_strategy_json(strategy_name)
    strategy_obj = Strategy.Strategy.read_strategy_json(strategy_path)

    # Resolve strategy name to prefix
    strategy_prefix = strategy_prefix_map.get(strategy_name)
    if not strategy_prefix:
        raise ValueError(f"Unknown strategy name: {strategy_name}")

    # Initialize strategy in state if not present
    if strategy_prefix not in trade_id_state:
        trade_id_state[strategy_prefix] = 1

    # Generate trade ID for entry
    if trade_type.lower() == 'entry':
        current_id = trade_id_state[strategy_prefix]
        trade_id_state[strategy_prefix] += 1
        trade_id = f"{strategy_prefix}{current_id}_entry"
        next_trade_id = f"{strategy_prefix}{trade_id_state[strategy_prefix]}"
        # Save new trade ID in strategy JSON
        strategy_obj.set_next_trade_id(next_trade_id)
        strategy_obj.write_strategy_json(strategy_path)

    # Use the same ID for exit
    elif trade_type.lower() == 'exit':
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


# 1. Renamed the function to avoid clash with the logging module
def log_order(order_id, order_details):
    print("in log_order")
    # Getting the json data and path for the user
    user_data, json_path = get_orders_json(order_details['username'])
    # Creating the order_dict structure
    order_dict = {
        "order_id": order_id,
        "qty": int(order_details['qty']),
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

def get_lot_size(base_symbol):
    fno_info_df = pd.read_csv(fno_info_path)
    lotsize = fno_info_df.loc[fno_info_df['base_symbol'] == base_symbol, 'lot_size'].values
    return lotsize[0]

def calculate_qty(risk,accountname,base_symbol=None,exchange_token=None):
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == accountname:
            if base_symbol == 'Stock':
                strategy_obj = Strategy.Strategy({})
                ltp = strategy_obj.get_single_ltp(Instrument().get_token_by_exchange_token(exchange_token))
                risk_capital = round(float(user['current_capital']*(int(risk)/100)))
                qty = math.ceil(risk_capital/ltp)
            else:
                strategy_obj = Strategy.Strategy({})
                ltp = strategy_obj.get_single_ltp(Instrument().get_token_by_exchange_token(exchange_token))
                lot_size = get_lot_size(base_symbol)####TODO Check this part
                raw_qty = (user['current_capital'] * (int(risk)/100))/ltp
                qty = math.ceil(raw_qty//lot_size) * lot_size
                if qty == 0:
                    qty = lot_size

            return qty


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
        'ET': 'ExpiryTrader',
        'OF': 'OvernightFutures',
        'EXTRA': 'Extra',
        'STOCK': 'Stock'
    }
    
    if trade_id.startswith('EXTRA'):
        return strategy_map['EXTRA']
    elif trade_id.startswith('STOCK'):
        return strategy_map['STOCK']

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

def read_max_order_qty_for_symbol(base_symbol):
    df = pd.read_csv(os.path.join(DIR_PATH,'fno_info.csv'))
    max_order_qty = df[df['base_symbol'] == base_symbol]['max_order_qty'].iloc[0]
    return max_order_qty


def create_telegram_order_details(details):
    import Brokers.place_order as place_order
    base_symbol = details['base_instrument']
    if base_symbol == 'Stock':
        base_symbol = details['stock_name']
    strategy_name = get_strategy_name(details['trade_id'])

    if details['strike_prc'] == "ATM":
        _, STRATEGY_PATH = place_order_calc.get_strategy_json(strategy_name)
        strategy_obj = Strategy.Strategy.read_strategy_json(STRATEGY_PATH)
        strike_prc = strategy_obj.calculate_current_atm_strike_prc(base_symbol)
    else:
        strike_prc = details['strike_prc']

    if details['option_type'] in ['FUT', 'Stock']:
        strike_prc = 0

    if details.get('option_type') == 'Stock':
        exchange_token = Instrument().get_exchange_token_by_name(details['stock_name'])
    else:
        expiry_date = Instrument().get_expiry_by_criteria(base_symbol, int(strike_prc), details['option_type'], details['expiry'])
        exchange_token = Instrument().get_exchange_token_by_criteria(base_symbol, int(strike_prc), details['option_type'], expiry_date)

    if details['base_instrument'] == 'Stock' and details['option_type'] != 'Stock':
        order_type = 'Limit'
        token = Instrument().get_token_by_exchange_token(exchange_token)
        price = round(strategy_obj.get_single_ltp(token),1)
    else:
        order_type = 'Market'
        order_details = {}

    order_details = {
        "strategy": strategy_name,
        "base_symbol": base_symbol,
        "exchange_token": exchange_token,
        "transaction_type": details['transaction_type'],
        "order_type": order_type,
        "product_type": details['product_type'],
        "trade_id": details['trade_id']
    }

    if order_details['order_type'] == 'Limit':
        order_details['limit_prc'] = price

    if details['order_type'] == 'PlaceOrder':
        order_details['order_mode'] = ['MainOrder']

    active_users = general_calc.read_json_file(active_users_json_path)
    for user in details['account_name']:
        for active_user in active_users:
            if active_user['account_name'] == user:
                order_details['username'] = user
                order_details['broker'] = active_user['broker']
                # Calculate quantity based on risk percentage if available
                if 'risk_percentage' in details:
                    order_details['qty'] = calculate_qty(details['risk_percentage'], user, base_symbol, int(exchange_token))
                elif 'qty' in details:
                    order_details['qty'] = details['qty']
                else:
                    print("Quantity not specified for", user)
                place_order.place_order_for_broker(order_details)
                break  # Break the inner loop after placing an order for a user
