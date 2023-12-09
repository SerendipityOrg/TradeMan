from kiteconnect import KiteConnect


def fetch_user_margins(user_list):
    user_margins = {}
    for user in user_list:
        try:
            kite = KiteConnect(api_key=user['api_key'], access_token=user['access_token'])
            margins = kite.margins()
            user_margins[user['name']] = margins['equity']['available']['live_balance']
        except Exception as e:
            return {f"Error fetching margins for user {user['name']}": str(e)}
    return user_margins
