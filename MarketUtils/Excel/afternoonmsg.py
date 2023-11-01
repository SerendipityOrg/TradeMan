import os
import general_calc
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from babel.numbers import format_currency

# Set up the directory paths
DIR = os.getcwd()
script_dir = os.path.dirname(os.path.realpath(__file__))
broker_filepath = os.path.join(DIR, "MarketUtils", "broker.json")
excel_dir = os.path.join(DIR, "UserProfile", "excel")


def custom_format(amount):
    """Format the currency amount in INR format and replace the default symbol."""
    formatted = format_currency(amount, 'INR', locale='en_IN')
    return formatted.replace('₹', '₹ ')


def load_existing_excel(excel_path):
    """Load an existing Excel file and return its data as a dictionary of pandas DataFrames."""
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    try:
        book = load_workbook(excel_path)
        return {sheet_name: pd.read_excel(excel_path, sheet_name=sheet_name) for sheet_name in book.sheetnames}
    except Exception as e:
        print(f"An error occurred while loading the Excel file: {excel_path}")
        print("Error:", e)
        return {}


def update_json_data(data, broker, user, net_pnl, current_capital, expected_capital, broker_filepath):
    """Update the JSON data with new PNL, capital values, etc."""
    for username in data:
        if user["account_name"] == username["account_name"]:
            user_details = username
            user_details["current_capital"] = round(current_capital, 2)
            user_details["yesterday_PnL"] = net_pnl
            user_details["expected_morning_balance"] = round(
                expected_capital, 2)
    general_calc.write_json_file(broker_filepath, data)


def build_message(user, gross_pnl, tax, current_capital, expected_capital):
    """Construct and return the message for the user based on their PNL and other metrics."""
    message_parts = [
        f"Hello {user},We hope you're enjoying a wonderful day.\n Here are your PNLs for today:\n"]
    message_parts.extend([
        f"\n**Gross PnL: {custom_format(gross_pnl)}**",
        f"**Expected Tax: {custom_format(tax)}**",
        f"**Current Capital: {custom_format(current_capital)}**",
        f"**Expected Morning Balance : {custom_format(expected_capital)}**",
        "\nBest Regards,\nSerendipity Trading Firm"
    ])

    return message_parts


def main():
    # Load active users data
    data = general_calc.read_json_file(
        os.path.join(script_dir, "..", "active_users.json"))
    today = datetime.now().strftime('%Y-%m-%d')  # Get today's date

    for user in data:
        excel_path = os.path.join(excel_dir, f"{user['account_name']}.xlsx")
        broker_json = general_calc.read_json_file(broker_filepath)
        broker = user["broker"]

        # Load the existing Excel data
        all_dfs = load_existing_excel(excel_path)

        # Initialize counters for the PNL and tax calculations
        strategy_results = {}
        gross_pnl = 0
        total_tax = 0

        # Calculate PNL and Tax for today for each strategy
        for strategy, df in all_dfs.items():
            df_today = df[df['entry_time'] == today]
            if not df_today.empty:
                pnl = df_today['pnl'].sum()
                tax = df_today['tax'].sum()
                strategy_results[strategy] = pnl  # Store PNL for each strategy
                gross_pnl += pnl
                total_tax += tax

        # Calculate Net PNL
        net_pnl = gross_pnl - total_tax

        for account in broker_json:
            if account["account_name"] == user["account_name"]:
                current_capital = account["expected_morning_balance"]

        expected_capital = current_capital + \
            net_pnl if net_pnl > 0 else current_capital - abs(net_pnl)

        # Construct the message and print
        message_parts = build_message(
            user['account_name'], gross_pnl, total_tax, current_capital, expected_capital)
        message = "\n".join(message_parts).replace('\u20b9', '₹')
        print(message)

        # Update the JSON data
        update_json_data(data, broker, user, net_pnl,
                         current_capital, expected_capital, broker_filepath)


# Execute the main function when script is run
if __name__ == "__main__":
    main()
