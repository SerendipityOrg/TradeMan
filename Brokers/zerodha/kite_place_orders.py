import sys,os

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order_calc as place_order_calc
import Brokers.Zerodha.kite_utils as kite_utils
from MarketUtils.InstrumentBase import Instrument

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

def kite_place_order(kite, order_details):
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
    strategy = order_details.get('strategy')
    exchange_token = order_details.get('exchange_token')
    segment = Instrument().get_segment_by_exchange_token(exchange_token)
    segment_type = kite_utils.calculate_segment_type(kite,segment)
    qty = int(order_details.get('qty'))
    product = order_details.get('product_type')

    transaction_type = kite_utils.calculate_transaction_type(kite,order_details.get('transaction_type'))
    order_type = kite_utils.calculate_order_type(kite,order_details.get('order_type'))
    product_type = kite_utils.calculate_product_type(kite,product)

    limit_prc = order_details.get('limit_prc', None) 
    trigger_price = order_details.get('trigger_prc', None)

    if limit_prc is not None:
        limit_prc = round(float(limit_prc), 2)
        if limit_prc < 0:
            limit_prc = 1.0
    else:
        limit_prc = 0.0
    
    if trigger_price is not None:
        trigger_price = round(float(trigger_price), 2)
        if trigger_price < 0:
            trigger_price = 1.5

    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange= segment_type, 
            price= limit_prc,
            tradingsymbol=Instrument().get_trading_symbol_by_exchange_token(exchange_token),
            transaction_type=transaction_type, 
            quantity= qty,
            trigger_price=trigger_price,
            product=product_type,
            order_type=order_type,
            tag= order_details.get('trade_id', None)
        )
        print(f"Order placed. ID is: {order_id}")
        return order_id
    
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        discord.discord_bot(message,strategy)
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
        order_id = kite_place_order(kite, order_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        order_id = None
    
    try:
        if order_details.get('strategy') == 'MPWizard':
            place_order_calc.log_order(order_id, order_details)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        
def update_kite_stoploss(order_details):
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    kite = kite_utils.create_kite_obj(user_details)
    order_id = place_order_calc.retrieve_order_id(
            order_details.get('username'),
            order_details.get('strategy'),
            order_details.get('transaction_type'),
            order_details.get('exchange_token')
        )

    new_stoploss = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)

    try:
        modify_order = kite.modify_order(variety=kite.VARIETY_REGULAR, 
                                    order_id=order_id, 
                                    price = new_stoploss,
                                    trigger_price = trigger_price)
        print("zerodha order modified", modify_order)
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        discord.discord_bot(message, order_details.get('strategy'))
        return None
        
    print("zerodha order modified")
