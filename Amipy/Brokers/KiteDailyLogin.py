from kiteconnect import KiteConnect
import apikey
import pyotp
import pandas as pd
from kiteconnect import KiteConnect
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import datetime

print("Today's date:", datetime.date.today())


def login_in_zerodha(api_key, api_secret, user_id, user_pwd, totp_key):
    global request_token, kite_access_token
    driver = uc.Chrome()
    
    driver.get(f'https://kite.trade/connect/login?api_key={api_key}&v=3')

    login_id = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input'))
    login_id.send_keys(user_id)

    time.sleep(2)

    pwd = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input'))
    pwd.send_keys(user_pwd)

    time.sleep(2)
    
    submit = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button'))
    submit.click()

    time.sleep(15)

    # adjustment to code to include TOTP
    totp = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div[2]/div/div/form/div[1]/input'))
    authkey = pyotp.TOTP(totp_key)
    print(authkey.now())
    totp.send_keys(authkey.now())
    # adjustment complete
    
    time.sleep(10)
    
    url = driver.current_url
    initial_token = url.split('request_token=')[1]
    request_token = initial_token.split('&')[0]

    driver.close()

    kite = KiteConnect(api_key = api_key)
    print('request_token:',request_token)
    data = kite.generate_session(request_token, api_secret=api_secret)
    kite_access_token = data['access_token']
    kite.set_access_token(kite_access_token)
    print('kite_access_token:',kite_access_token)
    
    # strip and output request token to acc_token.txt
    with open(r'req_token.txt', 'w') as f:
        f.write(request_token)
  
    # strip and output access token to acc_token.txt
    with open(r'acc_token.txt', 'w') as f:
        f.write(kite_access_token)
       
    return kite

login_in_zerodha(apikey.kite_api_key, apikey.kite_api_sec, apikey.kite_username, apikey.kite_password, apikey.kite_totp_key)


