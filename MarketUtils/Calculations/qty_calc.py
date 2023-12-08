import datetime as dt
import os, sys
import math

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
import MarketUtils.general_calc as general_calc
import Brokers.place_order_calc as place_order_calc
import Strategies.StrategyBase as StrategyBase
from MarketUtils.FNOInfoBase import FNOInfo
from MarketUtils.InstrumentBase import Instrument

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')

# Function to get price reference values from the strategy object
def get_price_reference(strategy_name, instrument):
    # Here we are using a mock strategy JSON for demonstration purposes
    _,strategy_path = general_calc.get_strategy_json(strategy_name)
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

    today_index = dt.datetime.today().weekday()
    key = f"{instrument}OptRef"
    price_ref_values = strategy_obj.get_extra_information().get(key, [])
    if price_ref_values:
        return price_ref_values[today_index]
    else:
        return 0 
# Function to calculate quantity based on capital, risk, price reference, and lot size
def calculate_qty_for_strategies(capital, risk, prc_ref_or_ltp, lot_size, strategy_name):
    if prc_ref_or_ltp is not None:
        raw_quantity = (risk * capital) / prc_ref_or_ltp
        quantity = int((raw_quantity // lot_size) * lot_size)
        if quantity == 0:
            quantity = lot_size
    else:
        # For other strategies, risk values represent the capital allocated
        lots = capital / risk
        quantity = math.ceil(lots) * lot_size
    return quantity


def calculate_lots(user):
    qty = {}
    current_capital = user['expected_morning_balance']
    user_details, _ = general_calc.get_user_details(user['account_name'])
    percentage_risk = user_details['percentage_risk']

    for strategy_name, risk in percentage_risk.items():
        if strategy_name not in qty:
            qty[strategy_name] = {}

        _, strategy_path = general_calc.get_strategy_json(strategy_name)
        strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
        instruments = strategy_obj.get_instruments()

        qty_calculation_type = strategy_obj.get_extra_information().get('QtyCalc')
        if qty_calculation_type == "DuringEntry":
            qty[strategy_name] = 0
            continue
        
        for instrument in instruments:  
            prc_ref = get_price_reference(strategy_name, instrument) if qty_calculation_type == "PrcRef" else None
            lot_size = FNOInfo().get_lot_size_by_base_symbol(instrument)
            quantity = calculate_qty_for_strategies(current_capital, risk, prc_ref, lot_size, strategy_name)
            if len(instruments) == 1:
                qty[strategy_name] = quantity
            else:
                qty[strategy_name][instrument] = quantity

    return qty

def update_qty_during_entry(ltp, strategy_name, base_symbol):
    _, strategy_path = general_calc.get_strategy_json(strategy_name)
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
    instruments = strategy_obj.get_instruments()

    if base_symbol not in instruments:
        print(f"{base_symbol} is not traded in {strategy_name}.")
        return

    try:
        active_users = general_calc.read_json_file(active_users_json_path)
    except FileNotFoundError:
        print(f"The file {active_users_json_path} does not exist.")
        return


    for user in active_users:#TODO this is fetch the capital from active_users.json instead of broker.json
        if strategy_name in user['qty']:
            user_details, _ = general_calc.get_user_details(user['account_name'])
            capital = user['expected_morning_balance']
            percentage_risk = user_details['percentage_risk'].get(strategy_name, 0)

            if percentage_risk <= 0:
                print(f"No risk allocated for strategy {strategy_name} or invalid risk value for user {base_symbol}.")
                return
            # calculate_qty_for_strategies(capital, risk, prc_ref, lot_size, strategy_name)
            lot_size = FNOInfo().get_lot_size_by_base_symbol(base_symbol)#TODO error
            quantity = calculate_qty_for_strategies(capital, percentage_risk, ltp, lot_size, strategy_name)

            # Update the quantity in the user's data
            user['qty'] = user.get('qty', {})
            user['qty'][strategy_name] = quantity

        # Save the updated active users back to the file
        general_calc.write_json_file(active_users_json_path, active_users)

def calculate_qty_for_telegram(risk,accountname,base_symbol=None,exchange_token=None):
    active_users = general_calc.read_json_file(active_users_json_path)
    for user in active_users:
        if user['account_name'] == accountname:
            if base_symbol == 'Stock':
                strategy_obj = StrategyBase.Strategy({})
                ltp = strategy_obj.get_single_ltp(Instrument().get_token_by_exchange_token(exchange_token))
                risk_capital = round(float(user['current_capital']*(int(risk)/100)))
                qty = math.ceil(risk_capital/ltp)
            else:
                strategy_obj = StrategyBase.Strategy({})
                ltp = strategy_obj.get_single_ltp(Instrument().get_token_by_exchange_token(exchange_token))
                lot_size = FNOInfo().get_lot_size_by_base_symbol(base_symbol)
                raw_qty = (user['current_capital'] * (int(risk)/100))/ltp
                qty = math.ceil(raw_qty//lot_size) * lot_size
                if qty == 0:
                    qty = lot_size
            return qty
        
