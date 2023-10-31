import json
from kiteconnect import KiteConnect
from pya3 import *
import logging
# from Utilities.messaging_bot import telegram_bot_sendtext_AK


def load_credentials(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def place_zerodha_order(trading_symbol, transaction_type, trade_type, qty, strike_price, index, broker='zerodha'):
    # print(trading_symbol, transaction_type, qty, strike_price, index, broker)
    filepath = "MarketSimulator.json"
    user_details = load_credentials(filepath)

    for user in user_details[broker]:
        api_key = user_details[broker][user]['api_key']
        access_token = user_details[broker][user]['access_token']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        if transaction_type == 'BUY':
            order_type = kite.TRANSACTION_TYPE_BUY
        elif transaction_type == 'SELL':
            order_type = kite.TRANSACTION_TYPE_SELL
        else:
            logging.info(f"Invalid trade type for user {user}.")
            continue

        try:           
            order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
                                        exchange=kite.EXCHANGE_NFO,
                                        tradingsymbol=trading_symbol,
                                        transaction_type=order_type,
                                        quantity=qty,
                                        product=kite.PRODUCT_MIS,
                                        order_type=kite.ORDER_TYPE_MARKET)

            print(f"Order placed for user {user}. ID is: {order_id}")
            logging.info(f"Order placed for user {user}. ID is: {order_id}")
            
            # Fetch avg_prc using the order_id
            order_history = kite.order_history(order_id=order_id)
            avg_prc = order_history[-1]['average_price']  # Assuming last entry contains the final average price

            order_trade_type = trade_type
            if str(strike_price) not in trading_symbol:
                order_trade_type = "HedgeOrder"

            # Create a new dict for the order
            order_dict = {
                "trade_type": order_trade_type,
                "avg_prc": avg_prc,
                "timestamp": str(datetime.now()),
                "strike_price": strike_price,
                "tradingsymbol": trading_symbol
            }

            # Create a new list for each trade_type if it doesn't exist
            if 'orders' not in user_details[broker][user]:
                user_details[broker][user]['orders'] = {}
            if trade_type not in user_details[broker][user]['orders']:
                user_details[broker][user]['orders'][trade_type] = []

            # Add the order_dict to the corresponding trade_type list
            user_details[broker][user]['orders'][trade_type].append(order_dict)

        except Exception as e:
            message = f"Order placement failed for user {user}: {e}"
            print(message)
            # telegram_bot_sendtext_AK(message)
            logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file
