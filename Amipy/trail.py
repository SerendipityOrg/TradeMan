# import json
# import pandas as pd
# from pya3 import *

# # Load the JSON data from file
# file_name = '28_Jun_23.json'
# with open(file_name, 'r') as file:
#     data = json.load(file)

# # Extract date from file name
# date = file_name.split('_')
# date = f"{date[0]}-{date[1]}-{date[2].split('.')[0]}"

# def calculate_trade_points(broker_json):
#     global date
#     rows = []
#     for broker in broker_json:
#         for user in broker_json[broker]:
#             user_data = broker_json[broker][user]
#             # date = user_data['date']
#             qty = user_data['qty']

#             # Calculate Long trade points
#             long_signal = sum(float(order['avg_prc']) for order in user_data['orders']['LongSignal'] if order['trade_type'] == 'LongSignal')
#             long_cover = sum(float(order['avg_prc']) for order in user_data['orders']['LongCoverSignal'] if order['trade_type'] == 'LongCoverSignal')
#             long_trade_points = long_cover - long_signal
#             rows.append({'User': user, 'Date': date, 'Trade_type': 'Long', 'Trade_points': long_trade_points, 'Qty': qty, 'PnL': long_trade_points * qty})

#             # Calculate Short trade points
#             short_signal = sum(float(order['avg_prc']) for order in user_data['orders']['ShortSignal'] if order['trade_type'] == 'ShortSignal')
#             short_cover = sum(float(order['avg_prc']) for order in user_data['orders']['ShortCoverSignal'] if order['trade_type'] == 'ShortCoverSignal')
#             hedge_order_short = sum(float(order['avg_prc']) for order in user_data['orders']['ShortSignal'] if order['trade_type'] == 'HedgeOrder')
#             hedge_order_cover = sum(float(order['avg_prc']) for order in user_data['orders']['ShortCoverSignal'] if order['trade_type'] == 'HedgeOrder')
#             short_trade_points = (short_signal - short_cover) - (hedge_order_short - hedge_order_cover)
#             rows.append({'User': user, 'Date': date, 'Trade_type': 'Short', 'Trade_points': short_trade_points, 'Qty': qty, 'PnL': short_trade_points * qty})

#     return pd.DataFrame(rows)


# trade_points_df = calculate_trade_points(data)
# # Write the DataFrame to a CSV file
# trade_points_df.to_csv('trade_data.csv', index=False)

# print("Data processing complete and written to trade_data.csv")

# def send_aliceblue_pnl():
#     for broker in data:
#         if broker == 'aliceblue':
#             print("Sending AliceBlue PnL")
#             for user in data[broker]:
#                 username = str(data[broker][user]['username'])
#                 api_key = data[broker][user]['api_key']
#                 alice = Aliceblue(username, api_key=api_key)
#                 session_id = alice.get_session_id()
#                 summary = alice.get_daywise_positions()
#                 print(summary)
                
#                 for i in range(len(summary)):
#                     # Get the AmiPy_PnL from the trade_points_df for this user
#                     amiPy_PnL = trade_points_df.loc[(trade_points_df['User'] == user)]['PnL'].sum()
#                     Total_PnL = summary[i]['MtoM']
#                     Difference_PnL = Total_PnL - amiPy_PnL
                    
#                     # Send the PnL details as a Telegram message
#                     message = f"AmiPy_PnL: {amiPy_PnL}\nDifference_PnL: {Difference_PnL}\nTotal_PnL: {Total_PnL}"
#                     print(message)

# send_aliceblue_pnl()


# import requests

# 1125674485744402505


