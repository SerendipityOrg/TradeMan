import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha
import os
import sys
from instrument_monitor import InstrumentMonitor
import threading
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *


def place_order_for_broker( strategy, order_details, qty =None):

    weeklyexpiry, _ = get_expiry_dates(order_details['base_symbol'])
    
    strike_prc = round_strike_prc(order_details['strike_prc'],order_details['base_symbol'])
    
    # Fetch tokens and trading symbols
    token, trading_symbol_list, trading_symbol_aliceblue = get_tokens(
        order_details['base_symbol'], 
        weeklyexpiry, 
        order_details['option_type'], 
        strike_prc
    )
    
    users_to_trade = get_strategy_users(strategy)
    
    for broker,user in users_to_trade:
        if broker == 'zerodha':
            trading_symbol = trading_symbol_list
            place_order_func = zerodha.place_zerodha_order
        elif broker == 'aliceblue':
            trading_symbol = trading_symbol_aliceblue[0]
            place_order_func = aliceblue.place_aliceblue_order
        else:
            print(f"Unknown broker: {broker}")
            return

        avg_prc = place_order_func(strategy, {
            'transaction_type': 'BUY',
            'tradingsymbol': trading_symbol,
            'user': user,
            'order_type': 'Market'
        }, qty=qty)
        
        if strategy == 'MPWizard' or strategy == 'Siri':
            limit_prc = float(avg_prc[1]) - order_details['stoploss_points']

            place_order_func(strategy, {
                        'transaction_type': 'SELL',
                        'tradingsymbol': trading_symbol,
                        'user': user,
                        'order_type': 'Stoploss',
                        'limit_prc': limit_prc,
                    }, qty=qty)
        #calculate the target based on the priceref
            target = round(float(avg_prc[1]) + order_details['stoploss_points'],1)
        
        monitor_order_func = {
            'token': token[0],
            'target': target,
            'limit_prc': limit_prc,
            'strategy': strategy,
            'trade_type': 'SELL' 
        }
        
        monitor = InstrumentMonitor()
        monitor.add_token(token[0])
        current_ltp = monitor.get_ltp_for_token(token[0])
        # ltp_of_token = monitor.get_ltp_for_token(token[0])
        # print(f"LTP for token {token[0]} is {ltp_of_token}.")
        
        # monitor_thread = threading.Thread(target=instrument_monitor.monitor_instruments, args=(monitor_order_func,))
        # monitor_thread.start()
        
        # monitor = instrument_monitor.monitor_instruments(monitor_order_func)

    
