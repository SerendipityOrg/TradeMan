import datetime as dt
import os,re
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *



def get_user_details(user):
    user_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'UserProfile', 'Json', f'{user}.json')
    json_data =read_json_file(user_json_path)
    return json_data, user_json_path

# 1. Renamed the function to avoid clash with the logging module
def log_order(order_id, avg_price, order_details, user_details,strategy):
    _, json_path = get_user_details(order_details['user'])
    order_dict = {
        "order_id": order_id,
        "trade_type": order_details['transaction_type'],
        "avg_prc": avg_price,
        "timestamp": str(dt.datetime.now().time()),
        "strike_price": order_details['tradingsymbol'].name[-7:-2],
        "tradingsymbol": order_details['tradingsymbol'].name
    }
    orders = user_details.setdefault('orders', {})
    strategy_orders = orders.setdefault(strategy, {})
    order_type_list = strategy_orders.setdefault(order_details['transaction_type'], [])
    order_type_list.append(order_dict)

    log_details = write_json_file(json_path, user_details)
    

def get_quantity(user_data, strategy, tradingsymbol,broker):
    strategy_key = f"{strategy}_qty"
    user_data_specific = user_data[broker]  # Access the specific user's data
    
    if strategy_key not in user_data_specific:
        return None

    quantity_data = user_data_specific[strategy_key]
    if strategy == 'MPWizard':
        if len(tradingsymbol) >= 3:
            tradingsymbol = tradingsymbol[2]
        elif len(tradingsymbol) == 1:
            tradingsymbol = tradingsymbol
                    
        if isinstance(tradingsymbol, str):
            ma = re.match(r"(NIFTY|BANKNIFTY|FINNIFTY)", tradingsymbol)
            return ma and quantity_data.get(f"{ma.group(1)}_qty")


    return quantity_data if isinstance(quantity_data, dict) else quantity_data

def retrieve_order_id(user, broker,strategy, trade_type, tradingsymbol):

    user_details, _ = get_user_details(user)

    # Navigate through the JSON structure to retrieve the desired order_id
    orders_dict = user_details.get(broker, {})
    strategy_orders = orders_dict.get('orders', {}).get(strategy, {})
    orders = strategy_orders.get(trade_type, [])
    for order in orders:
        if order['tradingsymbol'] == tradingsymbol:
            return order['order_id'],order['qty']

    return None











