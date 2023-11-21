import sys,os

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.Discord.discordchannels as discord
import Brokers.place_order_calc as place_order_calc
import Brokers.Aliceblue.alice_utils as alice_utils
from MarketUtils.InstrumentBase import Instrument

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

def alice_place_order(alice, order_details):
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
    strategy = order_details.get('strategy')
    exchange_token = order_details.get('exchange_token')
    segment = Instrument().get_segment_by_exchange_token(exchange_token)
    qty = int(order_details.get('qty'))
    product = order_details.get('product_type')

    transaction_type = alice_utils.calculate_transaction_type(order_details.get('transaction_type'))
    order_type = alice_utils.calculate_order_type(order_details.get('order_type'))
    product_type = alice_utils.calculate_product_type(product)

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
        
        print(f"Order placed. ID is: {order_id}")
        return order_id['NOrdNo'] 
  
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        discord.discord_bot(message,strategy)
        return None

def place_aliceblue_order(order_details: dict,alice = None):
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
    if alice is None:
        alice = alice_utils.create_alice_obj(user_details)   

    try:
        order_id = alice_place_order(alice, order_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        order_id = None
    try:
        if order_details.get('strategy') == 'MPWizard':
            place_order_calc.log_order(order_id, order_details)
    except Exception as e:
        print(f"Failed to log the order: {e}")  

def update_alice_stoploss(order_details,alice= None):
    user_details = place_order_calc.assign_user_details(order_details.get('username'))
    if alice is None:
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

    try:
        modify_order =  alice.modify_order(transaction_type = transaction_type,
                    order_id=str(order_id),
                    instrument = alice.get_instrument_by_token(segment, exchange_token),
                    quantity = qty,
                    order_type = order_type,
                    product_type = product_type,
                    price=new_stoploss,
                    trigger_price = trigger_price)
        print("alice modify_order",modify_order)
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['username']}"
        print(message)
        discord.discord_bot(message, order_details.get('strategy'))
        return None
    
def sweep_alice_orders(userdetails):
    try:
        alice = alice_utils.create_alice_obj(userdetails)
        orders = alice.get_order_history('')
        positions = alice.get_daywise_positions()
    except Exception as e:
        print(f"Failed to fetch orders and positions: {e}")
        return None

    if len(positions) == 2:
        print("No positions found")
    else:    
        token_quantities = {position['Token']: abs(int(position['Netqty'])) for position in positions if position['Pcode'] == 'MIS' and position['realisedprofitloss']=='0.00'}

        for token, quantity in token_quantities.items():
            max_qty = place_order_calc.read_max_order_qty_for_symbol(token)  # Fetch max qty for the token
            remaining_qty = quantity

            for order in orders:
                if token == order['token'] and order['remarks'] is not None and order['Status'] == 'complete':
                    while remaining_qty > 0:
                        current_qty = min(remaining_qty, max_qty)
                        order_details = {
                            'trade_id': order['remarks'],
                            'exchange_token': int(order['token']),
                            'transaction_type': order['Trantype'],
                            'qty': current_qty
                        }
                        place_aliceblue_order(order_details, alice)  # Place each split order
                        remaining_qty -= current_qty

        for pending_order in orders:
            if orders[0]['stat'] == 'Not_Ok':
                print("No orders found")
            elif pending_order['Status'] == 'trigger pending':
                print(pending_order['Nstordno'])
                alice.cancel_order(pending_order['Nstordno'])






    
                

    
