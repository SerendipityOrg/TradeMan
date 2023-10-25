from kiteconnect import KiteConnect
import pandas as pd
import json,sys


DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.Calculations.qty_calc as qty_calc
# import Brokers.BrokerUtils.Broker as Broker
import Brokers.Zerodha.kite_login as kite_login
import Brokers.place_order_calc as place_order_calc

def create_kite_obj(user_details=None,api_key=None,access_token=None):
    print(user_details)
    if api_key and access_token:
        return KiteConnect(api_key=api_key,access_token=access_token)
    elif user_details:
        return KiteConnect(api_key=user_details['api_key'],access_token=user_details['access_token'])
    else:
        raise ValueError("Either user_details or api_key and access_token must be provided")

def get_csv_kite(user_details):
    kite = KiteConnect(api_key=user_details['zerodha']['omkar']['api_key'])
    kite.set_access_token(user_details['zerodha']['omkar']['access_token'])
    instrument_dump = kite.instruments()
    instrument_df = pd.DataFrame(instrument_dump)
    instrument_df.to_csv(r'kite_instruments.csv') 

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
    else:
        raise ValueError("Invalid order_type in order_details")
    return order_type

def calculate_product_type(kite,product_type):
    if product_type == 'NRML':
        product_type = kite.PRODUCT_NRML
    elif product_type == 'MIS':
        product_type = kite.PRODUCT_MIS
    else:
        raise ValueError("Invalid product_type in order_details")
    return product_type

def get_avg_prc(kite,order_id):
    if not order_id:
        raise Exception("Order_id not found")
    
    order_history = kite.order_history(order_id=order_id)
    for order in order_history:
        if order.get('status') == 'COMPLETE':
            avg_prc = order.get('average_price', 0.0)
            break 
    return avg_prc

def get_order_details(user,trade_id):
    user_details = place_order_calc.get_user_details(user)
    kite = create_kite_obj(user_details)
    orders = kite.orders()
    orders_to_exit = []
    for order in orders:
        if order['remarks'] == trade_id:
            orders_to_exit.append(order)
    return orders_to_exit

