from typing import Dict, Callable, Any
from time import sleep
from kiteconnect import KiteConnect
import os,sys
from MarketUtils.InstrumentBase import Instrument
import threading

DIR_PATH = os.getcwd
sys.path.append(DIR_PATH)

import Brokers.BrokerUtils.Broker as Broker

api_key,access_token = Broker.get_primary_account()
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)


class InstrumentMonitor:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(InstrumentMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Check if the instance is already initialized
            self.lock = threading.Lock()
            self.tokens_to_monitor = {}
            self.callback = None
            self.monitor_thread = None
            self._initialized = True  # Set the initialized flag

    def start_monitoring(self):
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self.monitor)
            self.monitor_thread.daemon = False
            self.monitor_thread.start()

    def add_token(self, token: str = None, trigger_points: Dict[str, float] = None, order_details: Dict = None,ib_level=None):
        """Add a token to be monitored.
        
        Args:
        token (str): The token of the instrument.
        trigger_points (dict): A dictionary of trigger points.
        target (float, optional): The target price.
        limit (float, optional): The limit price.
        """
        if order_details:
            instrument_obj = Instrument()
            token = str(instrument_obj.get_token_by_exchange_token(order_details.get('exchange_token')))
            target = order_details.get('target')
            limit = order_details.get('limit_prc')
        else:
            target = None
            limit = None
        
        if token in self.tokens_to_monitor:
            print("Token already present:", token)
            return
        
        self.tokens_to_monitor[token] = {
            'trigger_points': trigger_points or {},
            'target': target,
            'limit': limit,
            'ltp': None,  # Last Traded Price
            'order_details' : order_details,
            'ib_level': ib_level
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

    def fetch_ltp(self, token):
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
                ltp_data = self.fetch_ltp(token)
                ltps[token] = ltp_data
            except Exception as e:
                print(f"Error fetching LTP for token {token}: {e}")
        return ltps


    def monitor(self):
        while True:
            tokens = list(self.tokens_to_monitor.keys())
            print(f"Monitoring tokens: {tokens}")
            for token in tokens:
                try:
                    ltp = self.fetch_ltp(token)
                    print(f"The LTP for {token} is {ltp}")
                    data = self.tokens_to_monitor[token]
                    self._process_token(token, ltp, data)
                except Exception as e:
                    print(f"Error processing token {token}: {e}")
            sleep(10)

    def _process_token(self, token, ltp, data):
        order_details = data.get('order_details')
        trigger_points = data.get('trigger_points')
        if trigger_points:
            # Initialize trigger states if not already done
            if 'IBHigh_triggered' not in data:
                data['IBHigh_triggered'] = False
            if 'IBLow_triggered' not in data:
                data['IBLow_triggered'] = False

            # Check for upward crossing of IBHigh
            if ltp >= data['trigger_points']['IBHigh'] and not data['IBHigh_triggered']:
                if self.callback:
                    self.callback(token, {'type': 'trigger', 'name': 'IBHigh', 'value': ltp, 'ib_level': data['ib_level']})
                data['IBHigh_triggered'] = True

            # Check for downward crossing of IBLow
            if ltp <= data['trigger_points']['IBLow'] and not data['IBLow_triggered']:
                if self.callback:
                    self.callback(token, {'type': 'trigger', 'name': 'IBLow', 'value': ltp, 'ib_level': data['ib_level']})
                data['IBLow_triggered'] = True

        if 'target_triggered' not in data:
            data['target_triggered'] = False
        if 'limit_triggered' not in data:
            data['limit_triggered'] = False

        # Check for target and limit
        if data['order_details']['target'] and ltp >= data['order_details']['target'] and self.callback:
            self.callback(token, {'type': 'target', 'value': ltp},order_details=order_details)
            data['target_triggered'] = True

        if data['order_details']['limit_prc'] and ltp <= data['order_details']['limit_prc'] and self.callback:
            self.callback(token, {'type': 'limit', 'value': ltp},order_details=order_details)
            data['limit_triggered'] = True

            

