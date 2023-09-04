import os
import json
import datetime as dt
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
        self.monitor = InstrumentMonitor()
        self.omkar = self._load_json_data(r'C:\Users\user\Desktop\Dev\UserProfile\Json\omkar.json')
        self.mood_data = self._load_json_data(r'Strategies\MPWizard\MPWizard.json')
        self.users = users
        self.instruments = instruments
        self.orders_placed_today = 0
        self.max_orders_per_day = 2  # Setting the daily limit to 2 signals.
        self.today_date = dt.date.today()
        self.done_for_the_day = False
        self.order_details_dict = {}

    @staticmethod
    def _load_json_data(filename):
        with open(filename, 'r') as file:
            return json.load(file)



    def _reset_daily_counters(self):
        self.today_date = dt.now().date()
        self.orders_placed_today = 0
        self.done_for_the_day = False


    def get_weekday_price_ref(self):
    # Load JSON data
        
        # Get the current weekday
        today = dt.date.today().strftime('%A')[:3]  # this will give you "Mon", "Tue", etc.

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

    
    def _process_instrument(self, ltp, instrument, prev_ltp, message_sent):
        if self.orders_placed_today >= self.max_orders_per_day:
            print("Daily signal limit reached. No more signals will be generated today.")
            return
        
        token = instrument.get_token()
        levels = instrument.get_trigger_points()
        name = instrument.get_name()
        
        cross_type = self._check_price_crossing(prev_ltp[name], ltp, levels)
        if cross_type:
            # Check if the daily limit has been reached
            self.orders_placed_today += 1
            mood_data_entry = self._get_mood_data_for_instrument(name)
            if not mood_data_entry:
                return

            option_type = self._determine_option_type(cross_type, mood_data_entry)
            if not option_type:
                return
            
            price_ref = self.get_weekday_price_ref()
            print(price_ref)
            
            print(f"{cross_type} at {ltp} for {name}!")
            
            order_details = {
                "base_symbol" : name,
                "option_type" : option_type,
                "strike_prc" : ltp,
                "stoploss_points" : price_ref
            }
            
            place_order.place_order_for_broker("MPWizard", order_details,monitor=self.monitor)
            
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
        def process_ltps(token, ltp):
            instrument = next((i for i in self.instruments if str(i.get_token()) == token), None)
            if instrument:
                self._process_instrument(ltp, instrument, prev_ltp, message_sent)
            
            print(f"The LTP for {token} is {ltp}")

        print("Monitoring started...")  

        prev_ltp = {instrument.get_name(): None for instrument in self.instruments}
        message_sent = {
            instrument.get_name(): {level: False for level in instrument.get_trigger_points()}
            for instrument in self.instruments
        }

        tokens = [str(instrument.get_token()) for instrument in self.instruments]
        monitor = self.monitor
        for token in tokens:
            monitor.add_token(token)
        monitor.callback = process_ltps
        

        while True:
            if dt.date.today() != self.today_date:
                self._reset_daily_counters()
            monitor.monitor()      
            sleep(10)
