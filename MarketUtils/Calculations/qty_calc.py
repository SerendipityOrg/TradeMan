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
from MarketUtils.Firebase.firebase_utils import fetch_collection_data_firebase,update_fields_firebase

active_users_json_path = os.path.join(DIR_PATH, 'MarketUtils', 'active_users.json')
strategy_data = fetch_collection_data_firebase('strategies')
   
def  get_price_reference_firebase(strategy_name, instrument):
    # Here we are using a mock strategy JSON for demonstration purposes
    strategy_data = fetch_collection_data_firebase('strategies')
    today_index = dt.datetime.today().weekday()
    key = f"{instrument}OptRef"
    price_ref_values = strategy_data[strategy_name]['ExtraInformation'].get(key, [])
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
    current_capital = user['expected_morning_balance']
    for key,value in user['Strategies'].items():
        strategy_name = key
        risk = value['Risk']
        instruments = strategy_data[strategy_name]['Instruments']
        if 'QtyCalc' not in strategy_data[strategy_name]['ExtraInformation']:
            continue
        qty_calculation_type = strategy_data[strategy_name]['ExtraInformation']['QtyCalc']
        if qty_calculation_type == "DuringEntry":
            qty = 0
            update_fields_firebase('new_clients',user['trademan_username'],{'Strategies':{strategy_name:{'Qty':qty}}})
            continue
        for instrument in instruments:
            prc_ref = strategy_data[strategy_name]['ExtraInformation'][f'{instrument}OptRef'] if qty_calculation_type == "PrcRef" else None
            prc_ref = get_price_reference_firebase(strategy_name, instrument) if qty_calculation_type == "PrcRef" else None
            lot_size = FNOInfo().get_lot_size_by_base_symbol(instrument)
            quantity = calculate_qty_for_strategies(current_capital, risk, prc_ref, lot_size)
            if len(instruments) == 1:
                qty = quantity
                update_fields_firebase('new_clients',user['trademan_username'],{'Strategies':{strategy_name:{'Qty':qty}}})
            else:
                qty = quantity
                update_fields_firebase('new_clients',user['trademan_username'],{'Strategies':{strategy_name:{'Qty':qty}}})

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
        
