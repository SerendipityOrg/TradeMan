import pytest

from .margin_utils import fetch_user_margins


def test_fetch_user_margins_empty_list():
    user_list = []
    expected_result = {}
    assert fetch_user_margins(user_list) == expected_result

def test_fetch_user_margins_valid_users():
    user_list = [{'name': 'user1', 'api_key': 'key1', 'access_token': 'token1'},
                 {'name': 'user2', 'api_key': 'key2', 'access_token': 'token2'}]
    expected_result = {'user1': 1000.0, 'user2': 2000.0}
    assert fetch_user_margins(user_list) == expected_result

def test_fetch_user_margins_error():
    user_list = [{'name': 'user1', 'api_key': 'key1', 'access_token': 'token1'},
                 {'name': 'user2', 'api_key': 'key2', 'access_token': 'token2'}]
    expected_result = {"Error fetching margins for user user1": "Some error"}
    assert fetch_user_margins(user_list) == expected_result
