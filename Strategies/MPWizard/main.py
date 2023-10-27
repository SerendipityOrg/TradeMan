# Import necessary libraries and modules
# from MPWizard_monitor import OrderMonitor
from MPW import OrderMonitor
import os,sys,json
from dotenv import load_dotenv
from MPWizard_calc import get_high_low_range_and_update_json, get_average_range_and_update_json
import datetime as dt
from time import sleep

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
# Load environment variables from .env file
load_dotenv(ENV_PATH)

import Strategies.StrategyBase as StrategyBase
import Brokers.place_order_calc as place_order_calc
import MarketUtils.general_calc as general_calc


_,strategy_path = place_order_calc.get_strategy_json('MPWizard')
strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

# Fetch the desired start time from the environment variables
desired_start_time_str = strategy_obj.get_entry_params().get('EntryTime')
start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))



# Fetch the list of users to trade with the strategy

def main():
    """
    Main function to execute the trading strategy.
    """
    # Update the JSON file with average range data
    # get_average_range_and_update_json(strategy_obj.get_general_params().get('ATRPeriod'))
    
    # Calculate the wait time before starting the bot
    now = dt.datetime.now()
    wait_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute) - now
    print(f"Waiting for {wait_time} before starting the bot")
    
    # Sleep for the calculated wait time if it's positive
    if wait_time.total_seconds() > 0:
        sleep(wait_time.total_seconds())
    
    # Update the JSON file with high-low range data
    # get_high_low_range_and_update_json()
    

    with open(strategy_path,'r') as file:
        instruments = file.read()
    
    # Initialize the OrderMonitor with the users and instruments, then start monitoring
    order_monitor = OrderMonitor(instruments,max_orders=2) 
    order_monitor.monitor_index()


if __name__ == "__main__":
    # Execute the main function if the script is run as the main module
    main()
