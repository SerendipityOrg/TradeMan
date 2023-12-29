import json,os,sys
from kiteconnect import KiteConnect
import datetime as dt
import pandas as pd

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
fno_info_path = os.path.join(DIR_PATH, 'fno_info.csv')

from Brokers.BrokerUtils import Broker
import MarketUtils.general_calc as general_calc


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
        self.extra_information = strategy_data.get('ExtraInformation', {})
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
        try:
            strategy_data = general_calc.read_json_file(file_path)
        except (FileNotFoundError, IOError, json.JSONDecodeError):
            # Handle file not found, I/O errors, or JSON parsing errors
            strategy_data = {}
        
        return cls(strategy_data)
    
    def write_strategy_json(self, file_path):
        strategy_data = {
            'StrategyName': self.strategy_name,
            'Description': self.description,
            'Instruments': self.instruments,
            'NextTradeId': self.next_trade_id,
            'GeneralParams': self.general_params,
            'EntryParams': self.entry_params,
            'ExitParams': self.exit_params,
            'TodayOrders': self.today_orders,
            'ExtraInformation': self.extra_information,
            'SignalEntry': self.signal_entry
        }
        general_calc.write_json_file(file_path, strategy_data)
    
    #TODD add a function to get exhange token from instrument.csv
    #TODO add a function to return the weekly expiry for a token 
    #TODO add a function to return the monthly expiry for a token
    #TODO add a function to return the next week expiry for a token
    
    
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
    
    def get_transaction_type(self,prediction):
        if prediction == 'Bearish':
            return 'SELL' 
        elif prediction == 'Bullish':
            return 'BUY'
        else:
            print("Invalid option mode")
    
    def get_single_ltp(self,token):
        kite = KiteConnect(api_key=Broker.get_primary_account()[0]) #####TODO pass directly apikey and accesstoken
        kite.set_access_token(access_token=Broker.get_primary_account()[1])
        ltp = kite.ltp(token)  # assuming 'kite' is accessible here or you may need to pass it
        return ltp[str(token)]['last_price']
    
    def get_token_from_info(self,base_symbol):
        fno_info_df = pd.read_csv(fno_info_path)
        token = fno_info_df.loc[fno_info_df['base_symbol'] == base_symbol, 'token'].values
        if len(token) == 0:
            return f"{base_symbol} not found"
        return token[0]
    
    def determine_expiry_index(self,day):
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

    def round_strike_prc(self,ltp,base_symbo): 
        strike_step = self.get_strike_step(base_symbo)
        return round(ltp / strike_step) * strike_step
    
    def get_strike_step(self, base_symbol):
        strike_step_df = pd.read_csv(fno_info_path)
        strike_step = strike_step_df.loc[strike_step_df['base_symbol'] == base_symbol, 'strike_step_size'].values[0]
        return strike_step

    def calculate_current_atm_strike_prc(self,base_symbol, token = None, prediction=None, strike_prc_multiplier=None):
        if token is None:
            token = int(self.get_token_from_info(base_symbol))
        ltp = self.get_single_ltp(token)
        base_strike = self.round_strike_prc(ltp, base_symbol)
        multiplier = self.get_strike_step(base_symbol)
        if strike_prc_multiplier:
            adjustment = multiplier * (strike_prc_multiplier if prediction == 'Bearish' else -strike_prc_multiplier)
            return base_strike + adjustment
        else:
            return base_strike
        
    def get_hedge_strikeprc(self,base_symbol,token, prediction, hedge_multiplier): 
        ltp = self.get_single_ltp(token)
        strike_prc = self.round_strike_prc(ltp, base_symbol)
        strike_prc_multiplier = self.get_strike_step(base_symbol)
        bear_strikeprc = strike_prc + (hedge_multiplier * strike_prc_multiplier)
        bull_strikeprc = strike_prc - (hedge_multiplier * strike_prc_multiplier)
        hedge_strikeprc = bear_strikeprc if prediction == 'Bearish' else bull_strikeprc
        return hedge_strikeprc
    
    def get_square_off_transaction(self,prediction):
        if prediction == 'Bearish':
            return 'BUY'
        elif prediction == 'Bullish':
            return'SELL'
        else:
            print("Invalid prediction")

    def get_strike_multiplier(self,base_symbol):
        fno_info_df = pd.read_csv(fno_info_path)
        strike_multiplier = fno_info_df.loc[fno_info_df['base_symbol'] == base_symbol, 'strike_multiplier'].values
        if len(strike_multiplier) == 0:
            return f"{base_symbol} not found"
        return strike_multiplier[0]
    
    def get_hedge_multiplier(self,base_symbol):
        fno_info_df = pd.read_csv(fno_info_path)
        hedge_multiplier = fno_info_df.loc[fno_info_df['base_symbol'] == base_symbol, 'hedge_multiplier'].values
        if len(hedge_multiplier) == 0:
            return f"{base_symbol} not found"
        return hedge_multiplier[0]
    
    def get_stoploss_multiplier(self,base_symbol):
        fno_info_df = pd.read_csv(fno_info_path)
        stoploss_multiplier = fno_info_df.loc[fno_info_df['base_symbol'] == base_symbol, 'stoploss_multiplier'].values
        if len(stoploss_multiplier) == 0:
            return f"{base_symbol} not found"
        return stoploss_multiplier[0]