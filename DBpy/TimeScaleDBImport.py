import csv
import psycopg2
from psycopg2 import sql
import pandas as pd

from Brokers import apikey
from kiteconnect import KiteConnect
import pandas.io.sql as sqlio

acctkn_file = r'Brokers\acc_token.txt'
reqtkn_file = r'Brokers\req_token.txt'
kite_access_token = open(acctkn_file,'r').read()
kite_request_token = open(reqtkn_file,'r').read()

kite = KiteConnect(apikey.kite_api_key)
kite.set_access_token(kite_access_token)

expiry_date = '2023-05-18'
tokens = []
strike_prcs = [18300]
main_symbol= 'NIFTY'

from_date = '2023-05-03'
to_date = '2023-05-08'
interval = 'minute'

holidays = ['2023-05-01', '2023-06-16']  # Add all trading holidays here

# for given strike price and option type, get instrument token from instruments.csv
instruments_df = pd.read_csv(r'Brokers\instruments.csv')
instruments_df = instruments_df[
    ["instrument_token", "tradingsymbol", "name", "exchange", "lot_size","instrument_type","expiry","strike"]
]

# Generate the range of strike prices
strike_range = list(range(strike_prcs[0] - 500, strike_prcs[0] + 500 + 1, 50))

# Filter the instruments_df for the required conditions
filtered_instruments = instruments_df[
    (instruments_df["name"].str.contains(main_symbol)) &
    (instruments_df["expiry"] == expiry_date) &
    (instruments_df["strike"].isin(strike_range)) &
    (instruments_df["instrument_type"].isin(["CE", "PE"]))
]

# Extract the instrument tokens
#tokens = filtered_instruments["instrument_token"].tolist()####### change this to tokens
tokens = [11848450,11848706]

for strike_prc in strike_prcs:
    # from instruments dataframe, get all instruments for 'NFO' exchange, name =='NIFTY',expiry date is 4thMay2023, strike value between 17000 to 19000
    nfo_ins_df = instruments_df[
        (instruments_df["exchange"] == "NFO")
        & (instruments_df["name"] == main_symbol)
        & (instruments_df["expiry"] == expiry_date)
        & (instruments_df["strike"] == strike_prc)
    ]
    tokens.append(nfo_ins_df['instrument_token'].values[0])
    tokens.append(nfo_ins_df['instrument_token'].values[1]) 

# Remove the holidays from the resampled dataframe
def remove_holiday_data(df, holidays):
    # Convert the holidays list into a set for faster lookup
    holidays_set = set(pd.to_datetime(holiday).date() for holiday in holidays)

    # Create a boolean mask to identify rows with dates not in the holidays set
    mask = [date not in holidays_set for date in df.index.date]

    # Apply the mask to the DataFrame to remove rows with dates in the holidays set
    df = df[mask]

    return df

def save_ohlc_data_to_timescaleDB(connection, token, ohlc_data):
    table_name = 'ohlc_' + str(token)
    header = ["date", "open", "high", "low", "close", "instrument_token"]

    with connection.cursor() as cursor:
        # Create table
        column_definitions = [
            sql.Identifier(col_name.lower()) + sql.SQL(" " + data_type)
            for col_name, data_type in zip(
                header, ["TIMESTAMPTZ", "DOUBLE PRECISION", "DOUBLE PRECISION", "DOUBLE PRECISION", "DOUBLE PRECISION", "DOUBLE PRECISION"]
            )
        ]
        create_table_query = (
            sql.SQL("CREATE TABLE {} (")
            .format(sql.Identifier(table_name))
            + sql.SQL(", ").join(column_definitions)
            + sql.SQL(", PRIMARY KEY (date));")
        )
        cursor.execute(create_table_query)

        # Insert data
        insert_query = sql.SQL("INSERT INTO {} VALUES (%s, %s, %s, %s, %s, %s);").format(sql.Identifier(table_name))
        for index, row in ohlc_data.iterrows():
            cursor.execute(insert_query, (index, float(row['open']), float(row['high']), float(row['low']), float(row['close']), int(row['instrument_token'])))

    connection.commit()

def read_data_from_timescaleDB(connection, token):
    table_name = 'ohlc_' + str(token)

    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'Asia/Kolkata';")
        query = f"SELECT * FROM {table_name};"
        ohlc_df = sqlio.read_sql_query(query, connection)
        
        #print the length of ohlc_df
        
        print("token:" + str(token))
        print("ohlc_df_length for token:" + str(len(ohlc_df)))

    return ohlc_df


def main():
    connection = psycopg2.connect(
        dbname="ohlc_token",
        user=apikey.postgres_username,
        password=apikey.postgres_pass,
        host="localhost",
        port="5432"
    )
    
    ohlc_data = {}
    
    tokens = [11848450,11848706]

    for token in tokens:
        ohlc_list = kite.historical_data(token, from_date, to_date, interval)
        ohlc_df = pd.DataFrame(ohlc_list)

        if 'date' not in ohlc_df.columns:
            print(f"Error: 'date' column not found for token {token}. Skipping...")
            continue

        ohlc_df = ohlc_df.set_index('date')
        ohlc_df['instrument_token'] = token

        save_ohlc_data_to_timescaleDB(connection, token, ohlc_df)
        # read_data_from_timescaleDB(connection, token)
        
    connection.close()

if __name__ == "__main__":
    main()

