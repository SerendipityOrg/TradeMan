import pandas as pd
import os

# Function to format numbers according to the Indian numbering system.


def format_indian(number):
    s = '%.2f' % number
    integer_part, fractional_part = s.split('.')
    integer_part = int(integer_part)

    # Create the formatted integer part
    thousands = integer_part % 1000
    integer_part //= 1000

    lakhs = integer_part % 100
    integer_part //= 100

    crores = integer_part

    if crores:
        result = '{}, {:02d}, {:03d}'.format(crores, lakhs, thousands)
    elif lakhs:
        result = '{:02d}, {:03d}'.format(lakhs, thousands)
    else:
        result = '{:03d}'.format(thousands)

    return result + '.' + fractional_part


# Check if the DataFrame contains the required columns.


def has_required_columns(df):
    required_columns = ['Date', 'Net PnL', 'Trade ID']
    return all(col in df.columns for col in required_columns)

# Fetch data from Excel and return a dictionary of DataFrames.


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

# Create and return the DTD DataFrame with correct running balance calculation and formatted columns.


def create_dtd_dataframe_updated_v3(data_mappings, opening_balance):
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
        'Date': '07-Jul-23',
        'Day': 'Friday',
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': '₹ ' + format_indian(opening_balance),
        'Running Balance': '₹ ' + format_indian(running_balance)
    })
    sl_no += 1

    start_date = pd.Timestamp('2023-07-10')
    for date in all_dates_sorted:
        if date < start_date:
            continue

        date_str = date.strftime('%d-%b-%y')
        day_str = date.strftime('%A')

        for transaction_id in default_details:
            if transaction_id in data_mappings:
                df = data_mappings[transaction_id]
                sub_df = df[df['Date'] == date]

                if transaction_id == "MP Wizard":
                    for _, row in sub_df.iterrows():
                        trade_id = row['Trade ID']
                        pnl = row['Net PnL']
                        amount = pnl
                        running_balance += amount  # Update running balance BEFORE appending
                        rows.append({
                            'Sl NO': sl_no,
                            'Date': date_str,
                            'Day': day_str,
                            'Trade ID': trade_id,
                            'Details': transaction_id,
                            'Amount': '₹ ' + format_indian(amount),
                            'Running Balance': '₹ ' + format_indian(running_balance)
                        })
                        sl_no += 1
                else:
                    aggregated_pnl = sub_df['Net PnL'].sum()
                    aggregated_trade_ids = ' '.join(
                        sub_df['Trade ID'].dropna())
                    amount = aggregated_pnl
                    if not (transaction_id == 'Overnight Options' and amount == 0.00):
                        running_balance += amount  # Update running balance BEFORE appending
                        rows.append({
                            'Sl NO': sl_no,
                            'Date': date_str,
                            'Day': day_str,
                            'Trade ID': aggregated_trade_ids,
                            'Details': transaction_id,
                            'Amount': '₹ ' + format_indian(amount),
                            'Running Balance': '₹ ' + format_indian(running_balance)
                        })
                        sl_no += 1

    dtd_df = pd.DataFrame(rows)
    return dtd_df, running_balance

# Retrieve existing 'Opening Balance' from the DTD sheet.


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

# Append new data to the existing DTD sheet or create a new one.


def check_and_update_dtd_sheet(file_name, new_dtd_df):
    if 'Details' not in new_dtd_df.columns:
        print(
            f"'Details' column missing in the new data for {file_name}. Skipping this file.")
        return

    existing_opening_balance = get_existing_opening_balance(file_name)

    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        if existing_opening_balance is not None:
            new_dtd_df.loc[new_dtd_df['Details'] == 'Opening Balance',
                           'Running Balance'] = '₹ ' + format_indian(existing_opening_balance)

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
if __name__ == "__main__":
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

            # Get the existing opening balance
            existing_opening_balance = get_existing_opening_balance(file_name)
            if existing_opening_balance is None:
                existing_opening_balance = 0.0  # Default value if no opening balance exists

            dtd_df, _ = create_dtd_dataframe_updated_v3(
                data_mappings, existing_opening_balance)
            check_and_update_dtd_sheet(file_name, dtd_df)
