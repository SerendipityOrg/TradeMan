import logging
from kiteconnect import KiteConnect
import sys,os


DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order_calc as place_order_calc
import Brokers.Zerodha.kite_utils as kite_utils
from MarketUtils.InstrumentBase import Instrument


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
    segment = Instrument().get_segment_by_exchange_token(exchange_token)
    strategy = order_details.get('strategy')
    qty = int(order_details.get('qty'))
    product = order_details.get('product_type')

    transaction_type = kite_utils.calculate_transaction_type(kite,order_details.get('transaction_type'))
    order_type = kite_utils.calculate_order_type(kite,order_details.get('order_type'))
    product_type = kite_utils.calculate_product_type(kite,product)


    limit_prc = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)

    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,  #TODO check for SENSEX
            price= limit_prc,
            tradingsymbol=Instrument().get_trading_symbol_by_exchange_token(exchange_token),
            transaction_type=transaction_type, 
            quantity= qty,
            trigger_price=trigger_price,
            product=product_type,
            order_type=order_type,
            tag= order_details.get('order_tag', None)
        )
        print(f"Order placed. ID is: {order_id}")
        print("order_id",order_id)
        return order_id
    
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        # general_calc.discord_bot(message)
        return None


def place_zerodha_order(order_details: dict):
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
    
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    kite = kite_utils.create_kite_obj(user_details)
    
    try:
        order_id = kite_place_order(kite, order_details, user_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        # You can set default or fallback values if needed
        order_id = None
    
    try:
        place_order_calc.log_order(order_id, order_details)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        

# def update_stoploss(monitor_order_func):
#     print("in update stoploss")
#     global kite
#     if kite is None:
#         user_details,_ = get_user_details(monitor_order_func.get('user'))
#         kite = KiteConnect(api_key=user_details['zerodha']['api_key'])
#         kite.set_access_token(user_details['zerodha']['access_token'])
    
#     order_id = retrieve_order_id(
#             monitor_order_func.get('user'),
#             monitor_order_func.get('broker'),
#             monitor_order_func.get('strategy'),
#             monitor_order_func.get('trade_type'),
#             monitor_order_func.get('token')
#         )

#     new_stoploss = round(float(monitor_order_func.get('limit_prc')),1)
#     trigger_price = round((float(new_stoploss)+1.00),1)
#     try:
#         modify_order = kite.modify_order(variety=kite.VARIETY_REGULAR, 
#                                     order_id=order_id, 
#                                     price = new_stoploss,
#                                     trigger_price = trigger_price)
#     except Exception as e:
#         print(f"Failed to modify the order: {e}")
#     print("zerodha order modified")

def update_kite_stoploss(order_details):
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    kite = kite_utils.create_kite_obj(user_details)
    order_id = place_order_calc.retrieve_order_id(
            order_details.get('user'),
            order_details.get('broker'),
            order_details.get('strategy'),
            order_details.get('trade_type'),
            order_details.get('token').name
        ) 

    # transaction_type = kite_utils.calculate_transaction_type(order_details.get('transaction_type'))
    # order_type = kite_utils.calculate_order_type(order_details.get('order_type'))
    # product_type = kite_utils.calculate_product_type(order_details.get('product_type'))
    # segment = order_details.get('segment')
    # exchange_token = order_details.get('exchange_token')
    # qty = int(order_details.get('qty'))
    new_stoploss = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)

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