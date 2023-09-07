import logging
from kiteconnect import KiteConnect
from place_order_calc import log_order, get_user_details, get_quantity
import sys,os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(CURRENT_DIR, '..', '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *

kite = None

def place_order(kite, order_details, qty):

    """
    Place an order with Zerodha broker.

    Args:
        kite (KiteConnect): The KiteConnect instance.
        order_details (dict): The details of the order.
        qty (int): The quantity of the order.

    Returns:
        float: The average price of the order.

    Raises:
        Exception: If the order placement fails.
    """
              
    if order_details['transaction_type'] == 'BUY':
        transaction_type = kite.TRANSACTION_TYPE_BUY
    elif order_details['transaction_type'] == 'SELL':
        transaction_type = kite.TRANSACTION_TYPE_SELL
    
    if order_details['order_type'] == 'Stoploss':
        order_type = kite.ORDER_TYPE_SL
    elif order_details['order_type'] == 'Market':
        order_type = kite.ORDER_TYPE_MARKET   
    
    avg_prc = 0.0
    limit_prc = 0.0 
    trigger_price = None   

    if 'limit_prc' in order_details:      
        limit_prc = round(float(order_details['limit_prc']),1)
        trigger_price = round((float(order_details['limit_prc'])+1.00),1) 
    
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            price=limit_prc,
            tradingsymbol=order_details['tradingsymbol'],
            transaction_type=transaction_type, 
            quantity=qty,
            trigger_price=trigger_price,
            product=kite.PRODUCT_MIS,
            order_type=order_type
        )
        logging.info(f"Order placed. ID is: {order_id}")
        
        order_history = kite.order_history(order_id=order_id)
        for i in order_history:
            if i['status'] == 'COMPLETE':
                avg_prc = i['average_price']
                break  # Exit the loop once you find the completed order

        return order_id, avg_prc
    
    except Exception as e:
        message = f"Order placement failed: {e}"
        print(message)
        # general_calc.discord_bot(message)
        return None


def place_zerodha_order(strategy: str, order_details: dict, qty=None):
    """
    Place an order with Zerodha broker.

    Args:
        strategy (str): The strategy name.
        order_details (dict): The details of the order.
        qty (int, optional): The quantity of the order. Defaults to None.

    Returns:
        float: The average price of the order.

    Raises:
        Exception: If the order placement fails.
    """
    global kite
    user_details,_ = get_user_details(order_details['user'])
    kite = KiteConnect(api_key=user_details['zerodha']['api_key'])
    kite.set_access_token(user_details['zerodha']['access_token'])

    if qty is None:
        qty = get_quantity(user_details, strategy, order_details['tradingsymbol'],'zerodha')
    
    order_details['qty'] = qty
    order_id, avg_price = place_order(kite, order_details, qty)
    log_order(order_id, avg_price, order_details, user_details,qty, strategy)
    return order_id, avg_price
        
        
def update_stoploss(order_id,trading_symbol, new_stoploss):
    global kite
    
    new_stoploss = round(float(new_stoploss),1)
    trigger_price = round((float(new_stoploss)+1.00),1)
    
    
    order = kite.modify_order(variety=kite.VARIETY_REGULAR, 
                                order_id=order_id, 
                                price = new_stoploss,
                                trigger_price = trigger_price)

    