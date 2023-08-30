import time
from dotenv import load_dotenv
import os 
from kiteconnect import KiteConnect

import sys
sys.path.append(r'C:\Users\user\Desktop\TradeMan\Utils')
from general_calc import *

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')

sys.path.append(BROKERS_DIR)
import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha

env_file_path = os.path.join(CURRENT_DIR, '.env')
env_file_path = os.path.abspath(env_file_path)

load_dotenv(env_file_path)

file_path = os.getenv('omkar_json_filepath')
omkar_details = read_json_file(file_path)
kite = KiteConnect(api_key=omkar_details['zerodha']['api_key'])
kite.set_access_token(omkar_details['zerodha']['access_token'])

# def monitor_index(tokens):
#     ltps = {}
    
#     for token in tokens:
#         try:
#             ltp_data = kite.ltp(token)
#             ltps[token] = ltp_data[token]['last_price']
#             # If you have other processing for individual tokens, you can do it here
            
#         except Exception as e:
#             print(f"Error fetching LTP for token {token}: {e}")
            
#     return ltps

# def monitor_instruments(monitor_order_func=None):
#     ltp = kite.ltp(monitor_order_func['token'])
#     ltp_data = ltp[str(monitor_order_func['token'])]['last_price']
    
#     return ltp_data
    

# def monitor_instruments(monitor_order_func=None):
#     if not monitor_order_func or 'token' not in monitor_order_func:
#         print("Error: monitor_order_func dictionary is missing or doesn't contain the required key 'token'")
#         return None

#     ltp = kite.ltp(monitor_order_func['token'])
#     ltp_data = ltp[str(monitor_order_func['token'])]['last_price']

#     if set(monitor_order_func.keys()) != {'token'}:
#         print(monitor_order_func)
#         print(f"LTP for {monitor_order_func['token']} is {ltp_data}")

#         if ltp_data >= float(monitor_order_func.get('target', 0)):  
#             broker = monitor_order_func.get('broker')
#             monitor_order_func['new_stoploss'] = monitor_order_func.get('target')
#             if broker == 'zerodha':
#                 modify_order = zerodha.update_stoploss(monitor_order_func)
#             elif broker == 'aliceblue':
#                 modify_order = aliceblue.update_stoploss(monitor_order_func)
#             print(f"Target reached for {monitor_order_func['token']}. Stoploss updated to {monitor_order_func.get('new_stoploss')}.")
    
                    
#     return ltp_data

class InstrumentMonitor:
    def __init__(self, initial_tokens=None, kite_client=None):
        self.tokens_to_monitor = set(initial_tokens) if initial_tokens else set()  # using a set to avoid duplicates
        self.kite = kite_client

    def add_token(self, token):
        self.tokens_to_monitor.add(token)

    def remove_token(self, token):
        self.tokens_to_monitor.discard(token)  # discard does not raise an error if the token is not present

    def monitor(self):
        while True:
            for token in self.tokens_to_monitor:
                print(f"Monitoring token {token}")
                ltp = self.get_ltp_for_token(token)
                
                print(f"LTP for token {token}: {ltp}")
                # If you have other processing for each token's LTP, you can do it here
            time.sleep(10)
    
    def get_ltp_for_token(self, token):
        try:
            ltp = kite.ltp(token)
            ltp_data = ltp[str(token)]['last_price']
            return ltp_data
        except Exception as e:
            print(f"Error fetching LTP for token {token}: {e}")
            return None







        

