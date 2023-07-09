from kiteconnect import KiteConnect
import pandas as pd


token = 256265
from_date = '2023-05-03'
to_date = '2023-05-08'
interval = 'minute'

kite = KiteConnect("6b0dp5ussukmo67h")
kite.set_access_token("C41XLlP4ClVieiBsJHqJ8jNJjyScnm68")

ohlc_list = kite.historical_data(token, from_date, to_date, interval)
ohlc_df = pd.DataFrame(ohlc_list)
ohlc_df.to_csv('nifty_50.csv')

