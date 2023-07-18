import json
from kiteconnect import KiteConnect
from pya3 import *
import logging
from MPWizard_calc import *
import datetime

def get_mpwizard_users(broker_filepath):
    with open(broker_filepath, 'r') as file:
        broker_config = json.load(file)
    accounts_to_trade = []
    zerodha_accounts = broker_config.get("zerodha", {})
    accounts_to_trade_zerodha = zerodha_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_zerodha:
        user_account = zerodha_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("MPWizard")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("zerodha", account))

    # Check Aliceblue accounts
    aliceblue_accounts = broker_config.get("aliceblue", {})
    accounts_to_trade_aliceblue = aliceblue_accounts.get("accounts_to_trade", [])

    for account in accounts_to_trade_aliceblue:
        user_account = aliceblue_accounts.get(account, {})
        mpwizard_percentage = user_account.get("percentageRisk", {}).get("MPWizard")
        if mpwizard_percentage is not None:
            accounts_to_trade.append(("aliceblue", account))

    return accounts_to_trade

script_dir = os.path.dirname(os.path.abspath(__file__))   
parent_dir = os.path.abspath(os.path.join(script_dir, '..'))

def load_credentials(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def place_zerodha_order(trading_symbol, transaction_type, trade_type, strike_price, index, users, broker='zerodha'):
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

    if index == 'NIFTY':
        qty = user_details[broker]['MPWizard_qty']['NIFTY_qty']
    elif index == 'BANKNIFTY':
        qty = user_details[broker]['MPWizard_qty']['BANKNIFTY_qty']
    elif index == 'FINNIFTY':
        qty = user_details[broker]['MPWizard_qty']['FINNIFTY_qty']

    if transaction_type == 'BUY':
        order_type = kite.TRANSACTION_TYPE_BUY
    elif transaction_type == 'SELL':
        order_type = kite.TRANSACTION_TYPE_SELL
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
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if trade_type not in user_details[broker]['orders']:
            user_details[broker]['orders']['MPWizard'][trade_type] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade_type].append(order_dict)

    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        mpwizard_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file
    return float(avg_prc)


def place_aliceblue_order(trading_symbol, transaction_type, trade_type, strike_price, index, users, broker='aliceblue'):
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

    if index == 'NIFTY':
        qty = user_details[broker]['MPWizard_qty']['NIFTY_qty']
    elif index == 'BANKNIFTY':
        qty = user_details[broker]['MPWizard_qty']['BANKNIFTY_qty']
    elif index == 'FINNIFTY':
        qty = user_details[broker]['MPWizard_qty']['FINNIFTY_qty']

    if transaction_type == 'BUY':
        order_type = TransactionType.Buy
    elif transaction_type == 'SELL':
        order_type = TransactionType.Sell
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

        order_trade_type = trade_type
        if str(strike_price) not in trading_symbol[3]:
            order_trade_type = "HedgeOrder"

        # Create a new dict for the order
        order_dict = {
            "trade_type": order_trade_type,
            "avg_prc": avg_prc,
            "timestamp": str(datetime.datetime.now()),
            "strike_price": strike_price,
            "tradingsymbol": trading_symbol[3]
        }

        # Create a new list for each trade_type if it doesn't exist
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if trade_type not in user_details[broker]['orders']:
            user_details[broker]['orders']['MPWizard'][trade_type] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade_type].append(order_dict)

    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        mpwizard_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file
    return float(avg_prc)

def place_stoploss_zerodha(trading_symbol, transaction_type, trade_type, strike_price, index, limit_prc, users, broker='zerodha'):
    filepath = os.path.join(parent_dir, 'Utils', 'users', f'{users}.json')
    if not os.path.exists(filepath):
        print("file not exist")
        return
    user_details = load_credentials(filepath)

    if broker not in user_details:
        return

    trigger_prc = limit_prc+1
    api_key = user_details[broker]['api_key']
    access_token = user_details[broker]['access_token']
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    if index == 'NIFTY':
        qty = user_details[broker]['MPWizard_qty']['NIFTY_qty']
    elif index == 'BANKNIFTY':
        qty = user_details[broker]['MPWizard_qty']['BANKNIFTY_qty']
    elif index == 'FINNIFTY':
        qty = user_details[broker]['MPWizard_qty']['FINNIFTY_qty']


    if transaction_type == 'BUY':
        order_type = kite.TRANSACTION_TYPE_BUY
    elif transaction_type == 'SELL':
        order_type = kite.TRANSACTION_TYPE_SELL
    else:
        logging.info(f"Invalid trade type for user {users}.")
        return
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


        logging.info(f"Order placed for user {users}. ID is: {order_id}")

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
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if trade_type not in user_details[broker]['orders']:
            user_details[broker]['orders']['MPWizard'][trade_type] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade_type].append(order_dict)

    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        mpwizard_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file
    return order_id


