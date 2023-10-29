import logging
from pya3 import *
import sys
import icecream as ic

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order_calc as place_order_calc
import Brokers.Aliceblue.alice_utils as alice_utils
from MarketUtils.InstrumentBase import Instrument

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

def alice_place_order(alice, order_details, user_details=None):
    """
    Place an order with Aliceblue broker.

    Args:
        alice (Aliceblue): The Aliceblue instance.
        order_details (dict): The details of the order.
        qty (int): The quantity of the order.

    Returns:
        float: The average price of the order.

    Raises:
        Exception: If the order placement fails.
    """  
    exchange_token = order_details.get('exchange_token')
    segment = Instrument().get_segment_by_exchange_token(exchange_token)
    qty = int(order_details.get('qty'))
    product = order_details.get('product_type')

    transaction_type = alice_utils.calculate_transaction_type(order_details.get('transaction_type'))
    order_type = alice_utils.calculate_order_type(order_details.get('order_type'))
    product_type = alice_utils.calculate_product_type(product)

    limit_prc = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)
    
    try:
        order_id = alice.place_order(transaction_type = transaction_type, 
                                        instrument = alice.get_instrument_by_token(segment, int(exchange_token)),
                                        quantity = qty ,
                                        order_type = order_type,
                                        product_type = product_type,
                                        price = limit_prc,
                                        trigger_price = trigger_price,
                                        stop_loss = None,
                                        square_off = None,
                                        trailing_sl = None,
                                        is_amo = False,
                                        order_tag = order_details.get('trade_id', None))
        print("order_id",order_id)

        return order_id['NOrdNo'] # Merge place_order  #TODO retrun only order_id for all the brokers
  
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        # general_calc.discord_bot(message)
        return None

def place_aliceblue_order(order_details: dict):
    """
    Place an order with Aliceblue broker.

    Args:
        strategy (str): The name of the strategy.
        order_details (dict): The details of the order.
        qty (int, optional): The quantity of the order. Defaults to None.

    Returns:
        float: The average price of the order.

    Raises:
        Exception: If the order placement fails.

    """
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    alice = alice_utils.create_alice_obj(user_details)   

    try:
        order_id = alice_place_order(alice, order_details, user_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        # You can set default or fallback values if needed
        order_id = None
    try:
        place_order_calc.log_order(order_id, order_details)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        


def update_alice_stoploss(order_details):
    print("in update stoploss")
    print(order_details)
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    alice = alice_utils.create_alice_obj(user_details)
    order_id = place_order_calc.retrieve_order_id(
            order_details.get('username'),
            order_details.get('strategy'),
            order_details.get('transaction_type'),
            order_details.get('exchange_token')
        ) 

    transaction_type = alice_utils.calculate_transaction_type(order_details.get('transaction_type'))
    order_type = alice_utils.calculate_order_type(order_details.get('order_type'))
    product_type = alice_utils.calculate_product_type(order_details.get('product_type'))
    segment = order_details.get('segment')
    exchange_token = order_details.get('exchange_token')
    qty = int(order_details.get('qty'))
    new_stoploss = order_details.get('limit_prc', 0.0)
    trigger_price = order_details.get('trigger_prc', None)

    modify_order =  alice.modify_order(transaction_type = transaction_type,
                order_id=str(order_id),
                instrument = alice.get_instrument_by_token(segment, exchange_token),
                quantity = qty,
                order_type = order_type,
                product_type = product_type,
                price=new_stoploss,
                trigger_price = trigger_price)
    print("alice modify_order",modify_order)




# def update_stoploss(order_details):
#     print("in update stoploss")
#     global alice
#     if alice is None:
#         user_details,_ = get_user_details(order_details.get('user'))
#         alice = create_alice(user_details)
#     print(order_details.get('token'))
#     order_id = retrieve_order_id(
#             order_details.get('user'),
#             order_details.get('broker'),
#             order_details.get('strategy'),
#             order_details.get('trade_type'),
#             order_details.get('token').name
#         )
#     new_stoploss = round(float(order_details.get('limit_prc')),1)
#     trigger_price = round((float(new_stoploss)+1.00),1)
#     modify_order =  alice.modify_order(transaction_type = TransactionType.Sell,
#                     order_id=str(order_id),
#                     instrument = order_details.get('token'),
#                     quantity = int(order_details.get('qty')),
#                     order_type = OrderType.StopLossLimit,
#                     product_type = ProductType.Intraday,
#                     price=new_stoploss,
#                     trigger_price = trigger_price)
#     print("alice modify_order",modify_order)

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
    alice = create_alice(user_details)
    order_details = alice.get_order_history('')
    return order_details