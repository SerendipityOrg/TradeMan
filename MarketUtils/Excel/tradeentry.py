import os,sys
import json
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from babel.numbers import format_currency
import strategy_calc as sc
import firebase_admin
from firebase_admin import credentials, storage
from telethon.sync import TelegramClient
from dotenv import load_dotenv
import dtdautomation as dtd


DIR = os.getcwd()
ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

api_id = os.getenv('telethon_api_id')
api_hash = os.getenv('telethon_api_hash')

marketutils_dir = os.path.join(DIR, "MarketUtils")
sys.path.append(marketutils_dir)
import general_calc as general_calc

broker_filepath = os.path.join(DIR,"MarketUtils", "broker.json")
userprofile_dir = os.path.join(DIR, "UserProfile","OrdersJson")
# excel_dir = os.path.join(DIR, "UserProfile","Excel")
excel_dir = '/Users/amolkittur/Library/CloudStorage/OneDrive-Personal/DONOTTOUCH/excel'
script_dir = os.path.dirname(os.path.realpath(__file__))

class TradingStrategy:
    def __init__(self, name, process_func):
        self.name = name
        self.process_func = process_func
    
    def process_data(self, user_data, broker):
        if self.name in user_data["orders"]:
            data = self.process_func(broker, user_data["orders"][self.name])
            df = pd.DataFrame(data)
            if 'pnl' in df.columns:
                PnL = round(df['pnl'].sum(), 1)
                Tax = round(df['tax'].sum(), 1)
            else:
                print("PnL column not found in DataFrame")
                PnL = 0
                Tax = 0
            return df, PnL, Tax
        return pd.DataFrame(), 0, 0

def custom_format(amount):
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹')

def load_existing_excel(excel_path):
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    try:
        book = load_workbook(excel_path)
        return {sheet_name: pd.read_excel(excel_path, sheet_name=sheet_name) for sheet_name in book.sheetnames}
    except Exception as e:
        print(f"An error occurred while loading the Excel file: {excel_path}")
        print("Error:", e)
        return {}

def update_excel_data(all_dfs, df, strategy_name):
    if not df.empty:
        all_dfs[strategy_name] = pd.concat([all_dfs.get(strategy_name, pd.DataFrame()), df])

def update_json_data(data, broker, user, net_pnl, expected_capital, broker_filepath):
    for username in data:
        if user["account_name"] == username["account_name"]:
            user_details = username
            user_details["yesterday_PnL"] = net_pnl
            user_details["expected_morning_balance"] = round(expected_capital, 2)
    general_calc.write_json_file(broker_filepath,data )

def save_all_sheets_to_excel(all_dfs, excel_path):
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, df in all_dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Now that the data is written, get the worksheet to apply styles
            worksheet = writer.sheets[sheet_name]

            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(horizontal='center')

def build_message(user, strategy_results, gross_pnl, tax, current_capital, expected_capital):
    message_parts = [f"Hello {user},We hope you're enjoying a wonderful day.\n Here are your PNLs for today:\n"]
    
    for strategy_name, pnl in strategy_results.items():
        if pnl != 0:
            message_parts.append(f"{strategy_name}: {custom_format(pnl)}")
    
    message_parts.extend([
        f"\n**Gross PnL: {custom_format(gross_pnl)}**",
        f"**Expected Tax: {custom_format(tax)}**",
        f"**Current Capital: {custom_format(current_capital)}**",
        f"**Expected Morning Balance : {custom_format(expected_capital)}**",
        "\nBest Regards,\nSerendipity Trading Firm"
    ])
    
    return message_parts

# Define a dictionary that maps strategy names to their processing functions
strategy_config = {
    "MPWizard": sc.process_mpwizard_trades,
    "AmiPy": sc.process_amipy_trades,
    "OvernightFutures": sc.process_overnight_futures_trades,
    "ExpiryTrader": sc.process_expiry_trades
    # Add new strategies here as needed
}
credentials_filepath = os.path.join(script_dir  ,"credentials.json")
cred = credentials.Certificate(credentials_filepath)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trading-app-caf8e-default-rtdb.firebaseio.com'
})

def save_to_firebase(user, excel_path):
    # Correct bucket name
    bucket = storage.bucket(name='trading-app-caf8e.appspot.com')
    blob = bucket.blob(f'{user}.xlsx')
    with open(excel_path, 'rb') as my_file:
        blob.upload_from_file(my_file)
    print(f"Excel file for {user} has been uploaded to Firebase.")

def send_telegram_message(phone_number, message):
    session_filepath = os.path.join(script_dir, "..",'..','..', "+918618221715.session")
    with TelegramClient(session_filepath, api_id, api_hash) as client:
        client.send_message(phone_number, message, parse_mode='md')


def main():
    data = general_calc.read_json_file(os.path.join(script_dir, "..", "active_users.json"))
    
    # Initialize TradingStrategy objects based on the configuration
    strategies = [TradingStrategy(name, func) for name, func in strategy_config.items()]

    for user in data:
        user_data = general_calc.read_json_file(os.path.join(userprofile_dir, f"{user['account_name']}.json"))
        phone_number = user["mobile_number"]
        broker = user["broker"]

        strategy_results = {}
        gross_pnl = 0
        total_tax = 0
        
        excel_path = os.path.join(excel_dir, f"{user['account_name']}.xlsx")
        all_dfs = load_existing_excel(excel_path)

        for strategy in strategies:
            df, pnl, tax = strategy.process_data(user_data, broker)
            strategy_results[strategy.name] = pnl
            gross_pnl += pnl
            total_tax += tax
            update_excel_data(all_dfs, df, strategy.name)

        net_pnl = gross_pnl - total_tax
        current_capital = user['current_capital']
        expected_capital = current_capital + net_pnl if net_pnl > 0 else current_capital - abs(net_pnl)

        message_parts = build_message(user['account_name'], strategy_results, gross_pnl, total_tax, current_capital, expected_capital)
        message = "\n".join(message_parts).replace('\u20b9', '₹')
        print(message)

        update_json_data(data, broker, user, net_pnl, expected_capital, broker_filepath)
        save_all_sheets_to_excel(all_dfs, excel_path)
        # dtd.update_dtd_sheets()


        # # save_to_firebase(user, excel_path)  # Existing function
        # send_telegram_message(phone_number, message)  # Existing function

if __name__ == "__main__":
    main()
