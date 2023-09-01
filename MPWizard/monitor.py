from kiteconnect import KiteConnect
from datetime import datetime as dt
from time import sleep
import json
from telegram_bot import discord_bot
from mpw_place_orders import *
from MPWizard_calc import *

script_dir = os.path.dirname(os.path.abspath(__file__))
zerodha_omkar_filepath = os.path.join(script_dir, '..', 'Utils', 'users/omkar.json')
levels_filepath = os.path.join(script_dir, 'MPWizard.json')

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
        self.done_for_the_day = False  # Flag to indicate if we're done trading for the day
        self.order_details_dict = {}

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
                    self.done_for_the_day = False

                for instrument in self.instruments:
                    # Extract instrument details
                    token = instrument.get_token()
                    levels = instrument.get_trigger_points()
                    name = instrument.get_name()

                    # Fetch LTP (Last Traded Price) using Kite Connect
                    ltp_data = kite.ltp(str(token))  # Convert token to string
                    print(f"{dt.now().strftime('%H:%M:%S')} - {ltp_data} ")

                    # Access the last_price using the string representation of the token
                    ltp = ltp_data[str(token)]['last_price'] 

                    if self.orders_placed_today < 2:  # If orders placed today are already 2
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
                                    message = f"{cross_type}{level_name}: {ltp} for {name}! Trade? Reply 'call' or 'put' or 'pass'"
                                    print(message)
                                    mpwizard_discord_bot(message)
                                    # search for the name in the mood data
                                    for mood_data in self.mood_data['indices']:
                                        if mood_data['name'] == name:
                                            weekday = dt.now().strftime('%a')
                                            ib_level = mood_data['IBLevel']
                                            instru_mood = mood_data['InstruMood']
                                            prc_ref = mood_data['WeekdayPrcRef'].get(weekday, 0)
                                            
                                            if ib_level == 'Big':
                                                option_type = 'PE' if cross_type == 'UpCross' else 'CE'
                                            elif ib_level == 'Small':
                                                option_type = 'PE' if cross_type == 'DownCross' else 'CE'    
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
                                                print("Finfinity expiry", expiry[1])
                                                # expiry_date = "2023-07-20"
                                                expiry_date = str(expiry[0])  # constant value
                                            elif name == 'FINNIFTY':
                                                # expiry_date = "2023-08-22"
                                                expiry_date = str(expiry[1])
                                            
                                            tokens, trading_symbol_list, trading_symbol_aliceblue = get_option_tokens(name, expiry_date, option_type, strike_prc)
                                            instrument.additional_tokens = tokens
                                            self.orders_placed_today += 1
                                            print(f"Orders placed today: {self.orders_placed_today}")
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

                                                with open(levels_filepath) as f:
                                                    data = json.load(f)
                                               
                                                SignalEntry= {
                                                        "Option": trading_symbol_list[0],
                                                        "Event": f"{instru_mood}-{ib_level}-{cross_type}",
                                                        "EntryPrice": avg_prc,
                                                        "EntryTime": dt.now().strftime('%H:%M:%S'),
                                                    }
                        
                                                # Append the new signal entry to the list
                                                idx = next((index for (index, d) in enumerate(data['indices']) if d["name"] == name), None)

                                                if idx is not None:
                                                    if 'SignalEntry' not in data['indices'][idx]:
                                                        data['indices'][idx]['SignalEntry'] = []
                                                    data['indices'][idx]['SignalEntry'] = SignalEntry                                               

                                                with open(levels_filepath, 'w') as json_file:
                                                    json.dump(data, json_file, indent=4)                                                                           

                                                if 'zerodha' in broker:
                                                    order_details = {
                                                        'token': tokens,
                                                        'trading_symbol': trading_symbol_list,
                                                        'avg_prc': avg_prc,
                                                        'order_id': order,
                                                        'prc_ref': prc_ref,
                                                        'next_stoploss': limit_prc + prc_ref / 2,
                                                        'next_change': avg_prc + prc_ref / 2,
                                                        'adjust_called': False,
                                                        'current_stoploss': avg_prc - prc_ref,
                                                        'stoploss_hit': False
                                                    }
                                                    if broker not in self.order_details_dict:
                                                        self.order_details_dict[broker] = [order_details]
                                                    else:
                                                        self.order_details_dict[broker].append(order_details)
                                                if 'aliceblue' in broker:
                                                    order_details = {
                                                        'token': tokens,
                                                        'trading_symbol': trading_symbol_aliceblue,
                                                        'avg_prc': avg_prc,
                                                        'order_id': order,
                                                        'prc_ref': prc_ref,
                                                        'next_stoploss': limit_prc + prc_ref / 2,
                                                        'next_change': avg_prc + prc_ref / 2,
                                                        'adjust_called': False,
                                                        'current_stoploss': avg_prc - prc_ref,
                                                        'stoploss_hit': False
                                                    }
                                                    if broker not in self.order_details_dict:
                                                        self.order_details_dict[broker] = [order_details]
                                                    else:
                                                        self.order_details_dict[broker].append(order_details)
                                        # Send alert message to Telegram group

                    if instrument.additional_tokens is not None:
                        for token in instrument.additional_tokens:
                            ltp_data = kite.ltp(str(token))
                            ltp_token = ltp_data[str(token)]['last_price']  # Access the last_price
                            print(f"{dt.now().strftime('%H:%M:%S')} - {ltp_data} ")
                            for broker, user in self.users:
                                order_data = self.order_details_dict.get(broker, None)
                                if order_data is not None:
                                    for order_details in order_data:
                                        order_token = str(order_details['token'][0])
                                        avg_prc = order_details['avg_prc']
                                        order_id = order_details['order_id']
                                        trading_symbol = (order_details['trading_symbol'])
                                        prc_ref = order_details['prc_ref']
                                        next_change = order_details['next_change']
                                        adjust_called = order_details['adjust_called']
                                        next_stoploss = order_details['next_stoploss']
                                        token_ltp = str(ltp_data[str(token)]['instrument_token'])
                                        if avg_prc is not None and token_ltp == order_token and ltp_token >= next_change and not adjust_called:
                                            print(f"Adjusting stoploss for token: {order_token}, LTP: {ltp_token}, next_change: {next_change}, adjust_called: {adjust_called}")

                                            next_stoploss = order_details['next_stoploss']
                                            limit_prc = next_stoploss  # New stoploss price
                                            print(f"Adjusting stoploss for {name} to {limit_prc}")

                                            # Call the adjust stoploss function with necessary parameters based on broker
                                            if broker == 'aliceblue':
                                                adjust_stoploss_aliceblue(order_id, trading_symbol[0], "SELL", name, limit_prc, user)
                                            elif broker == 'zerodha':
                                                adjust_stoploss_zerodha(order_id,limit_prc, user)

                                            order_details['current_stoploss'] = limit_prc                                                
                                            # After calling the function, update 'next_stoploss' and 'next_change'
                                            order_details['next_stoploss'] = limit_prc + (prc_ref / 2)
                                            order_details['next_change'] = ltp_token + (prc_ref / 2)

                                            # Mark that the adjust stoploss function has been called for this order
                                            order_details['adjust_called'] = True
                                            print(f"Stoploss adjusted for token: {order_token}, adjust_called set to: {order_details['adjust_called']}")
                                        else:
                                            print(f"No adjustment needed for token: {order_token}, LTP: {ltp_token}, next_change: {next_change}, adjust_called: {adjust_called}")
                                        if ltp_token < next_change:
                                            # If LTP drops below next_change, reset the adjust_called flag
                                            order_details['adjust_called'] = False

                                        if 'stoploss_hit' not in order_details:
                                            order_details['stoploss_hit'] = False

                                    # If the LTP has touched the stoploss, send a message
                                        elif ltp_token < order_details['current_stoploss'] and not order_details['stoploss_hit']:
                                            message = f"Stoploss hit for {name} at {ltp_token}"
                                            mpwizard_discord_bot(message)
                                            
                                            # mark the stoploss as hit
                                            order_details['stoploss_hit'] = True 
                                            
                                            user_filepath = os.path.join(script_dir, '..', 'Utils', 'users', f'{user}.json')
                                            with open(user_filepath, 'r') as f:
                                                user_details = json.load(f)
                                            
                                            ord_details =   {
                                                "order_no": order_id,
                                                "trade_type": "SELL",
                                                "avg_prc": ltp_token,
                                                "timestamp": str(dt.now()),
                                                "strike_price": strike_prc ,
                                                "tradingsymbol": trading_symbol,
                                            }

                                            if 'orders' not in user_details[broker]:
                                                user_details[broker]['orders'] = {}
                                            if 'MPWizard' not in user_details[broker]['orders']:
                                                user_details[broker]['orders']['MPWizard'] = {}
                                            if "SELL" not in user_details[broker]['orders']['MPWizard']:
                                                user_details[broker]['orders']['MPWizard']["SELL"] = []
                                            user_details[broker]['orders']['MPWizard']["SELL"].append(ord_details)

                                            # Now write the updated data back to the JSON file
                                            with open(user_filepath, 'w') as f:
                                                json.dump(user_details, f, indent=4)

                                        for idx, instrument in enumerate(data['indices']):
                                            if instrument['name'] == name:
                                                if instrument['SignalEntry']['Option'] == trading_symbol_list[0]: # replace with your condition
                                                    instrument['SignalEntry']['ExitPrice'] = ltp_token
                                                    instrument['SignalEntry']['ExitTime'] = dt.now().strftime('%H:%M:%S')
                                                
                                        # write the updated data back to the file
                                        with open(levels_filepath, 'w') as json_file:
                                            json.dump(data, json_file, indent=4)
                                
                                            # Remove the token from the additional tokens
                                        
                    # Update the previous LTP for the next iteration
                    prev_ltp[name] = ltp

                # Wait for 1 minute before the next iteration
                sleep(30)