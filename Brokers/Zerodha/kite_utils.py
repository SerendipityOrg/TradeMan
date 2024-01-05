from kiteconnect import KiteConnect
import pandas as pd
import os,sys


DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)


def create_kite_obj(user_details=None,api_key=None,access_token=None):
    if api_key and access_token:
        return KiteConnect(api_key=api_key,access_token=access_token)
    elif user_details:
        return KiteConnect(api_key=user_details['api_key'],access_token=user_details['access_token'])
    else:
        raise ValueError("Either user_details or api_key and access_token must be provided")

def get_csv_kite(user_details):
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    instrument_dump = kite.instruments()
    instrument_df = pd.DataFrame(instrument_dump)
    instrument_df.to_csv(r'instruments.csv') 

def get_kite_active_users(active_users, strategy_name):
    subscribed_users = []
    for user in active_users:
        if "zerodha" in user['broker']:
            if strategy_name in user['qty']:
                subscribed_users.append(user['account_name'])
    return subscribed_users

def calculate_transaction_type(kite,transaction_type):
    if transaction_type == 'BUY':
        transaction_type = kite.TRANSACTION_TYPE_BUY
    elif transaction_type == 'SELL':
        transaction_type = kite.TRANSACTION_TYPE_SELL
    else:
        raise ValueError("Invalid transaction_type in order_details")
    return transaction_type

def calculate_order_type(kite,order_type):
    if order_type == 'Stoploss':
        order_type = kite.ORDER_TYPE_SL
    elif order_type == 'Market':
        order_type = kite.ORDER_TYPE_MARKET
    elif order_type == 'Limit':
        order_type = kite.ORDER_TYPE_LIMIT
    else:
        raise ValueError("Invalid order_type in order_details")
    return order_type

def calculate_product_type(kite,product_type):
    if product_type == 'NRML':
        product_type = kite.PRODUCT_NRML
    elif product_type == 'MIS':
        product_type = kite.PRODUCT_MIS
    elif product_type == 'CNC':
        product_type = kite.PRODUCT_CNC
    else:
        raise ValueError("Invalid product_type in order_details")
    return product_type

def calculate_segment_type(kite, segment_type):
    # Prefix to indicate the exchange type
    prefix = "EXCHANGE_"
    
    # Construct the attribute name
    attribute_name = prefix + segment_type
    
    # Get the attribute from the kite object, or raise an error if it doesn't exist
    if hasattr(kite, attribute_name):
        return getattr(kite, attribute_name)
    else:
        raise ValueError(f"Invalid segment_type '{segment_type}' in order_details")

def get_avg_prc(kite,order_id):
    if not order_id:
        raise Exception("Order_id not found")
    
    order_history = kite.order_history(order_id=order_id)
    for order in order_history:
        if order.get('status') == 'COMPLETE':
            avg_prc = order.get('average_price', 0.0)
            break 
    return avg_prc

def get_order_details(user):
    kite = create_kite_obj(api_key=user['api_key'],access_token=user['access_token'])
    orders = kite.orders()
    return orders

def cash_balance(user_details):
    kite = KiteConnect(api_key=user_details['api_key'])
    kite.set_access_token(user_details['access_token'])
    # Fetch the account balance details
    balance_details = kite.margins(segment='equity')

    # Extract the 'cash' value
    cash_balance = balance_details.get('cash', 0)

    # If 'cash' key is not at the top level, we need to find where it is
    if cash_balance == 0 and 'cash' not in balance_details:
        # Look for 'cash' in nested dictionaries
        for key, value in balance_details.items():
            if isinstance(value, dict) and 'cash' in value:
                cash_balance = value.get('cash', 0)
                break
    return cash_balance