from datetime import datetime
from dotenv import load_dotenv
import os 
import threading
from kiteconnect import KiteConnect
import sys
from time import sleep

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order as place_order
import Brokers.BrokerUtils.Broker as Broker
from MarketUtils.InstrumentBase import Instrument

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

api_key,access_token = Broker.get_primary_account()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

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
        
    def add_token(self, order_details=None,token=None):
        """Add a token to the monitoring list."""
        instrument_obj = Instrument()
        if order_details:
            token = instrument_obj.get_token_by_exchange_token(order_details.get('exchange_token'))

        if token not in self.tokens_to_monitor:
            print(f"Added token {token} to monitor. Current tokens: {self.tokens_to_monitor}")
        else:
            print(f"Token {token} is already being monitored.")
            
        self.tokens_to_monitor[token] = {
            'order_details': order_details
        }
        # Print the price_ref from the order_details
        if self.tokens_to_monitor[token] is not None :
            print("tokens",self.tokens_to_monitor.keys())
            # print("price_ref:" ,self.tokens_to_monitor[token])
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
            print("in",self.tokens_to_monitor.keys())
            print(f"Fetching LTP for token {token}")
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
                order_details = token_data['order_details']

                # Check if the target is not None and if LTP has reached or exceeded it
                if order_details['target'] is not None and ltp >= order_details['target']:
                    print(f"Target reached for token {token}! LTP is {ltp}.")
                    target,limit_prc = place_order.place_tsl(order_details)
                    print(f"New target for token {token} is {target}.")
                    print(f"New limit price for token {token} is {limit_prc}.")
                    message = f"Order modified! new target {target}! and new stoploss is {limit_prc} ."
                    # discord.discord_bot(message,token_data['strategy'])

                # Check if the limit_prc is not None and if LTP has fallen below it
                elif order_details['limit_prc'] is not None and ltp <= order_details['limit_prc']:
                    print(f"Limit price reached for token {token}! LTP is {ltp}.") # TODO: send discord msg after sl
                    #remove the token from the list
                    self.remove_token(token)
                
                # #check if the time is 3:10 pm and if yes then remove the token from the list
                # elif datetime.now().strftime("%H:%M:%S") >= "15:57:00":
                #     print("Time is 3:10 pm")
                #     place_order.exit_order_details(token,monitor=self)
                #     self.remove_token(token)
                    
                # TODO: Check if there any open orders for the token at 3:10 pm if yes then cancel the order and sqaure off that order
                
            sleep(10)
