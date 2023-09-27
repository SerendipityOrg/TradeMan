import pandas as pd
import os


def has_required_columns(df):
    """Check if the DataFrame contains the required columns."""
    required_columns = ['Date', 'Net PnL']
    return all(col in df.columns for col in required_columns)


def fetch_data_from_excel(file_name, sheet_mappings):
    """Fetch data from Excel and return a dictionary of DataFrames."""
    data_mappings = {}

    # Iterating over each sheet mapping to read them into DataFrames
    for internal_name, actual_sheet_name in sheet_mappings.items():
        try:
            temp_df = pd.read_excel(file_name, sheet_name=actual_sheet_name)

            # Verify if the required columns exist in the sheet
            if has_required_columns(temp_df):
                data_mappings[internal_name] = temp_df
            else:
                print(
                    f"Sheet '{actual_sheet_name}' in {user_file} does not have all required columns. Skipping...")

        except ValueError:
            print(
                f"Sheet '{actual_sheet_name}' not found in {user_file}. Skipping...")

    return data_mappings


def create_dtd_dataframe(data_mappings):
    """Creates and returns the DTD DataFrame."""
    all_dates = pd.concat([df['Date']
                          for df in data_mappings.values()]).unique()
    all_dates_sorted = sorted(all_dates, key=pd.Timestamp)

    rows = []

    # List of transaction details we are interested in
    default_details = ['MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options',
                       'Error Trade', 'Deposit', 'Withdrawal', 'Comission']
    si_no = 1  # Initialize the serial number counter

    # Adding the 'Opening Balance' entry once at the beginning
    rows.append({
        'SI NO': '',
        'Date': '',
        'Day': '',
        'Trade ID': '',
        'Details': 'Opening Balance',
        'Amount': ''
    })

    # Iterating over each date to fetch transaction details
    for date in all_dates_sorted:
        for transaction_id in default_details:

            # Initializing default amount string
            amount_str = ''

            # If the transaction_id exists in our data mappings (i.e., if we have a sheet/data for it)
            if transaction_id in data_mappings:

                # Fetch the DataFrame for that transaction_id
                df = data_mappings[transaction_id]

                # Get the 'Net PnL' value for the given date
                amount = df[df['Date'] == date]['Net PnL'].sum()
                amount_str = f'₹ {amount:,.2f}' if amount != 0 else ''

            # Appending the transaction details to the rows list
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


# Directory and sheet mappings
script_dir = os.path.dirname(os.path.realpath(__file__))
user_profile = os.path.join(script_dir, '..', 'UserProfile')
excel_dir = os.path.join(user_profile, 'excel')

# Sheet mappings to their corresponding internal names
sheet_mappings = {
    'MP Wizard': 'MPWizard',
    'AmiPy': 'AmiPy',
    'ZRM': 'ZRM',
    'Overnight Options': 'Overnight_options'
}

# Process each excel file in the directory
for user_file in os.listdir(excel_dir):
    if user_file.endswith('.xlsx') and user_file != "signal.xlsx":
        file_name = os.path.join(excel_dir, user_file)

        # Fetching data from the excel file into a dictionary of DataFrames
        data_mappings = fetch_data_from_excel(file_name, sheet_mappings)

        # Creating the DTD DataFrame
        dtd_df = create_dtd_dataframe(data_mappings)

        # Saving the DTD DataFrame back to the same excel file as a new sheet
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
            book = writer.book
            if 'DTD' in book.sheetnames:
                std = book['DTD']
                book.remove(std)
            dtd_df.to_excel(writer, sheet_name='DTD', index=False)

        print(f"{user_file} has been updated with a DTD sheet!")
