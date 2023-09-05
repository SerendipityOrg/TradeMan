from dataclasses import dataclass

@dataclass
class Instrument:
    data: dict
    additional_tokens: list = None
    
    def get_name(self):
        return self.data["name"]

    def set_name(self, name):
        self.data["name"] = name

    def get_token(self):
        return self.data["token"]

    def set_token(self, token):
        self.data["token"] = token

    def get_next_expiry(self):
        return self.data["NextExpiry"]

    def set_next_expiry(self, next_expiry):
        self.data["NextExpiry"] = next_expiry

    def get_instru_mood(self):
        return self.data["InstruMood"]

    def set_instru_mood(self, instru_mood):
        self.data["InstruMood"] = instru_mood

    def get_option_regime(self):
        return self.data["OptionRegime"]

    def set_option_regime(self, option_regime):
        self.data["OptionRegime"] = option_regime

    def get_in_trade(self):
        return self.data["InTrade"]

    def set_in_trade(self, in_trade):
        self.data["InTrade"] = in_trade

    def get_weekday_prc_ref(self):
        return self.data["WeekdayPrcRef"]

    def set_weekday_prc_ref(self, weekday_prc_ref):
        self.data["WeekdayPrcRef"] = weekday_prc_ref

    def get_atr5d(self):
        return self.data["ATR5D"]

    def set_atr5d(self, atr5d):
        self.data["ATR5D"] = atr5d

    def get_ib_value(self):
        return self.data["IBValue"]

    def set_ib_value(self, ib_value):
        self.data["IBValue"] = ib_value

    def get_ib_level(self):
        return self.data["IBLevel"]

    def set_ib_level(self, ib_level):
        self.data["IBLevel"] = ib_level

    def get_trigger_points(self):
        return self.data["TriggerPoints"]

    def set_trigger_points(self, trigger_points):
        self.data["TriggerPoints"] = trigger_points

    def get_tsl_step_size(self):
        return self.data["TSLStepSize"]

    def set_tsl_step_size(self, tsl_step_size):
        self.data["TSLStepSize"] = tsl_step_size

    def get_signal_entry(self):
        return self.data["SignalEntry"]

    def set_signal_entry(self, signal_entry):
        self.data["SignalEntry"] = signal_entry

    # Additional getter and setter methods for the fields in SignalEntry

    def get_option(self):
        return self.data["SignalEntry"]["Option"]

    def set_option(self, option):
        self.data["SignalEntry"]["Option"] = option

    def get_event(self):
        return self.data["SignalEntry"]["Event"]

    def set_event(self, event):
        self.data["SignalEntry"]["Event"] = event

    def get_entry_time(self):
        return self.data["SignalEntry"]["EntryTime"]

    def set_entry_time(self, entry_time):
        self.data["SignalEntry"]["EntryTime"] = entry_time

    def get_entry_price(self):
        return self.data["SignalEntry"]["EntryPrice"]

    def set_entry_price(self, entry_price):
        self.data["SignalEntry"]["EntryPrice"] = entry_price

    def get_exit_time(self):
        return self.data["SignalEntry"]["ExitTime"]

    def set_exit_time(self, exit_time):
        self.data["SignalEntry"]["ExitTime"] = exit_time

    def get_exit_price(self):
        return self.data["SignalEntry"]["ExitPrice"]

    def set_exit_price(self, exit_price):
        self.data["SignalEntry"]["ExitPrice"] = exit_price