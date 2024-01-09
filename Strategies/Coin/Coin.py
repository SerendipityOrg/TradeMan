import random,time
import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.place_order as place_order
import Strategies.StrategyBase as StrategyBase
import MarketUtils.InstrumentBase as InstrumentBase
import Brokers.place_order_calc as place_order_calc
import MarketUtils.general_calc as general_calc
import MarketUtils.Calculations.qty_calc as qty_calc
import MarketUtils.Discord.discordchannels as discord 

_,coin_json = general_calc.get_strategy_json('Coin')
strategy_obj = StrategyBase.Strategy.read_strategy_json(coin_json)
instrument_obj = InstrumentBase.Instrument()

def flip_coin():
    # Randomly choose between 'Heads' and 'Tails'
    result = random.choice(['Heads', 'Tails'])
    return result

# Flipping the coin and printing the result

def determine_strike_and_option():
    base_symbol,_ = strategy_obj.determine_expiry_index()
    print(base_symbol)
    strike_prc = strategy_obj.calculate_current_atm_strike_prc(base_symbol)
    option_type = 'CE' if flip_coin() == 'Heads' else 'PE'
    today_expiry = instrument_obj.get_expiry_by_criteria(base_symbol,strike_prc,option_type, "current_week")
    exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol,strike_prc, option_type,today_expiry)
    order_details = [
        {  
        "strategy": strategy_obj.get_strategy_name(),
        "base_symbol": base_symbol,
        "exchange_token" : exchange_token,     
        "segment" : strategy_obj.get_general_params().get('Segment'),
        "transaction_type": strategy_obj.get_general_params().get('TransactionType'),  
        "order_type" : strategy_obj.get_general_params().get('OrderType'), 
        "product_type" : strategy_obj.get_general_params().get('ProductType'),
        "order_mode" : ["Main"],
        "trade_id" : place_order_calc.get_trade_id(strategy_obj.get_strategy_name(), "entry")
        }]
    return order_details

def calculate_qty(main_exchange_token,base_symbol):
    token = instrument_obj.get_token_by_exchange_token(main_exchange_token)
    ltp = strategy_obj.get_single_ltp(token)
    qty_calc.update_qty_during_entry(ltp,strategy_obj.get_strategy_name(),base_symbol)

def main():
    order_details = determine_strike_and_option()
    message = "Order placed for " + order_details[0].get('base_symbol')
    discord.discord_bot(message, strategy_obj.get_strategy_name())
    calculate_qty(order_details[0].get('exchange_token'),order_details[0].get('base_symbol'))
    print(order_details)
    place_order.place_order_for_strategy(strategy_obj.get_strategy_name(),order_details)

current_time = time.localtime()
seconds_since_midnight = current_time.tm_hour * 3600 + current_time.tm_min * 60 + current_time.tm_sec
seconds_until_10_am = 10 * 3600 - seconds_since_midnight

# Calculate the total number of seconds in the 10 AM to 1 PM window
seconds_in_window = 3 * 3600  # 3 hours

# Generate a random number of seconds to wait within this window
random_seconds = random.randint(0, seconds_in_window)

# Wait until 10 AM, then an additional random amount of time
time.sleep(seconds_until_10_am + random_seconds)
    

main()