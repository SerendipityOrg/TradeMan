from kiteconnect import KiteConnect
import pandas as pd
import json,sys


DIR_PATH = "/Users/amolkittur/Desktop/Dev/"
sys.path.append(DIR_PATH)
import MarketUtils.Calculations.qty_calc as qty_calc
import Brokers.BrokerUtils.Broker as Broker
import Brokers.Zerodha.kite_login as kite_login


def get_csv_kite(user_details):
    kite = KiteConnect(api_key=user_details['zerodha']['omkar']['api_key'])
    kite.set_access_token(user_details['zerodha']['omkar']['access_token'])
    instrument_dump = kite.instruments()
    instrument_df = pd.DataFrame(instrument_dump)
    instrument_df.to_csv(r'kite_instruments.csv') 



