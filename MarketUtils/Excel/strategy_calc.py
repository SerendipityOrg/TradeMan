import pandas as pd
import os,sys

script_dir = os.path.dirname(os.path.realpath(__file__))
utils_dir = os.path.join(script_dir, "..","Calculations")
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
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(buy_trade["qty"], float(
                buy_trade["avg_price"]), float(sell_trade["avg_price"]), 1)
        trade_points = float(sell_trade["avg_price"]) - float(buy_trade["avg_price"])
        pnl = trade_points * int(buy_trade["qty"])
        net_pnl = pnl - charges
        signal = "LongSignal"

        trade_data = {
                "trade_id": buy_trade["trade_id"],
                "trading_symbol": buy_trade["trading_symbol"],
                "signal": signal,
                "entry_time": pd.to_datetime(buy_trade["time"]).strftime('%d-%b-%y %H:%M'),
                "exit_time": pd.to_datetime(sell_trade["time"]).strftime('%d-%b-%y %H:%M'),
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

        trade_data = {
            "trade_id": short_signal_group[0]["trade_id"],
            "trading_symbol Symbol": short_signal_group[0]["trading_symbol"],
            "signal": signal,
            "entry_time": pd.to_datetime(short_signal_group[0]["time"]).strftime('%d-%b-%y %H:%M'),
            "exit_time": pd.to_datetime(short_cover_signal_group[0]["time"]).strftime('%d-%b-%y %H:%M'),
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

        trade_data = {
            "trade_id": long_signal_group[0]["trade_id"],
            "trading_symbol": long_signal_group[0]["trading_symbol"],
            "signal": signal,
            "entry_time": pd.to_datetime(long_signal_group[0]["time"]).strftime('%d-%b-%y %H:%M'),
            "exit_time": pd.to_datetime(long_cover_signal_group[0]["time"]).strftime('%d-%b-%y %H:%M'),
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


def process_overnight_futures_trades(broker,overnight_futures_trades):
    if not overnight_futures_trades:
        print("No Overnight_Options trades found.")
        return []

    result = []

    # Extracting trade details from Afternoon and Morning
    afternoon_trades = overnight_futures_trades.get("Afternoon", [])
    morning_trades = overnight_futures_trades.get("Morning", [])
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
    signal = "LongSignal" if direction == "BULLISH" else "ShortSignal"
    # Appending to result list
    trade_data = {
            "trade_id": afternoon_trades[0]["trade_id"],
            "trading_symbol": afternoon_trades[0]["trading_symbol"],
            "signal": signal,
            "entry_time": pd.to_datetime(afternoon_trades[0]["time"]).strftime('%d-%b-%y %H:%M'),
            "exit_time": pd.to_datetime(morning_trades[0]["time"]).strftime('%d-%b-%y %H:%M'),
            "entry_price": round(future_entry,2) ,
            "exit_price": round(future_exit,2) ,
            "hedge_entry_price": round(option_entry,2),
            "hedge_exit_price": round(option_exit,2),
            "trade_points": round(trade_points,2),
            "qty": qty,
            "pnl": round(PnL,2),
            "tax": round(total_tax,2),
            "net_pnl": round((PnL - total_tax),2)
        }
    result.append(trade_data)
    return result


def process_expiry_trades(broker, expiry_trades):
    if not expiry_trades:
        print("No ExpiryTrades trades found.")
        return []

    result = []
    trade_ids = set(trade["trade_id"] for trade in expiry_trades["SELL"])
    
    for trade_id in trade_ids:
        sell_trades = [trade for trade in expiry_trades["SELL"] if trade["trade_id"] == trade_id]
        buy_trades = [trade for trade in expiry_trades["BUY"] if trade["trade_id"] == trade_id]
        
        regular_sell = next((trade for trade in sell_trades if trade["trade_type"] == "SELL"), None)
        hedge_sell = next((trade for trade in sell_trades if trade["trade_type"] == "HedgeOrder"), None)
        regular_buy = next((trade for trade in buy_trades if trade["trade_type"] == "BUY"), None)
        hedge_buy = next((trade for trade in buy_trades if trade["trade_type"] == "HedgeOrder"), None)
        
        if broker == "zerodha":
            charges = tc.zerodha_taxes(regular_sell["qty"], float(regular_sell["avg_price"]), float(regular_buy["avg_price"]), 1)
        elif broker == "aliceblue":
            charges = tc.aliceblue_taxes(regular_sell["qty"], float(regular_sell["avg_price"]), float(regular_buy["avg_price"]), 1)
            
        hedge_entry = float(hedge_sell["avg_price"]) if hedge_sell else 0
        hedge_exit = float(hedge_buy["avg_price"]) if hedge_buy else 0
        
        trade_points = (float(regular_sell["avg_price"]) - float(regular_buy["avg_price"])) - (hedge_exit - hedge_entry)
        pnl = trade_points * regular_sell["qty"] 
        net_pnl = pnl - charges

        trade_data = {
            "trade_id": trade_id,
            "trading_symbol": regular_sell["trading_symbol"],
            "signal": "SELL",
            "entry_time": pd.to_datetime(regular_sell["time"]).strftime('%d-%b-%y %H:%M'),
            "exit_time": pd.to_datetime(regular_buy["time"]).strftime('%d-%b-%y %H:%M'),
            "entry_price": round(float(regular_sell["avg_price"]),2),
            "exit_price": round(float(regular_buy["avg_price"]),2),
            "hedge_entry_price": round(hedge_entry,2),
            "hedge_exit_price": round(hedge_exit,2),
            "trade_points": round(trade_points,2),
            "qty": regular_sell["qty"],
            "pnl": round(pnl,2),
            "tax": round(charges,2),
            "net_pnl": round(net_pnl,2)
        }

        result.append(trade_data)
        
    return result
