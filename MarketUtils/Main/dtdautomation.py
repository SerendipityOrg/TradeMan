import pandas as pd
import os,sys
from dotenv import load_dotenv


# Get the current working directory
DIR = os.getcwd()
sys.path.append(DIR)

from MarketUtils.Excel.strategy_calc import custom_format

# Function to check if DataFrame has required columns
def has_required_columns(df):
    required_columns = ['entry_time', 'net_pnl', 'trade_id']
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
def create_dtd_dataframe_updated(data_mappings, opening_balance, start_date):
    if not data_mappings:
        print("No valid DataFrames found!")
        return pd.DataFrame(), 0

    # Convert start_date to pandas Timestamp for comparison
    start_date = pd.to_datetime(start_date)

    # Extract all unique dates from the data mappings
    all_dates = pd.concat([df['exit_time'].dt.date for key, df in data_mappings.items()]).unique()

    # Filter out any NaT values (Not a Time) from the all_dates list to prevent errors during processing
    all_dates = [date for date in all_dates if pd.notna(date)]
    
    # Sort the dates
    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)
    rows = []
    default_details = ['MPWizard', 'AmiPy', 'ZRM', 'OvernightFutures', 'ExtraTrades',
                       'ExpiryTrader', 'ErrorTrade', 'ErrorTrades','Transactions']
    sl_no = 1

    # Initialize the running balance with the opening balance
    running_balance = opening_balance

    # Add the Opening Balance row with the correct start date
    rows.append({
        'Sl NO': sl_no,
        'Date': start_date.strftime('%d-%b-%y'),
        'Day': start_date.strftime('%A'),
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': custom_format(running_balance),
        'Running Balance': custom_format(running_balance)
    })
    sl_no += 1

    for date in all_dates_sorted:
        if pd.Timestamp(date) < start_date:
            continue  # Skip dates before the start date
        date_str = date.strftime('%d-%b-%y')
        day_str = date.strftime('%A')
        for transaction_id in default_details:
            if transaction_id in data_mappings:
                df = data_mappings[transaction_id]
                time_col = 'exit_time'
                sub_df = df[df[time_col].dt.date == date]

                for _, row in sub_df.iterrows():
                    trade_id = row['trade_id']
                    amount = row['net_pnl']
                    detail = transaction_id  # Default detail

                    # If the transaction_id is 'Transactions', use the 'transaction_type' for details
                    if transaction_id == 'Transactions' and 'transaction_type' in row:
                        detail = row['transaction_type']

                    # Check if amount is not NaN and not 0.00
                    if pd.notna(amount) and amount != 0.00:
                        running_balance += amount
                        rows.append({
                            'Sl NO': sl_no,
                            'Date': date_str,
                            'Day': day_str,
                            'Trade ID': trade_id,
                            'Details': detail,
                            'Amount': custom_format(amount),
                            'Running Balance': custom_format(running_balance)
                        })
                        sl_no += 1

    dtd_df = pd.DataFrame(rows)
    return dtd_df, running_balance

# Function to retrieve existing 'Opening Balance' from the DTD sheet
def get_existing_opening_balance(file_name):
    if 'DTD' in pd.ExcelFile(file_name).sheet_names:
        existing_dtd = pd.read_excel(file_name, sheet_name='DTD')
        details_column = existing_dtd.get('Details')
        if details_column is not None and 'Opening Balance' in details_column.values:
            running_balance_str = existing_dtd[details_column ==
                                               'Opening Balance']['Running Balance'].iloc[0]
            if isinstance(running_balance_str, (str, int, float)):
                return float(str(running_balance_str).replace('₹', '').replace(',', '').strip())
    return None

# Function to append new data to the existing DTD sheet or create a new one


def check_and_update_dtd_sheet(file_name, new_dtd_df):
    if 'Details' not in new_dtd_df.columns:
        print(
            f"'Details' column missing in the new data for {file_name}. Skipping this file.")
        return

    existing_opening_balance = get_existing_opening_balance(file_name)

    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        if existing_opening_balance is not None:
            new_dtd_df.loc[new_dtd_df['Details'] == 'Opening Balance',
                           'Running Balance'] = custom_format(existing_opening_balance)

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


def read_opening_balances(file_path):
    opening_balances = {}
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split('date:')
                if len(parts) == 2:
                    user_balance_part = parts[0].strip()
                    user_parts = user_balance_part.split(':')
                    date_str = parts[1].strip()
                    if len(user_parts) == 2:
                        user = user_parts[0].strip()
                        balance_str = user_parts[1].strip().replace('₹', '').replace(',', '').strip()
                        opening_balances[user] = {
                            'balance': float(balance_str),
                            'date': pd.to_datetime(date_str, format='%d-%b-%y')  # Assuming the date is in '04-Nov-23' format
                        }
    except FileNotFoundError:
        print("useropeningbalance.txt not found.")
    return opening_balances


# Main execution
def main():
    ENV_PATH = os.path.join(DIR, '.env')
    load_dotenv(ENV_PATH)
    
    # excel_dir = r"C:\Users\vanis\OneDrive\Desktop\TradeMan\UserProfile\excel"
    excel_dir = os.getenv('onedrive_excel_folder')
    opening_balances = read_opening_balances(os.path.join(DIR, 'MarketUtils', 'Main', 'useropeningbalance.txt'))

    sheet_mappings = {
        'MPWizard': 'MPWizard',
        'AmiPy': 'AmiPy',
        'ZRM': 'ZRM',
        'OvernightFutures': 'OvernightFutures',
        'ExpiryTrader': 'ExpiryTrader',
        'ErrorTrade': 'ErrorTrade',
        'ExtraTrades' : 'ExtraTrades',
        'Transactions': 'Transactions'
    }

    for root, dirs, files in os.walk(excel_dir):
        for file in files:
            if file.endswith(".xlsx"):
                file_name = os.path.join(root, file)
                user_name = os.path.splitext(file)[0]

                # Retrieve user data from opening_balances dictionary
                # This contains both the balance and the start date
                user_data = opening_balances.get(user_name, {'balance': 0.0, 'date': pd.Timestamp.now()})
                opening_balance = user_data['balance']
                opening_date = user_data['date']

                # Fetch data from Excel
                data_mappings = fetch_data_from_excel(file_name, sheet_mappings)

                # Now pass the 'opening_date' to 'create_dtd_dataframe_updated' function
                dtd_df, _ = create_dtd_dataframe_updated(
                    data_mappings, opening_balance, opening_date)

                # Check and update the DTD sheet with the new DataFrame
                check_and_update_dtd_sheet(file_name, dtd_df)

if __name__ == "__main__":
    main()
