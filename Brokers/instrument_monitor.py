import time
from dotenv import load_dotenv
import os 
import threading
from kiteconnect import KiteConnect
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(CURRENT_DIR, '..', 'Utils')

sys.path.append(UTILS_DIR)
from general_calc import *

BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')
sys.path.append(BROKERS_DIR)
import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha
import place_order as place_order

sys.path.append(os.path.join(UTILS_DIR, 'Discord'))
import discordchannels as discord

env_file_path = os.path.join(CURRENT_DIR, '.env')
env_file_path = os.path.abspath(env_file_path)

load_dotenv(env_file_path)

file_path = os.getenv('omkar_json_filepath')
omkar_details = read_json_file(file_path)
kite = KiteConnect(api_key=omkar_details['zerodha']['api_key'])
kite.set_access_token(omkar_details['zerodha']['access_token'])

class InstrumentMonitor:
    """
    Singleton class to monitor instruments and handle trading signals.
    """    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(InstrumentMonitor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, callback=None):
        self.lock = threading.Lock()
        self.tokens_to_monitor = {}  # Using a dictionary to store token along with its target and limit price
        self.callback = callback
        
    def add_token(self, token, target=None, limit_prc=None,order_details = None,strategy = None):
        """Add a token to the monitoring list."""
        if token not in self.tokens_to_monitor:
            print(f"Added token {token} to monitor. Current tokens: {self.tokens_to_monitor}")
        else:
            print(f"Token {token} is already being monitored.")
            
        self.tokens_to_monitor[token] = {
            'target': target,
            'limit_prc': limit_prc,
            'order_details': order_details,
            'strategy': strategy
        }
        # Print the price_ref from the order_details
        if self.tokens_to_monitor[token] is not None :
            print("price_ref:" ,self.tokens_to_monitor[token])
        print(f"Added token {token} to monitor. Current tokens: {self.tokens_to_monitor.keys()}")

    def remove_token(self, token):
        """Remove a token from the monitoring list."""
        if token in self.tokens_to_monitor:
            del self.tokens_to_monitor[token]

    def monitor(self):
        """Monitor tokens and execute callback on LTP changes."""
        while True:
            ltps = self._fetch_ltps()
            for token, ltp in ltps.items():
                if self.callback:
                    self.callback(token, ltp)
            sleep(10)

    def _fetch_ltp_for_token(self, token):
        """Fetch the LTP for a given token."""
        ltp = kite.ltp(token)  # assuming 'kite' is accessible here or you may need to pass it
        return ltp[str(token)]['last_price']

    def _fetch_ltps(self):
        """Fetch LTPs for all monitored tokens."""
        ltps = {}
        for token in self.tokens_to_monitor.keys():
            try:
                ltp_data = self._fetch_ltp_for_token(token)
                ltps[token] = ltp_data
            except Exception as e:
                print(f"Error fetching LTP for token {token}: {e}")
        return ltps
    
    def fetch(self):
        """Fetch and print LTPs for all monitored tokens and handle target/limit price scenarios."""
        while True:
            tokens = list(self.tokens_to_monitor.keys())
            print(f"fetching {tokens}")
            ltps = self._fetch_ltps()  # Using the class's method

            for token, ltp in ltps.items():
                print(f"The LTP for {token} is {ltp}")
                token_data = self.tokens_to_monitor[token]

                # Check if the target is not None and if LTP has reached or exceeded it
                if token_data['target'] is not None and ltp >= token_data['target']:
                    print(f"Target reached for token {token}! LTP is {ltp}.")
                    price_ref = token_data['order_details']['price_ref'] # TODO: This is related to MPwizard. Generalize this function
                    token_data['target'] += (price_ref / 2)  # Adjust target by half of price_ref
                    token_data['limit_prc'] += (price_ref / 2)  # Adjust limit_prc by half of price_ref
                    place_order.modify_orders(token,monitor=self)
                    print(f"New target for token {token} is {token_data['target']}.")
                    print(f"New limit price for token {token} is {token_data['limit_prc']}.")
                    message = f"Order modified! new target {token_data['target']}! and new stoploss is {token_data['limit_prc']} ."
                    discord.discord_bot(message,token_data['strategy'])

                # Check if the limit_prc is not None and if LTP has fallen below it
                elif token_data['limit_prc'] is not None and ltp <= token_data['limit_prc']:
                    print(f"Limit price reached for token {token}! LTP is {ltp}.") # TODO: send discord msg after sl
                    #remove the token from the list
                    self.remove_token(token)
                    
                # TODO: Check if there any open orders for the token at 3:10 pm if yes then cancel the order and sqaure off that order
                
            sleep(10)
