import os, sys
import urllib
from dotenv import load_dotenv
import numpy as np
import datetime as dt
from time import sleep

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

import Brokers.place_order as place_order
import Strategies.StrategyBase as StrategyBase
import MarketUtils.InstrumentBase as InstrumentBase
import Brokers.place_order_calc as place_order_calc
import Strategies.OvernightFutures.OvernightFutures_calc as OF_calc
import MarketUtils.Discord.discordchannels as discord

_,STRATEGY_PATH = place_order_calc.get_strategy_json('OvernightFutures')

hedge_transcation_type = "BUY"
futures_option_type = "FUT"
futures_strikeprc = 0

strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)
instrument_obj = InstrumentBase.Instrument()

strategy_name = strategy_obj.get_strategy_name()
expiry_token = strategy_obj.get_entry_params().get('Token')
strategy_index = strategy_obj.get_instruments()[0]

order_type = strategy_obj.get_general_params().get('OrderType')
segment_type = strategy_obj.get_general_params().get('Segment')
product_type = strategy_obj.get_general_params().get('ProductType')

def get_strikeprc(expiry_token,strategy_index,prediction):
    strike_prc_multiplier = strategy_obj.get_entry_params().get('SLMultipler')
    return strategy_obj.calculate_current_atm_strike_prc(expiry_token=expiry_token, base_symbol=strategy_index,prediction=prediction, strike_prc_multiplier=strike_prc_multiplier)


try:
    proxyServer = urllib.request.getproxies()['http']
except KeyError:
    proxyServer = ""

prediction = OF_calc.getNiftyPrediction(
                data= OF_calc.fetchLatestNiftyDaily(proxyServer=proxyServer), 
                proxyServer=proxyServer
            )
print(prediction)

strikeprc = get_strikeprc(expiry_token,strategy_index,prediction)
option_type = strategy_obj.get_option_type(prediction, "OS")
desired_start_time_str = strategy_obj.get_entry_params().get('EntryTime')
start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))

weekly_expiry_type = instrument_obj.weekly_expiry_type()
monthly_expiry_type = instrument_obj.monthly_expiry_type()

weekly_expiry = instrument_obj.get_expiry_by_criteria(strategy_index,strikeprc,option_type, weekly_expiry_type)
monthly_expiry = instrument_obj.get_expiry_by_criteria(strategy_index,0,"FUT", monthly_expiry_type)


hedge_exchange_token = instrument_obj.get_exchange_token_by_criteria(strategy_index,strikeprc, option_type,weekly_expiry)   
futures_exchange_token = instrument_obj.get_exchange_token_by_criteria(strategy_index,futures_strikeprc, futures_option_type,monthly_expiry)
trade_id = place_order_calc.get_trade_id(strategy_name, "entry")

future_trade_symbol = instrument_obj.get_trading_symbol_by_exchange_token(futures_exchange_token)
hedge_trade_symbol = instrument_obj.get_trading_symbol_by_exchange_token(hedge_exchange_token)

def message_for_orders(trade_type,prediction,main_trade_symbol,hedge_trade_symbol,weekly_expiry,monthly_expiry):
    if trade_type == 'Test':
        strategy_name = "Testorders"
    else:
        strategy_name = strategy_obj.get_strategy_name()

    message = ( f"Trade for {strategy_name}\n"
                f"Direction : {prediction}\n"
                f"Future : {main_trade_symbol} Expiry : {monthly_expiry}\n"
                f"Hedge : {hedge_trade_symbol} Expiry : {weekly_expiry}\n")
    print(message)
    discord.discord_bot(message, strategy_name)

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
        "exchange_token" : futures_exchange_token,     
        "segment" : segment_type,
        "transaction_type": strategy_obj.get_transaction_type(prediction), 
        "order_type" : order_type, 
        "product_type" : product_type,
        "order_mode" : ["Main"],
        "trade_id" : trade_id
    }
]


def main():
    global hedge_exchange_token, futures_exchange_token
    now = dt.datetime.now()

    if now.time() < dt.time(9, 0):
        print("Time is before 9:00 AM, placing test orders.")
        message_for_orders("Test",prediction,future_trade_symbol,hedge_trade_symbol,weekly_expiry,monthly_expiry)
    else:
        wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
        if wait_time.total_seconds() > 0:
            print(f"Waiting for {wait_time} before starting the bot")
            sleep(wait_time.total_seconds())
        
        message_for_orders("Live",prediction,future_trade_symbol,hedge_trade_symbol,weekly_expiry,monthly_expiry)
        print(orders_to_place)
        place_order.place_order_for_strategy(strategy_name,orders_to_place)


        hedge_exchange_token = np.int64(hedge_exchange_token)
        hedge_exchange_token = int(hedge_exchange_token)

        futures_exchange_token = np.int64(futures_exchange_token)
        futures_exchange_token = int(futures_exchange_token)


        extra_information = strategy_obj.get_extra_information()

        extra_information['hedge_exchange_token'] = hedge_exchange_token
        extra_information['futures_exchange_token'] = futures_exchange_token
        extra_information['prediction'] = prediction 

        strategy_obj.set_extra_information(extra_information)

        strategy_obj.write_strategy_json(STRATEGY_PATH)


if __name__ == "__main__":
    main()