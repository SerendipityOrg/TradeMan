import time
from kiteconnect import KiteConnect
import pya3
from telethon.sync import TelegramClient
import json
import datetime
import pandas as pd

class OrderManager:
    def __init__(self, brokers_file, instruments, telegram_bot):
        # Read brokers from file
        with open(brokers_file, 'r') as file:
            self.brokers = json.load(file)
        self.instruments = instruments
        self.telegram_bot = telegram_bot
    
    
    def place_order(self, broker, account, order_type):
        # Retrieve account details
        account_details = self.brokers.get(broker, {}).get(account, {})
        
        # Check if the broker is Zerodha
        if broker == 'zerodha':
            api_key = account_details.get('api_key')
            access_token = account_details.get('access_token')
            
            # Initialize Kite Connect
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            
            # Place order using Kite Connect API #TODO: Uncomment this block
            # try:
            #     order_id = kite.place_order(
            #         tradingsymbol="RELIANCE",
            #         exchange=kite.EXCHANGE_NSE,
            #         transaction_type=kite.TRANSACTION_TYPE_BUY,
            #         quantity=1,
            #         order_type=kite.ORDER_TYPE_MARKET,
            #         product=kite.PRODUCT_NRML
            #     )
            #     return order_id
            # except Exception as e:
            #     # Send a message to the Telegram group if the order is not placed successfully
            #     self.telegram_bot.send_message(f"Failed to place order with Zerodha: {str(e)}")
            #     return None
        
        # Check if the broker is Alice Blue
        elif broker == 'aliceblue':
            username = account_details.get('username')
            password = account_details.get('password')
            two_fa = account_details.get('two_fa')
            api_key = account_details.get('api_key')
            api_secret = account_details.get('api_secret')
            
            # Initialize Alice Blue
            alice = pya3.AliceBlue(username=username, password=password, twoFA=two_fa, api_secret=api_secret, app_id=api_key)
            
            # Place order using PyA3 API
            # try:
            #     instrument = alice.get_instrument_for_fno(exch="NFO", symbol='BANKNIFTY', expiry_date="2023-06-29", is_fut=False, strike=37700, is_CE=False)
            #     order_id = alice.place_order(instrument=instrument, qty=1, is_buy=True, order_type=pya3.OrderType.Market, price=0)
            #     return order_id
            # except Exception as e:
            #     # Send a message to the Telegram group if the order is not placed successfully
            #     self.telegram_bot.send_message(f"Failed to place order with Alice Blue: {str(e)}")
            #     return None
        
        else:
            self.telegram_bot.send_message(f"Unknown broker: {broker}")
            return None


    def place_stop_loss(self, broker, account, order_type):
        # Retrieve account details
        account_details = self.brokers.get(broker, {}).get(account, {})
        siri_capital = account_details.get('siri_capital')
        
        # Calculate the stop loss amount (2% of siri_capital)
        stop_loss_amount = 0.02 * siri_capital
        
        # Check if the broker is Zerodha
        if broker == 'zerodha':
            api_key = account_details.get('api_key')
            access_token = account_details.get('access_token')
            
            # Initialize Kite Connect
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            
            # Place SL order using Kite Connect API
            # try:
            #     order_id = kite.place_order(
            #         tradingsymbol="RELIANCE",
            #         exchange=kite.EXCHANGE_NSE,
            #         transaction_type=kite.TRANSACTION_TYPE_SELL if order_type == 'call' else kite.TRANSACTION_TYPE_BUY,
            #         quantity=1,
            #         order_type=kite.ORDER_TYPE_SL,
            #         product=kite.PRODUCT_NRML,
            #         trigger_price=stop_loss_amount
            #     )
            #     return order_id
            # except Exception as e:
            #     # Send a message to the Telegram group if the order is not placed successfully
            #     self.telegram_bot.send_message(f"Failed to place SL order with Zerodha: {str(e)}")
            #     return None
        
        # Check if the broker is Alice Blue
        elif broker == 'aliceblue':
            print("Alice Blue")
            # username = account_details.get('username')
            # password = account_details.get('password')
            # two_fa = account_details.get('two_fa')
            # api_key = account_details.get('api_key')
            # api_secret = account_details.get('api_secret')
            
            # # Initialize Alice Blue
            # alice = pya3.AliceBlue(username=username, password=password, twoFA=two_fa, api_secret=api_secret, app_id=api_key)
            
            # # Place SL order using PyA3 API
            # try:
            #     instrument = alice.get_instrument_for_fno(exch="NFO", symbol='BANKNIFTY', expiry_date="2023-06-29", is_fut=False, strike=37700, is_CE=False)
            #     order_id = alice.place_order(
            #         instrument=instrument,
            #         qty=1,
            #         is_buy=(order_type == 'put'),
            #         order_type=pya3.OrderType.StopLossMarket,
            #         price=stop_loss_amount
            #     )
            #     return order_id
            # except Exception as e:
            #     # Send a message to the Telegram group if the order is not placed successfully
            #     self.telegram_bot.send_message(f"Failed to place SL order with Alice Blue: {str(e)}")
            #     return None
        
        else:
            self.telegram_bot.send_message(f"Unknown broker: {broker}")
            return None


    def monitor_orders(self):
        while True:
            for broker_name, broker in self.brokers.items():
                for account_name, account in broker.get_accounts().items():
                    # Fetch the current order details
                    order_details = account.get_order_details()
                    
                    # Check if the order is open
                    if order_details and order_details['status'] == 'OPEN':
                        # Fetch the LTP (Last Traded Price) of the instrument
                        ltp = broker.get_ltp(order_details['instrument_token'])
                        
                        # Update the trailing stop loss if necessary
                        self.update_trailing_sl(broker, account, ltp)
                        
                        # Check if the stop loss is hit
                        if self.order_hit_sl(broker, account, ltp):
                            # Send a message to the Telegram group
                            message = f"Stop Loss hit for {order_details['instrument_name']} in account {account_name} with broker {broker_name}. Order exited at {ltp}."
                            self.telegram_bot.send_message(message)
                            
                            # Update the 'Brokers.json' file with the order exit details
                            broker.update_order_details(account, {
                                'status': 'CLOSED',
                                'exit_price': ltp
                            })
                            
            # Wait for 1 minute before checking again
            time.sleep(60)

    def update_trailing_sl(self, broker, account, ltp):
        """
        Update the trailing stop loss for an open order.
        
        :param broker: The broker through which the order was placed.
        :param account: The account in which the order was placed.
        :param ltp: The last traded price of the instrument.
        """
        # Fetch the current order details
        order_details = account.get_order_details()

        # Check if the order is open and has a stop loss
        if order_details and order_details['status'] == 'OPEN' and 'stop_loss' in order_details:
            # Calculate the new stop loss price as 2% below the LTP
            new_stop_loss = ltp * 0.98

            # If the new stop loss is higher than the current stop loss, update it
            if new_stop_loss > order_details['stop_loss']:
                # Update the stop loss in the order details
                order_details['stop_loss'] = new_stop_loss

                # Send the updated stop loss to the broker's API to modify the order
                broker.modify_order(account, order_details['order_id'], new_stop_loss)

                # Update the 'Brokers.json' file with the new stop loss
                broker.update_order_details(account, order_details)

                # Send a message to the Telegram group
                message = f"Trailing Stop Loss updated to {new_stop_loss} for {order_details['instrument_name']} in account {account.get_username()} with broker {broker.get_name()}."
                self.telegram_bot.send_message(message)

    def order_hit_sl(self, broker, account, ltp):
        """
        Check if the stop loss for an open order has been hit.
        
        :param broker: The broker through which the order was placed.
        :param account: The account in which the order was placed.
        :param ltp: The last traded price of the instrument.
        :return: True if the stop loss has been hit, False otherwise.
        """
        # Fetch the current order details
        order_details = account.get_order_details()

        # Check if the order is open and has a stop loss
        if order_details and order_details['status'] == 'OPEN' and 'stop_loss' in order_details:
            # Check if the LTP is below the stop loss
            if ltp <= order_details['stop_loss']:
                return True

        return False
    
        
##############################################################################################