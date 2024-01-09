import json
import os,sys
import datetime as dt
import pandas as pd
from pya3 import *

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

active_users_json_path = os.path.join(DIR_PATH,"MarketUtils", "active_users.json")

#Json Functions
def read_json_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def write_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_user_details(user):
    user_json_path = os.path.join(DIR_PATH, 'UserProfile', 'UserJson', f'{user}.json')
    json_data = read_json_file(user_json_path)
    return json_data, user_json_path

def get_orders_json(user):
    user_json_path = os.path.join(DIR_PATH, 'UserProfile', 'OrdersJson', f'{user}.json')
    json_data = read_json_file(user_json_path)
    return json_data, user_json_path

def get_strategy_json(strategy_name):
    strategy_json_path = os.path.join(DIR_PATH, 'Strategies', strategy_name, strategy_name+'.json')
    try:
        strategy_json = read_json_file(strategy_json_path)
    except (FileNotFoundError, IOError, json.JSONDecodeError):
        # Handle exceptions and use an empty dictionary if the file doesn't exist or an error occurs
        strategy_json = {}
    return strategy_json, strategy_json_path

def get_active_users(broker_json_details: list) -> list:
    active_users = [user for user in broker_json_details if 'Active' in user.get('account_type', '')]
    return active_users

def assign_user_details(account_name):
    matched_user = None
    user_details = read_json_file(active_users_json_path)
    for user in user_details:
        if user['account_name'] == account_name:
            matched_user = user
    return matched_user

holidays = [dt.date(2024, i, j) for i, j in [
    (1, 26),
    (3, 8),
    (3, 25),
    (3, 29),
    (4, 11),
    (4, 17),
    (5, 1),
    (6, 17),
    (7, 17),
    (8, 15),
    (10, 2),
    (11, 1),
    (11, 15),
    (12, 25)
]]

def get_previous_dates(num_dates):
    dates = []
    current_date = dt.date.today()

    while len(dates) < num_dates:
        current_date -= dt.timedelta(days=1)

        if current_date.weekday() >= 5 or current_date in holidays:
            continue

        dates.append(current_date.strftime("%Y-%m-%d"))

    return dates