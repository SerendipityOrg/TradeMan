import os,json
import datetime as dt
from dotenv import load_dotenv
import sys
from typing import Optional, Dict, List


DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)
max_orders = os.getenv('max_orders')
omkar_json = os.getenv('omkar_json_filepath')

import Brokers.place_order_calc as place_order_calc
import Brokers.place_order as place_order
import MarketUtils.general_calc as general_calc
import MarketUtils.Discord.discordchannels as discord
import MarketUtils.InstrumentBase as InstrumentBase
import Strategies.StrategyBase as StrategyBase

_,mpwizard_json = place_order_calc.get_strategy_json('MPWizard')
instrument_obj = InstrumentBase.Instrument()
strategy_obj = StrategyBase.Strategy.read_strategy_json(mpwizard_json)


class MPWInstrument:
    def __init__(self, name, token, trigger_points, price_ref):
        self.name = name
        self.token = token
        self.trigger_points = trigger_points
        self.price_ref = price_ref
    
    def get_name(self):
        return self.name
    
    def get_token(self):
        return self.token
    
    def get_trigger_points(self):
        return self.trigger_points
    
    def get_price_ref(self):
        return self.price_ref


class OrderMonitor:
    def __init__(self, json_data, max_orders):
        self.monitor = place_order_calc.monitor()
        self.mood_data = self._load_json_data(json_data)
        self.instruments = self._create_instruments(self.mood_data['EntryParams'])
        self.orders_placed_today = 0
        self.max_orders_per_day = max_orders
        self.today_date = dt.date.today()
        self.done_for_the_day = False
        self.indices_triggered_today = set()
        self.message_sent = {
            instrument.get_name(): {level: False for level in instrument.get_trigger_points()}
            for instrument in self.instruments
        }
        self._add_tokens_from_json()

    def _add_tokens_from_json(self):
        indices_tokens = self.mood_data['GeneralParams']['IndicesTokens']
        for token in indices_tokens.values():
            self.monitor.add_token(token=str(token))

    @staticmethod
    def _load_json_data(json_data):
        return json.loads(json_data)

    def _create_instruments(self, instruments_data):
        instruments = []
        for name, data in instruments_data.items():
            # Skip entries that do not have the 'TriggerPoints' key
            if 'TriggerPoints' not in data or 'PriceRef' not in data:
                continue
            
            token = self.mood_data['GeneralParams']['IndicesTokens'].get(name)
            if token is None:
                print(f"Warning: Token not found for instrument {name}")
                continue

            trigger_points = data['TriggerPoints']
            price_ref = data['PriceRef']
            instrument = MPWInstrument(name, token, trigger_points,price_ref)
            instruments.append(instrument)
        return instruments

    def _reset_daily_counters(self):
        self.today_date = dt.date.today()
        self.orders_placed_today = 0
        self.done_for_the_day = False
        self.indices_triggered_today = set()

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

    def create_order_details(self,name,cross_type,ltp,price_ref):
        mood_data_entry = self._get_mood_data_for_instrument(name)
        if not mood_data_entry:
            return #TODO add try exception for all the points of failure.

        option_type = self._determine_option_type(cross_type, mood_data_entry)
        if not option_type:
            return
        
        strikeprc = general_calc.round_strike_prc(ltp,name)
        expiry_date = instrument_obj.get_expiry_by_criteria(name,strikeprc,option_type,'current_week')
        exchange_token = instrument_obj.get_exchange_token_by_criteria(name,strikeprc,option_type,expiry_date)
        order_details = [
        {  
        "strategy": strategy_obj.get_strategy_name(),
        "exchange_token" : exchange_token,     
        "segment" : strategy_obj.get_general_params().get('Segment'),
        "transaction_type": strategy_obj.get_general_params().get('TransactionType'),  
        "order_type" : strategy_obj.get_general_params().get('OrderType'), 
        "product_type" : strategy_obj.get_general_params().get('ProductType'),
        "price_ref" : price_ref,
        "order_mode" : ["Main","Trailing"],
        "trade_id" : place_order_calc.get_trade_id(strategy_obj.get_strategy_name(), "entry")
        }]
        return order_details

    def _process_instrument(self, ltp, instrument, prev_ltp, message_sent):
        print("here")
        """Process an instrument's data and handle trading signals."""
        if self.orders_placed_today >= self.max_orders_per_day:
            print("Daily signal limit reached. No more signals will be generated today.")
            return
        
        token = instrument.get_token()
        levels = instrument.get_trigger_points()
        name = instrument.get_name()
        price_ref = instrument.get_price_ref()

        #check if the index has been triggered today
        if name in self.indices_triggered_today:
            return
        
        cross_type, level_name = self._check_price_crossing(prev_ltp[name], ltp, levels)
        if cross_type and not self.message_sent[instrument.get_name()][level_name]:
            order_to_place = self.create_order_details(name,cross_type,ltp,price_ref)
            print("in",order_to_place)
            place_order.place_order_for_strategy(strategy_obj.get_strategy_name(),order_to_place)  
            print(f"{cross_type} at {ltp} for {name}!")
            
            
            # place_order.place_order_for_broker("MPWizard", order_details, monitor=self.monitor)
            self.indices_triggered_today.add(name) 
            
            message = f"{cross_type} {self._get_mood_data_for_instrument(name)['IBLevel']} {self.mood_data['GeneralParams']['TradeView']} at {ltp} for {name}!"
            print(message)
            # discord.discord_bot(message,"MPWizard") 
            self.orders_placed_today += 1
            self.message_sent[name][level_name] = True
        prev_ltp[name] = ltp

    def _get_mood_data_for_instrument(self, name):
        return self.mood_data['EntryParams'].get(name)

    def _determine_option_type(self, cross_type, mood_data_entry):
        """Determine the option type based on cross type and mood data."""
        ib_level = mood_data_entry['IBLevel']
        instru_mood = self.mood_data['GeneralParams']['TradeView']

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
            ltp_monitor.add_token(token=token)
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
