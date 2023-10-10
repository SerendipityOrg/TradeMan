import aliceblue.alice_place_orders as aliceblue
import zerodha.kite_place_orders as zerodha
import os
import sys,threading
from functools import partial
from datetime import datetime
import place_order_calc as place_order_calc

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
UTILS_DIR = os.path.join(CURRENT_DIR, '..','Utils')

sys.path.append(UTILS_DIR)
import general_calc as gc

def start_monitoring(monitor):
    monitor_thread = threading.Thread(target=monitor.fetch)
    monitor_thread.daemon = True  # This ensures the thread will exit when the main program exits
    monitor_thread.start()

#TODO: write documentation
def place_order_for_broker(strategy, order_details=None, qty =None,monitor = None, trading_symbol = None, signal = None):
    print(order_details)
    from instrument_monitor import InstrumentMonitor

    if trading_symbol is not None:
        trading_symbol_list, trading_symbol_aliceblue = trading_symbol
    else:
        weeklyexpiry, monthlyexpiry = gc.get_expiry_dates(order_details['base_symbol']) # TODO: Process before 10:15 at the start of the script

        
        if strategy == "Overnight_Options" and order_details['strike_prc'] == 0:
            expiry = monthlyexpiry
        elif strategy == "Overnight_Options" and datetime.now().weekday() == 3 and order_details['strike_prc'] != 0 and signal=='Afternoon':
            expiry = gc.get_next_week_expiry(order_details['base_symbol'])
        else:
            expiry = weeklyexpiry
        token, trading_symbol_list, trading_symbol_aliceblue = gc.get_tokens(
                                                                order_details['base_symbol'], 
                                                                expiry, 
                                                                order_details['option_type'], 
                                                                order_details['strike_prc']
                                                            )
        
    users_to_trade = gc.get_strategy_users(strategy)
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
            'transaction_type': order_details['transaction'],
            'base_symbol': order_details['base_symbol'],
            'strike_prc': order_details['strike_prc'],
            'tradingsymbol': trading_symbol,
            'user': user,
            'order_trade_type': 'Market'}
        
        if 'option_type' in order_details:
            details['option_type'] = order_details['option_type']

        if 'direction' in order_details:
            details['direction'] = order_details['direction']

        if 'strike_prc' in order_details:
            details['strike_price'] = order_details['strike_prc']
        
        if signal is not None:
            details['signal'] = signal
        
        order_tag = place_order_calc.get_trade_id(strategy, signal=signal, order_details=order_details)
        if order_tag is not None:
                details['order_tag'] = order_tag

        _,avg_prc = place_order_func(strategy, details, qty=qty)
        #######################price ref can be none 
        
        if strategy == 'MPWizard' or strategy == 'Siri':
            option_ltp = InstrumentMonitor._fetch_ltp_for_token(monitor, token)
            if 'target' not in order_details:
                order_details['target'] = round(float(option_ltp) + (order_details['stoploss_points'] / 2))
            limit_prc = float(option_ltp) - order_details['stoploss_points']
            limit_prc = round(limit_prc)
            if limit_prc < 0:
                limit_prc = 1.0
            #change the order_details['transaction] to 'SELL'
            order_details['transaction'] = 'SELL'
            
            order_func ={
                        'transaction_type': order_details['transaction'],
                        'tradingsymbol': trading_symbol,
                        'user': user,
                        'broker': broker,
                        'base_symbol': order_details['base_symbol'],
                        'strike_prc': order_details['strike_prc'],
                        'option_type': order_details['option_type'],
                        'order_trade_type': 'Stoploss',
                        'limit_prc': round(limit_prc),
                        'price_ref' : order_details['stoploss_points']
                    }
            order_tag = place_order_calc.get_trade_id(strategy, signal=signal, order_details=order_details)
            if order_tag is not None:
                order_func['order_tag'] = order_tag
            place_order_func(strategy, order_func , qty=qty)
            order_details['transaction'] = 'BUY'
        #calculate the target based on the priceref
            target = order_details.get('target', round(float(avg_prc) + (order_details['stoploss_points'] / 2)))
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
               
    

def modify_orders(token=None,monitor=None,order_details=None):
    print("in modify orders")
    if token:
        token_data = monitor.tokens_to_monitor[token] #change monitor to intruMonitor
        order_details = token_data['order_details']
        order_details['target'] = token_data['target']
        order_details['limit_prc'] = token_data['limit_prc']
        order_details['strategy'] = token_data['strategy']
    print(order_details['target'],"target ",order_details['limit_prc'],"limit prc")

    
    weeklyexpiry, _ = gc.get_expiry_dates(order_details['base_symbol'])
    token, trading_symbol_list, trading_symbol_aliceblue = gc.get_tokens(
                                                            order_details['base_symbol'], 
                                                            weeklyexpiry, 
                                                            order_details['option_type'], 
                                                            order_details['strike_prc']
                                                        )


    users_to_trade = gc.get_strategy_users(order_details['strategy'])
    
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

    users_to_trade = gc.get_strategy_users(token_data['strategy'])

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




