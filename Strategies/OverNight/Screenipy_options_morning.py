import os, sys
import urllib
import numpy as np
import keras
import yfinance as yf
import joblib
import requests
from Utils.place_orders import *
from Utils.calculations import *
from kiteconnect import KiteConnect
import time

def load_credentials(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

script_dir = os.path.dirname(os.path.abspath(__file__))
broker_filepath = os.path.join(script_dir, '..', 'Utils', 'broker.json')
users_to_trade = get_overnight_users(broker_filepath)
future_expiry = get_future_expiry_date()
expiry = get_expiry_date()

for broker, user in users_to_trade:
    print(f"Trading for {user} on {broker}")
    user_filepath = os.path.join(script_dir, '..', 'Utils','users', f'{user}.json')
    order_details = load_credentials(user_filepath)
    trade_details = order_details[broker]["orders"]["Overnight_Options"]["Afternoon"]

    for item in trade_details:      
        if item['direction'] == 'BEARISH':
            direction = "BEARISH"
            strike_prc = item["strike_price"]
            qty = item["qty"]
            if strike_prc == "0":
                future_tokens, future_trading_symbol, future_trading_symbol_aliceblue = get_future_tokens(future_expiry)
            else:
                option_tokens, option_trading_symbol, option_trading_symbol_aliceblue = get_option_tokens(base_symbol='NIFTY', expiry_date=expiry, option_type='CE',strike_prc=strike_prc)
        elif item['direction'] == 'BULLISH':
            direction = "BULLISH"
            strike_prc = item["strike_price"]
            qty = item["qty"]
            if strike_prc == "0":
                future_tokens, future_trading_symbol, future_trading_symbol_aliceblue = get_future_tokens(future_expiry)
            else:
                option_tokens, option_trading_symbol, option_trading_symbol_aliceblue = get_option_tokens(base_symbol='NIFTY', expiry_date=expiry, option_type='PE',strike_prc=strike_prc)
        
    if direction == "BEARISH":
        if broker == 'aliceblue':
                future_avgprc = place_aliceblue_order(future_trading_symbol_aliceblue[0],'BUY',"Morning","0",user,direction,qty)
                option_avgprc = place_aliceblue_order(option_trading_symbol_aliceblue[0],'SELL','Morning',strike_prc,user,direction,qty)
        elif broker == 'zerodha':
                future_avgprc = place_zerodha_order(future_trading_symbol[0],'BUY',"Morning","0",user,direction,qty)
                option_avgprc = place_zerodha_order(option_trading_symbol[0],'SELL','Morning',strike_prc,user,direction,qty)
    elif direction == "BULLISH":
        if broker == 'aliceblue':
                future_avgprc = place_aliceblue_order(future_trading_symbol_aliceblue[0],'SELL','Morning',"0",user,direction,qty)
                option_avgprc = place_aliceblue_order(option_trading_symbol_aliceblue[0],'SELL','Morning',strike_prc,user,direction,qty)
        elif broker == 'zerodha':
                future_avgprc = place_zerodha_order(future_trading_symbol[0],'SELL','Morning',"0",user,direction,qty)
                option_avgprc = place_zerodha_order(option_trading_symbol[0],'SELL','Morning',strike_prc,user,direction,qty)
         


        
            
    
    




    
    

        


    

    
