import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha
import os
import sys,threading
from functools import partial

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *

def start_monitoring(monitor):
    monitor_thread = threading.Thread(target=monitor.fetch)
    monitor_thread.daemon = True  # This ensures the thread will exit when the main program exits
    monitor_thread.start()

def place_order_for_broker( strategy, order_details, qty =None,monitor = None):
    from instrument_monitor import InstrumentMonitor
    
           
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
            trading_symbol = trading_symbol_aliceblue
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
        
        #######################price ref can be none 
        
        if strategy == 'MPWizard' or strategy == 'Siri':
            limit_prc = float(avg_prc[1]) - order_details['stoploss_points']
            order_func ={
                        'transaction_type': 'SELL',
                        'tradingsymbol': trading_symbol,
                        'user': user,
                        'broker': broker,
                        'order_type': 'Stoploss',
                        'limit_prc': limit_prc,
                        'price_ref' : order_details['stoploss_points']
                    }
            place_order_func(strategy, order_func , qty=qty)
        #calculate the target based on the priceref
            target = round((float(avg_prc[1]) + (order_details['stoploss_points']/2)))
            print(f"Target is {target}")
            print(f"Limit price is {limit_prc}")
            monitor.add_token(token, target, limit_prc,order_func)
            
    if not monitor:
        monitor = InstrumentMonitor(callback=partial(modify_orders, monitor=monitor))
    start_monitoring(monitor)                
    # if not monitor:
    #     monitor = InstrumentMonitor()
    # start_monitoring(monitor)
    sleep(10)

def modify_orders(token,monitor=None):
    
    token_data = monitor.tokens_to_monitor[token] 
    order_details = token_data['order_details']
    print(f"Inside modify_orders for token {token} with LTP")
    
    monitor_order_func = {
                'user': order_details['user'],
                'broker': order_details['broker'],
                'qty' : order_details['qty'],
                'token': order_details['tradingsymbol'],
                'target': token_data['target'],
                'limit_prc': token_data['limit_prc'],
                'strategy': 'strategy',
                'trade_type': 'SELL'
            }
    
    if order_details['broker'] == 'aliceblue':
        aliceblue.update_stoploss(monitor_order_func)
    elif order_details['broker'] == 'zerodha':
        zerodha.update_stoploss(monitor_order_func)
        
            
            
    
