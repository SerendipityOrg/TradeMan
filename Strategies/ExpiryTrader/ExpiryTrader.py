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
import MarketUtils.Calculations.qty_calc as qty_calc
import MarketUtils.Discord.discordchannels as discord 
import MarketUtils.general_calc as general_calc 

ENV_PATH = os.path.join(DIR_PATH, '.env')
_,STRATEGY_PATH = general_calc.get_strategy_json('ExpiryTrader')
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

def calculate_qty(main_exchange_token,base_symbol):
    token = instrument_obj.get_token_by_exchange_token(main_exchange_token)
    ltp = expiry_trader_obj.get_single_ltp(token)
    qty_calc.update_qty_during_entry(ltp,expiry_trader_obj.get_strategy_name(),base_symbol)


# Extract strategy parameters
day = dt.datetime.today().weekday()
base_symbol, today_expiry_token = expiry_trader_obj.determine_expiry_index(day)
strategy_name = expiry_trader_obj.get_strategy_name()
prediction = expiry_trader_obj.get_general_params().get('TradeView')
order_type = expiry_trader_obj.get_general_params().get('OrderType')
segment_type = expiry_trader_obj.get_general_params().get('Segment')
product_type = expiry_trader_obj.get_general_params().get('ProductType')

strike_prc_multiplier = expiry_trader_obj.get_strike_multiplier(base_symbol)
hedge_multiplier = expiry_trader_obj.get_hedge_multiplier(base_symbol)
stoploss_mutiplier = expiry_trader_obj.get_stoploss_multiplier(base_symbol)
desired_start_time_str = expiry_trader_obj.get_entry_params().get('EntryTime')

start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))

main_strikeprc = expiry_trader_obj.calculate_current_atm_strike_prc(base_symbol,today_expiry_token, prediction, strike_prc_multiplier)
hedge_strikeprc = expiry_trader_obj.get_hedge_strikeprc(base_symbol, today_expiry_token, prediction, hedge_multiplier)
main_option_type = expiry_trader_obj.get_option_type(prediction, "OS")
hedge_option_type = expiry_trader_obj.get_hedge_option_type(prediction)

today_expiry = instrument_obj.get_expiry_by_criteria(base_symbol,main_strikeprc,main_option_type, "current_week")
main_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol,main_strikeprc, main_option_type,today_expiry)
hedge_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol,hedge_strikeprc,hedge_option_type, today_expiry)
trade_id = place_order_calc.get_trade_id(strategy_name, "entry")


main_trade_symbol = instrument_obj.get_trading_symbol_by_exchange_token(main_exchange_token)
hedge_trade_symbol = instrument_obj.get_trading_symbol_by_exchange_token(hedge_exchange_token)

orders_to_place = [
    {  
        "strategy": strategy_name,
        "base_symbol": base_symbol,
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
        "base_symbol": base_symbol,
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

def message_for_orders(trade_type,prediction,main_trade_symbol,hedge_trade_symbol):
    if trade_type == "Test":
        strategy_name = "TestOrders"
    else:
        strategy_name = expiry_trader_obj.get_strategy_name()

    message = ( f"{trade_type} Trade for {expiry_trader_obj.get_strategy_name()}\n"
            f"Direction : {prediction}\n"
            f"Main Trade : {main_trade_symbol}\n"
            f"Hedge Trade {hedge_trade_symbol} \n")    
    print(message)
    discord.discord_bot(message, strategy_name)
    

def main():
    now = dt.datetime.now()

    if now.date() in general_calc.holidays:
        print("Skipping execution as today is a holiday.")
        return

    if now.time() < dt.time(9, 0):
        print("Time is before 9:00 AM, placing test orders.")
        message_for_orders("Test",prediction,main_trade_symbol,hedge_trade_symbol)
    else:
        wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
        if wait_time.total_seconds() > 0:
            print(f"Waiting for {wait_time} before starting the bot")
            sleep(wait_time.total_seconds())
        
        print(orders_to_place)
        calculate_qty(main_exchange_token,base_symbol)
        message_for_orders("Live",prediction,main_trade_symbol,hedge_trade_symbol)
        place_order.place_order_for_strategy(strategy_name,orders_to_place)



if __name__ == "__main__":
    main()
