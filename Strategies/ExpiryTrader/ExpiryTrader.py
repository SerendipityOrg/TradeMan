import os
import sys
import datetime as dt
from time import sleep
from dotenv import load_dotenv

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.place_order as place_order
import Brokers.place_order_calc as place_order_calc
import Strategies.StrategyBase as StrategyBase
import MarketUtils.InstrumentBase as InstrumentBase
import Brokers.BrokerUtils.Broker as Broker

ENV_PATH = os.path.join(DIR_PATH, '.env')
_,STRATEGY_PATH = place_order_calc.get_strategy_json('ExpiryTrader')
load_dotenv(ENV_PATH)

class ExpiryTrader(StrategyBase.Strategy):
    def get_general_params(self):
        return self.general_params
    
    def get_entry_params(self):
        return self.entry_params
    
    def get_exit_params(self):
        return self.exit_params
    
# Testing the class with ExpiryTrader data
expiry_trader_obj = ExpiryTrader.read_strategy_json(STRATEGY_PATH)  
instrument_obj = InstrumentBase.Instrument()

hedge_transcation_type = expiry_trader_obj.get_general_params().get('HedgeTransactionType')
main_transcation_type = expiry_trader_obj.get_general_params().get('MainTransactionType')

# Extract strategy parameters
today_expiry_symbol, today_expiry_token = expiry_trader_obj.determine_expiry_index()
strategy_name = expiry_trader_obj.get_strategy_name()
prediction = expiry_trader_obj.get_general_params().get('TradeView')
order_type = expiry_trader_obj.get_general_params().get('OrderType')
segment_type = expiry_trader_obj.get_general_params().get('Segment')
product_type = expiry_trader_obj.get_general_params().get('ProductType')

strike_prc_multiplier = expiry_trader_obj.get_entry_params().get('StrikeMultiplier')
hedge_multiplier = expiry_trader_obj.get_entry_params().get('HedgeMultiplier')
stoploss_mutiplier = expiry_trader_obj.get_entry_params().get('SLMultipler')
desired_start_time_str = expiry_trader_obj.get_entry_params().get('EntryTime')

start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))

# Main logic
now = dt.datetime.now()
wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
if wait_time.total_seconds() > 0:
    print(f"Waiting for {wait_time} before starting the bot")
    sleep(wait_time.total_seconds())

main_strikeprc = expiry_trader_obj.calculate_current_atm_strike_prc(today_expiry_token, today_expiry_symbol, prediction, strike_prc_multiplier)
hedge_strikeprc = expiry_trader_obj.get_hedge_strikeprc(today_expiry_token, today_expiry_symbol, prediction, hedge_multiplier)
main_option_type = expiry_trader_obj.get_option_type(prediction, "OS")
hedge_option_type = expiry_trader_obj.get_hedge_option_type(prediction)

today_expiry = instrument_obj.get_expiry_by_criteria(today_expiry_symbol,main_strikeprc,main_option_type, "current_week")
main_exchange_token = instrument_obj.get_exchange_token_by_criteria(today_expiry_symbol,main_strikeprc, main_option_type,today_expiry)
hedge_exchange_token = instrument_obj.get_exchange_token_by_criteria(today_expiry_symbol,hedge_strikeprc,hedge_option_type, today_expiry)
trade_id = place_order_calc.get_trade_id(strategy_name, "entry")

print(f"Main Strike Price: {main_strikeprc}", f"main_option_type: {main_option_type}")
print(f"Hedge Strike Price: {hedge_strikeprc}", f"hedge_option_type: {hedge_option_type}")

orders_to_place = [
    {  
        "strategy": strategy_name,
        "exchange_token" : hedge_exchange_token,     
        "segment" : segment_type,
        "transaction_type": hedge_transcation_type,  
        "order_type" : order_type, 
        "product_type" : product_type,
        "order_mode" : ["Hedge"],
        "trade_id" : trade_id 
    },
    {
        "strategy": strategy_name,
        "exchange_token" : main_exchange_token,     
        "segment" : segment_type,
        "transaction_type": main_transcation_type, 
        "order_type" : order_type, 
        "product_type" : product_type,
        "stoploss_mutiplier": stoploss_mutiplier,
        "order_mode" : ["Main","SL"],
        "trade_id" : trade_id
    }
]
print(orders_to_place)
place_order.place_order_for_strategy(strategy_name,orders_to_place)


