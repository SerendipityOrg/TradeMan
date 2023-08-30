from json_utils import read_json_file
import os 

def get_strategy_users(strategy):
    data = read_json_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'broker.json'))
    
    users = []

    for broker, broker_data in data.items():
        # Extract account names that are allowed to trade
        accounts_to_trade = broker_data.get('accounts_to_trade', [])

        # For each user in accounts_to_trade, check if the strategy is in their percentageRisk and if its value is not zero
        for account in accounts_to_trade:
            user_details = broker_data.get(account, {})
            percentage_risk = user_details.get('percentageRisk', {})
            
            if strategy in percentage_risk and percentage_risk[strategy] != 0:
                users.append((broker, account))

    return users