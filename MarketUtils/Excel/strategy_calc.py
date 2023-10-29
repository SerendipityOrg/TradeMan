import pandas as pd
import os,sys

script_dir = os.path.dirname(os.path.realpath(__file__))
utils_dir = os.path.join(script_dir, "..","calculations")
sys.path.append(utils_dir)
import taxcalculation as tc


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
            index = buy_trade["trading_symbol"][:-12]
            strike_price = buy_trade["trading_symbol"][-7:-2]
            option_type = buy_trade["trading_symbol"][-2:]
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(buy_trade["qty"], float(
                buy_trade["avg_price"]), float(sell_trade["avg_price"]), 1)
            index = buy_trade["trading_symbol"][:-13]
            strike_price = buy_trade["trading_symbol"][-5::]
            option_type = "PE" if buy_trade["trading_symbol"][-6] == "P" else "CE"

        trade_data = {
            "Trade ID": buy_trade["trade_id"],
            "Strategy": "MPWizard",
            "Index": index,
            "Strike Prc": strike_price,
            "Option Type": option_type,
            "Date": pd.to_datetime(buy_trade["time"]).strftime('%d-%b-%y'),
            "Entry Time": pd.to_datetime(buy_trade["time"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(sell_trade["time"]).strftime('%H:%M'),
            "Entry Price": buy_trade["avg_price"],
            "Exit Price": sell_trade["avg_price"],
            "Trade points": float(sell_trade["avg_price"]) - float(buy_trade["avg_price"]),
            "Qty": buy_trade["qty"],
            "PnL": round((float(sell_trade["avg_price"]) - float(buy_trade["avg_price"])) * int(buy_trade["qty"]),2),
            "Tax": round(charges,2),
            "Net PnL" : round(((float(sell_trade["avg_price"]) - float(buy_trade["avg_price"])) * int(buy_trade["qty"]) - charges),2)
        }
        result.append(trade_data)
    return result

# def custom_format(amount):
#     formatted = format_currency(amount,'INR', locale='en_IN')
#     return formatted.replace('₹','₹')

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

        trade_data = {
            "Trade ID": short_signal_group[0]["trade_id"],
            "Strategy": "Nifty Straddle",
            "Index": "NIFTY",
            "Trade Type": signal,
            "Strike Prc": short_signal_group[0]["strike_price"],
            "Date": pd.to_datetime(short_signal_group[0]["time"]).strftime('%d-%b-%y'),
            "Entry Time": pd.to_datetime(short_signal_group[0]["time"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(short_cover_signal_group[0]["time"]).strftime('%H:%M'),
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Hedge Entry": hedge_entry,
            "Hedge Exit": hedge_exit,
            "Trade points": trade_points,
            "Qty": short_signal_group[0]["qty"],
            "PnL": round(trade_points * int(short_signal_group[0]["qty"]),2),
            "Tax": round(charges,2),
            "Net PnL" : round((trade_points * int(short_signal_group[0]["qty"]) - charges),2)
        }
        result.append(trade_data)
    return result


def process_long_trades(broker,long_signals, long_cover_signals,signal):
    if len(long_signals) != len(long_cover_signals):
        print("Mismatch in the number of LongSignal and LongCoverSignal trades.")
        return []

    result = []
    for i in range(0, len(long_signals), 2):  # Process each pair of trades together
        long_signal_pair = long_signals[i:i+2]
        long_cover_signal_pair = long_cover_signals[i:i+2]

        entry_price = sum(float(trade["avg_price"])
                          for trade in long_signal_pair)
        exit_price = sum(float(trade["avg_price"])
                         for trade in long_cover_signal_pair)
        trade_points = entry_price - exit_price

        if broker == "zerodha":
            charges = tc.zerodha_taxes(
                long_signal_pair[0]["qty"], entry_price, exit_price, 2)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(
                long_signal_pair[0]["qty"], entry_price, exit_price, 2)

        trade_data = {
            "Trade ID": long_signal_pair[0]["trade_id"],
            "Strategy": "Amipy",
            "Index": "NIFTY",
            "Trade Type": signal,
            "Strike Prc": long_signal_pair[0]["strike_price"],
            "Date": pd.to_datetime(long_signal_pair[0]["time"]).strftime('%d-%b-%y'),
            "Entry Time": pd.to_datetime(long_signal_pair[0]["time"]).strftime('%H:%M'),
            "Exit Time": pd.to_datetime(long_cover_signal_pair[0]["time"]).strftime('%H:%M'),
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Hedge Entry": 0.0,
            "Hedge Exit": 0.0,
            "Trade points": trade_points,
            "Qty": long_signal_pair[0]["qty"],
            "PnL": round(trade_points * int(long_signal_pair[0]["qty"]),2),
            "Tax": round(charges,2),
            "Net PnL" : round((trade_points * int(long_signal_pair[0]["qty"]) - charges),2)
        }
        result.append(trade_data)
    return result


def process_overnight_options_trades(broker,overnight_options_trades):
    if not overnight_options_trades:
        print("No Overnight_Options trades found.")
        return []

    result = []

    # Extracting trade details from Afternoon and Morning
    afternoon_trades = overnight_options_trades.get("Afternoon", [])
    morning_trades = overnight_options_trades.get("Morning", [])
    qty = afternoon_trades[0]["qty"]
    
    if afternoon_trades[0]["direction"] == "BULLISH":
    # Extracting BULLISH trades with strike_price = 0 for both Afternoon and Morning
        future_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] == 0), None)
        future_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] == 0), None)    
    # Extracting BULLISH trades with strike_price != 0 for both Afternoon and Morning
        option_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] != 0), None)
        option_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BULLISH' and trade['strike_price'] != 0), None)
    elif afternoon_trades[0]["direction"] == "BEARISH":
    # Extracting BEARISH trades with strike_price = 0 for both Afternoon and Morning
        future_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] == 0), None)
        future_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] == 0), None)
    # Extracting BEARISH trades with strike_price != 0 for both Afternoon and Morning
        option_entry = next((float(trade['avg_price']) for trade in afternoon_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] != 0), None)
        option_exit = next((float(trade['avg_price']) for trade in morning_trades if trade['direction'] == 'BEARISH' and trade['strike_price'] != 0), None)
    
    
    if broker == "zerodha":
        future_tax = tc.zerodha_futures_taxes(qty, future_entry, future_exit, 1)
        option_tax = tc.zerodha_taxes(qty, option_entry, option_exit, 1)
        total_tax = future_tax + option_tax
    elif broker == "aliceblue":
        future_tax = tc.aliceblue_futures_taxes(qty, future_entry, future_exit, 1)
        option_tax = tc.aliceblue_taxes(qty, option_entry, option_exit, 1)
        total_tax = future_tax + option_tax

    # Calculating trade points based on direction
    direction = afternoon_trades[0]["direction"]
    if direction == "BULLISH":
        trade_points = (future_exit - future_entry) + (option_exit - option_entry)
    elif direction == "BEARISH":  # Assuming BEARISH
        trade_points = (future_entry - future_exit) + (option_exit - option_entry)
    PnL = trade_points * qty

    # Appending to result list
    trade_data = {
        "Trade ID": afternoon_trades[0]["trade_id"],
        "Strategy": "Overnight_Options",
        "Trade_Type": direction,
        "Date": pd.to_datetime(morning_trades[0]["time"]).strftime('%d-%b-%y'),
        "Entry Time": pd.to_datetime(afternoon_trades[0]["time"]).strftime('%H:%M'),
        "Exit Time": pd.to_datetime(morning_trades[0]["time"]).strftime('%H:%M'),
        "Future_Entry": future_entry,
        "Future_Exit": future_exit,
        "Option_Entry": option_entry,
        "Option_Exit": option_exit,
        "Trade_Points": trade_points,
        "Qty": qty,
        "PnL": round(PnL,2),
        "Tax": round(total_tax,2),
        "Net PnL" : round((PnL - total_tax),2)
    }
    result.append(trade_data)
    return result