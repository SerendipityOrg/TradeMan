from kiteconnect import KiteConnect
from datetime import datetime as dt
from time import sleep
import json
from telegram_bot import discord_bot
from MPW_place_orders import *
from MPWizard_calc import *

script_dir = os.path.dirname(os.path.abspath(__file__))
zerodha_omkar_filepath = os.path.join(script_dir, '..', 'Utils', 'users/omkar.json')
levels_filepath = os.path.join(script_dir, 'mpwizard(omkar).json')

class OrderMonitor:
    def __init__(self, users,instruments):
        # Read brokers from file
        with open(zerodha_omkar_filepath, 'r') as file:
            self.omkar = json.load(file)  
        with open(levels_filepath) as f:
            self.mood_data = json.load(f)
        self.users = users
        self.instruments = instruments
        self.orders_placed_today = 0  # Add a counter for orders placed today
        self.today_date = dt.now().date()  # Store today's date

    def monitor_instruments(self):
            # Retrieve Zerodha account details for fetching live data
            zerodha_account = self.omkar.get('zerodha', {})
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
                # Check if date has changed, if yes, reset the counter
                if dt.now().date() != self.today_date:
                    self.today_date = dt.now().date()
                    self.orders_placed_today = 0

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

                    if self.orders_placed_today >= 2:  # If orders placed today are already 2
                        print("Done for the day")
                        continue

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
                                        weekday = dt.now().strftime('%a')
                                        ib_level = mood_data['IBLevel']
                                        instru_mood = mood_data['InstruMood']
                                        prc_ref = mood_data['WeekdayPrcRef'].get(weekday, 0)
                                        
                                        if ib_level == 'Big':
                                            option_type = 'PE' if cross_type == 'DownCross' else 'CE'
                                        elif ib_level == 'Small':
                                            option_type = 'PE' if cross_type == 'UpCross' else 'CE'
                                        elif ib_level == 'Medium':
                                            option_type = 'PE' if instru_mood == 'Bearish' else 'CE'   #check this logic 
                                        else:
                                            continue  # or handle unknown ib_level

                                        if name == 'NIFTY' or name == 'FINNIFTY': 
                                            strike_prc = round(ltp / 50) * 50
                                        else:
                                            strike_prc = round(ltp / 100) * 100

                                        if name == 'NIFTY' or name == 'BANKNIFTY':
                                            expiry = get_expiry_dates()
                                            expiry_date = expiry[0].strftime("%Y-%m-%d")  # constant value
                                        elif name == 'FINNIFTY':
                                            expiry_date = expiry[1].strftime("%Y-%m-%d")
                                        

                                        tokens, trading_symbol_list, trading_symbol_aliceblue = get_option_tokens(name, expiry_date, option_type, strike_prc)
                                        print(tokens)
                                        instrument.additional_tokens = tokens                                      
                                        
                                        if self.orders_placed_today < 2:
                                            for broker, user in self.users:
                                                # Send appropriate trading symbol to order functions based on broker
                                                if 'zerodha' in broker:
                                                    avg_prc =  place_zerodha_order(trading_symbol_list,"BUY", "BUY", strike_prc, name, user)                                                
                                                    limit_prc = avg_prc - prc_ref
                                                    order = place_stoploss_zerodha(trading_symbol_list, "SELL", "SELL", strike_prc, name, limit_prc, user, broker='zerodha')

                                                elif 'aliceblue' in broker:
                                                    avg_prc = place_aliceblue_order(trading_symbol_aliceblue[0],"BUY", "BUY", strike_prc, name, user)                                                                       
                                                    limit_prc = avg_prc - prc_ref
                                                    order = place_stoploss_aliceblue(trading_symbol_aliceblue[0], "SELL", "SELL", strike_prc, name, limit_prc, user, broker='aliceblue')
                                                else:
                                                # Continue with the next mood data
                                                    continue

                                            self.orders_placed_today += 1
                                            
                                    # Send alert message to Telegram group
                                message = f"{cross_type}{level_name}: {ltp} for {name}! Trade? Reply 'call' or 'put' or 'pass'"
                                mpwizard_discord_bot(message)
                                print(message)

                    if instrument.additional_tokens is not None:
                        for token in instrument.additional_tokens:
                            ltp_data = kite.ltp(str(token))
                            print(f"{dt.now().strftime('%H:%M:%S')} - {ltp_data} ")

                    # Update the previous LTP for the next iteration
                    prev_ltp[name] = ltp

                # Wait for 1 minute before the next iteration
                sleep(30)