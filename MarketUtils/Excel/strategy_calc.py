import pandas as pd
import os,sys
from pprint import pprint


DIR = os.getcwd()
sys.path.append(DIR)
import MarketUtils.Calculations.taxcalculation as tc

def process_mpwizard_trades(broker,mpwizard_trades):
    if not mpwizard_trades:
        print("No MPWizard trades found.")
        return []

    result = []
    # Extracting trade details
    for i in range(len(mpwizard_trades["BUY"])):
        buy_trade = mpwizard_trades["BUY"][i]
        sell_trade = mpwizard_trades["SELL"][i]

        if broker == "zerodha":
            charges = tc.zerodha_taxes(
                buy_trade["qty"], buy_trade["avg_price"], sell_trade["avg_price"], 1)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(buy_trade["qty"], float(
                buy_trade["avg_price"]), float(sell_trade["avg_price"]), 1)
        trade_points = float(sell_trade["avg_price"]) - float(buy_trade["avg_price"])
        pnl = trade_points * int(buy_trade["qty"])
        net_pnl = pnl - charges
        signal = "Long"

        entry_time = pd.to_datetime(buy_trade["time"], format='%d/%m/%Y %H:%M:%S').round('min')
        exit_time = pd.to_datetime(sell_trade["time"], format='%d/%m/%Y %H:%M:%S').round('min')

        trade_data = {
                "trade_id": buy_trade["trade_id"],
                "trading_symbol": buy_trade["trading_symbol"],
                "signal": signal,
                "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                "entry_price": round(buy_trade["avg_price"],2),
                "exit_price": round(sell_trade["avg_price"],2),
                "hedge_entry_price": 0,  # Assuming no hedge for this example
                "hedge_exit_price": 0,   # Assuming no hedge for this example
                "trade_points": round(trade_points,2),
                "qty": buy_trade["qty"],
                "pnl": round(pnl,2),
                "tax": round(charges,2),
                "net_pnl": round(net_pnl,2)
            } 
        result.append(trade_data)
    return result

def process_amipy_trades(broker,amipy_trades):
    amipy_data_short = []
    amipy_data_long = []
    if "ShortSignal" in amipy_trades:
        # Process the AmiPy ShortSignal and ShortCoverSignal trades
        amipy_data_short = process_short_trades(broker,amipy_trades["ShortSignal"],
                                                amipy_trades["ShortCoverSignal"],"Short")
    if "LongSignal" in amipy_trades:
        # Process the AmiPy LongSignal and LongCoverSignal trades
        amipy_data_long = process_long_trades(broker,amipy_trades["LongSignal"],
                                                amipy_trades["LongCoverSignal"],"Long")
    if amipy_data_short is not None:
        return amipy_data_short
    elif amipy_data_long is not None:
        return amipy_data_long
    
