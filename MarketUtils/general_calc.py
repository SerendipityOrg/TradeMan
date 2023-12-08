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


#Expiry Dates Calculation
holidays = [dt.date(2023, i, j) for i, j in [
    (1, 26), (3, 7), (3, 30), (4, 4), (4, 7), (4, 14),
    (4, 22), (5, 1), (6, 28), (8, 15), (9, 19), (10, 2),
    (10, 24), (11, 14), (11, 27), (12, 25)]
]

def get_previous_dates(num_dates):
    dates = []
    current_date = dt.date.today()

    while len(dates) < num_dates:
        current_date -= dt.timedelta(days=1)

        if current_date.weekday() >= 5 or current_date in holidays:
            continue

        dates.append(current_date.strftime("%Y-%m-%d"))

    return dates

# def get_next_weekday(d, weekday):
#     if d.weekday() == weekday:  # Check if today is already the desired weekday
#         return d
#     days_ahead = weekday - d.weekday()
#     if days_ahead <= 0:  
#         days_ahead += 7
#     next_date = d + dt.timedelta(days_ahead)
#     while next_date in holidays:
#         next_date -= dt.timedelta(1)
#     return next_date

# def last_weekday_of_month(year, month, weekday):
#     if month == 12:
#         # If the current month is December, increment the year and set the month to January
#         last_day = dt.date(year + 1, 1, 1) - dt.timedelta(1)
#     else:
#         # Otherwise, proceed to the next month
#         last_day = dt.date(year, month + 1, 1) - dt.timedelta(1)
    
#     # Find the last desired weekday of the month
#     while last_day.weekday() != weekday or last_day in holidays:
#         last_day -= dt.timedelta(1)
    
#     return last_day


# def get_expiry_dates(base_symbol):
#     today = dt.date.today()
    
#     if base_symbol == "MIDCPNIFTY":
#         weekly_expiry = get_next_weekday(today, 0)  # Monday
#     elif base_symbol == "FINNIFTY":
#         weekly_expiry = get_next_weekday(today, 1)  # Tuesday
#     elif base_symbol == "BANKNIFTY":
#         weekly_expiry = get_next_weekday(today, 2)  # Wednesday
#     elif base_symbol == "NIFTY" :
#         weekly_expiry = get_next_weekday(today, 3)  # Thursday
#     elif base_symbol == "SENSEX":
#         weekly_expiry = get_next_weekday(today, 4)  # Friday
#     else:
#         raise ValueError(f"Invalid base_symbol: {base_symbol}")
    
#     monthly_expiry = last_weekday_of_month(today.year, today.month, weekly_expiry.weekday())

#     if weekly_expiry > monthly_expiry:
#         if today.month == 12:
#             monthly_expiry = last_weekday_of_month(today.year+1, 1, weekly_expiry.weekday())
#         else:
#             monthly_expiry = last_weekday_of_month(today.year, today.month+1, weekly_expiry.weekday())

#     return weekly_expiry, monthly_expiry

# def get_next_week_expiry(base_symbol):
#     # First, get the weekly expiry for the current week
#     weekly_expiry, _ = get_expiry_dates(base_symbol)
    
#     # Now calculate the weekly expiry for the next week
#     next_week_expiry = weekly_expiry + dt.timedelta(days=7)

#     # If the next week expiry falls on a holiday or weekend, find the previous valid working day
#     while next_week_expiry in holidays:  # Checking if it's a holiday or weekend
#         next_week_expiry -= dt.timedelta(days=1)  # Decrement by one day
    
#     return next_week_expiry
