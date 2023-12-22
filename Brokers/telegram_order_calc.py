import os, sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Strategies.StrategyBase as StrategyBase
from MarketUtils.InstrumentBase import Instrument
import MarketUtils.general_calc as general_calc

active_users_json_path = os.path.join(DIR_PATH,"MarketUtils", "active_users.json")

def extract_base_symbol(details):
    return details['stock_name'] if details['base_instrument'] == 'Stock' else details['base_instrument']

def get_strategy_object(details):
    from Brokers.place_order_calc import calculate_strategy_name
    strategy_name = calculate_strategy_name(details['trade_id'])
    _, STRATEGY_PATH = general_calc.get_strategy_json(strategy_name)
    return strategy_name, StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)

def calculate_strike_price(details, strategy_obj, base_symbol):
    if details['strike_prc'] == "ATM":
        return strategy_obj.calculate_current_atm_strike_prc(base_symbol)
    elif details['option_type'] in ['FUT', 'Stock']:
        return 0
    else:
        return details['strike_prc']
    
def get_exchange_token(details, base_symbol, strike_prc):
    if details.get('option_type') == 'Stock':
        return Instrument().get_exchange_token_by_name(details['stock_name'], "NSE")
    else:
        expiry_date = Instrument().get_expiry_by_criteria(base_symbol, int(strike_prc), details['option_type'], details['expiry'])
        return Instrument().get_exchange_token_by_criteria(base_symbol, int(strike_prc), details['option_type'], expiry_date)

def prepare_order_details(details, strategy_name, base_symbol, exchange_token, strategy_obj):
    order_details = {
        "strategy": strategy_name,
        "base_symbol": base_symbol,
        "exchange_token": exchange_token,
        "transaction_type": details['transaction_type'],
        "product_type": details['product_type'],
        "trade_id": details['trade_id']
    }

    if details['base_instrument'] == 'Stock' and details['option_type'] != 'Stock':
        order_details['order_type'] = 'Limit'
        token = Instrument().get_token_by_exchange_token(exchange_token)
        order_details['limit_prc'] = round(strategy_obj.get_single_ltp(token), 1)
    else:
        order_details['order_type'] = 'Market'

    if details['order_type'] == 'PlaceOrder':
        order_details['order_mode'] = ['MainOrder']

    return order_details

def place_orders_for_users(details, order_details):
    from MarketUtils.Calculations.qty_calc import calculate_qty_for_telegram
    import Brokers.place_order as place_order
    active_users = general_calc.read_json_file(active_users_json_path)

    user = details['account_name']
    for active_user in active_users:
        if active_user['account_name'] == user:
            order_details['account_name'] = user
            order_details['broker'] = active_user['broker']
            if 'risk_percentage' in details:
                order_details['qty'] = calculate_qty_for_telegram(details['risk_percentage'], user, order_details.get('base_symbol'), int(order_details.get('exchange_token')))
            elif 'qty' in details:
                order_details['qty'] = details['qty']
            else:
                print("Quantity not specified for", user)
            place_order.place_order_for_broker(order_details)