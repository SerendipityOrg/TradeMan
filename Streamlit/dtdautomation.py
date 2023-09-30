import pandas as pd
import os

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

# Create and return the DTD DataFrame.


def create_dtd_dataframe(data_mappings, opening_balance):
    if not data_mappings:
        print("No valid DataFrames found!")
        return pd.DataFrame(), 0

    all_dates = pd.concat([df['Date']
                          for df in data_mappings.values()]).unique()
    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)

    rows = []
    default_details = ['MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options']
    si_no = 1

    running_balance = opening_balance
    rows.append({
        'SI NO': si_no,
        'Date': '08-Jul-23',
        'Day': 'Friday',
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': '0',
        'Running Balance': f'₹ {running_balance:,.2f}'
    })
    si_no += 1

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
                        running_balance += pnl  # Update running balance
                        rows.append({
                            'SI NO': si_no,
                            'Date': date_str,
                            'Day': day_str,
                            'Trade ID': trade_id,
                            'Details': transaction_id,
                            'Amount': f'₹ {pnl:,.2f}',
                            'Running Balance': f'₹ {running_balance:,.2f}'
                        })
                        si_no += 1
                else:
                    aggregated_pnl = sub_df['Net PnL'].sum()
                    aggregated_trade_ids = ' '.join(
                        sub_df['Trade ID'].dropna())
                    if transaction_id == "Overnight Options" and aggregated_pnl == 0.00:
                        continue
                    running_balance += aggregated_pnl  # Update running balance
                    rows.append({
                        'SI NO': si_no,
                        'Date': date_str,
                        'Day': day_str,
                        'Trade ID': aggregated_trade_ids,
                        'Details': transaction_id,
                        'Amount': f'₹ {aggregated_pnl:,.2f}',
                        'Running Balance': f'₹ {running_balance:,.2f}'
                    })
                    si_no += 1

    dtd_df = pd.DataFrame(rows)
    return dtd_df, running_balance


# Retrieve existing 'Opening Balance' from the DTD sheet


def get_existing_opening_balance(file_name):
    if 'DTD' in pd.ExcelFile(file_name).sheet_names:
        existing_dtd = pd.read_excel(file_name, sheet_name='DTD')
        details_column = existing_dtd.get('Details')

        if details_column is not None and 'Opening Balance' in details_column.values:
            running_balance_str = existing_dtd[details_column ==
                                               'Opening Balance']['Running Balance'].iloc[0]
            if isinstance(running_balance_str, str):
                return float(running_balance_str.replace('₹', '').replace(',', ''))
    return None

# Append new data to the existing DTD sheet or create a new one.


def check_and_update_dtd_sheet(file_name, new_dtd_df, default_opening_balance):
    # Check if 'Details' column exists in the dataframe
    if 'Details' not in new_dtd_df.columns:
        print(
            f"'Details' column missing in the new data for {file_name}. Skipping this file.")
        return

    existing_opening_balance = get_existing_opening_balance(file_name)

    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        if existing_opening_balance is not None:
            new_dtd_df.loc[new_dtd_df['Details'] == 'Opening Balance',
                           'Running Balance'] = f'₹ {existing_opening_balance:,.2f}'

        if 'DTD' in writer.book.sheetnames:
            existing_dtd = pd.read_excel(file_name, sheet_name='DTD')

            # Safe check for 'Date' column in both dataframes
            if 'Date' in existing_dtd.columns and 'Date' in new_dtd_df.columns:
                last_existing_date = pd.to_datetime(
                    existing_dtd['Date'].iloc[-1])
                new_dtd_df = new_dtd_df[pd.to_datetime(
                    new_dtd_df['Date']) > last_existing_date]
                updated_dtd_df = pd.concat(
                    [existing_dtd, new_dtd_df], ignore_index=True)
            else:
                print(
                    f"'Date' column not found in DTD sheet or new data of {file_name}. Skipping update for this file.")
                return

            std = writer.book['DTD']
            writer.book.remove(std)
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

    default_opening_balance = 0.0

    for user_file in os.listdir(excel_dir):
        if user_file.endswith('.xlsx') and user_file != "signal.xlsx":
            file_name = os.path.join(excel_dir, user_file)
            data_mappings = fetch_data_from_excel(file_name, sheet_mappings)
            dtd_df, _ = create_dtd_dataframe(
                data_mappings, default_opening_balance)
            check_and_update_dtd_sheet(
                file_name, dtd_df, default_opening_balance)
