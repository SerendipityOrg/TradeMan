from dataclasses import dataclass

@dataclass
class Broker:
    name: str
    data: dict

    def get_api_key(self):
        return self.data["api_key"]

    def set_api_key(self, api_key):
        self.data["api_key"] = api_key

    def get_api_secret(self):
        return self.data["api_secret"]

    def set_api_secret(self, api_secret):
        self.data["api_secret"] = api_secret

    def get_access_token(self):
        return self.data["access_token"]

    def set_access_token(self, access_token):
        self.data["access_token"] = access_token

    def get_current_capital(self):
        return self.data["current_capital"]

    def set_current_capital(self, current_capital):
        self.data["current_capital"] = current_capital

    def get_percentage_risk(self, account_name):
        return self.data[account_name]["percentageRisk"]

    def set_percentage_risk(self, account_name, percentage_risk):
        self.data[account_name]["percentageRisk"] = percentage_risk

    def get_account(self, account_name):
        return self.data[account_name]

    def set_account(self, account_name, account_details):
        self.data[account_name] = account_details

    def get_order_details(self, account_name):
        return self.data[account_name]["orders"]

    def update_order_details(self, account_name, order_details):
        self.data[account_name]["orders"].append(order_details)
