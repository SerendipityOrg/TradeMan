from pya3 import *
import sys

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
# import MarketUtils.Calculations.qty_calc as qty_calc
# import Brokers.BrokerUtils.Broker as Broker
# import Brokers.Aliceblue.alice_login as alice_login

def create_alice_obj(user_details): 
    return Aliceblue(user_id=user_details['username'],api_key=user_details['api_key'],session_id=user_details['session_id'])

def recreate_alice_obj(user_details):
    #TODO if session_id is expired, then recreate the alice obj
    pass

def get_csv_alice(user_details):
    alice = Aliceblue(user_id=user_details['aliceblue']['brijesh']['username'], api_key=user_details['aliceblue']['brijesh']['api_key'])
    alice.get_session_id()
    alice.get_contract_master("NFO") #TODO rename the NFO.csv to alice_instruments.csv


def get_alice_active_users(active_users, strategy_name):
    subscribed_users = []
    for user in active_users:
        if "aliceblue" in user['broker']:
            if strategy_name in user['qty']:
                subscribed_users.append(user['account_name'])
    return subscribed_users

def calculate_transaction_type(transaction_type):
    if transaction_type == 'BUY':
        transaction_type = TransactionType.Buy
    elif transaction_type == 'SELL':
        transaction_type = TransactionType.Sell
    else:
        raise ValueError("Invalid transaction_type in order_details")
    return transaction_type

def calculate_order_type(order_type):
    if order_type == 'Stoploss':
        order_type = OrderType.StopLossLimit
    elif order_type == 'Market':
        order_type = OrderType.Market
    else:
        raise ValueError("Invalid order_type in order_details")
    return order_type

def calculate_product_type(product_type):
    if product_type == 'NRML':
        product_type = ProductType.Normal
    elif product_type == 'MIS':
        product_type = ProductType.Intraday
    else:
        raise ValueError("Invalid product_type in order_details")
    return product_type

def get_avg_prc(alice,order_id):
    order_id_value = order_id['NOrdNo']
    if not order_id_value:
        raise Exception("Order_id not found")
    
    avg_prc_data = alice.get_order_history(order_id_value)
    avg_prc = avg_prc_data.get('Avgprc')
    return avg_prc