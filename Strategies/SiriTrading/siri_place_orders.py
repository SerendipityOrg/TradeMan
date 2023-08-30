import json
from kiteconnect import KiteConnect
from pya3 import *
import logging
from Utilities.messaging_bot import telegram_bot_sendtext_AK


def load_credentials(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def place_zerodha_order(trading_symbol, transaction_type, trade_type, strike_price, index, broker='zerodha'):
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)

    for user in user_details[broker]:
        api_key = user_details[broker][user]['api_key']
        access_token = user_details[broker][user]['access_token']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        if index == 'NIFTY':
            qty = user_details[broker][user]['nf_qty']
        elif index == 'BANKNIFTY':
            qty = user_details[broker][user]['bnf_qty']
        elif index == 'FINNIFTY':
            qty = user_details[broker][user]['fnf_qty']


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
            telegram_bot_sendtext_AK(message)
            logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file


def place_aliceblue_order(trading_symbol, transaction_type, trade_type, strike_price, index, broker='aliceblue'):
    print("Inside place_aliceblue_order")
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)   
    

    for user in user_details[broker]:
        username = str(user_details[broker][user]['username'])
        api_key = user_details[broker][user]['api_key']
        alice = Aliceblue(username, api_key = api_key)
        session_id = alice.get_session_id()
        if index == 'NIFTY':
            qty = user_details[broker][user]['nf_qty']  
        elif index == 'BANKNIFTY':
            qty = user_details[broker][user]['bnf_qty']
        elif index == 'FINNIFTY':
            qty = user_details[broker][user]['fnf_qty']

        if transaction_type == 'BUY':
            order_type = TransactionType.Buy
        elif transaction_type == 'SELL':
            order_type = TransactionType.Sell
        else:
            logging.info(f"Invalid trade type for user {user}.")
            continue

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
            logging.info(f"Order placed for user {user}. ID is: {order_id['NOrdNo']}")

            # Fetch avg_prc using the order_id
            avg_prc = alice.get_order_history(order_id['NOrdNo'])['Avgprc']

            order_trade_type = trade_type
            if str(strike_price) not in trading_symbol[3]:
                order_trade_type = "HedgeOrder"

            # Create a new dict for the order
            order_dict = {
                "trade_type": order_trade_type,
                "avg_prc": avg_prc,
                "timestamp": str(datetime.now()),
                "strike_price": strike_price,
                "tradingsymbol": trading_symbol[3]
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
            telegram_bot_sendtext_AK(message)
            logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file

def place_stoploss_zerodha(trading_symbol, transaction_type, trade_type, strike_price, index, limit_prc, trigger_prc, broker='zerodha'):
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)

    for user in user_details[broker]:
        api_key = user_details[broker][user]['api_key']
        access_token = user_details[broker][user]['access_token']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        if index == 'NIFTY':
            qty = user_details[broker][user]['nf_qty']
        elif index == 'BANKNIFTY':
            qty = user_details[broker][user]['bnf_qty']
        elif index == 'FINNIFTY':
            qty = user_details[broker][user]['fnf_qty']


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
                                        price=limit_prc,
                                        tradingsymbol=trading_symbol,
                                        transaction_type=order_type,
                                        quantity=qty,
                                        trigger_price=trigger_prc,
                                        product=kite.PRODUCT_MIS,
                                        order_type=kite.ORDER_TYPE_SL)


            logging.info(f"Order placed for user {user}. ID is: {order_id}")
            print(order_id)
            # Fetch avg_prc using the order_id
            order_history = kite.order_history(order_id=order_id)
            avg_prc = order_history[-1]['average_price']  # Assuming last entry contains the final average price

            order_trade_type = trade_type
            if str(strike_price) not in trading_symbol:
                order_trade_type = "HedgeOrder"

            # Create a new dict for the order
            order_dict = {
                "order_no": order_id,
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
            telegram_bot_sendtext_AK(message)
            logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file



def place_stoploss_aliceblue(trading_symbol, transaction_type, trade_type, strike_price, index, limit_prc, trigger_prc, broker='aliceblue'):
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)

    for user in user_details[broker]:
        username = str(user_details[broker][user]['username'])
        api_key = user_details[broker][user]['api_key']
        alice = Aliceblue(username, api_key = api_key)
        session_id = alice.get_session_id()
        if index == 'NIFTY':
            qty = user_details[broker][user]['nf_qty']  
        elif index == 'BANKNIFTY':
            qty = user_details[broker][user]['bnf_qty']
        elif index == 'FINNIFTY':
            qty = user_details[broker][user]['fnf_qty']

        if transaction_type == 'BUY':
            order_type = TransactionType.Buy
        elif transaction_type == 'SELL':
            order_type = TransactionType.Sell
        else:
            logging.info(f"Invalid trade type for user {user}.")
            continue

        try:
            order_id = alice.place_order(transaction_type = order_type,
                                         instrument = trading_symbol,
                                         quantity = qty ,
                                         order_type = OrderType.StopLossLimit,
                                         product_type = ProductType.Intraday,
                                         price = limit_prc, #####limit price
                                         trigger_price = trigger_prc,#########trigger price
                                         stop_loss = None,
                                         square_off = None,
                                         trailing_sl = None,
                                         is_amo = False)
            
            logging.info(f"Order placed for user {user}. ID is: {order_id['NOrdNo']}")
            order_no = order_id['NOrdNo']
            print(order_no)
            # Fetch avg_prc using the order_id
            avg_prc = alice.get_order_history(order_id['NOrdNo'])['Avgprc']

            order_trade_type = trade_type
            if str(strike_price) not in trading_symbol[3]:
                order_trade_type = "HedgeOrder"

            # Create a new dict for the order
            order_dict = {
                "order_no": order_no,
                "trade_type": order_trade_type,
                "avg_prc": avg_prc,
                "timestamp": str(datetime.now()),
                "strike_price": strike_price,
                "tradingsymbol": trading_symbol[3]
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
            telegram_bot_sendtext_AK(message)
            logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file