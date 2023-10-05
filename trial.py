# # import discord
# # import os
# # from discord.ext import commands
# # import asyncio

# # client = commands.Bot(command_prefix = '=',intents=discord.Intents.all())

# # @client.event
# # async def on_ready():
# #     await client.tree.sync()
# #     print('Bot is ready.')

# # async def load():
# #     for filename in os.listdir('./cogs'):
# #         if filename.endswith('.py'):
# #             client.load_extension(f'cogs.{filename[:-3]}')

# # class TestMenuButton(discord.ui.View):
# #     def __init__(self):
# #         super().__init__(timeout=None)

# #     @discord.ui.button(label='Test', style=discord.ButtonStyle.blurple)
# #     async def test(self, interaction:discord.Interaction, Button:discord.ui.Button):
# #         await interaction.channel.send(content='Test')
# #     @discord.ui.button(label='Test2', style=discord.ButtonStyle.green)
# #     async def test2(self, interaction:discord.Interaction, Button:discord.ui.Button):
# #         await interaction.channel.send(content='Test2')
# #     @discord.ui.button(label='Test3', style=discord.ButtonStyle.red)
# #     async def test3(self, interaction:discord.Interaction, Button:discord.ui.Button):
# #         await interaction.channel.send(content='Test3')

# # @client.tree.command(name='buttonmenu')
# # async def buttonmenu(interaction: discord.Interaction):
# #     await interaction.response.send_message(content='Here is the button menu!', view=TestMenuButton())

# # async def main():
# #     async with client:
# #         await client.start('MTEyODk0NjM1ODM2ODM1ODU1MQ.GXdOeu.lR7IU7OB8AqhSySBMde6oQas5P0AUzys1HpF5k')

# # asyncio.run(main())

# # from kiteconnect import KiteConnect
# # from pprint import pprint

# # api_key = '6b0dp5ussukmo67h'
# # api_secret = 'eln2qrqob5neowjuedmbv0f0hzq6lhby'
# # kite = KiteConnect(api_key=api_key)
# # # print(kite.login_url())
# # data = kite.generate_session('dVSA80jTIZy8wQ4t90Sz2sDmELz9w2fL', api_secret=api_secret)
# # print(data)
# # print(kite.set_access_token(data["access_token"]))


# #update ChromeDriver


# from pya3 import *

# alice = Aliceblue("929016",'NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f')
# alice.get_session_id()
# print(alice.get_order_history(''))

# # order_id = alice.place_order(transaction_type = TransactionType.Buy,
# #                     instrument =alice.get_instrument_for_fno(exch="NFO",symbol='BANKNIFTY', expiry_date="2023-09-13", is_fut=False,strike=44500, is_CE=False),
# #                     quantity = 15,
# #                     order_type = OrderType.Market,
# #                     product_type = ProductType.Intraday,
# #                     price=0.0,
# #                     trigger_price = 0.0)


# # order_id_value = order_id.get('NOrdNo')
# # print(order_id_value)
# # avg_prc_data = alice.get_order_history(order_id_value)
# # avg_prc = avg_prc_data.get('AvgPrice')

# # print(avg_prc)


# # output flowchart code.


# from pya3 import *
# import datetime

# alice = Aliceblue("AB068818","CBomUKElkhSmqOOIxSxeSMy49fANnfHmb5O85jkx9yTn6HhsPLlNBILrqqRQsrbaLTzK0MMFUHqOOOo2Ec5GllsLA3jdhkqHsjiEm0NqGFv7uRArn7r2gY5523Ur7M0y")


# alice.get_session_id()
# # trade = Instrument(exchange='NFO', token=57640, symbol='FINNIFTY', name='FINNIFTY26SEP23P20300', expiry=datetime.date(2023, 9, 26), lot_size=50)
# # trading_symbol = Instrument(exchange='NFO', token=86000, symbol='BANKNIFTY', name='BANKNIFTY28SEP23P45000', expiry='', lot_size=15)
# # print(trading_symbol)
# print(alice.get_scrip_info(alice.get_instrument_by_token('NSE', 11536)))

# # print(
# #    alice.place_order(transaction_type = TransactionType.Sell,
# #                      instrument = trade,
# #                      quantity = 15,
# #                      order_type = OrderType.StopLossLimit,
# #                      product_type = ProductType.Intraday,
# #                      price=15.00,
# #                      trigger_price = 16.0)
# # )

# from Brokers import instrument_monitor

# monitor = instrument_monitor.InstrumentMonitor()

# ltp = monitor._fetch_ltp_for_token(11536)

import pandas as pd


def zerodha_taxes(qty, entry_prc, exit_prc, orders):
    print(qty)
    print(entry_prc)
    print(exit_prc)

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
    columns = ["Tr no", "Strategy", "Index", "Strike Price", "Option Type", "Date", "Entry Time", "Exit Time",
               "Entry Price", "Exit Price", "Trade points", "Qty", "PnL", "Tax", "Net PnL"]
    df = pd.read_excel(file_path, sheet_name='MPWizard',
                       names=columns, header=1)

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
file_path = r"C:\Users\vanis\Downloads\venkatesh (2).xlsx"
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
