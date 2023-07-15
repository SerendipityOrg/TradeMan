from instrument import Instrument
from order_manager import OrderManager
from monitor import OrderMonitor
from json_utils import read_json_file, write_json_file
from MPW_place_orders import get_mpwizard_users
import os
from MPWizard_calc import get_high_low_range_and_update_json, get_average_range_and_update_json
import datetime
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
broker_filepath = os.path.join(script_dir, '..', 'Utils', 'broker.json')

users_to_trade = get_mpwizard_users(broker_filepath)


def main():
    get_average_range_and_update_json()
    now = datetime.datetime.now()
    wait_time = datetime.datetime(now.year, now.month, now.day, 10, 15) - now

    if wait_time.total_seconds() > 0:  # only sleep if wait_time is positive
        time.sleep(wait_time.total_seconds())
    get_high_low_range_and_update_json()

    # # 10:15AM Tasks
    levels_data = read_json_file("mpwizard(omkar).json")

    # Create a list of Instrument objects
    instruments = [Instrument(data) for data in levels_data["indices"]]

    # Start monitoring the instruments and managing orders
    order_monitor =OrderMonitor(users= users_to_trade ,instruments=instruments)
    order_monitor.monitor_instruments()

    # 03:15PM Tasks
    
if __name__ == "__main__":
    main()
