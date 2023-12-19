from typing import Dict, List

from pydantic import BaseModel


class Strategy(BaseModel):
    StrategyName: str
    Description: str
    Instruments: List[str]
    NextTradeId: str
    GeneralParams: Dict[str, str]
    EntryParams: Dict[str, Dict[str, str]]
    ExitParams: Dict[str, str]
    TodayOrders: List[str]
    ExtraInformation: Dict[str, List[int]]
    SignalEntry: Dict[str, str]

    # Getter methods
    def get_strategy_name(self):
        return self.StrategyName

    def get_description(self):
        return self.Description

    def get_instruments(self):
        return self.Instruments

    def get_next_trade_id(self):
        return self.NextTradeId

    def get_general_params(self):
        return self.GeneralParams

    def get_entry_params(self):
        return self.EntryParams

    def get_exit_params(self):
        return self.ExitParams

    def get_today_orders(self):
        return self.TodayOrders

    def get_extra_information(self):
        return self.ExtraInformation

    def get_signal_entry(self):
        return self.SignalEntry

    # Setter methods
    def set_strategy_name(self, name):
        self.StrategyName = name

    def set_description(self, desc):
        self.Description = desc

    def set_instruments(self, instruments):
        self.Instruments = instruments

    def set_next_trade_id(self, trade_id):
        self.NextTradeId = trade_id

    def set_general_params(self, params):
        self.GeneralParams = params

    def set_entry_params(self, params):
        self.EntryParams = params

    def set_exit_params(self, params):
        self.ExitParams = params

    def set_today_orders(self, orders):
        self.TodayOrders = orders

    def set_extra_information(self, info):
        self.ExtraInformation = info

    def set_signal_entry(self, signal):
        self.SignalEntry = signal
