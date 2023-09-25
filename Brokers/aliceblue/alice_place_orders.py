import logging
from pya3 import *
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(CURRENT_DIR, '..', '..','Utils')

sys.path.append(UTILS_DIR)
from general_calc import *

FILE_DIR = os.path.join(CURRENT_DIR,'..',)
sys.path.append(FILE_DIR)
from place_order_calc import *

sys.path.append(os.path.join(UTILS_DIR, 'Discord'))
import discordchannels as discord

alice = None

def alice_place_order(alice, strategy, order_details, qty, user_details):
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

    transaction_type = order_details.get('transaction_type')
    if transaction_type == 'BUY':
        transaction_type = TransactionType.Buy
    elif transaction_type == 'SELL':
        transaction_type = TransactionType.Sell
    else:
        raise ValueError("Invalid transaction_type in order_details")

    order_type_value = order_details.get('order_trade_type')
    if order_type_value == 'Stoploss':
        order_type = OrderType.StopLossLimit
    elif order_type_value == 'Market':
        order_type = OrderType.Market
    else:
        raise ValueError("Invalid order_type in order_details")
    
    if strategy == 'Overnight_Options':
        product_type = ProductType.Normal
    else:
        product_type = ProductType.Intraday
    
    limit_prc = round(float(order_details.get('limit_prc', 0.0)),1)
    trigger_price = round(float(limit_prc) + 1.00, 1) if limit_prc else None
    try:
        order_id = alice.place_order(transaction_type = transaction_type, 
                                        instrument = order_details['tradingsymbol'],
                                        quantity = qty ,
                                        order_type = order_type,
                                        product_type = product_type,
                                        price = round(limit_prc,1),
                                        trigger_price = trigger_price,
                                        stop_loss = None,
                                        square_off = None,
                                        trailing_sl = None,
                                        is_amo = False,
                                        order_tag = strategy)
        print("order_id",order_id)

        logging.info(f"Order placed. ID is: {order_id}")

        order_id_value = order_id['NOrdNo']
        if not order_id_value:
            raise Exception("Order_id not found")
        
        avg_prc_data = alice.get_order_history(order_id_value)
        avg_prc = avg_prc_data.get('Avgprc')

        if avg_prc == 0.0:
            try:
                log_order(order_id_value, 0.0, order_details, user_details, strategy)
            except Exception as e:
                print(f"Failed to log the order with zero avg_prc: {e}")
            
            raise Exception("Order completed but average price not found.")
        
        if strategy == 'Siri':
            try:
                msg = f"Avgprc is {avg_prc}"
                discord.discord_bot(msg,"siri")
            except Exception as e:
                print(f"Discord bot failed: {e}") 
        
        return order_id_value, avg_prc # Merge place_order
  
    except Exception as e:
        message = f"Order placement failed: {e} for {order_details['user']}"
        print(message)
        # general_calc.discord_bot(message)
        return None

def place_aliceblue_order(strategy: str, order_details: dict, qty=None):
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
    global alice
    user_details,_ = get_user_details(order_details['user'])
    alice = Aliceblue(user_id=user_details['aliceblue']['username'],api_key=user_details['aliceblue']['api_key'])
    session_id = alice.get_session_id()
    
    if qty is None:
        qty = get_quantity(user_details, 'aliceblue', strategy, order_details['tradingsymbol'])

    order_details['qty'] = qty
    try:
        order_id, avg_price = alice_place_order(alice, strategy, order_details, qty, user_details)
    except TypeError:
        print("Failed to place the order and retrieve the order ID and average price.")
        # You can set default or fallback values if needed
        order_id = None
        avg_price = 0.0
    try:
        log_order(order_id, avg_price, order_details, user_details, strategy)
    except Exception as e:
        print(f"Failed to log the order: {e}")
        
    return order_id, avg_price

def create_alice(user_details):
    global alice
    alice = Aliceblue(user_id=user_details['aliceblue']['username'],api_key=user_details['aliceblue']['api_key'])
    session_id = alice.get_session_id()
    return alice

def update_stoploss(monitor_order_func):
    global alice
    if alice is None:
        user_details,_ = get_user_details(monitor_order_func.get('user'))
        alice = create_alice(user_details)

    order_id = retrieve_order_id(
            monitor_order_func.get('user'),
            monitor_order_func.get('broker'),
            monitor_order_func.get('strategy'),
            monitor_order_func.get('trade_type'),
            monitor_order_func.get('token').name
        )
    new_stoploss = round(float(monitor_order_func.get('limit_prc')),1)
    trigger_price = round((float(new_stoploss)+1.00),1)
    modify_order =  alice.modify_order(transaction_type = TransactionType.Sell,
                    order_id=str(order_id),
                    instrument = monitor_order_func.get('token'),
                    quantity = int(monitor_order_func.get('qty')),
                    order_type = OrderType.StopLossLimit,
                    product_type = ProductType.Intraday,
                    price=new_stoploss,
                    trigger_price = trigger_price)
    print("alice modify_order",modify_order)
