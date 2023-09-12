import pandas as pd
import logging
import numpy as np
from datetime import datetime
from kiteconnect import KiteConnect

# File Paths
# acctkn_file = r'C:/Users/user/Desktop/GroundUp_Trading/NiftyStrategy/Brokers/acc_token.txt'
acctkn_file = r'/Users/amolkittur/Documents/NiftyStrategy/Brokers/acc_token.txt'
# reqtkn_file = r'C:/Users/user/Desktop/GroundUp_Trading/NiftyStrategy/Brokers/req_token.txt'
reqtkn_file = r'/Users/amolkittur/Documents/NiftyStrategy/Brokers/req_token.txt'
# instruments_file = r'C:/Users/user/Desktop/GroundUp_Trading/NiftyStrategy/Brokers/instruments.csv'
instruments_file = r'/Users/amolkittur/Documents/NiftyStrategy/Brokers/instruments.csv'

expiry_date = '2023-05-25'
tokens = [256265]
trading_symbols = []
qty = 50
interval = 'minute'

def initialize_kite():
    # Read tokens from file and initialize KiteConnect
    kite_access_token = open(acctkn_file,'r').read()
    kite = KiteConnect(api_key='6b0dp5ussukmo67h', access_token=kite_access_token)
    return kite

def fetch_hist_data(kite, token, from_date, to_date, interval):
    # Fetch historical data using kiteconnect API
    nf_hist_data = kite.historical_data(token, from_date, to_date, interval)
    df = pd.DataFrame(nf_hist_data).set_index('date')
    return df

def get_tokens(strike_prc, trend):
    instruments_df = pd.read_csv(instruments_file)
    option_type = "PE" if trend == "Long" else "CE" if trend == "Short" else None
    nfo_ins_df = instruments_df[(instruments_df["exchange"] == "NFO") & (instruments_df["name"] == "NIFTY")
                                & (instruments_df["expiry"] == expiry_date) & (instruments_df["strike"] == strike_prc)
                                & (instruments_df["instrument_type"] == option_type)]
    digits = nfo_ins_df['tradingsymbol'].values[0][-7:-2]
    new_numeric_part = int(digits) + 500 if option_type == 'CE' else int(digits) - 500 if option_type == 'PE' else None
    hedge_symbol = nfo_ins_df['tradingsymbol'].values[0].replace(str(digits), str(new_numeric_part))
    return [nfo_ins_df['tradingsymbol'].values[0], hedge_symbol]

def place_order(kite, trading_symbol, trade_type):
    print("Placing Order")
    try:
        order_id = kite.place_order(variety=kite.VARIETY_REGULAR, exchange=kite.EXCHANGE_NFO, tradingsymbol=trading_symbol,
                                    transaction_type=trade_type, quantity=qty, product=kite.PRODUCT_NRML,
                                    order_type=kite.ORDER_TYPE_MARKET)
        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e))

# Main function
def main():
    kite = initialize_kite()
    today_date = datetime.today().date()
    nf_df = fetch_hist_data(kite, tokens[0], today_date, today_date, interval)
    spot_prc = nf_df['close'].iloc[-1]
    strike_prc = int(round(spot_prc/100,0)*100)
    previous_day_weighted_average = np.average(nf_df.between_time('14:30', '15:15')['close'],
                                                weights=range(1, len(nf_df.between_time('14:30', '15:15')) + 1))
    trend = 'Long' if nf_df.at_time('15:15')['close'].values[0] - previous_day_weighted_average > 0 else 'Short'
    symbols = get_tokens(strike_prc, trend)
    print(symbols)
    # Place orders
    trade_types = ['BUY', 'SELL'] if trend == 'Long' else ['SELL', 'BUY']
    for symbol, trade_type in zip(symbols, trade_types):
        place_order(kite, symbol, trade_type)


# Execute main function
if __name__ == '__main__':
    main()
