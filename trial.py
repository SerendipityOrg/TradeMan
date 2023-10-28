#TODO System Wide Rules
#1 - All the non integer digits should be represented in 2 decimal places on all reports
#2 - Strategy name should be of format OvernightOptions across the entire code base including json files
#3 - All the base symbols should be in uppercase NIFTY
#4 - Strategy behaviour for order_tag in {strategy}.json file
#5 - Update the requirements.txt file



# from pya3 import *
# from pprint import pprint

# # alice = Aliceblue(user_id="BY1424",api_key="yn6YMylMSOa7Qmp9OPYhtFWSE4OL7hTMTIptvx1Odl1DkVOxqCFuboLnTCJiEd2IoEQolWY7G1JlABIkPxsvDL81hcAcOa08zszFj7DFgqPkNKGJAll3tP3OZjvmIYH6")
# alice = Aliceblue(user_id='929016',api_key='NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f')
# session = alice.get_session_id()

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

kite = KiteConnect(api_key="6b0dp5ussukmo67h",access_token='3IE37ECuWhjDlLsCPAvC41fGLmePACVl')









