import datetime as dt
import os, sys

print("Today's date:", dt.datetime.today())

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Brokers.Aliceblue.alice_login as alice_login
import Brokers.Zerodha.kite_login as kite_login
import MarketUtils.general_calc as general_calc
import MarketUtils.Calculations.qty_calc as qty_calc
import Brokers.place_order_calc as place_order_calc
import Brokers.Aliceblue.alice_utils as alice_utils
import Brokers.Zerodha.kite_utils as kite_utils

broker_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'broker.json')
active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

alice = None
kite = None

# Load the broker data
broker_json_details = general_calc.read_json_file(broker_json_path)

def all_broker_login(active_users):
    for user in active_users:
        if user['broker'] == 'zerodha':
            user['access_token'] = kite_login.login_in_zerodha(user)            
        elif user['broker'] == 'aliceblue':
            user['session_id'] = alice_login.login_in_aliceblue(user)
        else:
            print("Broker not supported")
        
    return active_users

def clear_json_file(user_name):
    order_json_folderpath = os.path.join(DIR_PATH, 'UserProfile','OrdersJson')
    order_json_filepath = os.path.join(order_json_folderpath, f'{user_name}.json')
    general_calc.write_json_file(order_json_filepath, {})

active_users = all_broker_login(place_order_calc.get_active_users(broker_json_details))

def calculate_qty(active_users):
    for user in active_users:
        lots = qty_calc.calculate_lots(user)
        user['qty'] = lots
        clear_json_file(user['account_name'])
    return active_users

active_users_json = calculate_qty(active_users)

general_calc.write_json_file(active_users_json_path, active_users_json)

def download_csv(active_users):
    # Flags to check if we have downloaded for each broker
    zerodha_downloaded = False
    aliceblue_downloaded = False

    for user in active_users:
        if not zerodha_downloaded and user['broker'] == 'zerodha':
            kite_utils.get_csv_kite(user)  # Get CSV for this user
            zerodha_downloaded = True  # Set the flag to True after download
        elif not aliceblue_downloaded and user['broker'] == 'aliceblue':
            alice_utils.get_csv_alice(user)  # Get CSV for this user
            aliceblue_downloaded = True  # Set the flag to True after download

        # If we have downloaded both, we can break the loop
        if zerodha_downloaded and aliceblue_downloaded:
            break

download_csv(active_users)
