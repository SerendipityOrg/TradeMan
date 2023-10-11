import os,sys
import general_calc as general_calc 
from datetime import datetime
from pprint import pprint

script_dir = os.path.dirname(os.path.realpath(__file__))
calc_dir = os.path.join(script_dir, '..',"Brokers")
sys.path.append(calc_dir)

import place_order_calc as place_order_calc
import zerodha.kite_place_orders as zerodha
import aliceblue.alice_place_orders as aliceblue

def simplify_zerodha_order(detail):
    trade_symbol = detail['tradingsymbol']
    
    # Check if the tradingsymbol is of futures type
    if trade_symbol.endswith("FUT"):
        strike_price = 0
        option_type = "FUT"
    else:
        strike_price = int(trade_symbol[-7:-2])  # Convert to integer to store as number
        option_type = trade_symbol[-2:]

    trade_id = detail['tag']
    if trade_id.endswith('_entry'):
        trade_id = trade_id.rsplit('_entry', 1)[0]
    elif trade_id.endswith('_exit'):
        trade_id = trade_id.rsplit('_exit', 1)[0]
    
    return {
        'trade_id' : trade_id,  # This is the order_id for zerodha
        'avg_price': detail['average_price'],
        'qty': detail['quantity'],
        'time': detail["order_timestamp"].strftime("%d/%m/%Y %H:%M:%S"),
        'strike_price': strike_price,
        'option_type': option_type,
        'trading_symbol': trade_symbol,
        'trade_type': detail['transaction_type']
    }

def simplify_aliceblue_order(detail):
    if detail['optionType'] == 'XX':
        strike_price = 0
        option_type = "FUT"
    else:
        strike_price = int(detail['strikePrice'])
        option_type = detail['optionType']

    trade_id = detail['remarks']
    if trade_id.endswith('_entry'):
        trade_id = trade_id.rsplit('_entry', 1)[0]
    elif trade_id.endswith('_exit'):
        trade_id = trade_id.rsplit('_exit', 1)[0]

    return {
        'trade_id' : trade_id,
        'avg_price': float(detail['Avgprc']),
        'qty': int(detail['Qty']),
        'time': detail['OrderedTime'],
        'strike_price': strike_price,
        'option_type': option_type,
        'trading_symbol': detail['Trsym'],
        'trade_type': 'BUY' if detail['Trantype'] == 'B' else 'SELL'
    }


def load_userdata():
    return general_calc.read_json_file(os.path.join(script_dir,"broker.json"))

json_data = load_userdata()

users_with_strategies = []

def assign_short_and_long_orders(orders):
    results = {
        "AmiPy": {
            "ShortSignal": [],
            "ShortCoverSignal": [],
            "LongSignal": [],
            "LongCoverSignal": []
        }
    }

    # Helper function to categorize orders based on strike prices
    def categorize_orders(order_list):
        # Group orders by strike price
        strike_prices = {}
        for order in order_list:
            if order["strike_price"] in strike_prices:
                strike_prices[order["strike_price"]].append(order)
            else:
                strike_prices[order["strike_price"]] = [order]

        main_orders = []
        hedge_orders = []

        # Determine which orders are main and which are hedge
        for _, orders in strike_prices.items():
            if len(orders) == 2:
                main_orders.extend(orders)
            else:
                hedge_orders.extend(orders)

        return main_orders, hedge_orders

    main_orders, hedge_orders = categorize_orders(orders)

    # Assign orders based on the logic provided
    if len(orders) == 4:
        if "_entry" in orders[0]["trade_id"]:
            for order in main_orders:
                order["trade_type"] = "ShortSignal"
            for order in hedge_orders:
                order["trade_type"] = "HedgeOrder"
            results["AmiPy"]["ShortSignal"].extend(main_orders)
            results["AmiPy"]["ShortSignal"].extend(hedge_orders)
        else:
            for order in main_orders:
                order["trade_type"] = "ShortCoverSignal"
            for order in hedge_orders:
                order["trade_type"] = "HedgeOrder"
            results["AmiPy"]["ShortCoverSignal"].extend(main_orders)
            results["AmiPy"]["ShortCoverSignal"].extend(hedge_orders)
    elif len(orders) == 2:
        if "_entry" in orders[0]["trade_id"]:
            results["AmiPy"]["LongSignal"] = main_orders
        else:
            results["AmiPy"]["LongCoverSignal"] = main_orders

    return results

