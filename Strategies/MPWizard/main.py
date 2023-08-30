from monitor import OrderMonitor
from instrument import Instrument
import json
from mpw_place_orders import get_mpwizard_users
import os
from MPWizard_calc import get_high_low_range_and_update_json, get_average_range_and_update_json, get_expiry_dates
import datetime
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(CURRENT_DIR, '..','..','Brokers','.env')
env_file_path = os.path.abspath(env_file_path)

print(env_file_path)

users_to_trade = get_mpwizard_users(r'C:\Users\user\Desktop\TradeMan\Utils\broker.json')

def main():
    # get_average_range_and_update_json()
    # now = datetime.datetime.now()
    # wait_time = datetime.datetime(now.year, now.month, now.day, 13, 13) - now
    # print(f"Waiting for {wait_time} before starting the bot")

    # if wait_time.total_seconds() > 0:  # only sleep if wait_time is positive
    #     time.sleep(wait_time.total_seconds())
    # get_high_low_range_and_update_json()

    # # 10:15AM Tasks
    with open("Strategies\MPWizard\MPWizard.json", "r") as file:
        levels_data = json.load(file)
    # levels_data = read_json_file("MPWizard.json")

    # Create a list of Instrument objects
    instruments = [Instrument(data) for data in levels_data["indices"]]


    # Start monitoring the instruments and managing orders
    order_monitor =OrderMonitor(users= users_to_trade ,instruments=instruments)
    order_monitor.monitor_index()

    # 03:15PM Tasks
    
if __name__ == "__main__":
    main()
