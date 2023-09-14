import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha
import os
import sys,threading
from functools import partial
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *

def start_monitoring(monitor):
    monitor_thread = threading.Thread(target=monitor.fetch)
    monitor_thread.daemon = True  # This ensures the thread will exit when the main program exits
    monitor_thread.start()

#TODO: write documentation
def place_order_for_broker(strategy, order_details=None, qty =None,monitor = None, trading_symbol = None, trade_type = None):
    from instrument_monitor import InstrumentMonitor

    if trading_symbol is not None:
        trading_symbol_list, trading_symbol_aliceblue = trading_symbol
    else:
        weeklyexpiry, monthlyexpiry = get_expiry_dates(order_details['base_symbol']) # TODO: Process before 10:15 at the start of the script

        
        if strategy == "overnight_option" and order_details['strike_prc'] == 0:
            expiry = monthlyexpiry
        elif strategy == "overnight_option" and datetime.now().weekday() == 3 and order_details['strike_prc'] != 0 and trade_type=='Afternoon':
            expiry = get_next_week_expiry(order_details['base_symbol'])
        else:
            expiry = weeklyexpiry

        token, trading_symbol_list, trading_symbol_aliceblue = get_tokens(
                                                                order_details['base_symbol'], 
                                                                expiry, 
                                                                order_details['option_type'], 
                                                                order_details['strike_prc']
                                                            )
        

    users_to_trade = get_strategy_users(strategy)
    token_added = False
    
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
        
        details = {
            'transaction_type': order_details['transcation'],
            'tradingsymbol': trading_symbol,
            'user': user,
            'order_type': 'Market'}

        if 'direction' in order_details:
            details['direction'] = order_details['direction']

        if 'strike_prc' in order_details:
            details['strike_price'] = order_details['strike_prc']
        
        if trade_type is not None:
            details['order_type'] = trade_type
            
        avg_prc = place_order_func(strategy, details, qty=qty)
        
        #######################price ref can be none 
        
        if strategy == 'MPWizard' or strategy == 'Siri':
            limit_prc = float(avg_prc[1]) - order_details['stoploss_points']
            order_func ={
                        'transaction_type': 'SELL',
                        'tradingsymbol': trading_symbol,
                        'user': user,
                        'broker': broker,
                        'order_type': 'Stoploss',
                        'limit_prc': round(limit_prc),
                        'price_ref' : order_details['stoploss_points']
                    }
            place_order_func(strategy, order_func , qty=qty)
        #calculate the target based on the priceref
            target = order_details.get('target', round(float(avg_prc[1]) + (order_details['stoploss_points'] / 2)))
            print(f"Target is {target}")
            print(f"Limit price is {limit_prc}")
            
             # Add token only if it's not added yet
            if not token_added:
                monitor.add_token(token, target, limit_prc, order_func, strategy)
                token_added = True  # Update the flag to indicate the token was added
    if strategy == 'MPWizard' or strategy == 'Siri':
        if not monitor:
            monitor = InstrumentMonitor(callback=partial(modify_orders,monitor=monitor))
        start_monitoring(monitor) 
               
    

def modify_orders(token,monitor=None):
    
    token_data = monitor.tokens_to_monitor[token] #change monitor to intruMonitor
    order_details = token_data['order_details']
    print("in modify orders")
    monitor_order_func = {
                'user': order_details['user'],
                'broker': order_details['broker'],
                'qty' : order_details['qty'],
                'token': order_details['tradingsymbol'],
                'target': token_data['target'],
                'limit_prc': token_data['limit_prc'],
                'strategy': token_data['strategy'],
                'trade_type': 'SELL'
            }
    
    if order_details['broker'] == 'aliceblue':
        print("Updating stoploss for Aliceblue")
        aliceblue.update_stoploss(monitor_order_func)
    elif order_details['broker'] == 'zerodha':
        print("Updating stoploss for Zerodha")
        zerodha.update_stoploss(monitor_order_func)
