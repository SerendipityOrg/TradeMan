import os
import sys
import datetime as dt
from time import sleep
from dotenv import load_dotenv

# Setup paths and load environment variables
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([os.path.join(ROOT_DIR, '..', path) for path in ['Utils', 'Brokers']])
load_dotenv(os.path.join(ROOT_DIR, '..', 'Brokers', '.env'))

UTILS_DIR = os.path.join(ROOT_DIR, '..','MarketUtils')
sys.path.append(UTILS_DIR)
import general_calc


BROKERS_DIR = os.path.join(ROOT_DIR, '..', 'Brokers')
sys.path.append(BROKERS_DIR)
import place_order 

# Add parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Now you can import the Strategy module
import StrategyBase

class ExpiryTrader(StrategyBase.Strategy):
    def get_general_params(self):
        return self.general_params
    
    def get_entry_params(self):
        return self.entry_params
    
    def get_exit_params(self):
        return self.exit_params
    
  # No additional methods or attributes for now. Can be expanded as needed.

# Testing the class with ExpiryTrader data
expiry_trader_obj = ExpiryTrader.read_strategy_json(r"Strategies/ExpiryTrader/ExpiryTrader.json")  #TODO pass the location as variable
# Update the JSON file with today's expiry
today_expiry, expiry_token = expiry_trader_obj.determine_expiry_index()

# Extract strategy parameters
prediction = expiry_trader_obj.get_general_params().get('TradeView')
strike_prc_multiplier = expiry_trader_obj.get_entry_params().get('StrikeMultiplier')
hedge_multiplier = expiry_trader_obj.get_entry_params().get('HedgeMultiplier')
stoploss_mutiplier = expiry_trader_obj.get_entry_params().get('SLMultipler')
desired_start_time_str = expiry_trader_obj.get_entry_params().get('EntryTime')
start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))

# Main logic
now = dt.datetime.now()
wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
if wait_time.total_seconds() > 0:
    print(f"Waiting for {wait_time} before starting the bot")
    sleep(wait_time.total_seconds())

main_strikeprc = expiry_trader_obj.calculate_strike_prc(expiry_token, today_expiry, prediction, strike_prc_multiplier)
option_type = expiry_trader_obj.get_option_type(prediction,"OB")
hedge_strikeprc = expiry_trader_obj.get_hedge_strikeprc(expiry_token, today_expiry, prediction, hedge_multiplier)
hedge_option_type = expiry_trader_obj.get_option_type(prediction,"OB")

print(f"Placing order for {today_expiry} {option_type} {main_strikeprc} {prediction} at {now}")
print(f"Placing order for {today_expiry} {hedge_option_type} {hedge_strikeprc} {prediction} at {now}")

orders_to_place = [
    ({
        "strategy": "ExpiryTrader",
        "base_symbol": today_expiry,
        "option_type": expiry_trader_obj.get_hedge_option_type(prediction),
        "strike_prc": hedge_strikeprc,
        "transaction": "BUY",
        "order_mode" : "Hedge"
    }),
    ({
        "strategy": "ExpiryTrader",
        "base_symbol": today_expiry,
        "option_type": expiry_trader_obj.get_option_type(prediction,expiry_trader_obj.get_general_params().get('StrategyType')),
        "strike_prc": main_strikeprc,
        "transaction": "SELL",
        "order_mode" : "Main",
        "stoploss_mutiplier": stoploss_mutiplier
    })
]

for order_details in orders_to_place:
    place_order.place_order_for_broker(order_details)

