import pytest
from holdings_utils import (find_first_empty_row, get_user_list,
                            is_order_present)
from openpyxl import Workbook


def test_find_first_empty_row():
    wb = Workbook()
    ws = wb.active
    ws.append(["data"])
    ws.append(["data"])
    assert find_first_empty_row(ws) == 3

def test_is_order_present():
    wb = Workbook()
    ws = wb.active
    ws.append(["", "symbol1", "timestamp1"])
    ws.append(["", "symbol2", "timestamp2"])
    assert is_order_present(ws, "symbol1", "timestamp1") == True
    assert is_order_present(ws, "symbol3", "timestamp3") == False

def test_get_user_list():
    data = {
        "broker1": {"accounts_to_trade": ["account1", "account2"]},
        "broker2": {"accounts_to_trade": ["account3"]}
    }
    assert get_user_list(data) == [("broker1", "account1"), ("broker1", "account2"), ("broker2", "account3")]
