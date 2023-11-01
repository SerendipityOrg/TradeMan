import os, sys
import urllib
from dotenv import load_dotenv
import numpy as np
import datetime as dt

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
weekly_expiry_type = instrument_obj.weekly_expiry_type()
monthly_expiry_type = instrument_obj.monthly_expiry_type()

weekly_expiry = instrument_obj.get_expiry_by_criteria(strategy_index,strikeprc,option_type, weekly_expiry_type)
monthly_expiry = instrument_obj.get_expiry_by_criteria(strategy_index,0,"FUT", monthly_expiry_type)


hedge_exchange_token = instrument_obj.get_exchange_token_by_criteria(strategy_index,strikeprc, option_type,weekly_expiry)   
futures_exchange_token = instrument_obj.get_exchange_token_by_criteria(strategy_index,futures_strikeprc, futures_option_type,monthly_expiry)
trade_id = place_order_calc.get_trade_id(strategy_name, "entry")

message = ( f"Trade for {dt.date.today()}\n"
            f"Direction : {prediction}\n"
            f"Future : {instrument_obj.get_trading_symbol_by_exchange_token(futures_exchange_token)}\n"
            f"Hedge : {instrument_obj.get_trading_symbol_by_exchange_token(hedge_exchange_token)}\n")

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