def amipy_details(orders, broker, user):
    # Simplify orders based on the broker
    simplified_orders = []
    for order in orders:
        if broker == "zerodha":
            simplified_orders.append(simplify_zerodha_order(order))
        elif broker == "aliceblue":
            simplified_orders.append(simplify_aliceblue_order(order))
        else:
            simplified_orders.append(order)
        
    # Step 2: Assign short and long orders
    organized_orders = assign_short_and_long_orders(simplified_orders)
    
    results = organized_orders  # This is now already structured as you want it

    # Clean up empty entries
    for signal_type in ["ShortSignal", "ShortCoverSignal", "LongSignal", "LongCoverSignal"]:
        if not results["AmiPy"][signal_type]:
            del results["AmiPy"][signal_type]

    return results

def mpwizard_details(orders, broker, user):
    results = {}
    buy_orders = []
    sell_orders = []

    # Simplify the orders and segregate them
    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order

        if simplified_order["trade_type"] == "BUY":
            buy_orders.append(simplified_order)
        elif simplified_order["trade_type"] == "SELL":
            sell_orders.append(simplified_order)

    results = {
        "MPWizard": {
            "BUY": buy_orders,
            "SELL": sell_orders
        }
    }
    return results

def overnight_options_details(orders, broker, user):
    results = {}
    morning_trade_orders = []

    # Simplify the orders and collect them
    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order
        morning_trade_orders.append(simplified_order)

    # Check if there are 2 orders and group them under "Morning Trade"
    # Afternoon orders are entered after placing the orders in the afternoon
    results = {
        "OverNight Options": {
            "Morning": morning_trade_orders
        }
    }
    return results



strategy_to_function = {
    'AmiPy': amipy_details,
    'MPWizard': mpwizard_details,
    'Overnight_Options': overnight_options_details,
    # Add other strategies and their functions here
}




# 1. Read broker.json and make a note of the strategies
users_with_strategies = []
for broker, accounts in json_data.items():
    accounts_to_trade = accounts.get("accounts_to_trade", [])
    for account_name in accounts_to_trade:
        if account_name in accounts:
            strategies = list(accounts[account_name]["percentageRisk"].keys())
            users_with_strategies.append({
                "user": account_name,
                "broker": broker,
                "strategies": strategies
            })

# Placeholder function to segregate orders
def segregate_by_strategy(details, strategies, broker):
    combined_details = {}
    for strategy in strategies:
        # 3. Get today_orders from the strategy's JSON and add _entry and _exit suffixes
        strategy_json, _ = place_order_calc.get_strategy_json(strategy)
        trade_ids = strategy_json.get('today_orders', [])
        entry_ids = [tid + "_entry" for tid in trade_ids]
        exit_ids = [tid + "_exit" for tid in trade_ids]
        
        # 4. Search for the orders in the details list
        for detail in details:
            key_to_check = 'remarks' if broker == 'aliceblue' else 'tag' if broker == 'zerodha' else None
            if key_to_check and detail.get(key_to_check) in (entry_ids + exit_ids):
                if strategy in combined_details:
                    combined_details[strategy].append(detail)
                else:
                    combined_details[strategy] = [detail]
    return combined_details

# 2. Process each user's strategies
for user in users_with_strategies:
    user_details, user_json_path = place_order_calc.get_user_details(user["user"])
    
    if user["broker"] == "zerodha":
        details = zerodha.get_order_details(user_details)
    elif user["broker"] == "aliceblue":
        details = aliceblue.get_order_details(user_details)
    
    # 5. Segregate and process the orders
    strategy_based_details = segregate_by_strategy(details, user["strategies"], user["broker"])
    combined_user_orders = {}
    for strategy, order_list in strategy_based_details.items():
        if strategy in strategy_to_function:
            processed_orders = strategy_to_function[strategy](order_list, user["broker"], user["user"])
            combined_user_orders.update(processed_orders)

    # # Output combined user orders
    if combined_user_orders:
        user_final_orders = {"orders": combined_user_orders}
        pprint(user_final_orders)

    # user_json_data = general_calc.read_json_file(user_json_path)
        
    # user_json_data[user["broker"]]["today_orders"] = user_final_orders

    # general_calc.write_json_file(user_json_path, user_json_data)