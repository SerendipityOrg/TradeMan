import random
import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import Strategies.StrategyBase as StrategyBase

def flip_coin():
    # Randomly choose between 'Heads' and 'Tails'
    result = random.choice(['Heads', 'Tails'])
    return result

# Flipping the coin and printing the result

def create_order_details():
    strategy_obj = StrategyBase.Strategy({})
    strike_prc = strategy_obj.calculate_current_atm_strike_prc('NIFTY')
    option_type = 'CE' if flip_coin() == 'Heads' else 'PE'
    print(strike_prc, option_type)

create_order_details()
