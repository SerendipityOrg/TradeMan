from kiteconnect import KiteConnect
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from time import sleep
import pyotp


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

    return kite_access_token 