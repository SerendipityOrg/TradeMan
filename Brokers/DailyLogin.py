from kiteconnect import KiteConnect
import pyotp
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
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

# Calculate lots for a given strategy based on the allocated amount and percentage
def calculate_lots(user_details, strategy_percentage, amt_per_lot):
    lots = {}
    for strategy in user_details.get('strategies', []):
        if strategy in strategy_percentage and strategy in amt_per_lot:
            allocated_amt = user_details.get(f"{strategy}_allocated", 0)
            percentage = strategy_percentage[strategy]
            lot = math.floor(allocated_amt  / amt_per_lot[strategy])
            lots[strategy] = lot
        else:
            lots[strategy] = 0
    return lots

script_dir = os.path.dirname(os.path.realpath(__file__))
user_details_path = os.path.join(script_dir, 'broker.json')

def create_strategy_json(broker_name, user, lots, user_details_path):

    with open(user_details_path, 'r') as json_file:
        broker = json.load(json_file)

    for strategy, lot in lots.items():
        # Construct the path to the file in the Utilities directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_dir, '..', 'Utilities', f"{strategy}.json")

        if os.path.exists(file_path):
            # If file exists, load it and update it
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
        else:
            # If file does not exist, create new dictionary
            data = {}

        if broker_name not in data:
            data[broker_name] = {}

        if strategy == 'Siri':
            data[broker_name][user]['nf_qty'] = 0
            data[broker_name][user]['bnf_qty'] = 0
            data[broker_name][user]['fnf_qty'] = 0
        else:
            data[broker_name][user] = {'qty': lot * 50}

        if broker_name == 'zerodha':
            data[broker_name][user]['api_key'] = user_details['api_key']
            data[broker_name][user]['access_token'] = user_details['access_token']
        elif broker_name == 'aliceblue':
            data[broker_name][user]['username'] = user_details['username']
            data[broker_name][user]['api_key'] = user_details['api_key']
            data[broker_name][user]['session_id'] = user_details['session_id']

        # Initialize list to store keys to be removed
        keys_to_remove = []
        
        for name in broker:
            if broker[name]['accounts_to_trade'] == []:  
                if name != broker_name:
                    keys_to_remove.append(name)
            else:
                # if the strategy does not exist under this broker, delete the user
                if 'strategies' in broker[name] and strategy not in broker[name]['strategies']:
                    if name in data and user in data[name]:
                        keys_to_remove.append((name, user))

        # Delete the keys from data
        for key in keys_to_remove:
            if isinstance(key, tuple):
                # Check if user exists in the broker before deleting
                if key[1] in data[key[0]]:
                    del data[key[0]][key[1]]  # Delete user from a broker
            else:
                # Check if broker exists before deleting
                if key in data:
                    del data[key]  # Delete broker

        # Save the data
        with open(file_path, 'w') as json_file:
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
    driver = uc.Chrome()
    
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
    strategy_percentage = user_details.get('percentage', {})
    for strategy in strategy_percentage:
        if strategy in user_details.get('strategies', []):
            user_details[f"{strategy}_allocated"] = balance * strategy_percentage[strategy]

    for strategy in list(user_details.keys()):
        if strategy.endswith("_allocated"):
            strategy_name = strategy.split("_allocated")[0]
            if strategy_name not in user_details['strategies']:
                user_details.pop(strategy, None)
                
    broker['aliceblue'][user] = user_details  # persist the changes
    lots = calculate_lots(user_details, strategy_percentage,amt_per_lot)
    create_strategy_json('aliceblue', user, lots,user_details_path)
    broker['aliceblue'][user] = user_details


# Get the accounts to trade for zerodha
zerodha_accounts_to_trade = broker['zerodha']['accounts_to_trade']

# Iterate over the accounts to trade
for user in zerodha_accounts_to_trade:
    user_details = broker['zerodha'][user]
    kite, user_details = login_in_zerodha(user_details)
    balance = kite.margins(segment = 'equity')['available']['opening_balance']
    # Updated logic to use strategy percentage
    strategy_percentage = user_details.get('percentage', {})
    for strategy in strategy_percentage:
        if strategy in user_details.get('strategies', []):
            user_details[f"{strategy}_allocated"] = balance * strategy_percentage[strategy]

    for strategy in list(user_details.keys()):
        if strategy.endswith("_allocated"):
            strategy_name = strategy.split("_allocated")[0]
            if strategy_name not in user_details['strategies']:
                user_details.pop(strategy, None)

    broker['zerodha'][user] = user_details  # persist the changes
    lots = calculate_lots(user_details, strategy_percentage,amt_per_lot)
    create_strategy_json('zerodha', user, lots,user_details_path)
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