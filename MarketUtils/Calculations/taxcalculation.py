# This function calculates the taxes for Zerodha trades.
def zerodha_taxes(qty, entry_prc, exit_prc,orders):
    if orders == 1:
       instruments = 2
    elif orders == 2:
        instruments = 4
    elif orders == 3:
        instruments = 6 
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
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)  # SEBI charges are Rs. 10 / crore

    # Stamp charges
    stamp_charges = 0.003 / 100 * entry_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + transaction_charges + gst + sebi_charges + stamp_charges
# This file contains functions to calculate taxes for different brokers and different types of trades.
# It includes functions to calculate taxes for Zerodha and Aliceblue for both regular and futures trades.
# Each function takes the quantity of the instrument traded, the entry price, the exit price, and the number of orders as inputs.
# It returns the total charges for the trade.
#
# The functions calculate the brokerage, STT/CTT, transaction charges, GST, SEBI charges, and stamp charges.
# The brokerage is a flat rate per executed order.
# The STT/CTT is calculated based on the intrinsic value of the trade and the exit price.
# The transaction charges are a percentage of the exit price.
# The GST is a percentage of the sum of the brokerage, SEBI charges, and transaction charges.
# The SEBI charges are a fixed rate per crore.
# The stamp charges are a percentage of the entry price.
# The total charges are the sum of all these charges.
#
# The functions for futures trades are similar, but they use different rates for the charges.
# The brokerage is a percentage of the entry price, capped at a maximum amount.
# The STT/CTT is a percentage of the exit price.
# The transaction charges are a percentage of the exit price.
# The SEBI charges are a fixed rate per crore.
# The GST is a percentage of the sum of the brokerage, SEBI charges, and transaction charges.
# The stamp charges are a percentage of the entry price, with a minimum amount.
# The total charges are the sum of all these charges.
#
# The functions assume that the number of orders is either 1 or 2, and that the number of instruments is twice the number of orders.
# This is because each order can involve two instruments (the instrument being traded and the instrument being used to hedge).
# If the number of orders is not 1 or 2, the functions will not work correctly.
#
# Note: These functions are specific to the Indian market and may not be applicable to other markets.
# Also, the rates used in these functions are based on the rates as of the time of writing and may have changed.
# Please check the latest rates before using these functions.
#
# Author: Your Name
# Date: The current date
#
# This file is part of the TradeMan project.
# TradeMan is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TradeMan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TradeMan.  If not, see <https://www.gnu.org/licenses/>.
#
# For any questions or concerns, please email Your Email Address
#
# We welcome any and all suggestions for improvements
# Contributions on GitHub are always welcomed!
# GitHub: Your GitHub Link

    return total_charges

# This function calculates the taxes for Aliceblue trades.
def aliceblue_taxes(qty, entry_prc, exit_prc,orders):
    if orders == 1:
       instruments = 2
    elif orders == 2:
        instruments = 4
    # Brokerage
    brokerage = 15 * instruments # Flat Rs. 20 per executed order

    # STT/CTT
    intrinsic_value = max(0, exit_prc - entry_prc) * qty
    stt_on_exercise = 0.125 / 100 * intrinsic_value
    stt_on_sell = 0.0625 / 100 * exit_prc * qty

    # Transaction charges
    transaction_charges = 0.05 / 100 * exit_prc * qty
    
    # SEBI charges
    sebi_charges = 10 / 10000000 * exit_prc * qty  # Rs. 10 / crore

    # GST
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)  # SEBI charges are Rs. 10 / crore

    # Stamp charges
    stamp_charges = 0.003 / 100 * exit_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + transaction_charges + gst + sebi_charges + stamp_charges

    return total_charges

# This function calculates the taxes for Zerodha futures trades.
def zerodha_futures_taxes(qty, entry_prc, exit_prc, orders):
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

    total_charges = brokerage + stt_ctt + transaction_charges + gst + sebi_charges + stamp_charges

    return total_charges

def aliceblue_futures_taxes(qty, entry_prc, exit_prc, orders):
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

    total_charges = brokerage + stt_ctt + transaction_charges + gst + sebi_charges + stamp_charges

    return total_charges

