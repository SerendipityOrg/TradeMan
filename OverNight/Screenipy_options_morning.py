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

script_dir = os.path.dirname(os.path.abspath(__file__))

for broker, user in users_to_trade:
    print(f"Trading for {user} on {broker}")
    user_filepath = os.path.join(script_dir, '..', 'Utils', f'{user}.json')
    order_details = load_credentials(user_filepath)

    token = order_details[broker]["orders"]
    print(token)
    

    
