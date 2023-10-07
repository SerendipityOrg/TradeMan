import pandas as pd


def zerodha_taxes(qty, entry_prc, exit_prc, orders):
    # print(qty)
    # print(entry_prc)
    # print(exit_prc)

    instruments = 0
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4

    # Brokerage
    brokerage = 20 * instruments  # Flat Rs. 20 per executed order

    # STT/CTT
    intrinsic_value = max(0, exit_prc - entry_prc) * qty
    stt_on_exercise = 0.125 / 100 * intrinsic_value
    stt_on_sell = 0.0625 / 100 * exit_prc * qty

    # Transaction charges
    transaction_charges = 0.05 / 100 * exit_prc * qty

    # GST
    sebi_charges = 10 / 10000000 * exit_prc * qty  # Rs. 10 / crore

    # SEBI charges
    # SEBI charges are Rs. 10 / crore
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges = 0.003 / 100 * entry_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + \
        transaction_charges + gst + sebi_charges + stamp_charges

    return round(total_charges, 2)


def aliceblue_taxes(qty, entry_prc, exit_prc, orders):
    # print(qty)
    # print(entry_prc)
    # print(exit_prc)

    instruments = 0
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4
    # Brokerage
    brokerage = 15 * instruments  # Flat Rs. 20 per executed order

    # STT/CTT
    intrinsic_value = max(0, exit_prc - entry_prc) * qty
    stt_on_exercise = 0.125 / 100 * intrinsic_value
    stt_on_sell = 0.0625 / 100 * exit_prc * qty

    # Transaction charges
    transaction_charges = 0.05 / 100 * exit_prc * qty

    # SEBI charges
    sebi_charges = 10 / 10000000 * exit_prc * qty  # Rs. 10 / crore

    # GST
    # SEBI charges are Rs. 10 / crore
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges = 0.003 / 100 * exit_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + \
        transaction_charges + gst + sebi_charges + stamp_charges

    return round(total_charges, 2)


def zerodha_futures_taxes(qty, entry_prc, exit_prc, orders):
    instruments = 0
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4

    # Brokerage
    brokerage_rate = 0.03 / 100
    brokerage = min(entry_prc * qty * brokerage_rate, 20) * instruments

    # STT/CTT
    stt_ctt_rate = 0.0125 / 100
    stt_ctt = stt_ctt_rate * exit_prc * qty

    # Transaction charges
    transaction_charges_rate = 0.0019 / 100
    transaction_charges = transaction_charges_rate * exit_prc * qty

    # SEBI charges
    sebi_charges_rate = 10 / 100000000
    sebi_charges = sebi_charges_rate * exit_prc * qty

    # GST
    gst_rate = 18 / 100
    gst = gst_rate * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges_rate = 0.002 / 100
    stamp_charges = max(stamp_charges_rate * entry_prc * qty, 200)

    total_charges = brokerage + stt_ctt + \
        transaction_charges + gst + sebi_charges + stamp_charges

    return round(total_charges, 2)


def aliceblue_futures_taxes(qty, entry_prc, exit_prc, orders):
    # print(qty)
    # print(entry_prc)
    # print(exit_prc)
    instruments = 0
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4

    # Brokerage
    brokerage_rate = 0.03 / 100
    brokerage = min(entry_prc * qty * brokerage_rate, 20) * instruments

    # STT/CTT
    stt_ctt_rate = 0.0125 / 100
    stt_ctt = stt_ctt_rate * exit_prc * qty

    # Transaction charges
    transaction_charges_rate = 0.0019 / 100
    transaction_charges = transaction_charges_rate * exit_prc * qty

    # SEBI charges
    sebi_charges_rate = 10 / 100000000
    sebi_charges = sebi_charges_rate * exit_prc * qty

    # GST
    gst_rate = 18 / 100
    gst = gst_rate * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges_rate = 0.002 / 100
    stamp_charges = max(stamp_charges_rate * entry_prc * qty, 200)

    total_charges = brokerage + stt_ctt + \
        transaction_charges + gst + sebi_charges + stamp_charges

    return round(total_charges, 2)


def calculate_tax_from_excel(file_path):
    columns = ["Trade ID", "Strategy", "Index", "Strike Price", "Option Type", "Date", "Entry Time", "Exit Time",
               "Entry Price", "Exit Price", "Trade points", "Qty", "PnL", "Tax", "Net PnL"]
    df = pd.read_excel(file_path, sheet_name='MPWizard',
                       names=columns)

    for index, row in df.iterrows():
        qty = row["Qty"]
        entry_prc = row["Entry Price"]
        exit_prc = row["Exit Price"]
        orders = 1

        # Default to aliceblue tax calculation as we don't have broker name
        tax = aliceblue_taxes(qty, entry_prc, exit_prc, orders)
        # Added +2 to account for 0-indexing and header row
        # print(f"Tax for row {index + 2}: {tax}")
        print(tax)


