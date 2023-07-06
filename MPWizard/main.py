from broker import Broker
from instrument import Instrument

from order_manager import OrderManager
from monitor import OrderMonitor
from json_utils import read_json_file, write_json_file
# import PreMarket as pm
from kiteconnect import KiteConnect

def main():
    # Read the brokers and levels JSON files
    with open ("brokers.json") as f:
        brokers_data = json.load(f)

    # Create a list of Broker objects
    brokers = [Broker(name, data) for name, data in brokers_data.items()]

    # 9.05AM Tasks
    # pm.setExpiryDate()
    # pm.setInstruMood()
    # pm.updateATR5d()

    # # 10:15AM Tasks
    # pm.updateIB()
    levels_data = read_json_file("MPWizard.json")
    print("Levels data: ", levels_data)

    with open(r"/Users/amolkittur/Documents/TradeMan/Utils/instruments.csv") as f:
        Instrument = f.readlines()
    # Create a list of Instrument objects
    instruments = [Instrument(data) for data in levels_data["indices"]]

    # Initialize the TelegramBot


    # Start monitoring the instruments and managing orders
    order_monitor =OrderMonitor(brokers_file='brokers.json', instruments=instruments)
    order_monitor.monitor_instruments()

    # 03:15PM Tasks
    
if __name__ == "__main__":
    main()
