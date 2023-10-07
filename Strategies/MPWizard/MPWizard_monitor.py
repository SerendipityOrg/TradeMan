import os
import datetime as dt
from dotenv import load_dotenv
import sys

# Constants and paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BROKERS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', 'Brokers'))
UTILS_DIR = os.path.join(CURRENT_DIR, '..', '..', 'Utils') # TODO move these three lines to a general location

# Load environment variables
mpwizard_json = os.path.abspath(os.path.join(CURRENT_DIR, "MPWizard.json"))
env_file_path = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', 'Brokers', '.env'))
load_dotenv(env_file_path)
max_orders = os.getenv('max_orders')
omkar_json = os.getenv('omkar_json_filepath')

# Append paths to system path
sys.path.append(BROKERS_DIR)
import instrument_monitor as instrument_monitor
import place_order as place_order

sys.path.append(UTILS_DIR)
import general_calc as general_calc    

sys.path.append(os.path.join(UTILS_DIR, 'Discord'))
import discordchannels as discord

class OrderMonitor:
    """
    Class to monitor orders and handle trading signals.
    """
    def __init__(self, instruments):
        self.monitor = instrument_monitor.InstrumentMonitor()
        # self.omkar = self._load_json_data(omkar_json)
        self.mood_data = self._load_json_data(mpwizard_json)
        self.instruments = instruments
        self.orders_placed_today = 0
        self.max_orders_per_day = int(max_orders)
        self.today_date = dt.date.today()
        self.done_for_the_day = False
        self.order_details_dict = {}
        self.indices_triggered_today = set() 
        self.message_sent = {
            instrument.get_name(): {level: False for level in instrument.get_trigger_points()}
            for instrument in self.instruments
        }

    @staticmethod
    def _load_json_data(filename):
        """Load JSON data from a given filename."""
        return general_calc.read_json_file(filename)

    def _reset_daily_counters(self):
        """Reset daily counters for orders."""
        self.today_date = dt.now().date()
        self.orders_placed_today = 0
        self.done_for_the_day = False
        self.indices_triggered_today = set()

    def get_weekday_price_ref(self,name):
        """Get the price reference for the current weekday."""
        today = dt.date.today().strftime('%A')[:3]
        for index_data in self.mood_data["indices"]:
            index_name = index_data["name"]
            if index_name == name:
                return index_data["WeekdayPrcRef"].get(today)

    def _check_price_crossing(self, prev_ltp, ltp, levels):
        """Check if the price has crossed a certain level."""
        for level_name, level_price in levels.items():
            if prev_ltp is None:
                continue
            if prev_ltp < level_price <= ltp:
                return "UpCross", level_name
            elif prev_ltp > level_price >= ltp:
                return "DownCross", level_name
        return None, None

    def _process_instrument(self, ltp, instrument, prev_ltp, message_sent):
        """Process an instrument's data and handle trading signals."""
        if self.orders_placed_today >= self.max_orders_per_day:
            print("Daily signal limit reached. No more signals will be generated today.")
            return
        
        token = instrument.get_token()
        levels = instrument.get_trigger_points()
        name = instrument.get_name()

        #check if the index has been triggered today
        if name in self.indices_triggered_today:
            return
        
        cross_type, level_name = self._check_price_crossing(prev_ltp[name], ltp, levels)
        if cross_type and not self.message_sent[name][level_name]:
            mood_data_entry = self._get_mood_data_for_instrument(name)
            if not mood_data_entry:
                return #TODO add try exception for all the points of failure.

            option_type = self._determine_option_type(cross_type, mood_data_entry)
            if not option_type:
                return
            
            price_ref = self.get_weekday_price_ref(name)
            strikeprc = general_calc.round_strike_prc(ltp,name)
            
            print(f"{cross_type} at {ltp} for {name}!")
            
            order_details = {
                "transaction":"BUY",
                "base_symbol" : name,
                "option_type" : option_type,
                "strike_prc" : strikeprc,
                "stoploss_points" : price_ref
            }
            
            place_order.place_order_for_broker("MPWizard", order_details, monitor=self.monitor)
            self.indices_triggered_today.add(name) 
            
            message = f"{cross_type} at {ltp} for {name}!"
            discord.discord_bot(message,"MPWizard") 
            self.orders_placed_today += 1
            self.message_sent[name][level_name] = True
        prev_ltp[name] = ltp

    def _get_mood_data_for_instrument(self, name):
        """Get mood data for a given instrument."""
        return next((data for data in self.mood_data['indices'] if data['name'] == name), None)

    def _determine_option_type(self, cross_type, mood_data_entry):
        """Determine the option type based on cross type and mood data."""
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
        """Monitor index and handle trading signals."""
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
        } # This is will check if the message/ signal has been triggered for that level or not.

        tokens = [str(instrument.get_token()) for instrument in self.instruments]
        ltp_monitor = self.monitor
        for token in tokens:
            ltp_monitor.add_token(token)
        ltp_monitor.callback = process_ltps

        while True:
            if dt.date.today() != self.today_date:
                self._reset_daily_counters()
                self.message_sent = {
                    instrument.get_name(): {level: False for level in instrument.get_trigger_points()}
                    for instrument in self.instruments
                }
            ltp_monitor.monitor()      
            sleep(10)
