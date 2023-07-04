from broker import Broker
from instrument import Instrument
import json
from order_manager import OrderManager
from monitor import OrderMonitor

import PreMarket as pm
from kiteconnect import KiteConnect

def main():
    # Read the brokers and levels JSON files
    with open ("brokers.json") as f:
        brokers_data = json.load(f)

    # Create a list of Broker objects
    brokers = [Broker(name, data) for name, data in brokers_data.items()]

    # 9.05AM Tasks
    pm.setExpiryDate()
    pm.setInstruMood()
    pm.updateATR5d()

    # 10:15AM Tasks
    pm.updateIB()
    with open ("mpwizard.json") as f:
        levels_data = json.load(f)
    print("Levels data: ", levels_data)

    # Create a list of Instrument objects
    instruments = [Instrument(data) for data in levels_data["indices"]]

    # Initialize the TelegramBot
    telegram_bot = TelegramBot()

    # Start monitoring the instruments and managing orders
    order_monitor =OrderMonitor(brokers_file='brokers.json', instruments=instruments, telegram_bot=telegram_bot)
    order_monitor.monitor_instruments()

    # 03:15PM Tasks
    
if __name__ == "__main__":
    main()
