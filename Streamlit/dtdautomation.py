import pandas as pd
import os

# # Construct the path to the excel directory inside user profile
# script_dir = os.path.dirname(os.path.realpath(__file__))
# user_profile = os.path.join(script_dir, '..','UserProfile')
# excel_dir = os.path.join(user_profile, 'excel')
# file_name = os.path.join(excel_dir, 'user.xlsx')

# Path to the Excel file
file_name = r'C:\Users\vanis\OneDrive\Desktop\TRADEMAN\TradeMan\UserProfile\excel\omkar.xlsx'

# Create a dictionary to map each sheet name to its respective DataFrame.
data_mappings = {
    'MP Wizard': pd.read_excel(file_name, sheet_name='MP Wizard'),
    'AmiPy': pd.read_excel(file_name, sheet_name='AmiPy'),
    'ZRM': pd.read_excel(file_name, sheet_name='ZRM'),
    'Overnight Options': pd.read_excel(file_name, sheet_name='Overnight Options')
}

# Define the column headers for the new DTD DataFrame.
header = ['SI NO', 'Date', 'Day', 'Transaction Type', 'Opening Balance', 'MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options', 'Error Trade','Gross PnL', 'Tax', 'Transaction Amount', 'Running Balance', 'Deposit','Withdrawal', 'Telegram Balance', 'Difference Amount', 'Remarks']

# Initialize an empty DataFrame with the defined headers.
dtd_df = pd.DataFrame(columns=header)

# Gather all unique dates from all sheets.
all_dates = pd.concat([df['Date'] for df in data_mappings.values()]).unique()

# Sort these dates.
sorted_dates = sorted(all_dates, key=pd.Timestamp)

# Assign the sorted dates to the 'Date' column of DTD DataFrame.
dtd_df['Date'] = sorted_dates

# Merge data from all sheets into the DTD DataFrame.
for column, df in data_mappings.items():
    if 'PnL' in df.columns and 'Tax' in df.columns:
        agg_df = df.groupby('Date').agg({'PnL': 'sum', 'Tax': 'sum'}).reset_index()
        dtd_df = pd.merge(dtd_df, agg_df, on='Date', how='left', suffixes=('', f'_{column}'))
        
        # Rename the columns after merging.
        if f'PnL_{column}' in dtd_df.columns:
            dtd_df[column] = dtd_df[f'PnL_{column}']
            dtd_df.drop(columns=[f'PnL_{column}'], inplace=True)
        else:
            dtd_df[column] = dtd_df['PnL']
            dtd_df.drop(columns=['PnL'], inplace=True)

# Calculate total Tax and Gross PnL.
dtd_df['Tax'] = dtd_df[['Tax_' + name for name in data_mappings.keys()]].sum(axis=1)
dtd_df['Gross PnL'] = dtd_df[list(data_mappings.keys())].sum(axis=1)

# Remove individual tax columns after consolidating.
for col in dtd_df.columns:
    if 'Tax_' in col:
        dtd_df.drop(columns=[col], inplace=True)

# Add serial numbers.
dtd_df['SI NO'] = range(1, len(dtd_df) + 1)

# Convert 'Date' to datetime for sorting and operations.
dtd_df['Date'] = pd.to_datetime(dtd_df['Date'], errors='coerce')

# Extract 'Day' from the 'Date' column.
dtd_df['Day'] = dtd_df['Date'].dt.day_name()

# Set Transaction Type as "Trade" for all rows.
dtd_df['Transaction Type'] = "Trade"

# Convert 'Date' back to the desired string format.
dtd_df['Date'] = dtd_df['Date'].dt.strftime('%d-%b-%y')

# Format financial columns with currency notation.
currency_cols = ['Opening Balance', 'MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options', 'Gross PnL', 'Tax', 'Transaction Amount', 'Running Balance', 'Deposit', 'Withdrawal', 'Telegram Balance', 'Difference Amount']
for col in currency_cols:
    dtd_df[col] = dtd_df[col].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Compute Transaction Amount (Gross PnL - Tax).
dtd_df['Transaction Amount'] = dtd_df.apply(lambda row: float(row['Gross PnL'].replace('₹', '').replace(',', '')) - float(row['Tax'].replace('₹', '').replace(',', '')), axis=1)
dtd_df['Transaction Amount'] = dtd_df['Transaction Amount'].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Compute 'Difference Amount' (difference between 'Running Balance' and 'Telegram Balance').
dtd_df['Difference Amount'] = dtd_df.apply(lambda row: float(row['Running Balance'].replace('₹', '').replace(',', '')) - float(row['Telegram Balance'].replace('₹', '').replace(',', '')) if row['Telegram Balance'] != '' else None, axis=1)
dtd_df['Difference Amount'] = dtd_df['Difference Amount'].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Populate 'Remarks' column.
dtd_df['Remarks'] = dtd_df.apply(lambda row: 'Difference' if row['Difference Amount'] != '' else '', axis=1)

# Load the entire Excel workbook
with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
    book = writer.book

# Check if the 'DTD' sheet exists
if 'DTD' in book.sheetnames:
    existing_dtd_df = pd.read_excel(file_name, sheet_name='DTD')
    
    # Extract the last date from the existing 'DTD' sheet
    last_date = pd.to_datetime(existing_dtd_df['Date'].iloc[-1], format='%d-%b-%y')
    
    # Filter the rows from dtd_df to only include rows with dates greater than last_date
    dtd_df = dtd_df[pd.to_datetime(dtd_df['Date'], format='%d-%b-%y') > last_date]

    # Append new data to existing DTD sheet
    combined_dtd_df = pd.concat([existing_dtd_df, dtd_df], ignore_index=True)
    
else:
    combined_dtd_df = dtd_df

# Save the updated workbook back
with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
    for sheetname, data in data_mappings.items():
        data.to_excel(writer, sheet_name=sheetname, index=False)
    combined_dtd_df.to_excel(writer, sheet_name='DTD', index=False)

print("DTD sheet has been updated!")