# Sample usage remains the same
file_path = r"C:\Users\vanis\OneDrive\Desktop\TRADEMAN\TradeMan\UserProfile\excel\vinod.xlsx"
calculate_tax_from_excel(file_path)


# def calculate_and_print_tax_from_excel(file_path):
#     columns = ["Tr no", "Strategy", "Index", "Strike Price", "Option Type", "Date", "Entry Time", "Exit Time",
#                "Entry Price", "Exit Price", "Trade points", "Qty", "PnL", "Tax", "Net PnL"]
#     df = pd.read_excel(file_path, sheet_name='MPWizard',
#                        names=columns, header=1)

#     tax_values = []

#     for index, row in df.iterrows():
#         qty = row["Qty"]
#         entry_prc = row["Entry Price"]
#         exit_prc = row["Exit Price"]
#         orders = 1

#         # Default to aliceblue tax calculation as we don't have broker name
#         tax = aliceblue_taxes(qty, entry_prc, exit_prc, orders)
#         tax_values.append(tax)
#         print(tax)

# # Print the calculated tax values for each row
# print(f"Row {index + 1}: Tax = {tax:.2f}")

# def update_tax_in_excel(file_path):
#     columns = ["Strategy", "Index", "Strike Price", "Option Type", "Date", "Entry Time", "Exit Time",
#                "Entry Price", "Exit Price", "Trade points", "Qty", "PnL", "Tax"]
#     df = pd.read_excel(file_path, sheet_name='MPWizard',
#                        names=columns, skiprows=1)

#     for index, row in df.iterrows():
#         qty = row["Qty"]
#         entry_prc = row["Entry Price"]
#         exit_prc = row["Exit Price"]
#         orders = 1
#         tax = aliceblue_taxes(qty, entry_prc, exit_prc, orders)
#         df.at[index, 'Tax'] = tax

#     df.to_excel(file_path, sheet_name='MPWizard', index=False)


# # Sample usage:
# file_path = r"C:\Users\vanis\Downloads\venkatesh (2).xlsx"
# calculate_and_print_tax_from_excel(file_path)
# update_tax_in_excel(file_path)


# def calculate_and_print_tax_from_excel(file_path):
#     columns = ["Trade ID", "Strategy", "Index", "Trade Type", "Strike Prc", "Date", "Entry Time", "Exit Time",
#                "Entry Price", "Exit Price", "Hedge Entry", "Hedge Exit",  "Trade points", "Qty", "PnL", "Tax"]

#     # Read the excel file
#     df = pd.read_excel(file_path, sheet_name='AmiPy', names=columns)

#     # Calculate and print the 'Tax' column
#     for index, row in df.iterrows():
#         qty = row["Qty"]
#         entry_prc = row["Entry Price"]
#         exit_prc = row["Exit Price"]
#         orders = 2
#         hedge_entry = row["Hedge Entry"]
#         hedge_exit = row["Hedge Exit"]

#         #  Calculate tax using aliceblue_taxes
#         hedge_tax = zerodha_taxes(qty, hedge_entry, hedge_exit, 2)
#         order_tax = zerodha_taxes(qty, entry_prc, exit_prc, 2)
#         # futures_tax = aliceblue_futures_taxes(qty, orders, entry_prc, exit_prc)

# def calculate_and_print_tax_from_excel(file_path):
#     columns = ["Trade ID", "Strategy", "Trade_Type", "Date", "Entry Time", "Exit Time",
#                "Future_Entry", "Future_Exit", "Option_Entry", "Option_Exit", "Trade_Points", "Qty", "PnL", "Tax", "Net PnL"]

#     # Read the excel file
#     df = pd.read_excel(
#         file_path, sheet_name='Overnight_options', names=columns, header=0)

#     # Calculate and print the 'Tax' column
#     for index, row in df.iterrows():
#         qty = row["Qty"]
#         entry_prc = row["Future_Entry"]
#         exit_prc = row["Future_Exit"]
#         orders = 1
#         hedge_entry = row["Option_Entry"]
#         hedge_exit = row["Option_Exit"]

#         # Calculate tax using aliceblue_taxes
#         tax = zerodha_taxes(qty, hedge_entry, hedge_exit, 1)
#         futures_tax = zerodha_futures_taxes(qty, entry_prc, exit_prc, 1)

#         taxes = tax + futures_tax

#         # print(tax)
#         # print(futures_tax)
#         print(taxes)

#         # # Print the calculated tax values for each row
#         # print(f"Row {index + 1}: Taxes = {Taxes:.2f}")


# # Sample usage:
# file_path = r"C:\Users\vanis\OneDrive\Desktop\TRADEMAN\TradeMan\UserProfile\excel\brijesh.xlsx"
# calculate_and_print_tax_from_excel(file_path)
