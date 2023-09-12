from kiteconnect import KiteConnect
import pandas as pd


# token = 256265 # nifty
token = 260105 # banknifty
from_date = '2023-06-03'
to_date = '2023-07-08'
interval = 'minute'

kite = KiteConnect("6b0dp5ussukmo67h")
kite.set_access_token("E5eXOEViUKy9qzwGwFc352w42HRHyCDC")

ohlc_list = kite.historical_data(token, from_date, to_date, interval)
ohlc_df = pd.DataFrame(ohlc_list)
# ohlc_df.to_csv('nifty_50.csv')
ohlc_df.to_csv("banknifty_50.csv")

