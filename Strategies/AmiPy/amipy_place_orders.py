import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

import MarketUtils.InstrumentBase as InstrumentBase
import Strategies.StrategyBase as StrategyBase
import Brokers.place_order_calc as place_order_calc
import Brokers.place_order as place_order

_,STRATEGY_PATH = place_order_calc.get_strategy_json('AmiPy')

instrument_obj = InstrumentBase.Instrument()
strategy_obj = StrategyBase.Strategy.read_strategy_json(STRATEGY_PATH)


def place_orders(strike_prc, signal):
    strategy_name = strategy_obj.get_strategy_name()
    segment_type = strategy_obj.get_general_params().get("Segment")
    order_type = strategy_obj.get_general_params().get("OrderType")
    product_type = strategy_obj.get_general_params().get("ProductType")

    base_symbol = strategy_obj.get_instruments()[0]
    expiry_date = instrument_obj.get_expiry_by_criteria(base_symbol, strike_prc, "CE", "current_week")

    orders_to_place = []
    
    if "Short" in signal:
        hedge_ce_strike_prc = strike_prc + strategy_obj.get_extra_information().get("HedgeDistance")
        hedge_pe_strike_prc = strike_prc - strategy_obj.get_extra_information().get("HedgeDistance")

        hedge_CE_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol, hedge_ce_strike_prc, "CE", expiry_date)
        hedge_PE_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol, hedge_pe_strike_prc, "PE", expiry_date)

        hedge_orders = [
            {"exchange_token": hedge_CE_exchange_token, "order_mode": ["Hedge"]},
            {"exchange_token": hedge_PE_exchange_token, "order_mode": ["Hedge"]}
        ]
        orders_to_place.extend(hedge_orders)
        hedge_transaction_type = "BUY" if "ShortSignal" in signal else "SELL"
        main_transaction_type = "SELL" if "ShortSignal" in signal else "BUY"
    
    else:  # Long Orders
        main_transaction_type = "BUY" if "LongSignal" in signal else "SELL"
        hedge_transaction_type = None  # No hedge orders for long positions

    main_CE_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol, strike_prc, "CE", expiry_date)
    main_PE_exchange_token = instrument_obj.get_exchange_token_by_criteria(base_symbol, strike_prc, "PE", expiry_date)

    main_orders = [
        {"exchange_token": main_CE_exchange_token, "order_mode": ["Main"]},
        {"exchange_token": main_PE_exchange_token, "order_mode": ["Main"]}
    ]
    orders_to_place.extend(main_orders)

    trade_type  = "entry" if signal == "ShortSignal" or signal == "LongSignal" else "exit"
    trade_id = place_order_calc.get_trade_id(strategy_name, trade_type)

    for order in orders_to_place:
        transaction_type = hedge_transaction_type if "Hedge" in order['order_mode'] else main_transaction_type
        order.update({
            "strategy": strategy_name,
            "segment": segment_type,
            "transaction_type": transaction_type,
            "order_type": order_type,
            "product_type": product_type,
            "trade_id": trade_id
        })
    # print(orders_to_place)
    place_order.place_order_for_strategy(strategy_name, orders_to_place)
