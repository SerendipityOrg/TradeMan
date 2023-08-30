import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from Brokers import apikey

# Connect to your postgres DB
conn = psycopg2.connect(
        dbname="GFDL_Daily",
        user=apikey.postgres_username,
        password=apikey.postgres_pass,
        host="localhost",
        port="5432"
    )
cur = conn.cursor()

# Directory where your CSV files are located
csv_directory = r"C:\Users\user\Downloads\Omkar Hegde_NFO"

# Get the list of csv files
csv_files = [os.path.join(csv_directory, f) for f in os.listdir(csv_directory) if f.endswith('.csv')]

# Get the list of csv files
csv_files = [os.path.join(csv_directory, f) for f in os.listdir(csv_directory) if f.endswith('.csv')]

# Loop through the list
for csv_file in csv_files:
    print(f"Processing file: {csv_file}")

    # Load the CSV data into a pandas DataFrame
    df = pd.read_csv(csv_file)
    
    # Extract unique ticker names
    unique_tickers = df['Ticker'].unique()
    
    # Iterate over unique tickers
    for ticker in unique_tickers:
        print(f"Processing ticker: {ticker}")

        # Filter rows for the current ticker
        ticker_data = df[df['Ticker'] == ticker]
        
        # Extract date from the first row of the ticker data and format it
        date = pd.to_datetime(ticker_data.iloc[0]['Date'], format='%d/%m/%Y').strftime('%d%b%y')
        
        # Format table name
        table_name = ticker.replace('.NFO', '_' + date)
        
        # Create table if it doesn't exist
        create_table_query = sql.SQL("""CREATE TABLE IF NOT EXISTS {} (
                                            Date DATE,
                                            Time TIME,
                                            Open FLOAT,
                                            High FLOAT,
                                            Low FLOAT,
                                            Close FLOAT,
                                            Volume INT,
                                            OpenInterest INT
                                        )""").format(sql.Identifier(table_name))

        cur.execute(create_table_query)
        
        conn.commit()

        # Insert data into the table
        for index, row in ticker_data.iterrows():
            insert_data_query = sql.SQL("""INSERT INTO {} (Date, Time, Open, High, Low, Close, Volume, OpenInterest) VALUES 
                                        (%s, %s, %s, %s, %s, %s, %s, %s)"""
                                        ).format(sql.Identifier(table_name))

            data_to_insert = (row['Date'], row['Time'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume'], row['Open Interest'])
            cur.execute(insert_data_query, data_to_insert)
            conn.commit()

        print(f"Data inserted for ticker: {ticker}")

cur.close()
conn.close()
