import os,sys
from datetime import datetime
from pprint import pprint

DIR = os.getcwd()
sys.path.append(DIR)

import Brokers.place_order_calc as place_order_calc
import Brokers.Zerodha.kite_utils as zerodha
import Brokers.Aliceblue.alice_utils as aliceblue
import MarketUtils.general_calc as general_calc
from Strategies.StrategyBase import Strategy


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
        order_type = "entry"
    elif trade_id.endswith('_exit'):
        order_type = "exit"
    
    return {
        'trade_id' : trade_id,  # This is the order_id for zerodha
        'avg_price': detail['average_price'],
        'qty': detail['quantity'],
        'time': detail["order_timestamp"].strftime("%d/%m/%Y %H:%M:%S"),
        'strike_price': strike_price,
        'option_type': option_type,
        'trading_symbol': trade_symbol,
        'trade_type': detail['transaction_type'],
        'order_type' : order_type
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
        order_type = "entry"
    elif trade_id.endswith('_exit'):
        order_type = "exit"

    return {
        'trade_id' : trade_id,
        'avg_price': float(detail['Avgprc']),
        'qty': int(detail['Qty']),
        'time': detail['OrderedTime'],
        'strike_price': strike_price,
        'option_type': option_type,
        'trading_symbol': detail['Trsym'],
        'trade_type': 'BUY' if detail['Trantype'] == 'B' else 'SELL',
        'order_type' : order_type
    }

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
    
    entry_orders = [order for order in orders if "_entry" in order["trade_id"]]
    exit_orders = [order for order in orders if "_exit" in order["trade_id"]]


    # Process entry orders
    main_orders, hedge_orders = categorize_orders(entry_orders)
    if len(entry_orders) in [4, 8]:
        for order in main_orders:
            order["trade_id"] = order["trade_id"].split('_')[0]
            order["trade_type"] = "ShortSignal"
        for order in hedge_orders:
            order["trade_id"] = order["trade_id"].split('_')[0]
            order["trade_type"] = "HedgeOrder"
        results["AmiPy"]["ShortSignal"].extend(main_orders)
        results["AmiPy"]["ShortSignal"].extend(hedge_orders)

    # Process exit orders
    main_orders, hedge_orders = categorize_orders(exit_orders)
    if len(exit_orders) in [4, 8]:
        for order in main_orders:
            order["trade_id"] = order["trade_id"].split('_')[0]
            order["trade_type"] = "ShortCoverSignal"
        for order in hedge_orders:
            order["trade_id"] = order["trade_id"].split('_')[0]
            order["trade_type"] = "HedgeOrder"
        results["AmiPy"]["ShortCoverSignal"].extend(main_orders)
        results["AmiPy"]["ShortCoverSignal"].extend(hedge_orders)

    return results

def amipy_details(orders, broker):
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

def mpwizard_details(orders, broker):
    results = {}
    buy_orders = []
    sell_orders = []

    # Simplify the orders and segregate them
    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order

        if simplified_order["trade_type"] == "BUY":
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            buy_orders.append(simplified_order)
        elif simplified_order["trade_type"] == "SELL":
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            sell_orders.append(simplified_order)

    def extract_numeric_part(trade_id):
        # Assuming the format is two letters followed by numbers 'MP201'
        return int(''.join(filter(str.isdigit, trade_id)))

    # Sort the buy and sell orders by the numeric part of trade_id
    buy_orders.sort(key=lambda x: extract_numeric_part(x["trade_id"]))
    sell_orders.sort(key=lambda x: extract_numeric_part(x["trade_id"]))

    results = {
        "MPWizard": {
            "BUY": buy_orders,
            "SELL": sell_orders
        }
    }
    return results

def overnight_futures_details(orders, broker):
    results = {}
    morning_trade_orders = []
    afternoon_trade_orders = []

    # Simplify the orders and collect them
    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order
        
        if simplified_order['order_type'] == 'entry':
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            afternoon_trade_orders.append(simplified_order)
        elif simplified_order['order_type'] == 'exit':
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            morning_trade_orders.append(simplified_order)
        

    if afternoon_trade_orders is not None:
        # Check if any order has trade_type as 'SELL'
        is_any_sell_order = any(order.get('trade_type') == 'SELL' for order in afternoon_trade_orders)

        # Assign direction based on the presence of any SELL order
        for order in afternoon_trade_orders:
            order['direction'] = 'BEARISH' if is_any_sell_order else 'BULLISH'


    if morning_trade_orders is not None:
        # Check if any order has trade_type as 'BUY'
        is_any_buy_order = any(order.get('trade_type') == 'BUY' for order in morning_trade_orders)

        # Assign direction based on the presence of any BUY order
        for order in morning_trade_orders:
            order['direction'] = 'BEARISH' if is_any_buy_order else 'BULLISH'


    # Check if there are 2 orders and group them under "Morning Trade"
    # Afternoon orders are entered after placing the orders in the afternoon
    results = {
        "OvernightFutures": {
            "Morning": morning_trade_orders,
            "Afternoon": afternoon_trade_orders
        }
    }
    return results

def expiry_trader_details(orders,broker):
    results = {}
    entry_orders = []
    exit_orders = []

    # Simplify the orders and segregate them
    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order

        if simplified_order["order_type"] == "entry":
            if simplified_order["trade_type"]=="BUY":
                simplified_order["trade_type"] = "HedgeOrder"
            elif simplified_order["trade_type"]=="SELL":
                simplified_order["trade_type"] = "MainOrder"
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            entry_orders.append(simplified_order)
        elif simplified_order["order_type"] == "exit":
            if simplified_order["trade_type"]=="BUY":
                simplified_order["trade_type"] = "MainOrder"
            simplified_order["trade_id"] = simplified_order["trade_id"].split('_')[0]
            exit_orders.append(simplified_order)

    results = {
        "ExpiryTrader": {
            "Entry": entry_orders,
            "Exit": exit_orders
        }
    }
    return results

def extra_details(orders,broker):
    results = {
        "EXTRA": {
            "Long": [],
            "Short": [],
            "LongCover": [],
            "ShortCover": []
        }
    }

    for order in orders:
        simplified_order = simplify_zerodha_order(order) if broker == "zerodha" else simplify_aliceblue_order(order) if broker == "aliceblue" else order

        if '_entry' in simplified_order['trade_id']:
            if simplified_order['trade_type'] == 'BUY':
                simplified_order['trade_type'] = 'LongOrder'
            elif simplified_order['trade_type'] == 'SELL':
                simplified_order['trade_type'] = 'ShortOrder'
        elif '_exit' in simplified_order['trade_id']:
            if simplified_order['trade_type'] == 'BUY':
                simplified_order['trade_type'] = 'ShortCoverOrder'
            elif simplified_order['trade_type'] == 'SELL':
                simplified_order['trade_type'] = 'LongCoverOrder'
            
        if simplified_order['trade_type'] == 'LongOrder':
            results['EXTRA']['Long'].append(simplified_order)
        elif simplified_order['trade_type'] == 'ShortOrder':
            results['EXTRA']['Short'].append(simplified_order)
        elif simplified_order['trade_type'] == 'LongCoverOrder':
            results['EXTRA']['LongCover'].append(simplified_order)
        elif simplified_order['trade_type'] == 'ShortCoverOrder':
            results['EXTRA']['ShortCover'].append(simplified_order)
    
    return results

        

strategy_to_function = {
    'AmiPy': amipy_details,
    'MPWizard': mpwizard_details,
    'OvernightFutures': overnight_futures_details,
    'ExpiryTrader' : expiry_trader_details,
    'Extra' : extra_details
    # Add other strategies and their functions here
}

# Placeholder function to segregate orders
def segregate_by_strategy(details, strategies, broker):
    combined_details = {}
    for strategy in strategies:
        # 3. Get today_orders from the strategy's JSON and add _entry and _exit suffixes
        _, strategy_path = place_order_calc.get_strategy_json(strategy)
        strategy_obj = Strategy.read_strategy_json(strategy_path)
        trade_ids = strategy_obj.get_today_orders()
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

active_users_path = os.path.join(DIR, "MarketUtils","active_users.json")
active_users = general_calc.read_json_file(active_users_path)

for user in active_users:
    if user["broker"] == "zerodha":
        details = zerodha.get_order_details(user)
    elif user["broker"] == "aliceblue":
        details = aliceblue.get_order_details(user)
    
    strategies = user["qty"]
    strategies = list(strategies.keys())
    #add "Extra" strategy to the list of strategies
    strategies.append("Extra")

    if "PreviousOvernightFutures" in strategies:
        strategies.remove("PreviousOvernightFutures")

    segregate_based_on_strategy = segregate_by_strategy(details, strategies, user["broker"])
    combined_user_orders = {}
    for strategy, order_list in segregate_based_on_strategy.items():
        if strategy in strategy_to_function:
            processed_orders = strategy_to_function[strategy](order_list, user["broker"])
            combined_user_orders.update(processed_orders)
    
    if combined_user_orders:
        user_final_orders = {"today_orders" : combined_user_orders}
        pprint(user_final_orders)

    order_json,order_json_path = place_order_calc.get_orders_json(user["account_name"])
    order_json["today_orders"] = combined_user_orders
    general_calc.write_json_file(order_json_path, order_json)