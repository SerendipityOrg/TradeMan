import datetime as dt
import os,re
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
import general_calc as general_calc

def get_user_details(user):
    user_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'UserProfile', 'json', f'{user}.json')
    json_data = general_calc.read_json_file(user_json_path)
    return json_data, user_json_path


# 1. Renamed the function to avoid clash with the logging module
def log_order(order_id, avg_price, order_details, user_details,strategy):
    user, json_path = get_user_details(order_details['user'])
    if 'strike_prc' in order_details:
        strike_prc = order_details['strike_prc']
    else:
        strike_prc = 0

    #check if order_details['tradingsymbol'] is a string or a dict, if dict then get the name attribute
    if isinstance(order_details['tradingsymbol'], str):
        tradesymbol = order_details['tradingsymbol']
    else:
        tradesymbol = order_details['tradingsymbol'].name

    print("in log orders",tradesymbol)

    # if hasattr(order_details['tradingsymbol'], 'name'):
    #     tradesymbol = order_details['tradingsymbol'].name
    # else:
    #     tradesymbol = order_details['tradingsymbol']

    order_dict = {
        "order_id": order_id,
        "avg_prc": avg_price,
        "qty": order_details['qty'],
        "timestamp": str(dt.datetime.now()),
        "strike_price": strike_prc,
        "tradingsymbol": tradesymbol
    }

    if hasattr(order_details['tradingsymbol'], 'name'):
        order_dict['tradingsymbol'] = order_details['tradingsymbol'].name
    else:
        order_dict['tradingsymbol'] = order_details['tradingsymbol']

    if 'signal' in order_details and strategy == "AmiPy":
        print(type(strike_prc))
        print(order_details['tradingsymbol'].name[-7:-2])
        if str(strike_prc) == order_details['tradingsymbol'].name[-7:-2] or str(strike_prc) == order_details['tradingsymbol'][-7:-2]:
            order_dict['trade_type'] = order_details['signal']
        else:
            order_dict['trade_type'] = "HedgeOrder"
    else:
        order_dict['trade_type'] = order_details['transaction_type']

    if 'direction' in order_details:
        order_dict['direction'] = order_details['direction']
    
    if 'signal' in order_details:
        order_dict['signal'] = order_details['signal']
    
    broker = list(user.keys())[0]
    broker = user_details.setdefault(broker, {})
    orders = broker.setdefault('orders', {})
    strategy_orders = orders.setdefault(strategy, {})

    #if trade_type is present in order_dict it should setdefault to that else it should setdefault to order_details['transaction_type']
    if 'signal' in order_dict:
        order_type_list = strategy_orders.setdefault(order_dict['signal'], [])
    else:
        order_type_list = strategy_orders.setdefault(order_details['transaction_type'], [])
    order_type_list.append(order_dict)

    log_details = general_calc.write_json_file(json_path, user_details)
    
def get_quantity(user_data, broker, strategy, tradingsymbol=None):
    strategy_key = f"{strategy}_qty"
    user_data_specific = user_data[broker]  # Access the specific user's data
    
    if strategy_key not in user_data_specific:
        return None
    
    quantity_data = user_data_specific[strategy_key]

    if strategy == 'MPWizard' or strategy == 'Siri':
        if broker == 'aliceblue':
            tradesymbol = tradingsymbol.name
        else:
            tradesymbol = tradingsymbol

        if isinstance(tradesymbol, str):
            ma = re.match(r"(NIFTY|BANKNIFTY|FINNIFTY)", tradesymbol)
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
            return order['order_id']

    return None