def place_stoploss_aliceblue(trading_symbol, transaction_type, trade_type, strike_price, index, limit_prc, users, broker='aliceblue'):
    filepath = os.path.join(parent_dir, 'Utils', 'users', f'{users}.json')
    if not os.path.exists(filepath):
        print("file not exist")
        return
    user_details = load_credentials(filepath)

    if broker not in user_details:
        return
    
    trigger_prc = limit_prc+1

    username = str(user_details[broker]['username'])
    api_key = user_details[broker]['api_key']
    alice = Aliceblue(username, api_key = api_key)
    session_id = alice.get_session_id()
    if index == 'NIFTY':
        qty = user_details[broker]['MPWizard_qty']['NIFTY_qty']
    elif index == 'BANKNIFTY':
        qty = user_details[broker]['MPWizard_qty']['BANKNIFTY_qty']
    elif index == 'FINNIFTY':
        qty = user_details[broker]['MPWizard_qty']['FINNIFTY_qty']

    if transaction_type == 'BUY':
        order_type = TransactionType.Buy
    elif transaction_type == 'SELL':
        order_type = TransactionType.Sell
    else:
        logging.info(f"Invalid trade type for user {users}.")
        return

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
        
        logging.info(f"Order placed for user {users}. ID is: {order_id['NOrdNo']}")
        order_no = order_id['NOrdNo']
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
            "timestamp": str(datetime.datetime.now()),
            "strike_price": strike_price,
            "tradingsymbol": trading_symbol[3]
        }

        # Create a new list for each trade_type if it doesn't exist
        if 'orders' not in user_details[broker]:
            user_details[broker]['orders'] = {}
        if trade_type not in user_details[broker]['orders']:
            user_details[broker]['orders'][trade_type] = []

        # Add the order_dict to the corresponding trade_type list
        user_details[broker]['orders'][trade_type].append(order_dict)

    except Exception as e:
        message = f"Order placement failed for user {users}: {e}"
        mpwizard_discord_bot(message)
        logging.info(message)

    with open(filepath, 'w') as file:
        json.dump(user_details, file, indent=4)  # Save the updated user_details back to json file
    return order_no

def adjust_stoploss_zerodha(token, order_id, sl_points, broker='zerodha'):
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)
    for user in user_details[broker]:
        api_key = user_details[broker][user]['api_key']
        access_token = user_details[broker][user]['access_token']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        while True:
            try:
                # Get the LTP
                ltp_data = kite.ltp('NSE:' + token)
                ltp = ltp_data['NSE:' + token]['last_price']

                # Calculate the new limit_prc
                limit_prc = ltp - (sl_points / 2)

                # Modify the stop loss order
                # modify_stoploss_zerodha(order_id, limit_prc)

            except Exception as e:
                message = f"Adjusting stoploss failed for user {user}: {e}"
                # telegram_bot_sendtext_AK(message)
                logging.info(message)
            time.sleep(1)  # Sleep for 1 second before checking again

def adjust_stoploss_aliceblue(token, order_id, sl_points, broker='zerodha'):
    filepath = "Utilities/Siri.json"
    user_details = load_credentials(filepath)
    for user in user_details[broker]:
        api_key = user_details[broker][user]['api_key']
        access_token = user_details[broker][user]['access_token']
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)

        while True:
            try:
                # Get the LTP
                ltp_data = kite.ltp('NSE:' + token)
                ltp = ltp_data['NSE:' + token]['last_price']

                # Calculate the new limit_prc
                limit_prc = ltp - (sl_points / 2)

                # Modify the stop loss order
                # modify_stoploss_zerodha(order_id, limit_prc)

            except Exception as e:
                message = f"Adjusting stoploss failed for user {user}: {e}"
                # telegram_bot_sendtext_AK(message)
                logging.info(message)
            time.sleep(1)  # Sleep for 1 second before checking again
