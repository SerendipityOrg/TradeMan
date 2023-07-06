from kiteconnect import KiteConnect
import time
import json
from telegram_bot import discord_bot

class OrderMonitor:
    def __init__(self, brokers_file, instruments):
        # Read brokers from file
        with open(brokers_file, 'r') as file:
            self.brokers = json.load(file)
        self.instruments = instruments


    def monitor_instruments(self):
            # Retrieve Zerodha account details for fetching live data
            zerodha_account = self.brokers.get('zerodha', {}).get('omkar', {})
            api_key = zerodha_account.get('api_key')
            access_token = zerodha_account.get('access_token')

            # Initialize Kite Connect
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)

            # Initialize a dictionary to track the previous LTP for each instrument
            prev_ltp = {instrument.get_name(): None for instrument in self.instruments}

            # Initialize a dictionary to track if a message has been sent for each level
            message_sent = {instrument.get_name(): {level: False for level in instrument.get_trigger_points()} for instrument in self.instruments}        

            while True:
                for instrument in self.instruments:
                    # Extract instrument details
                    token = instrument.get_token()
                    levels = instrument.get_trigger_points()
                    name = instrument.get_name()

                    # Fetch LTP (Last Traded Price) using Kite Connect
                    ltp_data = kite.ltp(str(token))  # Convert token to string

                    # print(ltp_data) alongwith time
                    print(f"{time.strftime('%H:%M:%S')} - {ltp_data} ")

                    # Access the last_price using the string representation of the token
                    ltp = ltp_data[str(token)]['last_price'] 

                    # Check if LTP crosses the given levels
                    for level_name, level_price in levels.items():
                        # Check if LTP crosses the level from the previous LTP
                        if prev_ltp[name] is not None:
                            if prev_ltp[name] < level_price <= ltp and not message_sent[name][level_name]:
                                # UpCross
                                cross_type = "UpCross"
                                message_sent[name][level_name] = True
                            elif prev_ltp[name] > level_price >= ltp and not message_sent[name][level_name]:
                                # DownCross
                                cross_type = "DownCross"
                                message_sent[name][level_name] = True
                            else:
                                continue

                            # Send alert message to Telegram group
                            message = f"{cross_type}{level_name}: {ltp} for {name}! Trade? Reply 'call' or 'put' or 'pass'"
                            discord_bot(message=f"{message}")
                            print(message)

                    # Update the previous LTP for the next iteration
                    prev_ltp[name] = ltp

                # Wait for 1 minute before the next iteration
                time.sleep(60)