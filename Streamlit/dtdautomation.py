import pandas as pd
import os

# # Construct the path to the excel directory inside user profile
# script_dir = os.path.dirname(os.path.realpath(__file__))
# user_profile = os.path.join(script_dir, '..','UserProfile')
# excel_dir = os.path.join(user_profile, 'excel')
# file_name = os.path.join(excel_dir, 'user.xlsx')

# Path to the Excel file
file_name = r'C:\Users\vanis\OneDrive\Desktop\TRADEMAN\TradeMan\UserProfile\excel\omkar.xlsx'

# Create a mapping between required columns and their respective DataFrames
data_mappings = {
    'MP Wizard': pd.read_excel(file_name, sheet_name='MPWizard'),
    'AmiPy': pd.read_excel(file_name, sheet_name='AmiPy'),
    'ZRM': pd.read_excel(file_name, sheet_name='ZRM'),
    'Overnight Options': pd.read_excel(file_name, sheet_name='Overnight_options')
}

# Create a new DTD DataFrame with the given header
header = ['SI NO', 'Date', 'Day', 'Transaction', 'Opening Balance', 'MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options', 'Gross PnL', 'Tax', 'Transaction Amount', 'Running Balance', 'Deposit','Withdrawal', 'Telegram Balance', 'Difference Amount', 'Remarks']
dtd_df = pd.DataFrame(columns=header)

# Initialize with all unique dates from all DataFrames
all_dates = pd.concat([df['Date'] for df in data_mappings.values()]).unique()
sorted_dates = sorted(all_dates, key=pd.Timestamp)
dtd_df['Date'] = sorted_dates

# Merge the DataFrames
for column, df in data_mappings.items():
    if 'PnL' in df.columns and 'Tax' in df.columns:
        agg_df = df.groupby('Date').agg({'PnL': 'sum', 'Tax': 'sum'}).reset_index()
        dtd_df = pd.merge(dtd_df, agg_df, on='Date', how='left', suffixes=('', f'_{column}'))
        
        # Handle the column naming
        if f'PnL_{column}' in dtd_df.columns:
            dtd_df[column] = dtd_df[f'PnL_{column}']
            dtd_df.drop(columns=[f'PnL_{column}'], inplace=True)
        else:
            dtd_df[column] = dtd_df['PnL']
            dtd_df.drop(columns=['PnL'], inplace=True)

# Calculate the sum of all taxes and PnL
dtd_df['Tax'] = dtd_df[['Tax_' + name for name in data_mappings.keys()]].sum(axis=1)
dtd_df['Gross PnL'] = dtd_df[list(data_mappings.keys())].sum(axis=1)

# Remove unwanted Tax columns
for col in dtd_df.columns:
    if 'Tax_' in col:
        dtd_df.drop(columns=[col], inplace=True)

# Add 'SI NO' (Serial Number)
dtd_df['SI NO'] = range(1, len(dtd_df) + 1)


# Format Date and get Day of the week
dtd_df['Date'] = pd.to_datetime(dtd_df['Date']).dt.strftime('%d-%b-%y')
dtd_df['Day'] = pd.to_datetime(dtd_df['Date'], errors='coerce').dt.day_name()

# Currency formatting for appropriate columns
for col in ['Opening Balance', 'MP Wizard', 'AmiPy', 'ZRM', 'Overnight Options', 'Gross PnL', 'Tax', 'Transaction Amount', 'Running Balance', 'Deposit', 'Withdrawal', 'Telegram Balance', 'Difference Amount']:
    dtd_df[col] = dtd_df[col].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Compute Transaction Amount
dtd_df['Transaction Amount'] = dtd_df.apply(lambda row: float(row['Gross PnL'].replace('₹', '').replace(',', '')) - float(row['Tax'].replace('₹', '').replace(',', '')), axis=1)
dtd_df['Transaction Amount'] = dtd_df['Transaction Amount'].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Compute 'Difference Amount' (difference between 'Running Balance' and 'Telegram Balance')
dtd_df['Difference Amount'] = dtd_df.apply(lambda row: float(row['Running Balance'].replace('₹', '').replace(',', '')) - float(row['Telegram Balance'].replace('₹', '').replace(',', '')) if row['Telegram Balance'] != '' else None, axis=1)
dtd_df['Difference Amount'] = dtd_df['Difference Amount'].apply(lambda x: f'₹ {x:,.2f}' if pd.notna(x) else '')

# Add 'Remarks' based on 'Difference Amount'
dtd_df['Remarks'] = dtd_df.apply(lambda row: 'Difference' if row['Difference Amount'] != '' else '', axis=1)

# Save the DTD DataFrame to the Excel file
with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
    dtd_df.to_excel(writer, sheet_name='DTD', index=False)

print("DTD sheet has been created!")
