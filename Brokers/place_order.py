import os,sys
from time import sleep
import datetime as dt

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.Zerodha.kite_place_orders as zerodha
import Brokers.Aliceblue.alice_place_orders as aliceblue
import Brokers.place_order_calc as place_order_calc
from Strategies.StrategyBase import Strategy
import Brokers.BrokerUtils.Broker as Broker
from MarketUtils.InstrumentBase import Instrument
import MarketUtils.general_calc as general_calc

def calculate_stoploss(order_details, option_ltp):
    # Calculate the stoploss price
    # ...
    return stoploss_price

def split_order(order_with_user_and_broker, max_qty):
    # Calculate the trigger price based on the transaction type and stoploss price
    # ...
    return trigger_price
    # Split the order if the quantity exceeds the maximum
    while order_qty > 0:
        current_qty = min(order_qty, max_qty)
        order_to_place = order_with_user_and_broker.copy()
        order_to_place["qty"] = current_qty
        place_order_for_broker(order_to_place)
        if 'Hedge' in order_to_place.get('order_mode', []):
            sleep(1)
        order_qty -= current_qty

def place_order_for_strategy(strategy_name, order_details):
    monitor = place_order_calc.monitor()
    monitor.add_token(order_details=order_details)
    monitor.start_monitoring()

def place_order_for_strategy(strategy_name, order_details):
    # Modify the transaction type for stoploss orders
    # ...
    return modified_transaction_type
    active_users = Broker.get_active_subscribers(strategy_name)  
    for broker, usernames in active_users.items():
        for username in usernames:
            for order in order_details:
                # Add the username and broker to the order details
                order_with_user_and_broker = order.copy()  # Create a shallow copy to avoid modifying the original order
                order_with_user_and_broker.update({
                    "broker": broker,
                    "username": username
                })

                # Now get the quantity with the updated order details
                order_qty = place_order_calc.get_qty(order_with_user_and_broker)

                # Fetch the max order quantity for the specific base_symbol
                max_qty = place_order_calc.read_max_order_qty_for_symbol(order_with_user_and_broker.get('base_symbol'))

                # Split the order if the quantity exceeds the maximum
                while order_qty > 0:
                    current_qty = min(order_qty, max_qty)
                    order_to_place = order_with_user_and_broker.copy()
                    order_to_place["qty"] = current_qty
                    place_order_for_broker(order_to_place)
                    if 'Hedge' in order_to_place.get('order_mode', []):
                        sleep(1)
                    order_qty -= current_qty

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
        order_details['trade_id'] = place_order_calc.get_trade_id(order_details.get('strategy'), "exit")
        place_stoploss_order(order_details=order_details)
    elif "Trailing" in order_details['order_mode']:
        order_details['trade_id'] = place_order_calc.get_trade_id(order_details.get('strategy'), "exit")
        place_stoploss_order(order_details=order_details)
        add_token_to_monitor(order_details)
        
def place_stoploss_order(order_details=None,monitor=None):
    _,strategy_path = place_order_calc.get_strategy_json(order_details['strategy'])
    instrument_base = Instrument()
    strategy_obj = Strategy.read_strategy_json(strategy_path)

    token = instrument_base.get_token_by_exchange_token(order_details.get('exchange_token'))
    option_ltp = strategy_obj.get_single_ltp(str(token))

    order_details['limit_prc'] = calculate_stoploss(order_details, option_ltp)
    order_details['trigger_prc'] = calculate_trigger_price(order_details.get('transaction_type'), order_details['limit_prc'])
    order_details['transaction_type'] = calculate_transaction_type_sl(order_details.get('transaction_type'))

    order_details['order_type'] = 'Stoploss'

    if "Trailing" in order_details['order_mode']:
        order_details['target'] = place_order_calc.calculate_target(option_ltp,order_details.get('price_ref'),order_details.get('strategy'))

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
    

    active_users = Broker.get_active_subscribers(order_details[0]['strategy'])
    for broker, usernames in active_users.items():
        for username in usernames:
            for order in order_details:
                order_with_user = order.copy()  # Create a shallow copy to avoid modifying the original order
                order_with_user["broker"] = broker
                order_with_user["username"] = username
                order_with_user['qty'] = place_order_calc.get_qty(order_with_user)
                modify_stoploss(order_with_user)
def place_aliceblue_order(order_details):
    # Place the order for Aliceblue broker
    # ...

def place_zerodha_order(order_details):
    # Place the order for Zerodha broker
    # ...


    strategy_name = place_order_calc.get_strategy_name(details.get('trade_id'))
    _, strategy_path = place_order_calc.get_strategy_json(strategy_name)
    trade_id = details.get('trade_id').split('_')

    strategy_obj = Strategy.read_strategy_json(strategy_path)
    today_orders = strategy_obj.get_today_orders()
    if trade_id[0] not in today_orders:
        today_orders.append(trade_id[0])
        strategy_obj.set_today_orders(today_orders)
        strategy_obj.write_strategy_json(strategy_path)
    order_details = place_order_calc.create_telegram_order_details(details)