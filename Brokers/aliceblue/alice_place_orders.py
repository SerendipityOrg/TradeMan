import logging
from pya3 import *
from place_order_calc import log_order, get_user_details, get_quantity,retrieve_order_id
import sys
sys.path.append(r'C:\Users\user\Desktop\Dev\Utils')
import general_calc

alice = None


def place_order(alice, order_details, qty):

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
    
    if order_details['transaction_type'] == 'BUY':
        transaction_type = TransactionType.Buy
    elif order_details['transaction_type'] == 'SELL':
        transaction_type = TransactionType.Sell
        
    if order_details['order_type'] == 'Stoploss':
        order_type = OrderType.StopLossLimit
    elif order_details['order_type'] == 'Market':
        order_type = OrderType.Market
        
    limit_prc = 0.0 
    trigger_price = None   

    if 'limit_prc' in order_details:      
        limit_prc = round(float(order_details['limit_prc']),1)
        trigger_price = round((float(order_details['limit_prc'])+1.00),1)
    try:
        order_id = alice.place_order(transaction_type = transaction_type, 
                                        instrument = order_details['tradingsymbol'],
                                        quantity = qty ,
                                        order_type = order_type,
                                        product_type = ProductType.Intraday,
                                        price = limit_prc,
                                        trigger_price = trigger_price,
                                        stop_loss = None,
                                        square_off = None,
                                        trailing_sl = None,
                                        is_amo = False)
        logging.info(f"Order placed. ID is: {order_id}")
        
        avg_prc = alice.get_order_history(order_id['NOrdNo'])['Avgprc']
        order_id = order_id['NOrdNo']
        return order_id, avg_prc
  
    except Exception as e:
        message = f"Order placement failed: {e}"
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
        qty = get_quantity(user_details, strategy, order_details['tradingsymbol'],'aliceblue')
    
    order_details['qty'] = qty
    order_id, avg_price = place_order(alice, order_details, qty)
    log_order(order_id, avg_price, order_details, user_details, qty ,strategy)
    return order_id, avg_price



def update_stoploss(monitor_order_func):
    global alice
    print(monitor_order_func)
    order_id = retrieve_order_id(
            monitor_order_func.get('user'),
            monitor_order_func.get('broker'),
            monitor_order_func.get('strategy'),
            monitor_order_func.get('trade_type'),
            monitor_order_func['token']
        )
    
    new_stoploss = round(float(monitor_order_func.get('target')),1)
    trigger_price = round((float(new_stoploss)+1.00),1)
    print(order_id,new_stoploss,trigger_price,monitor_order_func.get('token'))
    modify_order =  alice.modify_order(transaction_type = TransactionType.Sell,
                    order_id=str(order_id),
                    instrument = monitor_order_func.get('token'),
                    quantity = int(monitor_order_func.get('qty')),
                    order_type = OrderType.StopLossLimit,
                    product_type = ProductType.Intraday,
                    price=new_stoploss,
                    trigger_price = trigger_price)
    print(modify_order)
    
