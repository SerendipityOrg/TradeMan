import datetime as dt
import os, sys
import math

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)
import MarketUtils.general_calc as general_calc
import Brokers.place_order_calc as place_order_calc
import Strategies.StrategyBase as StrategyBase


# Function to get price reference values from the strategy object
def get_price_reference(strategy_name, instrument):
    # Here we are using a mock strategy JSON for demonstration purposes
    _,strategy_path = place_order_calc.get_strategy_json(strategy_name)
    strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

    today_index = dt.datetime.today().weekday()
    key = f"{instrument}OptRef"
    price_ref_values = strategy_obj.get_extra_information().get(key, [])
    if price_ref_values:
        return price_ref_values[today_index]
    else:
        return 0 
# Function to calculate quantity based on capital, risk, price reference, and lot size
def calculate_quantity(capital, risk, prc_ref, lot_size, strategy_name):
    if strategy_name == "MPWizard" and prc_ref is not None:
        if prc_ref == 0:
            print("Price reference is 0")
            return 0
        raw_quantity = (risk * capital) / prc_ref
        quantity = int((raw_quantity // lot_size) * lot_size)
        if quantity == 0:
            quantity = lot_size
    else:
        # For other strategies, risk values represent the capital allocated
        if risk <= 1:
            print(f"Risk for {strategy_name} is not in absolute capital terms. Skipping calculation.")
            return 0
        lots = capital / risk
        quantity = math.ceil(lots) * lot_size
    return quantity


def calculate_lots(active_users):
    qty = {}
    for user in active_users:
        current_capital = user['expected_morning_balance']
        user_details, _ = general_calc.get_user_details(user['account_name'])
        percentage_risk = user_details['percentage_risk']

        indices_lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40, "MIDCAP": 75, "SENSEX": 10}

        for strategy_name, risk in percentage_risk.items():
            _, strategy_path = place_order_calc.get_strategy_json(strategy_name)
            strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)
            instruments = strategy_obj.get_instruments()
            
            if len(instruments) == 1:
                # If there is only one instrument for the strategy, store the quantity directly
                instrument = instruments[0]
                prc_ref = get_price_reference(strategy_name, instrument) if strategy_name == "MPWizard" else None
                lot_size = indices_lot_sizes.get(instrument, 1)
                quantity = calculate_quantity(current_capital, risk, prc_ref, lot_size, strategy_name)
                qty[strategy_name] = quantity
            else:
                # If there are multiple instruments, store the quantities in a nested dictionary
                qty[strategy_name] = {}
                for instrument in instruments:
                    prc_ref = get_price_reference(strategy_name, instrument) if strategy_name == "MPWizard" else None
                    lot_size = indices_lot_sizes.get(instrument, 1)
                    quantity = calculate_quantity(current_capital, risk, prc_ref, lot_size, strategy_name)
                    qty[strategy_name][instrument] = quantity

    return qty


