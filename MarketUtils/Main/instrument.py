import os
import pandas as pd 

class Instrument:
    def __init__(self, instrument_token, exchange_token, tradingsymbol, name, last_price,
                 expiry, strike, tick_size, lot_size, instrument_type, segment, exchange):
        self._instrument_token = instrument_token
        self._exchange_token = exchange_token
        self._tradingsymbol = tradingsymbol
        self._name = name
        self._last_price = last_price
        self._expiry = expiry
        self._strike = strike
        self._tick_size = tick_size
        self._lot_size = lot_size
        self._instrument_type = instrument_type
        self._segment = segment
        self._exchange = exchange

    # Getter methods
    def get_instrument_token(self):
        return self._instrument_token

    def get_exchange_token(self):
        return self._exchange_token

    def get_tradingsymbol(self):
        return self._tradingsymbol

    def get_name(self):
        return self._name

    def get_last_price(self):
        return self._last_price

    def get_expiry(self):
        return self._expiry

    def get_strike(self):
        return self._strike

    def get_tick_size(self):
        return self._tick_size

    def get_lot_size(self):
        return self._lot_size

    def get_instrument_type(self):
        return self._instrument_type

    def get_segment(self):
        return self._segment

    def get_exchange(self):
        return self._exchange
    
    def get_tokens(base_symbol, expiry_date, option_type, strike_prc=0):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Reading instruments.csv
        instruments_df = pd.read_csv(os.path.join(script_dir, 'instruments.csv'))
        instruments_df = instruments_df[
            ["instrument_token","exchange_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike", "segment"]
        ]

        # Check for option_type
        if option_type != 'CE' and option_type != 'PE':
            option_type = 'FUT'
            segment = 'NFO-FUT'
        else:
            segment = 'NFO-OPT'

        # Filter using instruments.csv
        nfo_ins_df = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == str(base_symbol))
            & (instruments_df["expiry"] == str(expiry_date))
            & (instruments_df["strike"] == int(strike_prc))
            & (instruments_df["instrument_type"] == str(option_type))
            & (instruments_df["segment"] == segment)
        ]

        tokens = int(nfo_ins_df["instrument_token"].values[0])
        exchange_token = int(nfo_ins_df["exchange_token"].values[0])
        trading_symbols = nfo_ins_df["tradingsymbol"].values[0]

    def get_kite_tokens(base_symbol, expiry_date, option_type, strike_prc=0):
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Reading instruments.csv
        instruments_df = pd.read_csv(os.path.join(script_dir, 'instruments.csv'))
        instruments_df = instruments_df[
            ["instrument_token","exchange_token", "tradingsymbol", "name", "exchange", "lot_size", "instrument_type", "expiry", "strike", "segment"]
        ]

        # Check for option_type
        if option_type != 'CE' and option_type != 'PE':
            option_type = 'FUT'
            segment = 'NFO-FUT'
        else:
            segment = 'NFO-OPT'

        # Filter using instruments.csv
        nfo_ins_df = instruments_df[
            (instruments_df["exchange"] == "NFO")
            & (instruments_df["name"] == str(base_symbol))
            & (instruments_df["expiry"] == str(expiry_date))
            & (instruments_df["strike"] == int(strike_prc))
            & (instruments_df["instrument_type"] == str(option_type))
            & (instruments_df["segment"] == segment)
        ]

        tokens = int(nfo_ins_df["instrument_token"].values[0])
        exchange_token = int(nfo_ins_df["exchange_token"].values[0])
        trading_symbols_kite = nfo_ins_df["tradingsymbol"].values[0]
        return trading_symbols_kite
    
    def get_aliceblue_tokens(base_symbol, expiry_date, option_type, strike_prc=0):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Reading NFO.csv
        nfo_df = pd.read_csv(os.path.join(script_dir, 'NFO.csv'))
        if option_type == 'FUT':
            option_type = 'XX'
        if strike_prc == 0:
            strike_prc = -1
            
        # Filtering using NFO.csv
        nfo_trading_symbols_df = nfo_df[
            (nfo_df["Exch"] == "NFO")
            & (nfo_df["Symbol"] == str(base_symbol))
            & (nfo_df["Expiry Date"] == str(expiry_date))
            & (nfo_df["Strike Price"] == int(strike_prc))
            & (nfo_df["Option Type"] == str(option_type))
        ]
        exchange_token = int(nfo_trading_symbols_df["exchange_token"].values[0])
        lot_size = int(nfo_trading_symbols_df["Lot Size"].values[0])
        trading_symbols_aliceblue = nfo_trading_symbols_df["Trading Symbol"].values[0]
        
        # Assuming Instrument is a class or function. If it's different, modify accordingly.
        trading_symbols_aliceblue = Instrument("NFO", exchange_token, base_symbol, trading_symbols_aliceblue, expiry_date, lot_size)

        return trading_symbols_aliceblue


