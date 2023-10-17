from pya3 import *
import sys

DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.Calculations.qty_calc as qty_calc
import Brokers.BrokerUtils.Broker as Broker
import Brokers.Aliceblue.alice_login as alice_login

def get_csv_alice(user_details):
    alice = Aliceblue(user_id=user_details['aliceblue']['brijesh']['username'], api_key=user_details['aliceblue']['brijesh']['api_key'])
    alice.get_session_id()
    alice.get_contract_master("NFO") #TODO rename the NFO.csv to alice_instruments.csv




