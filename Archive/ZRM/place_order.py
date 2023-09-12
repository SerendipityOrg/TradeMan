import json
from kiteconnect import KiteConnect
from pya3 import *
import logging
from ZrOm_calc import zrm_discord_bot
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))   
parent_dir = os.path.abspath(os.path.join(script_dir, '..'))

def load_credentials(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)


def place_zerodha_order(trading_symbol, transaction_type, trade_type, qty, strike_price, index, users, broker='zerodha'):
    filepath = os.path.join(parent_dir, 'Utils', 'users', f'{users}.json')
    if not os.path.exists(filepath):
        print("file not exist")
        return
    user_details = load_credentials(filepath)

    if broker not in user_details:
        return

    api_key = user_details[broker]['api_key']
    access_token = user_details[broker]['access_token']
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)


    if transaction_type == 'BUY':
        order_type = kite.TRANSACTION_TYPE_BUY
        trade = 'BUY'
    elif transaction_type == 'SELL':
        order_type = kite.TRANSACTION_TYPE_SELL
        trade = 'SELL'
    else:
        logging.info(f"Invalid trade type for user {users}.")
        return

    try:           
        order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
                                    exchange=kite.EXCHANGE_NFO,
                                    tradingsymbol=trading_symbol,
                                    transaction_type=order_type,
                                    quantity=qty,
                                    product=kite.PRODUCT_MIS,
                                    order_type=kite.ORDER_TYPE_MARKET)


        logging.info(f"Order placed for user {users}. ID is: {order_id}")
        
        # Fetch avg_prc using the order_id
        order_history = kite.order_history(order_id=order_id)
        avg_prc = order_history[-1]['average_price']  # Assuming last entry contains the final average price

        order_trade_type = trade
        print("checking the orderdict")
        # Create a new dict for the order
        order_dict = {
            "trade_type": order_trade_type,
            "avg_prc": avg_prc,
            "timestamp": str(datetime.now()),
            "strike_price": strike_price,
            "tradingsymbol": trading_symbol
        }

        print(order_dict)

        # Create a new list for each trade_type if it doesn't exist
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if 'ZRM' not in user_details[broker]['orders']:
            user_details[broker]['orders']['ZRM'] = {}
        if trade_type not in user_details[broker]['orders']['ZRM']:
            user_details[broker]['orders']['ZRM'][trade] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade].append(order_dict)
        print(order_id)
    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        zrm_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file



def place_aliceblue_order(trading_symbol, transaction_type, trade_type, qty, strike_price, index, users, broker='aliceblue'):
    filepath = os.path.join(parent_dir, 'Utils', 'users', f'{users}.json')
    if not os.path.exists(filepath):
        print("file not exist")
        return
    user_details = load_credentials(filepath)

    if broker not in user_details:
        return
    
    username = str(user_details[broker]['username'])
    api_key = user_details[broker]['api_key']
    alice = Aliceblue(username, api_key = api_key)
    session_id = alice.get_session_id()

    if transaction_type == 'BUY':
        order_type = TransactionType.Buy
        trade = 'BUY'
    elif transaction_type == 'SELL':
        order_type = TransactionType.Sell
        trade = 'SELL'
    else:
        logging.info(f"Invalid trade type for user {users}.")
        return
    
    try:
        order_id = alice.place_order(transaction_type = order_type,
                                        instrument = trading_symbol,
                                        quantity = qty ,
                                        order_type = OrderType.Market,
                                        product_type = ProductType.Intraday,
                                        price = 0.0,
                                        trigger_price = None,
                                        stop_loss = None,
                                        square_off = None,
                                        trailing_sl = None,
                                        is_amo = False)
        logging.info(f"Order placed for user {users}. ID is: {order_id['NOrdNo']}")

        # Fetch avg_prc using the order_id
        avg_prc = alice.get_order_history(order_id['NOrdNo'])['Avgprc']

        order_trade_type = trade

        # Create a new dict for the order
        order_dict = {
            "trade_type": order_trade_type,
            "avg_prc": avg_prc,
            "timestamp": str(datetime.now()),
            "strike_price": strike_price,
            "tradingsymbol": trading_symbol[3]
        }

        # Create a new list for each trade_type if it doesn't exist
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if 'ZRM' not in user_details[broker]['orders']:
            user_details[broker]['orders']['ZRM'] = {}
        if trade_type not in user_details[broker]['orders']['ZRM']:
            user_details[broker]['orders']['ZRM'][trade_type] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade_type].append(order_dict)

    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        zrm_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file

