from kiteconnect import KiteConnect
import pandas as pd

import datetime as dt
import json
import math
import os, sys

print("Today's date:", dt.datetime.today())

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.Aliceblue.alice_login as alice_login
import Brokers.Zerodha.kite_login as kite_login
import Brokers.Aliceblue.alice_utils as alice_utils
import Brokers.Zerodha.kite_utils as kite_utils
import MarketUtils.general_calc as general_calc
import MarketUtils.Calculations.qty_calc as qty_calc

broker_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'broker.json')
active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')
mpwizard_json_path = os.path.join(DIR_PATH, 'Strategies','MPWizard', 'MPWizard.json')
amipy_json_path = os.path.join(DIR_PATH, 'Strategies','Amipy', 'AmiPy.json')


alice = None
kite = None

# Load the broker data
broker_json_details = general_calc.read_json_file(broker_json_path)

def get_active_users(broker_json_details):
    active_users = []
    for user in broker_json_details:
        if 'Active' in user['account_type']:
            active_users.append(user)
    return active_users

def all_broker_login(active_users):
    for user in active_users:
        if user['broker'] == 'zerodha':
            user['access_token'] = kite_login.login_in_zerodha(user)            
        elif user['broker'] == 'aliceblue':
            user['session_id'] = alice_login.login_in_aliceblue(user)
        else:
            print("Broker not supported")
        
    return active_users

active_users = all_broker_login(get_active_users(broker_json_details))

def calculate_lot(active_users):
    lots = qty_calc.calculate_lots(active_users)
    for user in active_users:
        user['qty'] = lots
        print(user)
    return active_users

active_users = calculate_lot(active_users)

general_calc.write_json_file(active_users_json_path, active_users)





# if datetime.today().weekday() == 4:
    # kite_utils.get_csv_kite(user_details)
    # alice_utils.get_csv_alice()


