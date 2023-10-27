import os
import sys
from dotenv import load_dotenv

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

broker_json_filepath = os.getenv('broker_json_filepath')

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.general_calc as general_calc
import Brokers.Aliceblue.alice_utils as alice_utils
import Brokers.Zerodha.kite_utils as kite_utils


active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

def get_primary_account():
    primary_account = broker_json_filepath
    user_details = general_calc.read_json_file(primary_account)
    api_key = '6b0dp5ussukmo67h'
    access_token = 'JKTDjG377Y6UDXu4I6aYLqCBHM6g9znq'
    # api_key = user_details['zerodha']['omkar']['api_key'] ###TODO Create a broker class and extarct the api key and access token from the json file
    # access_token = user_details['zerodha']['omkar']['access_token']
    return api_key,access_token

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


