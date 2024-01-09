def zerodha_taxes(qty, entry_prc, exit_prc, orders):
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4
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

    # SEBI charges are Rs. 10 / crore
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges = 0.003 / 100 * entry_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + transaction_charges + gst + sebi_charges + stamp_charges

    return total_charges

def aliceblue_taxes(qty, entry_prc, exit_prc, orders):
    if orders == 1:
        instruments = 2
    elif orders == 2:
        instruments = 4
    # Brokerage
    brokerage = 15 * instruments  # Flat Rs. 20 per executed order

    # STT/CTT
    intrinsic_value = max(0, exit_prc - entry_prc) * qty
    stt_on_exercise = 0.125 / 100 * intrinsic_value
    stt_on_sell = 0.0625 / 100 * exit_prc * qty

    # Transaction charges
    transaction_charges = 0.05 / 100 * exit_prc * qty

    # SEBI charges
    sebi_charges = 10 / 10000000 * exit_prc * qty  # Rs. 10 / crore

    # GST
    gst = 18 / 100 * (brokerage + sebi_charges + transaction_charges)

    # Stamp charges
    stamp_charges = 0.003 / 100 * exit_prc * qty

    total_charges = brokerage + stt_on_exercise + stt_on_sell + transaction_charges + gst + sebi_charges + stamp_charges

    return total_charges

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
