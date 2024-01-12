import os,sys
import pandas as pd
import strategy_calc as sc
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

DIR = os.getcwd()
sys.path.append(DIR)

import MarketUtils.general_calc as general_calc
import DBpy.DB_utils as db_utils

ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')
excel_dir = os.getenv('onedrive_excel_folder')

broker_filepath = os.path.join(DIR,"MarketUtils", "broker.json")
userprofile_dir = os.path.join(DIR, "UserProfile","OrdersJson")
active_users_filepath = os.path.join(DIR,"MarketUtils", "active_users.json")
credentials_filepath = os.path.join(DIR,"MarketUtils","Excel","credentials.json")


class TradingStrategy:
    def __init__(self, name, process_func):
        self.name = name
        self.process_func = process_func
    
    def process_data(self, user_data, broker,username):
        if self.name in user_data["today_orders"]:
            data = self.process_func(broker, user_data["today_orders"][self.name],username)
            df = pd.DataFrame(data)
            if 'pnl' in df.columns:
                PnL = round(df['pnl'].sum(), 1)
                Tax = round(df['tax'].sum(), 1)
            else:
                print("PnL column not found in DataFrame")
                PnL = 0
                Tax = 0
            return df, PnL, Tax
        return pd.DataFrame(), 0, 0

def append_to_db_table(conn, df, table_name):
    """Append data from DataFrame to the specified table in the database."""
    if not df.empty:
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        except Exception as e:
            print(f"An error occurred while appending to the table {table_name}: {e}")

def format_decimal_values(df, decimal_columns):
    """Format specified columns of a DataFrame to show two decimal places."""
    for col in decimal_columns:
        if col in df.columns:
            # Convert to float and format as a string with two decimal places
            df[col] = df[col].apply(lambda x: "{:.2f}".format(float(x)))

    return df

def save_to_db(conn, df, table_name, decimal_columns):
    """Format values to show two decimals and append data from DataFrame to the specified table in the database."""
    if not df.empty:
        formatted_df = format_decimal_values(df, decimal_columns)
        # Cast decimal columns to text
        for col in decimal_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].astype(str)
        try:
            formatted_df.to_sql(table_name, conn, if_exists='append', index=False)
        except Exception as e:
            print(f"An error occurred while appending to the table {table_name}: {e}")

# Define a dictionary that maps strategy names to their processing functions
strategy_config = {
    "MPWizard": sc.process_mpwizard_trades,
    "AmiPy": sc.process_amipy_trades,
    "OvernightFutures": sc.process_overnight_futures_trades,
    "ExpiryTrader": sc.process_expiry_trades,
    "Extra": sc.process_extra_trades
    # Add new strategies here as needed
}

cred = credentials.Certificate(credentials_filepath)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trading-app-caf8e-default-rtdb.firebaseio.com'
})

def save_to_firebase(user, excel_path):
    # Correct bucket name
    bucket = storage.bucket(name='trading-app-caf8e.appspot.com')
    blob = bucket.blob(f'{user}.xlsx')
    with open(excel_path, 'rb') as my_file:
        blob.upload_from_file(my_file)
    print(f"Excel file for {user} has been uploaded to Firebase.")

def main():
    data = general_calc.read_json_file(active_users_filepath)
    
    # Initialize TradingStrategy objects based on the configuration
    strategies = [TradingStrategy(name, func) for name, func in strategy_config.items()]

    for user in data:
        username = user['account_name']
        user_data = general_calc.read_json_file(os.path.join(userprofile_dir, f"{user['account_name']}.json"))
        broker = user["broker"]

        strategy_results = {}
        gross_pnl = 0
        total_tax = 0
        
        db_path = os.path.join(excel_dir, f"{username}.db")  # Assuming the DB file name is the same as the Excel file name
        conn = db_utils.get_db_connection(db_path)

        for strategy in strategies:
            df, pnl, tax = strategy.process_data(user_data, broker,username)
            strategy_results[strategy.name] = pnl
            gross_pnl += pnl
            total_tax += tax
            decimal_columns = ['pnl', 'tax', 'entry_price', 'exit_price', 'hedge_entry_price', 'hedge_exit_price', 'trade_points', 'net_pnl']
            save_to_db(conn, df, strategy.name, decimal_columns)

        print(f"Strategy results for {username}: {strategy_results}")

        # save_to_firebase(username,excel_path)
        conn.close()
if __name__ == "__main__":
    main()
