import datetime as dt
import json, sys
import math

mpwizard_json = '/Users/amolkittur/Desktop/Dev/Strategies/MPWizard/MPWizard.json'
DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.general_calc as general_calc

def calculate_quantity(capital, risk, prc_ref, lot_size):
    if prc_ref == 0:
        print("Price reference is 0")
    raw_quantity = (risk * capital) / prc_ref
    qty = int((raw_quantity // lot_size) * lot_size)
    if qty == 0:
        qty = lot_size
    return qty

def calculate_lots(active_users):
    lots = {}
    for user in active_users:
        current_capital = user['expected_morning_balance']
        user_details,_ = general_calc.get_user_details(user['account_name'])
        percentage_risk = user_details['percentage_risk']


    weekday = dt.datetime.now().strftime('%a')
    indices_lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40}

    with open(mpwizard_json, 'r') as file:
        data = json.load(file)
        indices_data = data.get('indices', [])

    for strategy in percentage_risk:
        if strategy in percentage_risk:
            percentage = percentage_risk[strategy]
            if percentage > 1:
                # If the percentage is greater than 1, it is considered as an amount
                lots[strategy] = {f'{strategy}_qty': math.floor(current_capital / percentage)}
            else:
                # If the percentage is less than 1, it is considered as a percentage
                strategy_dict = {}
                if strategy == 'MPWizard':  #TODO remove hardcoding move the calc to respective strategy
                    for index in indices_data:
                        prc_ref = index['WeekdayPrcRef'].get(weekday, 0)
                        lot_size = indices_lot_sizes.get(index['name'], 0)
                        strategy_dict[f'{index["name"]}_qty'] = calculate_quantity(current_capital, percentage, prc_ref, lot_size)
                        lots[strategy] = strategy_dict
                else:
                    lots[strategy] = {f'{strategy}_qty': math.floor(current_capital / percentage)}
                
    return lots