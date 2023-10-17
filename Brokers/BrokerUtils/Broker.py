import os
import sys
import json
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Brokers', '.env')
load_dotenv(ENV_PATH)

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.general_calc as general_calc

def get_primary_account():
    primary_account = os.getenv('broker_json_filepath')
    user_details = general_calc.read_json_file(primary_account)
    api_key = user_details['zerodha']['omkar']['api_key'] ###TODO Create a broker class and extarct the api key and access token from the json file
    access_token = user_details['zerodha']['omkar']['access_token']
    return api_key,access_token

def get_secondary_account():
    #apikey,access_token
    return

