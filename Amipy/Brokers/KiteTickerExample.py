###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Zerodha Technology Pvt. Ltd.
#
# This example shows how to subscribe and get ticks from Kite Connect ticker,
# For more info read documentation - https://kite.trade/docs/connect/v1/#streaming-websocket
###############################################################################

import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

acctkn_file = r'Brokers\acc_token.txt'
reqtkn_file = r'Brokers\req_token.txt'
kite_access_token = open(acctkn_file,'r').read()
kite_request_token = open(reqtkn_file,'r').read()

# Initialise
kws = KiteTicker("6b0dp5ussukmo67h", kite_access_token)

def on_ticks(ws, ticks):  # noqa
    # Callback to receive ticks.
    logging.info("Ticks: {}".format(ticks))

def on_connect(ws, response):  # noqa
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([11848450, 11848706])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP, [11848450,11848706])

def on_order_update(ws, data):
    logging.debug("Order update : {}".format(data))

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_order_update = on_order_update

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()