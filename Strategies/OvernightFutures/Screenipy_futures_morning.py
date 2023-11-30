import os
import sys
from dotenv import load_dotenv
import datetime as dt
from time import sleep

# Set up paths and import modules
DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

import Brokers.place_order as place_order
import Strategies.StrategyBase as StrategyBase
import MarketUtils.InstrumentBase as InstrumentBase
import Brokers.place_order_calc as place_order_calc
import MarketUtils.general_calc as general_calc

_,STRATEGY_PATH = place_order_calc.get_strategy_json('OvernightFutures')

strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)
instrument_obj = InstrumentBase.Instrument()

strategy_name = strategy_obj.get_strategy_name()

prediction = strategy_obj.get_extra_information().get('prediction')
hedge_exchange_token = strategy_obj.get_extra_information().get('hedge_exchange_token')
futures_exchange_token = strategy_obj.get_extra_information().get('futures_exchange_token')

hedge_transcation_type = strategy_obj.get_general_params().get('HedgeTransactionType')

order_type = strategy_obj.get_general_params().get('OrderType')
segment_type = strategy_obj.get_general_params().get('Segment')
product_type = strategy_obj.get_general_params().get('ProductType')


orders_to_place = [
    {  
        "strategy": strategy_name,
        "base_symbol" : strategy_obj.get_instruments()[0],
        "exchange_token" : hedge_exchange_token,     
        "segment" : segment_type,
        "transaction_type": hedge_transcation_type,  
        "order_type" : order_type, 
        "product_type" : product_type,
        "order_mode" : ["Hedge"]
    },
    {
        "strategy": strategy_name,
        "base_symbol" : strategy_obj.get_instruments()[0],
        "exchange_token" : futures_exchange_token,     
        "segment" : segment_type,
        "transaction_type": strategy_obj.get_square_off_transaction(prediction), 
        "order_type" : order_type, 
        "product_type" : product_type,
        "order_mode" : ["Main"]
    }
]


def is_yesterday_holiday(today):
    """Check if yesterday was a holiday."""
    yesterday = today - dt.timedelta(days=1)
    return yesterday in general_calc.holidays

def main():
    now = dt.datetime.now()

    # Check if today is the day after a holiday
    if is_yesterday_holiday(now.date()):
        print("Skipping execution as yesterday was a holiday.")
        return

    desired_end_time_str = strategy_obj.get_exit_params().get('SqroffTime')
    start_hour, start_minute, start_second = map(int, desired_end_time_str.split(':'))
    wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
    if wait_time.total_seconds() > 0:
        print(f"Waiting for {wait_time} before starting the bot")
        sleep(wait_time.total_seconds())
        
    trade_id = place_order_calc.get_trade_id(strategy_name, "exit")
    for order in orders_to_place:
        order["trade_id"] = trade_id

    print(orders_to_place)
    place_order.place_order_for_strategy(strategy_name,orders_to_place)

if __name__ == "__main__":
    main()