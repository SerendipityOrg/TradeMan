# Import necessary libraries and modules
from monitor import OrderMonitor
import os,sys
from dotenv import load_dotenv
from MPWizard_calc import get_high_low_range_and_update_json, get_average_range_and_update_json
import datetime as dt
import time

# Define the current directory and paths for JSON and environment files
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
mpwizard_json = os.path.abspath(os.path.join(CURRENT_DIR, "MPWizard.json"))
env_file_path = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', 'Brokers', '.env'))

# Load environment variables from .env file
load_dotenv(env_file_path)

# Fetch the desired start time from the environment variables
desired_start_time_str = os.getenv('program_start_time')  # e.g., "10:15"
desired_start_hour, desired_start_minute = map(int, desired_start_time_str.split(':'))

# Define the utilities directory and append it to the system path
UTILS_DIR = os.path.join(CURRENT_DIR, '..', '..', 'Utils')
sys.path.append(UTILS_DIR)

# Import utility functions and classes
from general_calc import *
from instrument import Instrument as instru

# Fetch the list of users to trade with the strategy
users_to_trade = get_strategy_users('MPWizard')

def main():
    """
    Main function to execute the trading strategy.
    """
    # Update the JSON file with average range data
    get_average_range_and_update_json()
    
    # Calculate the wait time before starting the bot
    now = dt.datetime.now()
    wait_time = dt.datetime(now.year, now.month, now.day, desired_start_hour, desired_start_minute) - now
    print(f"Waiting for {wait_time} before starting the bot")
    
    # Sleep for the calculated wait time if it's positive
    if wait_time.total_seconds() > 0:
        time.sleep(wait_time.total_seconds())
    
    # Update the JSON file with high-low range data
    get_high_low_range_and_update_json()
    
    # Read the levels data from the JSON file
    levels_data = read_json_file(mpwizard_json)
    
    # Create a list of Instrument objects from the levels data
    instruments = [instru(data) for data in levels_data["indices"]]
    
    # Initialize the OrderMonitor with the users and instruments, then start monitoring
    order_monitor = OrderMonitor(users=users_to_trade, instruments=instruments)
    order_monitor.monitor_index()


if __name__ == "__main__":
    # Execute the main function if the script is run as the main module
    main()
