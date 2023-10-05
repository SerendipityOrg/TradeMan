import pandas as pd
import psycopg2
from psycopg2 import sql
import os

def get_dbname_from_ticker(ticker):
    if ticker.startswith('BANKNIFTY'):
        return 'gfdlbnf'
    elif ticker.startswith('FINNIFTY'):
        return 'gfdlfnf'
    elif ticker.startswith('NIFTY'):
        return 'gfdlnf'
    else:
        return 'gfdl'
    
def connect_to_db(base_symbol):
    return psycopg2.connect(
        dbname=base_symbol.lower(),
        user="postgres",
        password="K@nnada0",
        host="localhost",
        port="5432"
    )

def create_and_insert_data(data, file_name):
    table_names = data['Ticker'].str.replace('.NFO', '').unique()

    for table in table_names:
        base_symbol = get_dbname_from_ticker(table)
        
        # If the ticker doesn't match any of the provided prefixes, skip it
        if not base_symbol:
            continue

        # Connect to the appropriate database based on the ticker
        conn = connect_to_db(base_symbol)
        cursor = conn.cursor()


        # Filter data for the current ticker
        sub_data = data[data['Ticker'] == table + '.NFO']

        # Create table if not exists
        create_table_query = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            Ticker TEXT,
            Open FLOAT,
            High FLOAT,
            Low FLOAT,
            Close FLOAT,
            Volume INT,
            Open_Interest INT,
            date TIMESTAMP
        );
        """).format(sql.Identifier(table))
        
        cursor.execute(create_table_query)

        # Insert data into the table
        for _, row in sub_data.iterrows():
            insert_data_query = sql.SQL("""
            INSERT INTO {} (Ticker, Open, High, Low, Close, Volume, Open_Interest, date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """).format(sql.Identifier(table))
            
            cursor.execute(insert_data_query, (row['Ticker'], row['Open'], row['High'], 
                                               row['Low'], row['Close'], row['Volume'], 
                                               row['Open Interest'], row['date']))
        
        # Commit changes
        conn.commit()


    # Close the connection
    cursor.close()
    conn.close()

    # Delete the CSV file after processing
    os.remove(file_name)
    # Log the processed file
    with open("processed_files.txt", "a") as f:
        f.write(file_name + "\n")

    print(f"File {file_name} processed and deleted.")

def main():
    # Check for processed files
    if os.path.exists("processed_files.txt"):
        with open("processed_files.txt", "r") as f:
            processed_files = f.readlines()
    else:
        processed_files = []

    # Folder path (adjust as needed)
    folder_path = r'C:\Users\user\Downloads\NSE Data\Omkar Hegde_NFO'

    # Loop through all CSV files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv") and file_name not in processed_files:
            print(f"Starting processing for file {file_name}...")
            full_path = os.path.join(folder_path, file_name)
            data = pd.read_csv(full_path)
            data['date'] = pd.to_datetime(data['Date'] + ' ' + data['Time'], format='%d/%m/%Y %H:%M:%S')
            data = data.drop(columns=['Date', 'Time'])
            create_and_insert_data(data, full_path)

if __name__ == "__main__":
    main()