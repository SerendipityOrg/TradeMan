from kiteconnect import KiteConnect
import pyotp
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from time import sleep
import datetime
import json
import requests
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import base64
from pya3 import *
import math
import os

print("Today's date:", datetime.today())

class CryptoJsAES:
    @staticmethod
    def __pad(data):
        BLOCK_SIZE = 16
        length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
        return data + (chr(length) * length).encode()

    @staticmethod
    def __unpad(data):
        return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]

    def __bytes_to_key(data, salt, output=48):
        assert len(salt) == 8, len(salt)
        data += salt
        key = hashlib.md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = hashlib.md5(key + data).digest()
            final_key += key
        return final_key[:output]

    @staticmethod
    def encrypt(message, passphrase):
        salt = Random.new().read(8)
        key_iv = CryptoJsAES.__bytes_to_key(passphrase, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(b"Salted__" + salt + aes.encrypt(CryptoJsAES.__pad(message)))

    @staticmethod
    def decrypt(encrypted, passphrase):
        encrypted = base64.b64decode(encrypted)
        assert encrypted[0:8] == b"Salted__"
        salt = encrypted[8:16]
        key_iv = CryptoJsAES.__bytes_to_key(passphrase, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return CryptoJsAES.__unpad(aes.decrypt(encrypted[16:]))

script_dir = os.path.dirname(os.path.realpath(__file__))
user_details_path = os.path.join(script_dir, 'broker.json')

#go outside the folder and then go inside MPWizard folder
script_dir = os.path.dirname(script_dir)
mpwizard_json_path = os.path.join(script_dir, 'Strategies','MPWizard', 'MPWizard.json')
amipy_json_path = os.path.join(script_dir, 'Strategies','Amipy', 'AmiPy.json')

def calculate_quantity(capital, risk, prc_ref, lot_size):
    if prc_ref == 0:
        print("Price reference is 0")
    raw_quantity = (risk * capital) / prc_ref
    qty = int((raw_quantity // lot_size) * lot_size)
    if qty == 0:
        qty = lot_size
    return qty

def calculate_lots(user_details, strategy_percentage, mpwizard_json):
    lots = {}
    current_capital = user_details.get('current_capital', 0)
    percentage_risk = user_details.get('percentageRisk', {})
    weekday = datetime.now().strftime('%a')
    indices_lot_sizes = {"NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 40}

    with open(mpwizard_json, 'r') as file:
        data = json.load(file)
        indices_data = data.get('indices', [])

    for strategy in percentage_risk:
        if strategy in strategy_percentage:
            percentage = strategy_percentage[strategy]
            if percentage > 1:
                # If the percentage is greater than 1, it is considered as an amount
                lots[strategy] = {f'{strategy}_qty': math.floor(current_capital / percentage)}
            else:
                # If the percentage is less than 1, it is considered as a percentage
                strategy_dict = {}
                for index in indices_data:
                    prc_ref = index['WeekdayPrcRef'].get(weekday, 0)
                    lot_size = indices_lot_sizes.get(index['name'], 0)
                    strategy_dict[f'{index["name"]}_qty'] = calculate_quantity(current_capital, percentage, prc_ref, lot_size)
                lots[strategy] = strategy_dict
    return lots


def create_strategy_json(broker_name, user, lots, balance, user_details_path, mpwizard_json_path):
    with open(user_details_path, 'r') as json_file:
        broker = json.load(json_file)

    user_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','UserProfile','json')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    user_file_path = os.path.join(user_dir, f"{user}.json")

    if os.path.exists(user_file_path):
        with open(user_file_path, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    if broker_name not in data:
        data[broker_name] = {}
    
    data[broker_name]['username'] = user_details['username']
    data[broker_name]['api_key'] = user_details['api_key']    

    if broker_name == 'aliceblue':
        data[broker_name]['session_id'] = user_details['session_id']
    elif broker_name == 'zerodha':
        data[broker_name]['access_token'] = user_details['access_token']
    else:
        print("Broker not supported")
    data[broker_name]["Current_Capital"] = balance

    for strategy, qty in lots.items():
        if strategy == 'AmiPy':
            qty = qty['AmiPy_qty']*50
        data[broker_name][f"{strategy}_qty"] = qty
        if strategy == 'overnight_option':
            qty = qty['overnight_option_qty']*50
        data[broker_name][f"{strategy}_qty"] = qty

    if 'orders' in data[broker_name]:
        overnight_option_data = data[broker_name]['orders'].get('Overnight_Options', None)
        data[broker_name]['orders'] = {}
        if overnight_option_data is not None:
            data[broker_name]['orders']['Overnight_Options'] = overnight_option_data


    with open(user_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


alice = None
kite = None

def login_in_aliceblue(user_details):
    global alice
    BASE_URL="https://ant.aliceblueonline.com/rest/AliceBlueAPIService"
    
    totp = pyotp.TOTP(user_details["totp_access"])

    def getEncryptionKey():
        url = BASE_URL+"/customer/getEncryptionKey"
        payload = json.dumps({"userId": user_details["username"]})
        headers = {'Content-Type': 'application/json'}
        response = requests.post( url, headers=headers, data=payload)
        return response.json()['encKey']

    getEncryptionKey = getEncryptionKey()
    checksum = CryptoJsAES.encrypt(user_details["password"].encode(), getEncryptionKey.encode()).decode('UTF-8')

    def weblogin():
        url = BASE_URL+"/customer/webLogin"
        payload = json.dumps({"userId": user_details["username"], "userData": checksum})                    
        headers = {'Content-Type': 'application/json'}
        response = requests.post( url, headers=headers, data=payload)
        return response.json()

    weblogin = weblogin()
    sCount = weblogin['sCount']
    sIndex = weblogin['sIndex']

    def twoFa(sCount, sIndex):
        url = BASE_URL+"/sso/2fa"
        payload = json.dumps({"answer1": user_details["twoFA"],
                    "userId": user_details["username"],
                    "sCount": sCount,
                    "sIndex": sIndex})                    
        headers = {'Content-Type': 'application/json'}
        response = requests.post( url, headers=headers, data=payload)
        return response.json()

    twoFa = twoFa(sCount, sIndex)
    loPreference = twoFa['loPreference']
    totpAvailable = twoFa['totpAvailable']

    def verifyTotp(twofa):
        if twofa["loPreference"] == "TOTP" and twofa["totpAvailable"]:
            url = BASE_URL+"/sso/verifyTotp"
            payload = json.dumps({"tOtp": totp.now(), "userId": user_details["username"] })
            headers = {
                'Authorization': 'Bearer '+user_details["username"]+' '+twofa['us'],
                'Content-Type': 'application/json'}
            response = requests.request("POST", url, headers=headers, data=payload,verify=True)
            if response.text:  # Check if response contains any data
                try:
                    response_data = response.json()
                    if response_data.get("userSessionID"):
                        print("Login Successfully")
                        return response_data
                    else:
                        print("User is not enable TOTP! Please enable TOTP through mobile or web")
                except json.JSONDecodeError:
                    print(f"Could not parse response as JSON: {response.text}")
            else:
                print(f"No data returned from server. HTTP Status Code: {response.status_code}")
        else:
            print("Try Again")
        return None


    if loPreference == "TOTP" and totpAvailable:
        verifyTotp = verifyTotp(twoFa)
        userSessionID = verifyTotp['userSessionID']
    else:
        userSessionID = twoFa['userSessionID']

    alice = Aliceblue(user_id=user_details["username"], api_key=user_details["api_key"])
    alice_session_id = alice.get_session_id()["sessionID"]
    print(f"Session id for {user_details['username']}: {alice_session_id}")

    # Updating the user_details with new session_id
    user_details['session_id'] = alice_session_id

    return user_details

def login_in_zerodha(user_details):
    global kite
    api_key = user_details['api_key']
    api_secret = user_details['api_secret']
    user_id = user_details['username']
    user_pwd = user_details['password']
    totp_key = user_details['totp']

    global request_token, kite_access_token
    driver = webdriver.Chrome(ChromeDriverManager().install())
    # driver  = webdriver.Chrome()

    driver.get(f'https://kite.trade/connect/login?api_key={api_key}&v=3')

    login_id = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input'))
    login_id.send_keys(user_id)

    sleep(2)

    pwd = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input'))
    pwd.send_keys(user_pwd)

    sleep(2)
    
    submit = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button'))
    submit.click()

    sleep(15)

    # adjustment to code to include TOTP
    totp = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div[2]/div/div/form/div[1]/input'))
    authkey = pyotp.TOTP(totp_key)
    totp.send_keys(authkey.now())
    # adjustment complete
    
    sleep(10)
    
    url = driver.current_url
    initial_token = url.split('request_token=')[1]
    request_token = initial_token.split('&')[0]

    driver.close()

    kite = KiteConnect(api_key = api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    kite_access_token = data['access_token']
    kite.set_access_token(kite_access_token)
    print(f'kite_access_token for {user_id}:', kite_access_token)

    # Updating the user_details with new access_token
    user_details['access_token'] = kite_access_token
    
    return kite, user_details

# Load the broker data
with open(user_details_path) as f:
    broker = json.load(f)

# Define the strategies and their respective percentages here
amt_per_lot = {'AmiPy': 250000}

# Get the accounts to trade for aliceblue
aliceblue_accounts_to_trade = broker['aliceblue']['accounts_to_trade']

for user in aliceblue_accounts_to_trade:
    user_details = broker['aliceblue'][user]
    user_details = login_in_aliceblue(user_details)
    balance = float(alice.get_balance()[0]['cashmarginavailable'])
    # Updated logic to use strategy percentage
    strategy_percentage = user_details.get('percentageRisk', {})
    # user_details['current_capital'] = balance
    broker['aliceblue'][user] = user_details  # persist the changes
    lots = calculate_lots(user_details, strategy_percentage,mpwizard_json_path)
    create_strategy_json('aliceblue', user, lots, balance, user_details_path,mpwizard_json_path)
    broker['aliceblue'][user] = user_details


# Get the accounts to trade for zerodha
zerodha_accounts_to_trade = broker['zerodha']['accounts_to_trade']

# Iterate over the accounts to trade
for user in zerodha_accounts_to_trade:
    user_details = broker['zerodha'][user]
    kite, user_details = login_in_zerodha(user_details)
    balance = kite.margins(segment = 'equity')['available']['opening_balance']
    # Updated logic to use strategy percentage
    strategy_percentage = user_details.get('percentageRisk', {})
    # user_details['current_capital'] = balance

    broker['zerodha'][user] = user_details  # persist the changes
    lots = calculate_lots(user_details, strategy_percentage,mpwizard_json_path)
    create_strategy_json('zerodha', user, lots,balance, user_details_path,mpwizard_json_path)
    broker['zerodha'][user] = user_details

# Save the updated data
with open(user_details_path, 'w') as f:
    json.dump(broker, f, indent=4)

if datetime.today().weekday() == 4:
    kite = KiteConnect(api_key=broker['zerodha']['omkar']['api_key'])
    kite.set_access_token(broker['zerodha']['omkar']['access_token'])
    instrument_dump = kite.instruments()
    instrument_df = pd.DataFrame(instrument_dump)
    instrument_df.to_csv(r'instruments.csv')

with open(mpwizard_json_path) as f:
    mpwizard_data = json.load(f)

# Iterate over the list of dictionaries
for dictionary in mpwizard_data["indices"]:
    # Remove 'SignalEntry' from the dictionary
    dictionary.pop('SignalEntry', None)

# Save the modified data back to the file
with open(mpwizard_json_path, 'w') as f:
    json.dump(mpwizard_data, f,indent=4)

with open(amipy_json_path) as f:
    amipy_data = json.load(f)

for dictionary in amipy_data["Nifty"]:
    dictionary.pop('SignalEntry', None)

with open(amipy_json_path, 'w') as f:
    json.dump(amipy_data, f,indent=4)
