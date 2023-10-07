from pya3 import *
import datetime

alice = Aliceblue("AB068818","CBomUKElkhSmqOOIxSxeSMy49fANnfHmb5O85jkx9yTn6HhsPLlNBILrqqRQsrbaLTzK0MMFUHqOOOo2Ec5GllsLA3jdhkqHsjiEm0NqGFv7uRArn7r2gY5523Ur7M0y")
alice.get_contract_master("NFO")

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

from kiteconnect import KiteConnect

kite = KiteConnect(api_key="5q0q0q0q0q0q0q0q0q")

