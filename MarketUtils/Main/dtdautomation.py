import pandas as pd
import os,sys
from dotenv import load_dotenv
from firebase_admin import db
from firebase_admin import credentials, storage
import firebase_admin

# Get the current working directory
DIR = os.getcwd()
sys.path.append(DIR)

from MarketUtils.Excel.strategy_calc import custom_format
import MarketUtils.Firebase.firebase_utils as firebase_utils

# Function to check if DataFrame has required columns
def has_required_columns(df):
    required_columns = ['exit_time', 'net_pnl', 'trade_id']
    return all(col in df.columns for col in required_columns)

# Function to fetch data from Excel and return a dictionary of DataFrames
def fetch_data_from_excel(file_name, sheet_mappings):
    data_mappings = {}
    for internal_name, actual_sheet_name in sheet_mappings.items():
        try:
            temp_df = pd.read_excel(file_name, sheet_name=actual_sheet_name)
            
            # Ensure 'exit_time' column exists in the dataframe
            if 'exit_time' in temp_df.columns:
                # Explicitly convert the 'exit_time' column to datetime to avoid FutureWarning
                temp_df['exit_time'] = pd.to_datetime(temp_df['exit_time'], errors='coerce')
                
                if has_required_columns(temp_df):
                    data_mappings[internal_name] = temp_df
                else:
                    print(
                        f"Sheet '{actual_sheet_name}' in {file_name} does not have all required columns. Skipping...")
            else:
                print(
                    f"Sheet '{actual_sheet_name}' in {file_name} does not contain an 'exit_time' column. Skipping...")
        except ValueError as e:
            print(
                f"Sheet '{actual_sheet_name}' not found in {file_name} or other ValueError: {e}. Skipping...")
    return data_mappings

# Function to create and return the DTD DataFrame with individual transactions and formatted columns
def create_dtd_dataframe_updated(data_mappings):
    if not data_mappings:
        print("No valid DataFrames found!")
        return pd.DataFrame()

    all_dates = pd.concat([df['exit_time'].dt.date for df in data_mappings.values() if 'exit_time' in df.columns]).unique()
    all_dates = [date for date in all_dates if pd.notna(date)]
    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)
    
    rows = []
    sl_no = 1

    for date in all_dates_sorted:
        date_str = date.strftime('%d-%b-%y')
        day_str = date.strftime('%A')
        for transaction_id, df in data_mappings.items():
            sub_df = df[df['exit_time'].dt.date == date]

            for _, row in sub_df.iterrows():
                trade_id = row['trade_id']
                amount = row['net_pnl']
                detail = transaction_id  # Default detail

                if pd.notna(amount) and amount != 0.00:
                    rows.append({
                        'Sl NO': sl_no,
                        'Date': date_str,
                        'Day': day_str,
                        'Trade ID': trade_id,
                        'Details': detail,
                        'Amount': custom_format(amount),
                    })
                    sl_no += 1

    return pd.DataFrame(rows)

# Function to append new data to the existing DTD sheet or create a new one
def check_and_update_dtd_sheet(file_name, new_dtd_df):
    if 'Details' not in new_dtd_df.columns:
        print(
            f"'Details' column missing in the new data for {file_name}. Skipping this file.")
        return

    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        if 'DTD' in writer.book.sheetnames:
            existing_dtd = pd.read_excel(file_name, sheet_name='DTD')
            if 'Date' in existing_dtd.columns and 'Date' in new_dtd_df.columns:
                last_existing_date = pd.to_datetime(
                    existing_dtd['Date'].iloc[-1])
                new_dtd_df = new_dtd_df[pd.to_datetime(
                    new_dtd_df['Date']) > last_existing_date]
                updated_dtd_df = pd.concat(
                    [existing_dtd, new_dtd_df], ignore_index=True)

                std = writer.book['DTD']
                writer.book.remove(std)
            else:
                print(
                    f"'Date' column not found in DTD sheet or new data of {file_name}. Skipping update for this file.")
                return
        else:
            updated_dtd_df = new_dtd_df

        updated_dtd_df.to_excel(writer, sheet_name='DTD', index=False)

# Main execution
def main():
    ENV_PATH = os.path.join(DIR, '.env')
    load_dotenv(ENV_PATH)

     # Retrieve values from .env
    firebase_credentials_path = os.getenv('firebase_credentials_path')
    database_url = os.getenv('database_url')
    storage_bucket = os.getenv('storage_bucket')

    # Initialize Firebase app
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url,
            'storageBucket': storage_bucket
        })
    
    excel_dir = r"C:\Users\vanis\OneDrive\Desktop\TradeMan\UserProfile\excel"
    # excel_dir = os.getenv('onedrive_excel_folder')
    
    sheet_mappings = {
        'MPWizard': 'MPWizard',
        'AmiPy': 'AmiPy',
        'ZRM': 'ZRM',
        'OvernightFutures': 'OvernightFutures',
        'ExpiryTrader': 'ExpiryTrader',
        'ErrorTrade': 'ErrorTrade',
        'ExtraTrades' : 'ExtraTrades',
    }

    for root, dirs, files in os.walk(excel_dir):
        for file in files:
            if file.endswith(".xlsx"):
                file_name = os.path.join(root, file)

                data_mappings = fetch_data_from_excel(file_name, sheet_mappings)
                dtd_df = create_dtd_dataframe_updated(data_mappings)

                check_and_update_dtd_sheet(file_name, dtd_df)
                firebase_utils.save_file_to_firebase(file_name, storage_bucket)

if __name__ == "__main__":
    main()
