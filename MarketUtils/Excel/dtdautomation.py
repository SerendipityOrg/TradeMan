import pandas as pd
import os
from babel.numbers import format_currency

# Function to format the 'Running Balance' column


def format_running_balance_column(df):
    df['Running Balance'] = df['Running Balance'].apply(custom_format)
    return df

# Function to check if DataFrame has required columns


def has_required_columns(df):
    required_columns = ['Date', 'Net PnL', 'Trade ID']
    return all(col in df.columns for col in required_columns)

# Function to fetch data from Excel and return a dictionary of DataFrames


def fetch_data_from_excel(file_name, sheet_mappings):
    data_mappings = {}
    for internal_name, actual_sheet_name in sheet_mappings.items():
        try:
            temp_df = pd.read_excel(
                file_name, sheet_name=actual_sheet_name, parse_dates=['Date'])
            if has_required_columns(temp_df):
                data_mappings[internal_name] = temp_df
            else:
                print(
                    f"Sheet '{actual_sheet_name}' in {file_name} does not have all required columns. Skipping...")
        except ValueError:
            print(
                f"Sheet '{actual_sheet_name}' not found in {file_name}. Skipping...")
    return data_mappings

# Custom format function for currency


def custom_format(amount):
    if isinstance(amount, (int, float)):
        formatted = format_currency(amount, 'INR', locale='en_IN')
        return formatted.replace('₹', '₹ ')
    elif isinstance(amount, str):
        # Handle the case where 'amount' is already a formatted string
        return amount
    else:
        # Return the value as is (not formatted)
        return amount

# Function to create and return the DTD DataFrame with individual transactions and formatted columns


def create_dtd_dataframe_updated_v10(data_mappings, opening_balance):
    if not data_mappings:
        print("No valid DataFrames found!")
        return pd.DataFrame(), 0

    all_dates = pd.concat([df['Date']
                           for df in data_mappings.values()]).unique()
    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)

    rows = []
    default_details = ['MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options']
    sl_no = 1

    # Initialize the running balance with the opening balance
    running_balance = opening_balance

    # Add the Opening Balance row
    rows.append({
        'Sl NO': sl_no,
        'Date': '01-Jul-23',
        'Day': 'Saturday',
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': custom_format(running_balance),
        'Running Balance': custom_format(running_balance)
    })
    sl_no += 1

    start_date = pd.Timestamp('2023-07-1')
    for date in all_dates_sorted:
        if date < start_date:
            continue
        date_ts = pd.Timestamp(date)  # Convert to pandas.Timestamp
        date = date_ts.to_pydatetime()
        date_str = date.strftime('%d-%b-%y')
        day_str = date.strftime('%A')

        for transaction_id in default_details:
            if transaction_id in data_mappings:
                df = data_mappings[transaction_id]
                sub_df = df[df['Date'] == date]

                for _, row in sub_df.iterrows():
                    trade_id = row['Trade ID']
                    amount = row['Net PnL']
                    if amount != 0.00:
                        running_balance += amount
                        rows.append({
                            'Sl NO': sl_no,
                            'Date': date_str,
                            'Day': day_str,
                            'Trade ID': trade_id,
                            'Details': transaction_id,
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
            existing_dtd = format_running_balance_column(existing_dtd)
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

# Function to read opening balances from useropeningbalance.txt and return as a dictionary


def read_opening_balances(file_path):
    opening_balances = {}
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    user = parts[0].strip()
                    balance_str = parts[1].strip().replace(
                        '₹', '').replace(',', '').strip()
                    opening_balances[user] = float(balance_str)
    except FileNotFoundError:
        print("useropeningbalance.txt not found.")
    return opening_balances


# Main execution
# if __name__ == "__main__":
#     user_profile = os.path.join(script_dir, '..', 'UserProfile')
#     excel_dir = os.path.join(user_profile, 'excel')
#     opening_balances = read_opening_balances(
#         os.path.join(script_dir, 'useropeningbalance.txt'))

#     
def update_dtd_sheets():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    user_profile = os.path.join(script_dir, '..','..', 'UserProfile')
    excel_dir = os.path.join(user_profile, 'excel')
    opening_balances = read_opening_balances(
        os.path.join(script_dir, 'useropeningbalance.txt'))

    sheet_mappings = {
        'MP Wizard': 'MPWizard',
        'AmiPy': 'AmiPy',
        'ZRM': 'ZRM',
        'Overnight Options': 'Overnight_options'
    }

    for root, dirs, files in os.walk(excel_dir):
        for file in files:
            if file.endswith(".xlsx"):
                file_name = os.path.join(root, file)
                user_name = os.path.splitext(file)[0]
                opening_balance = opening_balances.get(user_name, 0.0)
                data_mappings = fetch_data_from_excel(
                    file_name, sheet_mappings)
                dtd_df, _ = create_dtd_dataframe_updated_v10(
                    data_mappings, opening_balance)
                check_and_update_dtd_sheet(file_name, dtd_df)
