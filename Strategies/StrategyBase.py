import json,os,sys
from kiteconnect import KiteConnect
import datetime as dt

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROKERS_DIR = os.path.join(ROOT_DIR, '..', 'Brokers')
sys.path.append(BROKERS_DIR)

import Broker as Broker



class Strategy:
    def __init__(self, strategy_data):
        self.strategy_name = strategy_data.get('StrategyName', None)
        self.description = strategy_data.get('Description', None)
        self.instruments = strategy_data.get('Instruments', [])
        self.next_trade_id = strategy_data.get('NextTradeId', None)
        self.general_params = strategy_data.get('GeneralParams', {})
        self.entry_params = strategy_data.get('EntryParams', {})
        self.exit_params = strategy_data.get('ExitParams', {})
        self.today_orders = strategy_data.get('TodayOrders', [])
        self.extra_information = strategy_data.get('ExtraInformation', strategy_data.get('ExtarInformation', {}))  # Handling the typo
        self.signal_entry = strategy_data.get('SignalEntry', {})
    
    # Getter methods
    def get_strategy_name(self):
        return self.strategy_name
    
    def get_description(self):
        return self.description
    
    def get_instruments(self):
        return self.instruments
    
    def get_next_trade_id(self):
        return self.next_trade_id
    
    def get_general_params(self):
        return self.general_params
    
    def get_entry_params(self):
        return self.entry_params
    
    def get_exit_params(self):
        return self.exit_params
    
    def get_today_orders(self):
        return self.today_orders
    
    def get_extra_information(self):
        return self.extra_information
    
    def get_signal_entry(self):
        return self.signal_entry
    
    # Setter methods
    def set_strategy_name(self, name):
        self.strategy_name = name
    
    def set_description(self, desc):
        self.description = desc
    
    def set_instruments(self, instruments):
        self.instruments = instruments
    
    def set_next_trade_id(self, trade_id):
        self.next_trade_id = trade_id
    
    def set_general_params(self, params):
        self.general_params = params
    
    def set_entry_params(self, params):
        self.entry_params = params
    
    def set_exit_params(self, params):
        self.exit_params = params
    
    def set_today_orders(self, orders):
        self.today_orders = orders
    
    def set_extra_information(self, info):
        self.extra_information = info
    
    def set_signal_entry(self, signal):
        self.signal_entry = signal

    @classmethod
    def read_strategy_json(cls, file_path):
        with open(file_path, "r") as file:
            strategy_data = json.load(file)
        return cls(strategy_data)
    
    def get_option_type(self,prediction,strategy_option_mode):
        if strategy_option_mode == "OS":
            return 'CE' if prediction == 'Bearish' else 'PE'
        elif strategy_option_mode == "OB":
            return 'CE' if prediction == 'Bullish' else 'PE'
        else:
            print("Invalid option mode")
    
    def get_hedge_option_type(self,prediction):
        if prediction == 'Bearish':
            return 'CE' 
        elif prediction == 'Bullish':
            return 'PE'
        else:
            print("Invalid option mode")
    
    def get_single_ltp(self,token):
        kite = KiteConnect(api_key=Broker.get_primary_account()[0]) #####TODO pass directly apikey and accesstoken
        kite.set_access_token(access_token=Broker.get_primary_account()[1])
        return kite.ltp(token)[token]['last_price']
    
    def determine_expiry_index(self):
        day = dt.datetime.today().weekday()
        if day == 0:  # Monday
            return "MIDCPNIFTY","288009"
        elif day == 1:  # Tuesday
            return "FINNIFTY","257801"
        elif day == 2:  # Wednesday
            return "BANKNIFTY","260105"
        elif day == 3:  # Thursday
            return "NIFTY","256265"
        elif day == 4:  # Friday
            return "SENSEX","265"
        else:
            return "No expiry today"

    def round_strike_prc(self,ltp, base_symbol): #TODO: Add support for other base symbols using a csv list
        print(ltp, base_symbol)
        if base_symbol == 'NIFTY' or base_symbol == 'FINNIFTY' or base_symbol == 'MIDCPNIFTY':
            return round(ltp / 50) * 50
        if base_symbol == 'BANKNIFTY' or base_symbol == 'SENSEX':
            return round(ltp / 100) * 100
    
    def get_strike_distance_multiplier(self,base_symbol): #TODO: Add support for other base symbols using a csv list
        if base_symbol == 'NIFTY' or base_symbol == 'FINNIFTY' or base_symbol == 'MIDCPNIFTY':
            return 50
        if base_symbol == 'BANKNIFTY' or base_symbol == 'SENSEX':
            return 100
       
    def calculate_strike_prc(self,expiry_token, base_symbol, prediction, strike_prc_multiplier):
        ltp = self.get_single_ltp(expiry_token)
        base_strike = self.round_strike_prc(ltp, base_symbol)
        multiplier = self.get_strike_distance_multiplier(base_symbol)
        adjustment = multiplier * (strike_prc_multiplier if prediction == 'Bearish' else -strike_prc_multiplier)
        return base_strike + adjustment
    
    def get_hedge_strikeprc(self,expiry_token, base_symbol, prediction, hedge_multiplier): #TODO get_strike_distance_multiplier as global variable
        ltp = self.get_single_ltp(expiry_token)
        strike_prc = self.round_strike_prc(ltp, base_symbol)
        strike_prc_multiplier = self.get_strike_distance_multiplier(base_symbol)
        bear_strikeprc = strike_prc + (hedge_multiplier * strike_prc_multiplier)
        bull_strikeprc = strike_prc - (hedge_multiplier * strike_prc_multiplier)
        hedge_strikeprc = bear_strikeprc if prediction == 'Bearish' else bull_strikeprc
        return hedge_strikeprc
