# This file contains functions for calculating quantities for trading strategies.
# It includes functions to get price reference values, calculate quantities based on various parameters, 
# calculate lots for a user, and calculate quantities based on the last traded price (LTP).

import datetime as dt
import math
import os
import sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
import Brokers.place_order_calc as place_order_calc
import MarketUtils.general_calc as general_calc
import Strategies.StrategyBase as StrategyBase


# This function gets the price reference values from the strategy object.
# Inputs: strategy_name (string), instrument (string)
# Returns: price reference value (float) or 0 if no values are found
def get_price_reference(strategy_name, instrument):
    # Fetch the strategy JSON
    _,strategy_path = place_order_calc.get_strategy_json(strategy_name)
    # Read the strategy JSON into a Strategy object
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

    # Get the index of the current day of the week (0 = Monday, 6 = Sunday)
    today_index = dt.datetime.today().weekday()
    # Construct the key to fetch the price reference values from the strategy object
    key = f"{instrument}OptRef"
    # Fetch the price reference values
    price_ref_values = strategy_obj.get_extra_information().get(key, [])
    # If price reference values are found, return the value for the current day
    if price_ref_values:
        return price_ref_values[today_index]
    # If no price reference values are found, return 0
    else:
        return 0 

# This function calculates the quantity of an instrument to be traded based on the capital, risk, price reference, and lot size.
# Inputs: capital (float), risk (float), prc_ref (float), lot_size (int), strategy_name (string)
# Returns: quantity (int)
def calculate_quantity(capital, risk, prc_ref, lot_size, strategy_name):
    # If the strategy is MPWizard and a price reference is provided
    if strategy_name == "MPWizard" and prc_ref is not None:
        # If the price reference is 0, print a message and return 0
        if prc_ref == 0:
            print("Price reference is 0")
            return 0
        # Calculate the raw quantity based on the risk, capital, and price reference
        raw_quantity = (risk * capital) / prc_ref
        # Calculate the final quantity by rounding down the raw quantity to the nearest multiple of the lot size
        quantity = int((raw_quantity // lot_size) * lot_size)
        # If the final quantity is 0, set it to the lot size
        if quantity == 0:
            quantity = lot_size
    else:
        # For other strategies, the risk values represent the capital allocated
        # If the risk is less than or equal to 1, print a message and return 0
        if risk <= 1:
            print(f"Risk for {strategy_name} is not in absolute capital terms. Skipping calculation.")
            return 0
        # Calculate the number of lots based on the capital and risk
        lots = capital / risk
        # Calculate the final quantity by rounding up the number of lots to the nearest whole number and multiplying by the lot size
        quantity = math.ceil(lots) * lot_size
    # Return the final quantity
    return quantity


def calculate_lots(user):
    qty = {}
    current_capital = user['expected_morning_balance']
    user_details, _ = general_calc.get_user_details(user['account_name'])
    percentage_risk = user_details['percentage_risk']

    indices_lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40, "MIDCAP": 75, "SENSEX": 10}

    for strategy_name, risk in percentage_risk.items():
        if strategy_name not in qty:
            qty[strategy_name] = {}

        _, strategy_path = place_order_calc.get_strategy_json(strategy_name)
        strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
        instruments = strategy_obj.get_instruments()

        qty_calculation_type = strategy_obj.get_extra_information().get('QtyCalc')
        if qty_calculation_type == "DuringEntry":
            qty[strategy_name] = 0
            continue
        
        for instrument in instruments:
            prc_ref = get_price_reference(strategy_name, instrument) if strategy_name == "MPWizard" else None
            lot_size = indices_lot_sizes.get(instrument, 1)
            quantity = calculate_quantity(current_capital, risk, prc_ref, lot_size, strategy_name)
            if len(instruments) == 1:
                qty[strategy_name] = quantity
            else:
                qty[strategy_name][instrument] = quantity

    return qty

def calculate_quantity_based_on_ltp(ltp, strategy_name, base_symbol):
    active_users_file = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')
    indices_lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40, "MIDCPNIFTY": 75, "SENSEX": 10}

    _, strategy_path = place_order_calc.get_strategy_json(strategy_name)
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
    instruments = strategy_obj.get_instruments()

    if base_symbol not in instruments:
        print(f"{base_symbol} is not traded in {strategy_name}.")
        return

    try:
        active_users = general_calc.read_json_file(active_users_file)
    except FileNotFoundError:
        print(f"The file {active_users_file} does not exist.")
        return


    for user in active_users:
        # if user['account_name'] != base_symbol:
        #     continue
        if strategy_name in user['qty']:
            print(user['account_name'], "already has a quantity for", strategy_name)
            
        
            user_details, _ = general_calc.get_user_details(user['account_name'])
            capital = user['expected_morning_balance']
            percentage_risk = user_details['percentage_risk'].get(strategy_name, 0)

            if percentage_risk <= 0:
                print(f"No risk allocated for strategy {strategy_name} or invalid risk value for user {base_symbol}.")
                return

            lot_size = indices_lot_sizes.get(base_symbol, 1)
            risk = percentage_risk if percentage_risk < 1 else percentage_risk / capital
            raw_quantity = (risk * capital) / ltp
            quantity = int((raw_quantity // lot_size) * lot_size)
            print(f"Quantity for {base_symbol} is {quantity}")
            if quantity == 0:
                quantity = lot_size

            # Update the quantity in the user's data
            user['qty'] = user.get('qty', {})
            user['qty'][strategy_name] = quantity

        # Save the updated active users back to the file
        general_calc.write_json_file(active_users_file, active_users)




