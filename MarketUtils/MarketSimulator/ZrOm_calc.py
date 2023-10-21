import os
import pandas as pd
from collections import namedtuple



Instrument = namedtuple("Instrument", ['exchange', 'token', 'symbol', 'name', 'expiry', 'lot_size'])

def get_option_tokens(base_symbol, expiry_date, strike_prc, option_type):
    #get out of the folder and then go to Utils folder and fetch the instruments.csv file
    instrument_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Utils", "instruments.csv")
    instruments_df = pd.read_csv(instrument_path)

    instruments_df = instruments_df[
        ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike"]
    ]
    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == base_symbol)
        & (instruments_df["expiry"] == expiry_date)
        & (instruments_df["strike"] == strike_prc)
        & (instruments_df["instrument_type"] == option_type)
    ]
    tokens = []
    trading_symbol_list = []

    tokens.append(int(nfo_ins_df['instrument_token'].values[0]))  # CE token

    trading_symbol_list.append(nfo_ins_df['tradingsymbol'].values[0])  # CE trading symbol

    # Extract the token from the trading symbol
    token_CE = nfo_ins_df['tradingsymbol'].values[0]

    print("Trading symbol: ",trading_symbol_list)
    exchange = 'NFO'

    trading_symbol_aliceblue = []
    for token, single_trading_symbol in zip(tokens, trading_symbol_list):
        trading_symbol_aliceblue.append(Instrument(exchange, token, base_symbol, single_trading_symbol, expiry_date, 50))

    return tokens, trading_symbol_list, trading_symbol_aliceblue