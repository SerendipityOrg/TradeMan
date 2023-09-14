import os
import sys
from dotenv import load_dotenv

# Set up paths and import modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BROKERS_DIR = os.path.join(CURRENT_DIR, '..', '..', 'Brokers')

sys.path.append(os.path.join(CURRENT_DIR, '..', '..', 'Utils'))
import general_calc as gc

sys.path.append(BROKERS_DIR)
import place_order
import place_order_calc as place_order_calc

dotenv_path = os.path.join(BROKERS_DIR, '.env')
load_dotenv(dotenv_path)

index = os.getenv('overnight_index')

def determine_option_and_transaction(direction, strike_price):
    """Determine the option type and transaction type based on direction and strike price."""
    if direction == 'BEARISH':
        option_type = 'CE' if strike_price != "0" else 'FUT'
        transaction = "SELL" if strike_price != '0' else "BUY"
    elif direction == 'BULLISH':
        option_type = 'PE' if strike_price != "0" else 'FUT'
        transaction = "SELL"
    
    return option_type, transaction

def fetch_order_details_for_user(user, broker):
    """Get order details for given user and broker."""
    json_data, _ = place_order_calc.get_user_details(user)
    trade_details = json_data[broker]["orders"]["overnight_option"]["BUY"]

    order_details_opt, order_details_future = None, None
    for trade in trade_details:
        strike_price = trade["strike_price"]
        direction = trade['direction']
        option_type, transaction_type = determine_option_and_transaction(direction, strike_price)

        if option_type != 'FUT':
            order_details_opt = {
                "direction": direction,
                "base_symbol": index,
                "option_type": option_type,
                "strike_prc": strike_price,
                "transcation": transaction_type
            }
        else:
            order_details_future = {
                "direction": direction,
                "base_symbol": index,
                "option_type": 'FUT',
                "strike_prc": 0,
                "transcation": transaction_type
            }

    return order_details_opt, order_details_future

def main():
    # Taking the first user and broker
    broker, user = gc.get_strategy_users("overnight_option")[0]
    
    order_details_opt, order_details_future = fetch_order_details_for_user(user, broker)
    print("Option Details:", order_details_opt)
    print("Future Details:", order_details_future)

    place_order.place_order_for_broker("overnight_option", order_details_future,trade_type='Morning')
    place_order.place_order_for_broker("overnight_option", order_details_opt,trade_type='Morning')

if __name__ == "__main__":
    main()
