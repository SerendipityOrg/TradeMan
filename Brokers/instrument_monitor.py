from typing import Dict, Callable, Any
import time
from kiteconnect import KiteConnect
import os,sys

DIR_PATH = os.getcwd
sys.path.append(DIR_PATH)

import Brokers.BrokerUtils.Broker as Broker

api_key,access_token = Broker.get_primary_account()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)


class InstrumentMonitor:
    def __init__(self):
        self.instruments = {}
        self.callback = None

    def add_token(self, token: str, trigger_points: Dict[str, float], target: float = None, limit: float = None):
        """Add a token to be monitored.
        
        Args:
        token (str): The token of the instrument.
        trigger_points (dict): A dictionary of trigger points.
        target (float, optional): The target price.
        limit (float, optional): The limit price.
        """
        self.instruments[token] = {
            'trigger_points': trigger_points,
            'target': target,
            'limit': limit,
            'ltp': None  # Last Traded Price
        }

    def remove_token(self, token: str):
        """Remove a token from monitoring.
        
        Args:
        token (str): The token of the instrument.
        """
        if token in self.instruments:
            del self.instruments[token]

    def set_callback(self, callback: Callable[[str, Any], None]):
        """Set the callback function to be called on trigger events.
        
        Args:
        callback (callable): The callback function.
        """
        self.callback = callback

    def fetch_ltp(self, token: str) -> float:
        """Fetch the Last Traded Price (LTP) for a given token using Kite API.
        
        Args:
        token (str): The token of the instrument.
        
        Returns:
        float: The LTP of the instrument.
        """
        ltp = kite.ltp(token)  # assuming 'kite' is accessible here or you may need to pass it
        ltp = ltp[str(token)]['last_price']
        print(f"LTP for token {token}: {ltp}")
        return ltp

    def monitor(self):
        """Monitor the instruments and handle triggers."""
        for token, data in self.instruments.items():
            # Fetch LTP
            ltp = self.fetch_ltp(token)
            data['ltp'] = ltp

            # Check for trigger points
            for trigger_name, trigger_value in data['trigger_points'].items():
                if ltp == trigger_value and self.callback:
                    self.callback(token, {'type': 'trigger', 'name': trigger_name, 'value': ltp})

            # Check for target and limit
            if data['target'] and ltp >= data['target'] and self.callback:
                self.callback(token, {'type': 'target', 'value': ltp})

            if data['limit'] and ltp <= data['limit'] and self.callback:
                self.callback(token, {'type': 'limit', 'value': ltp})

    def start_monitoring(self, interval: int = 10):
        """Start the monitoring loop.
        
        Args:
        interval (int, optional): The interval between monitoring in seconds. Defaults to 10.
        """
        while True:
            self.monitor()
            time.sleep(interval)

