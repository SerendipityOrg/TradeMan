# Import necessary libraries and modules
from MPWizard_monitor import OrderMonitor
import os,sys
from dotenv import load_dotenv
import MPWizard_calc as MPWizard_calc
import datetime as dt
from time import sleep

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

import Strategies.StrategyBase as StrategyBase
import Brokers.place_order_calc as place_order_calc
import MarketUtils.general_calc as general_calc
from MarketUtils.InstrumentBase import Instrument
import MarketUtils.Discord.discordchannels as discord


_,strategy_path = general_calc.get_strategy_json('MPWizard')
strategy_obj = StrategyBase.Strategy.read_strategy_json(strategy_path)

# Fetch the desired start time from the environment variables
desired_start_time_str = strategy_obj.get_entry_params().get('EntryTime')
start_hour, start_minute, start_second = map(int, desired_start_time_str.split(':'))

# Fetch the list of users to trade with the strategy

def place_test_orders():
    indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    cross_types = ["UpCross", "DownCross"]
    ib_levels = ["Big", "Medium", "Small"]
    _,STRATEGY_PATH = general_calc.get_strategy_json('MPWizard')
    strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)

    for index in indices:
        for cross_type in cross_types:
            for ib_level in ib_levels:
                # Generate a message for testing
                
                # Fetch the token for the index
                token = strategy_obj.get_general_params()['IndicesTokens'][index]
                ltp = strategy_obj.get_single_ltp(token)
                trade_view = strategy_obj.get_general_params()['TradeView']
                option_type = MPWizard_calc.calculate_option_type(ib_level,cross_type, trade_view)
                strikeprc = strategy_obj.round_strike_prc(ltp,index)
                expiry_date = Instrument().get_expiry_by_criteria(index,strikeprc,option_type,'current_week')
                exchange_token = Instrument().get_exchange_token_by_criteria(index,strikeprc,option_type,expiry_date)
                trade_symbol = Instrument().get_trading_symbol_by_exchange_token(exchange_token)

                message = f"Test order for {index} {trade_view} {cross_type} {ib_level} {trade_symbol}"
                print(message)
                discord.discord_bot(message, 'TestOrders')

def main():
    """
    Main function to execute the trading strategy.
    """
    now = dt.datetime.now()

    if now.date() in general_calc.holidays:
        print("Skipping execution as today is a holiday.")
        return
    
    if now.time() < dt.time(9, 0):
        print("Time is before 9:00 AM, placing test orders.")
        place_test_orders()
    else:
        # Update the JSON file with average range data
        MPWizard_calc.get_average_range_and_update_json(strategy_obj.get_general_params().get('ATRPeriod'))
        
        # Calculate the wait time before starting the bot
        desired_start_time = dt.datetime(now.year, now.month, now.day, start_hour, start_minute)
        wait_time = desired_start_time - now
        print(f"Waiting for {wait_time} before starting the bot")
        
        # Sleep for the calculated wait time if it's positive
        if wait_time.total_seconds() > 0:
            sleep(wait_time.total_seconds())
        
        # Update the JSON file with high-low range data
        MPWizard_calc.get_high_low_range_and_update_json()
        
        with open(strategy_path,'r') as file:
            instruments = file.read()
        
        # Initialize the OrderMonitor with the users and instruments, then start monitoring
        order_monitor = OrderMonitor(instruments, max_orders=2) 
        order_monitor.monitor_index()

if __name__ == "__main__":
    main()
