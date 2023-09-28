import pandas as pd
import os
from datetime import datetime


def has_required_columns(df):
    """Check if the DataFrame contains the required columns."""
    required_columns = ['Date', 'Net PnL']
    return all(col in df.columns for col in required_columns)


def fetch_data_from_excel(file_name, sheet_mappings):
    """Fetch data from Excel and return a dictionary of DataFrames."""
    data_mappings = {}
    for internal_name, actual_sheet_name in sheet_mappings.items():
        try:
            temp_df = pd.read_excel(file_name, sheet_name=actual_sheet_name)
            if has_required_columns(temp_df):
                data_mappings[internal_name] = temp_df
            else:
                print(
                    f"Sheet '{actual_sheet_name}' in {file_name} does not have all required columns. Skipping...")
        except ValueError:
            print(
                f"Sheet '{actual_sheet_name}' not found in {file_name}. Skipping...")
    return data_mappings


def create_dtd_dataframe(data_mappings):
    """Creates and returns the DTD DataFrame."""

    if not data_mappings:
        print("No valid DataFrames found!")
        return pd.DataFrame()

    all_dates = pd.concat([df['Date']
                          for df in data_mappings.values()]).unique()

    # Filter out dates before 10 July 2023
    start_date = datetime.strptime("10-07-2023", "%d-%m-%Y")
    all_dates = [date for date in all_dates if date >= start_date]

    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)

    rows = []
    default_details = ['MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options',
                       'Error Trade', 'Deposit', 'Withdrawal', 'Comission']
    si_no = 1

    rows.append({
        'SI NO': '',
        'Date': '',
        'Day': '',
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': '',
        'Running Balance': ''
    })

    for date in all_dates_sorted:
        for transaction_id in default_details:
            amount_str = ''
            if transaction_id in data_mappings:
                df = data_mappings[transaction_id]
                amount = df[df['Date'] == date]['Net PnL'].sum()
                amount_str = f'₹ {amount:,.2f}' if amount != 0 else ''
            if amount_str or transaction_id == 'Opening Balance':
                rows.append({
                    'SI NO': si_no,
                    'Date': date.strftime('%d-%b-%y'),
                    'Day': date.strftime('%A'),
                    'Trade ID': '',
                    'Details': transaction_id,
                    'Amount': amount_str
                })
                si_no += 1

    dtd_df = pd.DataFrame(rows)
    return dtd_df


def check_and_update_dtd_sheet(file_name, new_dtd_df):
    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        book = writer.book
        if 'DTD' in book.sheetnames:
            existing_dtd_df = pd.read_excel(file_name, sheet_name='DTD')

            # Check if 'Date' column exists in both new and existing DataFrames
            if 'Date' not in new_dtd_df.columns or 'Date' not in existing_dtd_df.columns:
                print(
                    f"DTD sheet in {file_name} is missing the 'Date' column or has unexpected structure.")
                return

            if not set(new_dtd_df['Date']).issubset(set(existing_dtd_df['Date'])):
                updated_dtd_df = pd.concat(
                    [existing_dtd_df, new_dtd_df], ignore_index=True)

                # Remove the existing 'DTD' sheet
                std = book['DTD']
                book.remove(std)

                updated_dtd_df.to_excel(writer, sheet_name='DTD', index=False)
                print(f"DTD sheet in {file_name} has been updated!")
            else:
                print(
                    f"DTD sheet in {file_name} already contains all entries. No updates made.")
        else:
            new_dtd_df.to_excel(writer, sheet_name='DTD', index=False)
            print(f"DTD sheet has been added to {file_name}!")


# Directory and sheet mappings
script_dir = os.path.dirname(os.path.realpath(__file__))
user_profile = os.path.join(script_dir, '..', 'UserProfile')
excel_dir = os.path.join(user_profile, 'excel')
sheet_mappings = {
    'MP Wizard': 'MPWizard',
    'AmiPy': 'AmiPy',
    'ZRM': 'ZRM',
    'Overnight Options': 'Overnight_options'
}

for user_file in os.listdir(excel_dir):
    if user_file.endswith('.xlsx') and user_file != "signal.xlsx":
        file_name = os.path.join(excel_dir, user_file)
        data_mappings = fetch_data_from_excel(file_name, sheet_mappings)
        dtd_df = create_dtd_dataframe(data_mappings)
        check_and_update_dtd_sheet(file_name, dtd_df)
