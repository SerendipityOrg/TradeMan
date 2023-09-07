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
              
    transaction_type = order_details.get('transaction_type')
    if transaction_type == 'BUY':
        transaction_type = kite.TRANSACTION_TYPE_BUY
    elif transaction_type == 'SELL':
        transaction_type = kite.TRANSACTION_TYPE_SELL
    else:
        raise ValueError("Invalid transaction_type in order_details")

    order_type_value = order_details.get('order_type')
    if order_type_value == 'Stoploss':
        order_type = kite.ORDER_TYPE_SL
    elif order_type_value == 'Market':
        order_type = kite.ORDER_TYPE_MARKET
    else:
        raise ValueError("Invalid order_type in order_details")
    
    avg_prc = 0.0
    limit_prc = order_details.get('limit_prc', 0.0)
    trigger_price = round(float(limit_prc) + 1.00, 1) if limit_prc else None
    
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            price=float(limit_prc),
            tradingsymbol=order_details['tradingsymbol'],
            transaction_type=transaction_type, 
            quantity=qty,
            trigger_price=trigger_price,
            product=kite.PRODUCT_MIS,
            order_type=order_type
        )
        logging.info(f"Order placed. ID is: {order_id}")
        
        # Safely fetch the order history.
        order_history = kite.order_history(order_id=order_id)
        for order in order_history:
            if order.get('status') == 'COMPLETE':
                avg_prc = order.get('average_price', 0.0)
                break  # Exit the loop once you find the completed order
        if avg_prc == 0.0:
            raise Exception("Order completed but average price not found.")

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
    try:
        order_id, avg_price = place_order(kite, order_details, qty)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        # You can set default or fallback values if needed
        order_id = None
        avg_price = 0.0
    
    try:
        log_order(order_id, avg_price, order_details, user_details,qty, strategy)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        
    return order_id, avg_price
        
        
def update_stoploss(order_id,trading_symbol, new_stoploss):
    global kite
    
    new_stoploss = round(float(new_stoploss),1)
    trigger_price = round((float(new_stoploss)+1.00),1)
    
    
    order = kite.modify_order(variety=kite.VARIETY_REGULAR, 
                                order_id=order_id, 
                                price = new_stoploss,
                                trigger_price = trigger_price)

    