import pandas as pd
import os

DIR_PATH = os.getcwd()
fno_info_csv_path = os.path.join(DIR_PATH,'fno_info.csv')


class FNOInfo:
    def __init__(self, file_path=fno_info_csv_path):
        self.file_path = file_path
        self.data = None  # Initialize data as None

    def _ensure_data_loaded(self):
        """
        Internal method to load data from the CSV file if it hasn't been loaded yet.
        """
        if self.data is None:
            self.df = pd.read_csv(self.file_path)
            self.data = self.df.to_dict(orient='records')

    def get_data_by_base_symbol(self, base_symbol):
        """
        Get data by 'base_symbol'.
        """
        self._ensure_data_loaded()  # Ensure data is loaded
        return [record for record in self.data if record['base_symbol'] == base_symbol]

    def get_lot_size_by_base_symbol(self, base_symbol):
        """
        Get the 'lot_size' for a given 'base_symbol'.
        """
        self._ensure_data_loaded()  # Ensure data is loaded
        qty = [record['lot_size'] for record in self.data if record['base_symbol'] == base_symbol]
        return qty[0] if qty else None

    def get_max_order_qty_by_base_symbol(self, base_symbol):
        """
        Get the 'max_order_qty' for a given 'base_symbol'.
        """
        self._ensure_data_loaded()
        qty = [record['max_order_qty'] for record in self.data if record['base_symbol'] == base_symbol]
        return qty[0] if qty else None
