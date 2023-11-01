import os
import sys,json
from dotenv import load_dotenv

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)


import MarketUtils.general_calc as general_calc
import Brokers.Aliceblue.alice_utils as alice_utils
import Brokers.Zerodha.kite_utils as kite_utils

broker_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'broker.json')
active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')
# active_users_json_details = general_calc.read_json_file(active_users_json_path)

def get_primary_user_details(active_users_json_path):
    details  = []
    with open(active_users_json_path, 'r') as f:
        active_users = json.load(f)
    for user in active_users:
        if 'LiveData1' in user.get('account_type', ''):
            details.append(user)
    
    return details

def get_primary_account(): 
    users = get_primary_user_details(active_users_json_path)
    for user in users:
        api_key = user['api_key']
        access_token = user['access_token']
    return api_key,access_token


# def get_primary_account():
#     api_key = '6b0dp5ussukmo67h'
#     access_token = '26D8gxZKUT8x9ULUZ5P66M76qlcdzBv7'
#     return api_key,access_token

def get_secondary_account():
    #apikey,access_token
    return

def get_active_subscribers(strategy_name):
    #read the broker json file and get the active subscribers for the strategy
    active_users_data = general_calc.read_json_file(active_users_json_path)
    
    zerodha_users = kite_utils.get_kite_active_users(active_users_data, strategy_name)
    alice_users = alice_utils.get_alice_active_users(active_users_data, strategy_name)
    
    #create a dict with a list of zerodha and alice users
    active_subscribers = {}
    active_subscribers['zerodha'] = zerodha_users
    active_subscribers['aliceblue'] = alice_users

    return active_subscribers


