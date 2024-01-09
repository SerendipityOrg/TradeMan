import unittest
from unittest import mock

from Brokers.Aliceblue.alice_utils import *
from Brokers.place_order_calc import *


class TestPlaceOrderCalc(unittest.TestCase):
    def setUp(self):
        self.user_details = {
            'username': 'test_user',
            'broker': 'test_broker',
            'strategy': 'test_strategy',
            'transaction_type': 'BUY',
            'exchange_token': 12345,
            'qty': 10,
            'order_type': 'Market',
            'product_type': 'MIS',
            'trade_id': 'test_trade_id'
        }
        self.order_details = {
            'username': 'test_user',
            'broker': 'test_broker',
            'strategy': 'test_strategy',
            'transaction_type': 'BUY',
            'exchange_token': 12345,
            'qty': 10,
            'order_type': 'Market',
            'product_type': 'MIS',
            'trade_id': 'test_trade_id'
        }
        self.mock_instrument = mock.create_autospec(Instrument)
        self.mock_strategy = mock.create_autospec(Strategy)

    @mock.patch('Brokers.place_order_calc.general_calc.read_json_file')
    def test_get_user_details(self, mock_read_json_file):
        mock_read_json_file.return_value = self.user_details
        result = get_user_details('test_user')
        self.assertEqual(result, (self.user_details, 'test_user.json'))

    @mock.patch('Brokers.place_order_calc.general_calc.read_json_file')
    def test_get_orders_json(self, mock_read_json_file):
        mock_read_json_file.return_value = self.order_details
        result = get_orders_json('test_user')
        self.assertEqual(result, (self.order_details, 'test_user.json'))

    @mock.patch('Brokers.place_order_calc.get_strategy_json')
    @mock.patch('Brokers.place_order_calc.Strategy.Strategy.read_strategy_json')
    def test_get_trade_id(self, mock_read_strategy_json, mock_get_strategy_json):
        mock_get_strategy_json.return_value = (self.mock_strategy, 'test_strategy.json')
        mock_read_strategy_json.return_value = self.mock_strategy
        result = get_trade_id('test_strategy', 'entry')
        self.assertEqual(result, 'AP1_entry')

    @mock.patch('Brokers.place_order_calc.get_orders_json')
    @mock.patch('Brokers.place_order_calc.general_calc.write_json_file')
    def test_log_order(self, mock_write_json_file, mock_get_orders_json):
        mock_get_orders_json.return_value = (self.order_details, 'test_user.json')
        log_order('test_order_id', self.order_details)
        mock_write_json_file.assert_called_once()

    @mock.patch('Brokers.place_order_calc.general_calc.read_json_file')
    def test_assign_user_details(self, mock_read_json_file):
        mock_read_json_file.return_value = [self.user_details]
        result = assign_user_details('test_user')
        self.assertEqual(result, self.user_details)

    @mock.patch('Brokers.place_order_calc.general_calc.read_json_file')
    def test_fetch_orders_json(self, mock_read_json_file):
        mock_read_json_file.return_value = self.order_details
        result = fetch_orders_json('test_user')
        self.assertEqual(result, self.order_details)

    @mock.patch('Brokers.place_order_calc.fetch_orders_json')
    def test_retrieve_order_id(self, mock_fetch_orders_json):
        mock_fetch_orders_json.return_value = self.order_details
        result = retrieve_order_id('test_user', 'test_strategy', 'BUY', 12345)
        self.assertEqual(result, 'test_order_id')

    @mock.patch('Brokers.place_order_calc.assign_user_details')
    def test_get_qty(self, mock_assign_user_details):
        mock_assign_user_details.return_value = self.user_details
        result = get_qty(self.order_details)
        self.assertEqual(result, 10)

    @mock.patch('Brokers.place_order_calc.pd.read_csv')
    def test_get_lot_size(self, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame({'base_symbol': ['test_symbol'], 'lot_size': [100]})
        result = get_lot_size('test_symbol')
        self.assertEqual(result, 100)

    @mock.patch('Brokers.place_order_calc.calculate_qty')
    @mock.patch('Brokers.place_order_calc.place_order.place_order_for_broker')
    @mock.patch('Brokers.place_order_calc.general_calc.read_json_file')
    def test_create_telegram_order_details(self, mock_read_json_file, mock_place_order_for_broker, mock_calculate_qty):
        mock_read_json_file.return_value = [self.user_details]
        mock_calculate_qty.return_value = 10
        create_telegram_order_details(self.order_details)
        mock_place_order_for_broker.assert_called_once()

if __name__ == '__main__':
    unittest.main()
