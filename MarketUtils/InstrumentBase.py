import pandas as pd
import os

DIR_PATH = os.getcwd()
insrument_csv_path = os.path.join(DIR_PATH,'instruments.csv')

from datetime import datetime
from calendar import monthrange

from datetime import timedelta  # Importing the missing timedelta

class Instrument:
    def __init__(self, csv_path=insrument_csv_path):
        self._dataframe = pd.read_csv(csv_path)
        self._instrument_token = None
        self._exchange_token = None

    def _filter_data(self, base_symbol, option_type, strike_price, expiry=None):
        """Filter the dataframe based on the given criteria."""
        criteria = (
            (self._dataframe['name'] == base_symbol) &
            (self._dataframe['instrument_type'] == option_type) &
            (self._dataframe['strike'] == strike_price)
        )
        if expiry:
            criteria &= (self._dataframe['expiry'] == expiry)
        return self._dataframe[criteria].sort_values(by='expiry')
    
    def _filter_data_by_exchange_token(self, exchange_token):
        """Filter the dataframe based on the given exchange token."""
        return self._dataframe[self._dataframe['exchange_token'] == exchange_token]


    def _get_monthly_expiries(self, filtered_data, option_type):
        """Identify and return monthly expiry dates from the filtered data."""
        monthly_expiries = []
        if option_type == "FUT":  # Only consider as monthly expiry for FUT type
            for expiry in filtered_data['expiry'].unique():
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                if expiry_date.day > (monthrange(expiry_date.year, expiry_date.month)[1] - 7):
                    monthly_expiries.append(expiry)
        return monthly_expiries

    def _get_last_weekly_expiry(self, weekly_expiries, target_month):
        """Return the last weekly expiry of the target month."""
        return max([expiry for expiry in weekly_expiries if datetime.strptime(expiry, "%Y-%m-%d").date().month == target_month])
    
    def weekly_expiry_type(self):
        if datetime.today().weekday() == 3:
            weekly_expiry_type = "next_week"
        else:
            weekly_expiry_type = "current_week"
        return weekly_expiry_type

    def monthly_expiry_type(self):
        today = datetime.today()
        # Find the last day of the previous month
        last_day_of_previous_month = today.replace(day=1) - timedelta(days=1)

        # Find the last Thursday of the previous month
        last_thursday_of_previous_month = last_day_of_previous_month
        while last_thursday_of_previous_month.weekday() != 3:
            last_thursday_of_previous_month -= timedelta(days=1)

        # If today is before the last Thursday of the previous month
        if today < last_thursday_of_previous_month:
            return "current_month"
        # If today is the last Thursday of the previous month
        elif today == last_thursday_of_previous_month:
            return "next_month"
        # If today is after the last Thursday of the previous month
        else:
            # Find the last day of the current month
            next_month = today.replace(day=28) + timedelta(days=4)
            last_day_of_current_month = next_month - timedelta(days=next_month.day)

            # If today is after the last Thursday but still in the previous month
            if today <= last_day_of_current_month:
                return "current_month"
            # If we have moved into a new month
            else:
                return "next_month"

    def get_expiry_by_criteria(self, base_symbol, strike_price, option_type,expiry_type="current_week"):
        filtered_data = self._filter_data(base_symbol, option_type, strike_price)
        today = datetime.now().date()
        future_expiries = filtered_data[filtered_data['expiry'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").date()) >= today]['expiry'].tolist()
        monthly_expiries = self._get_monthly_expiries(filtered_data, option_type)
        # Exclude monthly expiries to get the list of weekly expiries
        weekly_expiries = [expiry for expiry in future_expiries if expiry not in monthly_expiries]

        # Define strategy dictionary with safety checks for list indices
        expiry_strategies = {
            "current_week": lambda: weekly_expiries[0] if weekly_expiries else None,
            "next_week": lambda: weekly_expiries[1] if len(weekly_expiries) > 1 else None,
            "current_month": lambda: monthly_expiries[0] if monthly_expiries else self._get_last_weekly_expiry(weekly_expiries, today.month),
            "next_month": lambda: monthly_expiries[1] if len(monthly_expiries) > 1 else self._get_last_weekly_expiry(weekly_expiries, (today + timedelta(days=30)).month)
        }

        # If FUT with strike price 0, override to only consider monthly expiries
        if option_type == "FUT" and strike_price == 0:
            expiry_strategies = {
                "current_month": lambda: monthly_expiries[0] if monthly_expiries else None,
                "next_month": lambda: monthly_expiries[1] if len(monthly_expiries) > 1 else None
            }
        return expiry_strategies[expiry_type]()
    
    def get_exchange_token_by_criteria(self, base_symbol,strike_price, option_type,expiry):
        filtered_data = self._filter_data(base_symbol, option_type, strike_price, expiry)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['exchange_token']
        else:
            return None
    
    def get_token_by_exchange_token(self, exchange_token):
        filtered_data = self._filter_data_by_exchange_token(exchange_token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['instrument_token']
        else:
            return None

    def get_lot_size_by_exchange_token(self, exchange_token):
        filtered_data = self._filter_data_by_exchange_token(exchange_token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['lot_size']
        else:
            return None

    def get_trading_symbol_by_exchange_token(self, exchange_token,segment=None):
        if segment:
            filtered_data = self._filter_data_by_exchange_token(exchange_token)
            filtered_data = filtered_data[filtered_data['segment'] == segment]
            return filtered_data.iloc[0]['tradingsymbol']
        filtered_data = self._filter_data_by_exchange_token(exchange_token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['tradingsymbol']
        else:
            return None
    
    def get_base_symbol_by_exchange_token(self, exchange_token):
        filtered_data = self._filter_data_by_exchange_token(exchange_token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['name']
        else:
            return None
        
    def get_segment_by_exchange_token(self, exchange_token):
        filtered_data = self._filter_data_by_exchange_token(exchange_token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['exchange']
        else:
            return None

    def _filter_data_by_token(self, token):
        return self._dataframe[self._dataframe['instrument_token'] == token]

    def get_exchange_token_by_token(self, token):
        filtered_data = self._filter_data_by_token(token)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['exchange_token']
        else:
            return None
    
    def _filter_data_by_name(self, name):
        return self._dataframe[self._dataframe['tradingsymbol'] == name]

    def get_exchange_token_by_name(self, name, segment=None):
        if segment:
            filtered_data = self._filter_data_by_name(name)
            filtered_data = filtered_data[filtered_data['segment'] == segment]
            return filtered_data.iloc[0]['exchange_token']
        elif segment is None:
            filtered_data = self._filter_data_by_name(name)
            return filtered_data.iloc[0]['exchange_token']
        else:
            return None
    
    def get_token_by_name(self,name):
        filtered_data = self._filter_data_by_name(name)
        if not filtered_data.empty:
            return filtered_data.iloc[0]['instrument_token']
        else:
            return None
