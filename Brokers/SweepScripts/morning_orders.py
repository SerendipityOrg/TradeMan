import os,sys

DIR = os.getcwd()
sys.path.append(DIR)

import MarketUtils.Excel.strategy_calc as sc
import MarketUtils.general_calc as general_calc
import Brokers.Aliceblue.alice_utils as aliceblue



def find_blank_exit_trades(df):
    # Filter the dataframe for rows where 'exit_time' is NaT (Not a Time, pandas representation of blank)
    filtered_df = df[df['exit_time'].isna()]

    # Convert the filtered dataframe to a dictionary with the column name as keys
    # Each key will have a list of values corresponding to the rows where 'exit_time' is blank
    trade_details = filtered_df.to_dict(orient='list')
    return trade_details

excel_path = os.path.join(DIR, f"UserProfile/Excel/vimala.xlsx")
excel_data = sc.load_existing_excel(excel_path)

# Process the 'Stocks' and 'Extra' sheets if they exist in the Excel file
if "Stocks" in excel_data and "Extra" in excel_data:
    stocks_trades = find_blank_exit_trades(excel_data["Stocks"])
    extra_trades = find_blank_exit_trades(excel_data["Extra"])
    print("Stocks Trades with Blank Exit Time:", type(stocks_trades))
    print("Extra Trades with Blank Exit Time:", type(extra_trades))
else:
    print("The required sheets ('Stocks' and 'Extra') are not in the Excel file.")

def alice_morning(user):
    alice = aliceblue.create_alice_obj(user)
    positions = alice.get_daywise_positions()
    print(positions)
    if len(positions) == 2:
        print("No positions found")
    else:
        print("here")



active_users = general_calc.read_json_file(os.path.join(DIR,"MarketUtils","active_users.json"))
for user in active_users:
        if user['broker'] == "aliceblue":
            alice_morning(user)
        elif user['broker'] == "zerodha":
            print("zerodha")
        else:
            print("Unknown broker")