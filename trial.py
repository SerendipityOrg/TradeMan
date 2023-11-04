#TODO System Wide Rules
#1 - All the non integer digits should be represented in 2 decimal places on all reports
#2 - Strategy name should be of format OvernightOptions across the entire code base including json files
#3 - All the base symbols should be in uppercase NIFTY
#4 - Strategy behaviour for order_tag in {strategy}.json file
#5 - Update the requirements.txt file



# from pya3 import *
# from pprint import pprint

# # # alice = Aliceblue(user_id="BY1424",api_key="yn6YMylMSOa7Qmp9OPYhtFWSE4OL7hTMTIptvx1Odl1DkVOxqCFuboLnTCJiEd2IoEQolWY7G1JlABIkPxsvDL81hcAcOa08zszFj7DFgqPkNKGJAll3tP3OZjvmIYH6")
# alice = Aliceblue(user_id='929016',api_key='NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f')
# session = alice.get_session_id()

# orders = alice.get_order_history('')
# pprint(orders)

# orders = alice.get_daywise_positions()
# pprint(orders)
# overnight = []
# for order in orders:
#     if order['remarks'] == 'OF3_entry':
#         overnight.append(order)
    
# pprint(overnight)


# alice.get_instrument_by_token('NFO',67310)
# # order =  alice.place_order(transaction_type = TransactionType.Buy,
# #                      instrument = alice.get_instrument_by_token('NFO', 67310),
# #                      quantity = 50,
# #                      order_type = OrderType.Market,
# #                      product_type = ProductType.Intraday,
# #                      price = 0.0,
# #                      trigger_price = None,
# #                      stop_loss = None,
# #                      square_off = None,
# #                      trailing_sl = None,
# #                      is_amo = False,
# #                      order_tag='order1')
# # print(order)

# print(alice.get_instrument_by_token('NFO',67310))

# a = alice.get_order_history('')
# #write a to json file 
# # filepath = '/Users/amolkittur/Library/CloudStorage/OneDrive-Personal/DONOTTOUCH/excel/o.json'
# with open('order_history.json', 'w') as f:
#     json.dump(a, f, indent=4)


from kiteconnect import KiteConnect
from pprint import pprint
kite = KiteConnect(api_key="6b0dp5ussukmo67h",access_token='1T1QyNIboYIINZf7j2PzPcXrTjxf3mph')

pprint(kite.orders())

# from datetime import datetime, timedelta

# def monthly_expiry_type():
#     # Convert today to a date object to remove the time component
#     now = datetime.today()

#     today = now.date()
    
#     # Check if today is the 2nd day of the month
#     if today.day == 2:
#         return "next_month"
    
#     # Find the last day of the current month
#     last_day_of_current_month = today.replace(day=28) + timedelta(days=4)
#     last_day_of_current_month -= timedelta(days=last_day_of_current_month.day)
    
#     # Find the last Thursday of the current month
#     last_thursday_of_current_month = last_day_of_current_month
#     while last_thursday_of_current_month.weekday() != 3:
#         last_thursday_of_current_month -= timedelta(days=1)
    
#     # Find the first Thursday of the next month
#     first_day_of_next_month = last_day_of_current_month + timedelta(days=1)
#     days_until_thursday = (3 - first_day_of_next_month.weekday() + 7) % 7
#     first_thursday_of_next_month = first_day_of_next_month + timedelta(days=days_until_thursday)
    
#     # Find the first day of the last week of the current month
#     first_day_of_last_week_of_current_month = last_day_of_current_month - timedelta(days=last_day_of_current_month.weekday())
    
#     # Print relevant dates for debugging
#     print("Today:", today)
#     print("Last Thursday of Current Month:", last_thursday_of_current_month)
#     print("First Thursday of Next Month:", first_thursday_of_next_month)
#     print("First Day of Last Week of Current Month:", first_day_of_last_week_of_current_month)
    
#     # Check the conditions
#     if today >= first_day_of_last_week_of_current_month or (today > last_thursday_of_current_month and today < first_thursday_of_next_month):
#         return "next_month"
#     else:
#         return "current_month"

# result = monthly_expiry_type()


# print(result)


