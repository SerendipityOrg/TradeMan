import logging
from kiteconnect import KiteConnect
import sys,os


DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order_calc as place_order_calc
import Brokers.Zerodha.kite_utils as kite_utils


active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

def kite_place_order(kite, order_details, user_details=None):
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
    exchange_token = order_details.get('exchange_token')
    segment = order_details.get('segment')
    strategy = order_details.get('strategy')
    qty = int(order_details.get('qty'))
    product = order_details.get('product_type')

    transaction_type = kite_utils.calculate_transaction_type(order_details.get('transaction_type'))
    order_type = kite_utils.calculate_order_type(order_details.get('order_type'))
    product_type = kite_utils.calculate_product_type(product)

    avg_prc = 0.0
    limit_prc = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)

    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            price= limit_prc,
            tradingsymbol=order_details['tradingsymbol'],
            transaction_type=transaction_type, 
            quantity= qty,
            trigger_price=trigger_price,
            product=product_type,
            order_type=order_type,
            tag= order_details.get('order_tag', None)
        )
        print(f"Order placed. ID is: {order_id}")
        avg_prc = kite_utils.get_avg_prc(kite,order_id)

        if avg_prc == 0.0:
            try:
                place_order_calc.log_order(order_id, 0.0, order_details, user_details, strategy)
            except Exception as e:
                print(f"Failed to log the order with zero avg_prc: {e}")
            
            raise Exception("Order completed but average price not found.")
        
        return order_id, avg_prc
    
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['user']}"
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
    
    user_details = place_order_calc.assign_user_details(active_users_json_path,order_details)
    kite = kite_utils.create_kite_obj(user_details)

    order_details['qty'] = user_details['qty'][order_details['strategy']]#TODO: write a logic to get the qty for MPWizard
    
    try:
        order_id, avg_price = kite_place_order(kite, order_details, user_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        # You can set default or fallback values if needed
        order_id = None
        avg_price = 0.0
    
    try:
        place_order_calc.log_order(order_id, avg_price, order_details, user_details, strategy)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        
    return order_id, avg_price

def update_stoploss(monitor_order_func):
    print("in update stoploss")
    global kite
    if kite is None:
        user_details,_ = get_user_details(monitor_order_func.get('user'))
        kite = KiteConnect(api_key=user_details['zerodha']['api_key'])
        kite.set_access_token(user_details['zerodha']['access_token'])
    
    order_id = retrieve_order_id(
            monitor_order_func.get('user'),
            monitor_order_func.get('broker'),
            monitor_order_func.get('strategy'),
            monitor_order_func.get('trade_type'),
            monitor_order_func.get('token')
        )

    new_stoploss = round(float(monitor_order_func.get('limit_prc')),1)
    trigger_price = round((float(new_stoploss)+1.00),1)
    try:
        modify_order = kite.modify_order(variety=kite.VARIETY_REGULAR, 
                                    order_id=order_id, 
                                    price = new_stoploss,
                                    trigger_price = trigger_price)
    except Exception as e:
        print(f"Failed to modify the order: {e}")
    print("zerodha order modified")

def exit_order(exit_order_func):
    order_id = retrieve_order_id(
        exit_order_func.get('user'),
        exit_order_func.get('broker'),
        exit_order_func.get('strategy'),
        exit_order_func.get('trade_type'),
        exit_order_func.get('token')
    )
    print("order_id",order_id)
    
def get_order_details(user_details):
    kite = create_kite(user_details)
    orders = kite.orders()
    return orders