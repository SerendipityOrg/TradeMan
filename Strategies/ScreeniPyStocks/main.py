import os,sys
from dotenv import load_dotenv
import datetime as dt
from time import sleep

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.place_order as place_order
import Brokers.place_order_calc as place_order_calc
import Strategies.StrategyBase as StrategyBase
import MarketUtils.InstrumentBase as InstrumentBase
import MarketUtils.Calculations.qty_calc as qty_calc
import MarketUtils.Discord.discordchannels as discord 
import MarketUtils.general_calc as general_calc 
import pystock_calc

ENV_PATH = os.path.join(DIR_PATH, '.env')
_,STRATEGY_PATH = place_order_calc.get_strategy_json('PyStocks')
load_dotenv(ENV_PATH)

class PyStocks(StrategyBase.Strategy):
    def get_general_params(self):
        return self.general_params
    
    def get_entry_params(self):
        return self.entry_params
    
    def get_exit_params(self):
        return self.exit_params

pystocks_obj = PyStocks.read_strategy_json(STRATEGY_PATH)  

def get_symbols():
    shortterm_symbols,midterm_symbols,longterm_symbols = pystock_calc.get_symbols()
    return shortterm_symbols,midterm_symbols,longterm_symbols

strategy_name = pystocks_obj.get_strategy_name()
prediction = pystocks_obj.get_general_params().get('TradeView')
order_type = pystocks_obj.get_general_params().get('OrderType')
segment_type = pystocks_obj.get_general_params().get('Segment')
product_type = pystocks_obj.get_general_params().get('ProductType')
desired_start_time_str = pystocks_obj.get_entry_params().get('EntryTime')

start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))
trade_id = place_order_calc.get_trade_id(strategy_name, "entry")

def order():
    shortterm_symbols,midterm_symbols,longterm_symbols = get_symbols()
    for symbol in shortterm_symbols:
         orders_to_place = [
             {
                "strategy": strategy_name,
                "base_symbol": symbol,   
                "segment" : segment_type,
                "order_type" : order_type, 
                "product_type" : product_type,
                "trade_id" : trade_id 
             }
         ]
         place_order.place_order_for_strategy(strategy_name,orders_to_place)
    for symbol in midterm_symbols:
        orders_to_place = [
             {
                "strategy": strategy_name,
                "base_symbol": symbol,   
                "segment" : segment_type,
                "order_type" : order_type, 
                "product_type" : product_type,
                "trade_id" : trade_id 
             }
         ]
        place_order.place_order_for_strategy(strategy_name,orders_to_place)
    for symbol in longterm_symbols:
        orders_to_place = [
             {
                "strategy": strategy_name,
                "base_symbol": symbol,   
                "segment" : segment_type,
                "order_type" : order_type, 
                "product_type" : product_type,
                "trade_id" : trade_id 
             }
         ]
        place_order.place_order_for_strategy(strategy_name,orders_to_place)
def main():
    """
    Main function to execute the trading strategy.
    """
    now = dt.datetime.now()

    if now.date() in general_calc.holidays:
        print("Skipping execution as today is a holiday.")
        return
    
    if now.time() < dt.time(9, 0):
        print("Time is before 8:40 AM, placing test orders.")
        #test order Module here
    else:
        wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
        if wait_time.total_seconds() > 0:
            print(f"Waiting for {wait_time} before starting the bot")
            sleep(wait_time.total_seconds())
        order()

if __name__ == "__main__":
    main()

