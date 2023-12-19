import os, sys
import datetime as dt

# Adding the path to the sys.path
DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

# Importing the required modules
from MarketUtils.general_calc import write_json_file,get_orders_json

def log_order(order_id, order_details):
    # Getting the json data and path for the user
    user_data, json_path = get_orders_json(order_details['account_name'])
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
    write_json_file(json_path, user_data)