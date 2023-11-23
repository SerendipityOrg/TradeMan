import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.general_calc as general_calc
import Brokers.Aliceblue.alice_place_orders as aliceblue
import Brokers.Zerodha.kite_place_orders as zerodha

def sweep_open_orders():
    active_users = general_calc.read_json_file(os.path.join(DIR_PATH,"MarketUtils","active_users.json"))
    for user in active_users:
        if user['broker'] == "aliceblue":
            aliceblue.sweep_alice_orders(user)
        elif user['broker'] == "zerodha":
            zerodha.sweep_kite_orders(user)
        else:
            print("Unknown broker")
            return

if __name__ == "__main__":
    sweep_open_orders()