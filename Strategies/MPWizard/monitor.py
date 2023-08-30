import os
import json
import datetime
from datetime import datetime as dt
from kiteconnect import KiteConnect
# from telegram_bot import discord_bot
from mpw_place_orders import *
from MPWizard_calc import *
import sys

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
BROKERS_DIR = os.path.abspath(os.path.join(CURRENT_DIR,'..','..', 'Brokers'))
UTILS_DIR = os.path.join(CURRENT_DIR, '..','..','Utils')

sys.path.append(BROKERS_DIR)
from instrument_monitor import *
import place_order 

sys.path.append(UTILS_DIR)
import general_calc

class OrderMonitor:
    def __init__(self, users, instruments):
        self.omkar = self._load_json_data(r'C:\Users\user\Desktop\TradeMan\UserProfile\Json\omkar.json')
        self.mood_data = self._load_json_data(r'Strategies\MPWizard\MPWizard.json')
        self.users = users
        self.instruments = instruments
        self.orders_placed_today = 0
        self.today_date = dt.now().date()
        self.done_for_the_day = False
        self.order_details_dict = {}

    @staticmethod
    def _load_json_data(filename):
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # filepath = os.path.join(script_dir, '..', '..', 'UserProfile', 'Json', filename)
        # path = os.path.abspath(filepath)
        with open(filename, 'r') as file:
            return json.load(file)

    # def _initialize_kite(self, api_key, access_token):
    #     kite = KiteConnect(api_key=api_key)
    #     kite.set_access_token(access_token)
    #     return kite

    def _reset_daily_counters(self):
        self.today_date = dt.now().date()
        self.orders_placed_today = 0
        self.done_for_the_day = False


    def get_weekday_price_ref(self):
    # Load JSON data
        
        # Get the current weekday
        today = datetime.date.today().strftime('%A')[:3]  # this will give you "Mon", "Tue", etc.

        # Access WeekdayPrcRef
        for index_data in self.mood_data["indices"]:
            index_name = index_data["name"]
            weekday_price_ref = index_data["WeekdayPrcRef"].get(today)
            
        return weekday_price_ref

    
    def _check_price_crossing(self, prev_ltp, ltp, level_price):

        if prev_ltp is None:
            return None
        for level_name , level_price in level_price.items():
            if prev_ltp < level_price <= ltp:
                return "UpCross"
            elif prev_ltp > level_price >= ltp:
                return "DownCross"
        return None

    def _handle_order_placement(self, name, cross_type, ltp ):
        # calculate the strike prc and expiry date and send them to place_order and monitor tokens


        pass

    def _alert_via_telegram(self, message):
        mpwizard_discord_bot(message)

    # def _process_instrument(self, ltp, instrument, prev_ltp, message_sent):
    #     # ltp_data = kite.ltp(str(instrument.get_token()))
    #     # ltp = ltp_data[str(instrument.get_token())]['last_price']
    #     # print(ltp_data)
        

    #     if self.orders_placed_today < 2:
    #         levels = instrument.get_trigger_points()
    #         name = instrument.get_name()
            
    #         for level_name, level_price in levels.items():
    #             cross_type = self._check_price_crossing(prev_ltp[name], ltp, level_price)
    #             if cross_type and not message_sent[name][level_name]:
    #                 message_sent[name][level_name] = True
    #                 print(f"{cross_type} {level_name}: {ltp} for {name}!")
    #                 # Further handle order placement
    #                 self._handle_order_placement(name, cross_type, ltp)
    #                 # Alert via telegram or discord
    #                 message = f"{cross_type} {level_name}: {ltp} for {name}!"
    #                 self._alert_via_telegram(message)

    #     prev_ltp[instrument.get_name()] = ltp
    
    def _process_instrument(self, ltp, instrument, prev_ltp, message_sent):
        token = instrument.get_token()
        levels = instrument.get_trigger_points()
        name = instrument.get_name()
        

        cross_type = self._check_price_crossing(prev_ltp[name], ltp, levels)
        if cross_type:
            mood_data_entry = self._get_mood_data_for_instrument(name)
            if not mood_data_entry:
                return

            option_type = self._determine_option_type(cross_type, mood_data_entry)
            if not option_type:
                return
            
            price_ref = self.get_weekday_price_ref()
            
            
            
            order_details = {
                "base_symbol" : name,
                "option_type" : option_type,
                "strike_prc" : ltp,
                "stoploss_points" : price_ref
            }
            
            place_order.place_order_for_broker("MPWizard", order_details)
            
            
            
            message = f"{cross_type} at {ltp} for {name}! Trade? Reply 'call' or 'put' or 'pass'"
            # mpwizard_discord_bot(message)

        prev_ltp[name] = ltp

    def _get_mood_data_for_instrument(self, name):
        return next((data for data in self.mood_data['indices'] if data['name'] == name), None)

    def _determine_option_type(self, cross_type, mood_data_entry):
        ib_level = mood_data_entry['IBLevel']
        instru_mood = mood_data_entry['InstruMood']

        if ib_level == 'Big':
            return 'PE' if cross_type == 'UpCross' else 'CE'
        elif ib_level == 'Small':
            return 'PE' if cross_type == 'DownCross' else 'CE'
        elif ib_level == 'Medium':
            return 'PE' if instru_mood == 'Bearish' else 'CE'
        else:
            print(f"Unknown IB Level: {ib_level}")
        return None

    def monitor_index(self):
        # zerodha_account = self.omkar.get('zerodha', {})
        # api_key = zerodha_account.get('api_key')
        # access_token = zerodha_account.get('access_token')
        # kite = self._initialize_kite(api_key, access_token)
        print("Monitoring started...")

        prev_ltp = {instrument.get_name(): None for instrument in self.instruments}
        message_sent = {
            instrument.get_name(): {level: False for level in instrument.get_trigger_points()}
            for instrument in self.instruments
        }

        while True:
            if dt.now().date() != self.today_date:
                self._reset_daily_counters()

            tokens = [str(instrument.get_token()) for instrument in self.instruments]
            monitor = InstrumentMonitor(tokens)
            monitor.monitor()

            # while True:
            #     ltps = monitor._fetch_ltps()
            #     for token, ltp in ltps.items():
            #         # Assuming you have a _process_instrument function or similar to process each LTP
            #         instrument = next((i for i in self.instruments if str(i.get_token()) == token), None)
            #         if instrument:
            #             print(ltp, instrument.get_name())
            #             self._process_instrument(ltp, instrument, prev_ltp, message_sent)
        
            sleep(10)
