from firebase_admin import db
from firebase_admin import credentials, storage
import firebase_admin
import os, sys
from io import BytesIO
from dotenv import load_dotenv
import datetime
import pandas as pd

# Get the current working directory
DIR = os.getcwd()
active_users_json_path = os.path.join(DIR,"MarketUtils", "active_users.json")
broker_filepath = os.path.join(DIR,"MarketUtils", "broker.json")
env_path = os.path.join(DIR, '.env')

load_dotenv(env_path)
sys.path.append(DIR)
import MarketUtils.general_calc as general_calc

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

    
# Function to get the current week's start and end dates
def get_current_week():
    current_date = datetime.date.today()
    start_week = current_date - datetime.timedelta(current_date.weekday())
    end_week = start_week + datetime.timedelta(6)
    return start_week, end_week

# Function to load an existing Excel file from Firebase Storage
def load_excel_from_firebase(excel_file_name):
    # Connect to the Firebase bucket
    bucket = storage.bucket(storage_bucket)
    blob = bucket.blob(excel_file_name)

    # Check if the file exists in Firebase and download it
    if blob.exists():
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)

        try:
            # Read the 'DTD' and 'Holdings' sheets using pandas
            df_dtd = pd.read_excel(byte_stream, sheet_name='DTD', parse_dates=['Date'], date_parser=lambda x: pd.to_datetime(x, format='%d-%b-%y'))
            df_holdings = pd.read_excel(byte_stream, sheet_name='Holdings')
            return df_dtd, df_holdings
        except ValueError as e:
            print(f"Error reading sheets: {e}")
            return None, None
    else:
        print(f"File {excel_file_name} does not exist in Firebase.")
        return None, None

# Function to process data within the current week
def process_DTD(excel_file_name):
        # Load the Excel file within the function
    df_dtd, _ = load_excel_from_firebase(excel_file_name)  # Only load the 'DTD' sheet

    result_list = []  # Initialize an empty list to store the results

    if df_dtd is not None:
        # Ensure 'Amount' column is numeric
        df_dtd['Amount'] = pd.to_numeric(df_dtd['Amount'].replace('[₹,]', '', regex=True).replace('-', '-0'), errors='coerce').fillna(0)

        # Filter data for the current week
        start_week, end_week = get_current_week()
        current_week_df = df_dtd[(df_dtd['Date'].dt.date >= start_week) & (df_dtd['Date'].dt.date <= end_week)]
        
        # Summarize data by 'Details'
        details_summary = current_week_df.groupby('Details')['Amount'].sum()

        # Collect the results in the list
        for detail, total_amount in details_summary.items():
            result_list.append(f"{detail}: ₹{total_amount:,.2f}")

    return result_list  # Return the list of results

# Main function to execute the script for generating weekly reports
def main():
    # Read broker data from JSON file
    broker_data = general_calc.read_json_file(broker_filepath)

    # Process Excel files for each active user
    for user in broker_data:
        if "Active" in user['account_type']:
            excel_file_name = f"{user['account_name']}.xlsx"
            results = process_DTD(excel_file_name)
            # # Print the account name and the results from process_DTD
            # print(user['account_name'])
            # for result in results:
            #     print(result)

if __name__ == "__main__":
    main()


# Function to save file to Firebase Storage
def save_file_to_firebase(excel_file_name, firebase_bucket_name):
    bucket = storage.bucket(firebase_bucket_name)

    # Create a blob for uploading the file
    blob = bucket.blob(os.path.basename(excel_file_name))
    # Upload the file
    blob.upload_from_filename(excel_file_name)
    print(f"File {excel_file_name} uploaded to {firebase_bucket_name}.")

# Function to load an existing Excel file from Firebase Storage
def load_excel(excel_file_name):
    # Connect to the Firebase bucket
    bucket = storage.bucket(storage_bucket)
    blob = bucket.blob(excel_file_name)

    # Download the file if it exists in Firebase and return its content as a Pandas DataFrame
    if blob.exists():
        byte_stream = BytesIO()
        blob.download_to_file(byte_stream)
        byte_stream.seek(0)
        # Load the Excel file into a Pandas DataFrame
        xls = pd.ExcelFile(byte_stream)
        # Return the ExcelFile object and the sheet names
        return xls, xls.sheet_names
    else:
        print(f"The file {excel_file_name} does not exist in Firebase Storage.")
        return None, None