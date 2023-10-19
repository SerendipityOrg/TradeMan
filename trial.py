# from pya3 import *
# from pprint import pprint

# alice = Aliceblue(user_id="929016",api_key="NRmFZkHUFYn08WrOT340eRGR5Sh4NdQ3arVBEak3UvgimY91CftfTWvx9QRXYLAtgCFFkrKQ1ax5yTaPKINLYLiLK48YziRLHFv84lf1v8hKWlBjclQhggNXJaj5h67f")
# alice.get_session_id()
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

#TODO System Wide Rules
#1 - All the non integer digits should be represented in 2 decimal places on all reports
#2 - Strategy name should be of format OvernightOptions across the entire code base including json files
#3 - All the base symbols should be in uppercase NIFTY
#4 - Strategy behaviour for order_tag in {strategy}.json file


from Brokers.place_order import place_order_for_strategy
from Brokers.instrument_monitor import InstrumentMonitor


order_details =  {'strategy': 'MPWizard', 'exchange_token': 67300, 'segment': 'NFO', 'transaction_type': 'SELL', 'order_type': 'Stoploss', 'product_type': 'MIS', 'order_mode': ['Main', 'TSL'], 'price_ref': 18, 'trade_id': 'MPW1', 'broker': 'aliceblue', 'username': 'vimala', 'qty': 1500, 'limit_prc': 18.1, 'trigger_prc': 17.1}
place_order_for_strategy('MPWizard',[order_details])