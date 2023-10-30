import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
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
    # option_ltp = monitor.fetch_ltp(token)


    order_details['limit_prc'] = place_order_calc.calculate_stoploss(order_details,option_ltp)
    order_details['trigger_prc'] = place_order_calc.calculate_trigger_price(order_details.get('transaction_type'),order_details['limit_prc'])
    order_details['transaction_type'] = place_order_calc.calculate_transaction_type_sl(order_details.get('transaction_type'))
    order_details['order_type'] = 'Stoploss'
    
    print("stoploss",order_details['limit_prc'])

    if "Trailing" in order_details['order_mode']:
        order_details['target'] = place_order_calc.calculate_target(option_ltp,order_details.get('price_ref'))

    if order_details['broker'] == "aliceblue":
        aliceblue.place_aliceblue_order(order_details)
    elif order_details['broker'] == "zerodha":
        zerodha.place_zerodha_order(order_details)
    else:
        print("Unknown broker")
        return

def modify_stoploss(order_details=None,monitor=None):
    if order_details['broker'] == "aliceblue":
        aliceblue.update_alice_stoploss(order_details)
    elif order_details['broker'] == "zerodha":
        zerodha.update_kite_stoploss(order_details) #TODO
    else:
        print("Unknown broker")
    

def place_tsl(order_details):
    print("in place tsl")
    modify_stoploss(order_details=order_details)
    price_ref = order_details['price_ref'] # TODO: This is related to MPwizard. Generalize this function
    order_details['target'] += (price_ref / 2)  # Adjust target by half of price_ref
    order_details['limit_prc'] += (price_ref / 2)  # Adjust limit_prc by half of price_ref
    return order_details['target'], order_details['limit_prc']


def modify_orders(token=None,monitor=None,order_details=None):
    print("in modify orders")
    if token:
        token_data = monitor.tokens_to_monitor[token] #change monitor to intruMonitor
        order_details = token_data['order_details']
        order_details['target'] = token_data['target']
        order_details['limit_prc'] = token_data['limit_prc']
        order_details['strategy'] = token_data['strategy']
    # print(order_details['target'],"target ",order_details['limit_prc'],"limit prc")

    
    weeklyexpiry, _ = general_calc.get_expiry_dates(order_details['base_symbol'])
    token, trading_symbol_list, trading_symbol_aliceblue = general_calc.get_tokens(
                                                            order_details['base_symbol'], 
                                                            weeklyexpiry, 
                                                            order_details['option_type'], 
                                                            order_details['strike_prc']
                                                        )


    users_to_trade = general_calc.get_strategy_users(order_details['strategy'])
    
    for broker,user in users_to_trade:
        user_details,_ = place_order_calc.get_user_details(user)
        if broker == 'zerodha':
            trading_symbol = trading_symbol_list
        elif broker == 'aliceblue':
            trading_symbol = trading_symbol_aliceblue
        qty = place_order_calc.get_quantity(user_details, broker, order_details['strategy'], trading_symbol)

        monitor_order_func = {
                    'user': user,
                    'broker': broker,
                    'qty' : qty,
                    'limit_prc': order_details['limit_prc'],
                    'strategy': order_details['strategy'],
                    'trade_type': 'SELL'
                }
        if broker == 'zerodha' :
            monitor_order_func['token'] = trading_symbol_list
            zerodha.update_stoploss(monitor_order_func)
        elif broker == 'aliceblue':
            monitor_order_func['token'] = trading_symbol_aliceblue
            aliceblue.update_stoploss(monitor_order_func)

def exit_order_details(token=None,monitor=None):
    token_data = monitor.tokens_to_monitor[token]
    order_details = token_data['order_details']
    if isinstance(order_details['tradingsymbol'], str):
        trading_symbol = order_details['tradingsymbol']
    else:
        trading_symbol = order_details['tradingsymbol'].name
    print("trading_symbol",trading_symbol)

    users_to_trade = general_calc.get_strategy_users(token_data['strategy'])

    for broker,user in users_to_trade:
        exit_order_func = {
                    'user': user,
                    'broker': broker,
                    'limit_prc': order_details['limit_prc'],
                    'strategy': token_data['strategy'],
                    'trade_type': 'SELL',
                    'token' : trading_symbol
                }
        if broker == 'zerodha' :
            zerodha.exit_order(exit_order_func)
        elif broker == 'aliceblue':
            aliceblue.exit_order(exit_order_func)




