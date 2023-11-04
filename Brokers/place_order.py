import os,sys
from time import sleep

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.Zerodha.kite_place_orders as zerodha
import Brokers.Aliceblue.alice_place_orders as aliceblue
import Brokers.place_order_calc as place_order_calc
from Strategies.StrategyBase import Strategy
import Brokers.BrokerUtils.Broker as Broker
from MarketUtils.InstrumentBase import Instrument

def add_token_to_monitor(order_details):
    monitor = place_order_calc.monitor()
    monitor.add_token(order_details=order_details)
    monitor.start_monitoring()
    
def place_order_for_strategy(strategy_name,order_details):
    active_users = Broker.get_active_subscribers(strategy_name)
    for broker, usernames in active_users.items():
        for username in usernames:
            for order in order_details:
                order_with_user = order.copy()  # Create a shallow copy to avoid modifying the original order
                order_with_user["broker"] = broker
                order_with_user["username"] = username
                order_with_user['qty'] = place_order_calc.get_qty(order_with_user)
                place_order_for_broker(order_with_user)

#TODO: write documentation
def place_order_for_broker(order_details):
    if order_details['broker'] == "aliceblue":  #TODO make this a list of brokers and fetch them in the form of enum
        aliceblue.place_aliceblue_order(order_details=order_details)
    elif order_details['broker'] == "zerodha":
        zerodha.place_zerodha_order(order_details=order_details)
    else:
        print("Unknown broker")
        return

    if "SL" in order_details['order_mode']:
        sleep(1)
        order_details['trade_id'] = place_order_calc.get_trade_id(order_details.get('strategy'), "exit")
        place_stoploss_order(order_details=order_details)
    elif "Trailing" in order_details['order_mode']:
        sleep(1)
        order_details['trade_id'] = place_order_calc.get_trade_id(order_details.get('strategy'), "exit")
        place_stoploss_order(order_details=order_details)
        add_token_to_monitor(order_details)
        
def place_stoploss_order(order_details=None,monitor=None):
    _,strategy_path = place_order_calc.get_strategy_json(order_details['strategy'])
    instrument_base = Instrument()
    strategy_obj = Strategy.read_strategy_json(strategy_path)

    token = instrument_base.get_token_by_exchange_token(order_details.get('exchange_token'))
    option_ltp = strategy_obj.get_single_ltp(str(token))

    order_details['limit_prc'] = place_order_calc.calculate_stoploss(order_details,option_ltp)
    order_details['trigger_prc'] = place_order_calc.calculate_trigger_price(order_details.get('transaction_type'),order_details['limit_prc'])
    order_details['transaction_type'] = place_order_calc.calculate_transaction_type_sl(order_details.get('transaction_type'))

    order_details['order_type'] = 'Stoploss'

    if "Trailing" in order_details['order_mode']:
        order_details['target'] = place_order_calc.calculate_target(option_ltp,order_details.get('price_ref'))

    if order_details['broker'] == "aliceblue":
        aliceblue.place_aliceblue_order(order_details)
    elif order_details['broker'] == "zerodha":
        zerodha.place_zerodha_order(order_details)
    else:
        print("Unknown broker")
        return

def modify_stoploss(order_details=None):
    if order_details['broker'] == "aliceblue":
        aliceblue.update_alice_stoploss(order_details)
    elif order_details['broker'] == "zerodha":
        zerodha.update_kite_stoploss(order_details) 
    else:
        print("Unknown broker")
    
def modify_orders(order_details=None):
    active_users = Broker.get_active_subscribers(order_details[0]['strategy'])
    for broker, usernames in active_users.items():
        for username in usernames:
            for order in order_details:
                order_with_user = order.copy()  # Create a shallow copy to avoid modifying the original order
                order_with_user["broker"] = broker
                order_with_user["username"] = username
                order_with_user['qty'] = place_order_calc.get_qty(order_with_user)
                modify_stoploss(order_with_user)
