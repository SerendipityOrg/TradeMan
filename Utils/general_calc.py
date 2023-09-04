import json
import os
import datetime as dt
from collections import namedtuple
import pandas as pd
# from pya3 import *


#Json Functions
def read_json_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def write_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

#Gets users
def get_strategy_users(strategy):
    data = read_json_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'broker.json'))
    
    users = []

    for broker, broker_data in data.items():
        # Extract account names that are allowed to trade
        accounts_to_trade = broker_data.get('accounts_to_trade', [])

        # For each user in accounts_to_trade, check if the strategy is in their percentageRisk and if its value is not zero
        for account in accounts_to_trade:
            user_details = broker_data.get(account, {})
            percentage_risk = user_details.get('percentageRisk', {})
            
            if strategy in percentage_risk and percentage_risk[strategy] != 0:
                users.append((broker, account))

    return users


#Expiry Dates Calculation
holidays = [dt.date(2023, i, j) for i, j in [
    (1, 26), (3, 7), (3, 30), (4, 4), (4, 7), (4, 14),
    (4, 22), (5, 1), (6, 28), (8, 15), (9, 19), (10, 2),
    (10, 24), (11, 14), (11, 27), (12, 25)]
]

def get_next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  
        days_ahead += 7
    next_date = d + dt.timedelta(days_ahead)
    while next_date in holidays:
        next_date += dt.timedelta(1)
    return next_date

def last_weekday_of_month(year, month, weekday):
    last_day = dt.date(year, month+1, 1) - dt.timedelta(1)
    while last_day.weekday() != weekday or last_day in holidays:
        last_day -= dt.timedelta(1)
    return last_day


def get_expiry_dates(base_symbol):
    today = dt.date.today()
    
    if base_symbol == "MIDCAP":
        weekly_expiry = get_next_weekday(today, 0)  # Monday
    elif base_symbol == "FINNIFTY":
        weekly_expiry = get_next_weekday(today, 1)  # Tuesday
    elif base_symbol == "BANKNIFTY":
        weekly_expiry = get_next_weekday(today, 2)  # Wednesday
    elif base_symbol == "NIFTY" :
        weekly_expiry = get_next_weekday(today, 3)  # Thursday
    elif base_symbol == "SENSEX":
        weekly_expiry = get_next_weekday(today, 4)  # Friday
    else:
        raise ValueError(f"Invalid base_symbol: {base_symbol}")
    
    monthly_expiry = last_weekday_of_month(today.year, today.month, weekly_expiry.weekday())

    if weekly_expiry > monthly_expiry:
        if today.month == 12:
            monthly_expiry = last_weekday_of_month(today.year+1, 1, weekly_expiry.weekday())
        else:
            monthly_expiry = last_weekday_of_month(today.year, today.month+1, weekly_expiry.weekday())

    return weekly_expiry, monthly_expiry


#token calculation
from pya3 import *
def get_tokens(base_symbol, expiry_date, option_type, strike_prc=0):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instruments_df = pd.read_csv(os.path.join(script_dir, 'instruments.csv'))

    instruments_df = instruments_df[
        ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike", "segment"]
    ]

    #if option_type is other than CE or PE the segement should be futures
    if option_type != 'CE' and option_type != 'PE':
        option_type = 'FUT'
        segment = 'NFO-FUT'
    else:
        segment = 'NFO-OPT'
    
    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == str(base_symbol))
        & (instruments_df["expiry"] == str(expiry_date))
        & (instruments_df["strike"] == int(strike_prc))
        & (instruments_df["instrument_type"] == str(option_type))
        & (instruments_df["segment"] == segment)
    ]

    tokens = int(nfo_ins_df["instrument_token"].values[0])
    trading_symbols = nfo_ins_df["tradingsymbol"].values[0]
    trading_symbols_aliceblue = []
    trading_symbols_aliceblue = Instrument("NFO", tokens, base_symbol, trading_symbols, expiry_date, 50)
    return tokens, trading_symbols, trading_symbols_aliceblue

##########################append the lot_size to env file ############
def round_qty(qty, base_symbol):
    if base_symbol == 'NIFTY':
        lot_size = 50
    if base_symbol == 'BANKNIFTY':
        lot_size = 15
    if base_symbol == 'FINNIFTY':
        lot_size = 40
    return int(qty / lot_size) * lot_size

def round_strike_prc(strike_prc, base_symbol):
    if base_symbol == 'NIFTY' or base_symbol == 'FINNIFTY':
        return round(strike_prc / 50) * 50
    if base_symbol == 'BANKNIFTY':
        return round(strike_prc / 100) * 100

