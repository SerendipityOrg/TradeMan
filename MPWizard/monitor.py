from kiteconnect import KiteConnect
from datetime import datetime as dt
from time import sleep
import json
from telegram_bot import discord_bot
from mpw_place_orders import *
from MPWizard_calc import *

class OrderMonitor:
    def __init__(self, brokers_file, instruments):
        # Read brokers from file
        with open(brokers_file, 'r') as file:
            self.brokers = json.load(file)
        with open('MPWizard.json') as f:
            self.mood_data = json.load(f)
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
                    print(f"{dt.now().strftime('%H:%M:%S')} - {ltp_data} ")

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

                            if cross_type is not None:
                                # search for the name in the mood data
                                for mood_data in self.mood_data['indices']:
                                    if mood_data['name'] == name:
                                        ib_level = mood_data['IBLevel']
                                        instru_mood = mood_data['InstruMood']

                                        if ib_level == 'Big':
                                            option_type = 'PE' if cross_type == 'DownCross' else 'CE'
                                        elif ib_level == 'Small':
                                            option_type = 'PE' if cross_type == 'UpCross' else 'CE'
                                        elif ib_level == 'Medium':
                                            option_type = 'PE' if instru_mood == 'Bearish' else 'CE'
                                        else:
                                            continue  # or handle unknown ib_level

                                        if name == 'NIFTY' or name == 'FINNIFTY': 
                                            strike_prc = round(ltp / 50) * 50
                                        else:
                                            strike_prc = round(ltp / 100) * 100

                                        expiry_date = "2023-07-13"  # constant value
                                        tokens, trading_symbol_list, trading_symbol_aliceblue = get_option_tokens(name, expiry_date, option_type, strike_prc )
                                        instrument.additional_tokens = tokens                                      
                                        
                                        #append tokens to instruments

                                        # Send appropriate trading symbol to order functions based on broker
                                        if 'zerodha' in self.brokers:
                                            print(tokens,strike_prc,option_type,expiry_date)
                                            avg_prc =  place_zerodha_order(trading_symbol_list,"BUY", "BUY", strike_prc, option_type, name)
                                            print(avg_prc)
                                            avg_prc = (avg_prc[0])
                                            print("the type of avg prc is ",type(avg_prc))
                                            if name == "NIFTY":
                                                limit_prc = avg_prc - 20
                                            elif name == "FINNIFTY":
                                                limit_prc = avg_prc - 24
                                            elif name == "BANKNIFTY":
                                                limit_prc = avg_prc - 40

                                            place_stoploss_zerodha(trading_symbol_list, "SELL", "SELL", strike_prc, name, limit_prc, broker='zerodha')


                                        elif 'aliceblue' in self.brokers:
                                            print(tokens,strike_prc,option_type,expiry_date)
                                            avg_prc = place_aliceblue_order(trading_symbol_aliceblue,"BUY", "BUY", strike_prc, option_type, name)
                                            print(avg_prc)
                                            avg_prc = (avg_prc[0])
                                            print("the type of avg prc is ",type(avg_prc))
                                            if name == "NIFTY":
                                                limit_prc = avg_prc - 20
                                            elif name == "FINNIFTY":
                                                limit_prc = avg_prc - 24
                                            elif name == "BANKNIFTY":
                                                limit_prc = avg_prc - 40

                                            print(" limit prc is ",limit_prc )
                                            place_stoploss_zerodha(trading_symbol_aliceblue, "SELL", "SELL", strike_prc, name, limit_prc, broker='aliceblue')
                                        else:
                                        # Continue with the next mood data
                                            continue
                                    # Send alert message to Telegram group
                                        message = f"{cross_type}{level_name}: {ltp} for {name}! Trade? Reply 'call' or 'put' or 'pass'"
                                        # self.telegram_bot.send_message(message=f"{message}")
                                        print(message)

                    if instrument.additional_tokens is not None:
                        for token in instrument.additional_tokens:
                            ltp_data = kite.ltp(str(token))
                            print(f"{dt.now().strftime('%H:%M:%S')} - {ltp_data} ")


                    # Update the previous LTP for the next iteration
                    prev_ltp[name] = ltp

                # Wait for 1 minute before the next iteration
                sleep(60)