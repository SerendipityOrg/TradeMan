import pandas as pd
import os,sys
from dotenv import load_dotenv
from firebase_admin import db
from firebase_admin import credentials, storage
import firebase_admin
from io import BytesIO

# Get the current working directory
DIR = os.getcwd()
sys.path.append(DIR)

from MarketUtils.Excel.strategy_calc import custom_format
import MarketUtils.Firebase.firebase_utils as firebase_utils
import MarketUtils.general_calc as general_calc

# Function to check if DataFrame has required columns
def has_required_columns(df):
    required_columns = ['exit_time', 'net_pnl', 'trade_id']
    return all(col in df.columns for col in required_columns)

# Hybrid function to load and process Excel file from Firebase
def load_excel(excel_file_name, sheet_mappings):
    # Connect to the Firebase bucket
    bucket = storage.bucket()
    blob = bucket.blob(excel_file_name)

    data_mappings = {}

    # Download the file if it exists in Firebase and return its content as a Pandas DataFrame
    if blob.exists():
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)

        # Load the Excel file into a Pandas DataFrame
        xls = pd.ExcelFile(byte_stream)

        # Process each specified sheet
        for internal_name, actual_sheet_name in sheet_mappings.items():
            try:
                temp_df = pd.read_excel(xls, sheet_name=actual_sheet_name)

                # Ensure 'exit_time' column exists in the dataframe
                if 'exit_time' in temp_df.columns:
                    # Explicitly convert the 'exit_time' column to datetime
                    temp_df['exit_time'] = pd.to_datetime(temp_df['exit_time'], errors='coerce')

                    if has_required_columns(temp_df):
                        data_mappings[internal_name] = temp_df
                    else:
                        print(f"Sheet '{actual_sheet_name}' in {excel_file_name} does not have all required columns. Skipping...")
                else:
                    print(f"Sheet '{actual_sheet_name}' in {excel_file_name} does not contain an 'exit_time' column. Skipping...")
            except ValueError as e:
                print(f"Sheet '{actual_sheet_name}' not found in {excel_file_name} or other ValueError: {e}. Skipping...")
    else:
        print(f"The file {excel_file_name} does not exist in Firebase Storage.")

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

# Function to check and update the DTD sheet from a file in Firebase
# Function to check and update the DTD sheet and save locally
def check_and_update_dtd_sheet(firebase_bucket_name, file_name, new_dtd_df, local_save_path):
    # Ensure 'Details' column is present
    if 'Details' not in new_dtd_df.columns:
        print(f"'Details' column missing in the new data for {file_name}. Skipping this file.")
        return None

    bucket = storage.bucket(firebase_bucket_name)
    blob = bucket.blob(file_name)

    # Check if the file exists in Firebase
    if blob.exists():
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)

        with pd.ExcelWriter(local_save_path, engine='openpyxl', mode='a') as writer:
            byte_stream.seek(0)
            if 'DTD' in writer.book.sheetnames:
                existing_dtd_df = pd.read_excel(byte_stream, sheet_name='DTD')

                # Process and update only new entries
                if 'Date' in existing_dtd_df.columns and 'Date' in new_dtd_df.columns:
                    last_existing_date = pd.to_datetime(existing_dtd_df['Date'].iloc[-1])
                    new_dtd_df = new_dtd_df[pd.to_datetime(new_dtd_df['Date']) > last_existing_date]
                    updated_dtd_df = pd.concat([existing_dtd_df, new_dtd_df], ignore_index=True)

                    std = writer.book['DTD']
                    writer.book.remove(std)
                else:
                    print(f"'Date' column not found in DTD sheet or new data of {file_name}. Skipping update for this file.")
                    return None
            else:
                updated_dtd_df = new_dtd_df

            # Save the updated DTD DataFrame locally
            updated_dtd_df.to_excel(writer, sheet_name='DTD', index=False)
        return local_save_path
    else:
        print(f"File {file_name} does not exist in {firebase_bucket_name}.")
        return None

# Main execution function
def main():
    # Get the current working directory and set environment
    DIR = os.getcwd()
    sys.path.append(DIR)
    load_dotenv(os.path.join(DIR, '.env'))
    
    # Retrieve Firebase configuration from .env file
    firebase_credentials_path = os.getenv('firebase_credentials_path')
    database_url = os.getenv('database_url')
    storage_bucket = os.getenv('storage_bucket')

    excel_dir = os.getenv('onedrive_excel_folder')

    # Initialize Firebase app if not done already
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url,
            'storageBucket': storage_bucket
        })

    broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
    broker_data = general_calc.read_json_file(broker_filepath)    
    
    sheet_mappings = {
        'MPWizard': 'MPWizard',
        'AmiPy': 'AmiPy',
        'ZRM': 'ZRM',
        'OvernightFutures': 'OvernightFutures',
        'ExpiryTrader': 'ExpiryTrader',
        'ErrorTrade': 'ErrorTrade',
        'ExtraTrades' : 'ExtraTrades',
    }

    # Iterate through each user in broker_data
    for user in broker_data:
        if "Active" in user['account_type']:
            excel_file_name = f"{user['account_name']}.xlsx"

            # Set the local save path to the user's account name
            # local_save_path = os.getenv(DIR, 'Userprofile', 'excel', f"{user['account_name']}.xlsx")
            print(excel_dir)
            local_save_path = os.path.join(excel_dir, f"{user['account_name']}.xlsx")

            data_mappings = load_excel(excel_file_name, sheet_mappings)
            
            if data_mappings:
                dtd_df = create_dtd_dataframe_updated(data_mappings)
                local_file_path = check_and_update_dtd_sheet(storage_bucket, excel_file_name, dtd_df, local_save_path)
                
                # If a local file was updated, upload it to Firebase
                if local_file_path:
                    firebase_utils.save_file_to_firebase(local_file_path, storage_bucket)
            else:
                print(f"Failed to load the file for {user['account_name']} or no data mappings were found.")

if __name__ == "__main__":
    main()