def process_short_trades(broker,short_signals, short_cover_signals,signal):
    if len(short_signals) != len(short_cover_signals):
        print("Mismatch in the number of ShortSignal and ShortCoverSignal trades.")
        return []

    result = []
    for i in range(0, len(short_signals), 4):  # Process each group of 4 trades together
        short_signal_group = short_signals[i:i+4]
        short_cover_signal_group = short_cover_signals[i:i+4]

        hedge_entry = sum(float(
            trade["avg_price"]) for trade in short_signal_group if trade["trade_type"] == "HedgeOrder")
        hedge_exit = sum(float(
            trade["avg_price"]) for trade in short_cover_signal_group if trade["trade_type"] == "HedgeOrder")

        entry_price = sum(float(
            trade["avg_price"]) for trade in short_signal_group if trade["trade_type"] == "ShortSignal")
        exit_price = sum(float(
            trade["avg_price"]) for trade in short_cover_signal_group if trade["trade_type"] == "ShortCoverSignal")
        hedge_price = hedge_exit - hedge_entry
        trade_points = (entry_price - exit_price) + hedge_price
        

        if broker == "zerodha":
            charges = tc.zerodha_taxes(
                short_signal_group[0]["qty"], entry_price, exit_price, 2)
            hedge_charges = tc.zerodha_taxes(
                short_signal_group[0]["qty"], hedge_entry, hedge_exit, 2)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(
                short_signal_group[0]["qty"], entry_price, exit_price, 2)
            hedge_charges = tc.aliceblue_taxes(
                short_signal_group[0]["qty"], hedge_entry, hedge_exit, 2)
        charges = charges + hedge_charges

        entry_time = pd.to_datetime(short_signal_group[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')
        exit_time = pd.to_datetime(short_cover_signal_group[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')

        trade_data = {
            "trade_id": short_signal_group[0]["trade_id"],
            "trading_symbol Symbol": short_signal_group[0]["trading_symbol"],
            "signal": signal,
            "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            "entry_price": round(entry_price,2),
            "exit_price": round(exit_price,2),
            "hedge_entry_price": round(hedge_entry,2),
            "hedge_exit_price": round(hedge_exit,2),
            "trade_points": round(trade_points,2),
            "qty": short_signal_group[0]["qty"],
            "pnl": round(trade_points * int(short_signal_group[0]["qty"]),2),
            "tax": round(charges,2),
            "net_pnl" : round((trade_points * int(short_signal_group[0]["qty"]) - charges),2)
        }           
        result.append(trade_data)
    return result


def process_long_trades(broker,long_signals, long_cover_signals,signal):
    if len(long_signals) != len(long_cover_signals):
        print("Mismatch in the number of LongSignal and LongCoverSignal trades.")
        return []

    result = []
    for i in range(0, len(long_signals), 2):  # Process each pair of trades together
        long_signal_group = long_signals[i:i+2]
        long_cover_signal_group = long_cover_signals[i:i+2]

        entry_price = sum(float(trade["avg_price"])
                          for trade in long_signal_group)
        exit_price = sum(float(trade["avg_price"])
                         for trade in long_cover_signal_group)
        trade_points = entry_price - exit_price

        if broker == "zerodha":
            charges = tc.zerodha_taxes(
                long_signal_group[0]["qty"], entry_price, exit_price, 2)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(
                long_signal_group[0]["qty"], entry_price, exit_price, 2)

        entry_time = pd.to_datetime(long_signal_group[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')
        exit_time = pd.to_datetime(long_cover_signal_group[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')

        trade_data = {
            "trade_id": long_signal_group[0]["trade_id"],
            "trading_symbol": long_signal_group[0]["trading_symbol"],
            "signal": signal,
            "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            "entry_price": round(entry_price,2),
            "entry_price": round(exit_price,2),
            "hedge_entry_price": 0,
            "hedge_exit_price": 0,
            "trade_points": round(trade_points,2),
            "qty": long_signal_group[0]["qty"],
            "pnl": round(trade_points * int(long_signal_group[0]["qty"]),2),
            "tax": round(charges,2),
            "net_pnl" : round((trade_points * int(long_signal_group[0]["qty"]) - charges),2)
        }
        result.append(trade_data)
    return result





def process_expiry_trades(broker, expiry_trades):
    if not expiry_trades:
        print("No ExpiryTrades trades found.")
        return []

    result = []
    trade_ids = set(trade["trade_id"] for trade in expiry_trades["Entry"])

    for trade_id in trade_ids:
        entry_trades = [trade for trade in expiry_trades["Entry"] if trade["trade_id"] == trade_id]
        exit_trades = [trade for trade in expiry_trades["Exit"] if trade["trade_id"] == trade_id]

        main_entry = next((trade for trade in entry_trades if trade["trade_type"] == "MainOrder"), None)
        hedge_entry = next((trade for trade in entry_trades if trade["trade_type"] == "HedgeOrder"), None)
        main_exit = next((trade for trade in exit_trades if trade["trade_type"] == "MainOrder"), None)
        hedge_exit = next((trade for trade in exit_trades if trade["trade_type"] == "HedgeOrder"), None)

        if broker == "zerodha":
            charges = tc.zerodha_taxes(main_entry["qty"], float(main_entry["avg_price"]), float(main_exit["avg_price"]), 1)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(main_entry["qty"], float(main_entry["avg_price"]), float(main_exit["avg_price"]), 1)
        else:
            charges = 0  # No charges if broker is not recognized

        main_trade_points = float(main_exit["avg_price"]) - float(main_entry["avg_price"])
        hedge_trade_points = float(hedge_exit["avg_price"]) - float(hedge_entry["avg_price"]) if hedge_entry else 0
        trade_points = main_trade_points - hedge_trade_points
        pnl = trade_points * main_entry["qty"]
        net_pnl = pnl - charges

        # Parse dates with the correct format
        entry_time = pd.to_datetime(main_entry["time"], format='%d/%m/%Y %H:%M:%S').round('min')
        exit_time = pd.to_datetime(main_exit["time"], format='%d/%m/%Y %H:%M:%S').round('min')

        trade_data = {
            "trade_id": trade_id,
            "trading_symbol": main_entry["trading_symbol"],
            "signal": "Short",
            "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            "entry_price": round(float(main_entry["avg_price"]), 2),
            "exit_price": round(float(main_exit["avg_price"]), 2),
            "hedge_entry_price": round(float(hedge_entry["avg_price"]), 2) if hedge_entry else 0,
            "hedge_exit_price": round(float(hedge_exit["avg_price"]), 2) if hedge_exit else 0,
            "trade_points": round(trade_points, 2),
            "qty": main_entry["qty"],
            "pnl": round(pnl, 2),
            "tax": round(charges, 2),
            "net_pnl": round(net_pnl, 2)
        }

        result.append(trade_data)

    return result


def process_overnight_futures_trades(afternoon_trade_details, morning_trade_details, broker,entry_trade=None):
    # Initialize the results list, which will contain up to two dictionaries
    result = []

    # If there are details for a morning trade, process them
    if morning_trade_details:
        for trade in morning_trade_details:

            if trade['option_type'] != "FUT":
                option_exit_price = trade['avg_price']
            else:
                future_exit_price = trade['avg_price']

        qty = trade['qty']

        if broker == "zerodha":
            future_tax = tc.zerodha_futures_taxes(qty, entry_trade['entry_price'], future_exit_price, 1)
            option_tax = tc.zerodha_taxes(qty, entry_trade["hedge_entry_price"],option_exit_price, 1)
        elif broker == "aliceblue":
            future_tax = tc.aliceblue_futures_taxes(qty, entry_trade["entry_price"], future_exit_price, 1)
            option_tax = tc.aliceblue_taxes(qty, entry_trade["hedge_entry_price"], option_exit_price, 1)
        # Calculating trade points based on direction
        direction = entry_trade["signal"]
        if direction == "Long":
            trade_points = (entry_trade["entry_price"] - future_exit_price) + (entry_trade["hedge_entry_price"] - option_exit_price)
        elif direction == "Short":  
            trade_points = (future_exit_price - entry_trade["entry_price"]) + (option_exit_price - entry_trade["hedge_entry_price"])
        pnl = trade_points * qty

        exit_time = pd.to_datetime(morning_trade_details[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')
        
        # Construct the morning trade data dictionary
        trade_data_morning = {
            "trade_id": morning_trade_details[0]["trade_id"],
            "exit_time": exit_time,
            "exit_price": future_exit_price,
            "hedge_exit_price": option_exit_price,
            "pnl": pnl,
            "trade_points": trade_points,
            "tax": future_tax + option_tax,
            "net_pnl": pnl - (future_tax + option_tax)
        }
        # Add the morning trade data to the result list
        result.append(trade_data_morning)

    # If there are details for an afternoon trade, process them
    if afternoon_trade_details:
        signal = "Long" if afternoon_trade_details[0]['direction'] == "BULLISH" else "Short"

        for trade in afternoon_trade_details:
            if trade['option_type'] != "FUT":
                option_entry_price = trade['avg_price']

            else:
                future_entry_price = trade['avg_price']
                trading_symbol = trade['trading_symbol']
                trade_id = trade['trade_id']
                qty = trade['qty']
                entry_time = pd.to_datetime(trade['time'], format='%d/%m/%Y %H:%M:%S').round('min')

        # Here you might not have all the data to calculate PnL, tax, and net PnL
        # Since it's a new trade, the exit details are not known yet
        trade_data_afternoon = {
            "trade_id": trade_id,
            "trading_symbol": trading_symbol,  # Assuming the trading symbol is the same as the morning trade
            "signal": signal,
            "entry_time": entry_time,
            "entry_price": future_entry_price,
            "hedge_entry_price": option_entry_price,
            "qty": qty
            # ...
        }
        # Add the afternoon trade data to the result list
        result.append(trade_data_afternoon)

    # Return the list of trade data dictionaries
    return result


# def process_overnight_futures_trades(broker,overnight_futures_trades):
#     if not overnight_futures_trades:
#         print("No Overnight_Options trades found.")
#         return []

#     result = []

#     # Extracting trade details from Afternoon and Morning
#     afternoon_trades = overnight_futures_trades.get("Afternoon", [])
#     morning_trades = overnight_futures_trades.get("Morning", [])
#     qty = afternoon_trades[0]["qty"]
    
#     if afternoon_trades[0]["direction"] == "BULLISH":
#     # Extracting BULLISH trades with strike_price = 0 for both Afternoon and Morning
#         future_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] == 0), None)
#         future_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] == 0), None)    
#     # Extracting BULLISH trades with strike_price != 0 for both Afternoon and Morning
#         option_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] != 0), None)
#         option_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] != 0), None)
#     elif afternoon_trades[0]["direction"] == "BEARISH":
#     # Extracting BEARISH trades with strike_price = 0 for both Afternoon and Morning
#         future_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] == 0), None)
#         future_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] == 0), None)
#     # Extracting BEARISH trades with strike_price != 0 for both Afternoon and Morning
#         option_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] != 0), None)
#         option_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] != 0), None)
    
    
#     if broker == "zerodha":
#         future_tax = tc.zerodha_futures_taxes(qty, future_entry, future_exit, 1)
#         option_tax = tc.zerodha_taxes(qty, option_entry, option_exit, 1)
#         total_tax = future_tax + option_tax
#     elif broker == "aliceblue":
#         future_tax = tc.aliceblue_futures_taxes(qty, future_entry, future_exit, 1)
#         option_tax = tc.aliceblue_taxes(qty, option_entry, option_exit, 1)
#         total_tax = future_tax + option_tax

#     # Calculating trade points based on direction
#     direction = afternoon_trades[0]["direction"]
#     if direction == "BULLISH":
#         trade_points = (future_exit - future_entry) + (option_exit - option_entry)
#     elif direction == "BEARISH":  # Assuming BEARISH
#         trade_points = (future_entry - future_exit) + (option_exit - option_entry)
#     PnL = trade_points * qty
#     signal = "Long" if direction == "BULLISH" else "Short"

#     entry_time = pd.to_datetime(afternoon_trades[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')
#     exit_time = pd.to_datetime(morning_trades[0]["time"], format='%d/%m/%Y %H:%M:%S').round('min')

#     # Appending to result list
#     trade_data = {
#             "trade_id": afternoon_trades[0]["trade_id"],
#             "trading_symbol": afternoon_trades[0]["trading_symbol"],
#             "signal": signal,
#             "entry_time": entry_time.strftime('%Y-%m-%d %H:%M:%S'),
#             "exit_time": exit_time.strftime('%Y-%m-%d %H:%M:%S'),
#             "entry_price": round(future_entry,2) ,
#             "exit_price": round(future_exit,2) ,
#             "hedge_entry_price": round(option_entry,2),
#             "hedge_exit_price": round(option_exit,2),
#             "trade_points": round(trade_points,2),
#             "qty": qty,
#             "pnl": round(PnL,2),
#             "tax": round(total_tax,2),
#             "net_pnl": round((PnL - total_tax),2)
#         }
#     result.append(trade_data)
#     return result