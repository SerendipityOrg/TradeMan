import os, sys
import urllib
import numpy as np
import keras
import yfinance as yf
import joblib
import requests
from kiteconnect import KiteConnect
import time
from dotenv import load_dotenv



# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navigate to the Brokers and Utils directories relative to the current script's location
BROKERS_DIR = os.path.join(CURRENT_DIR,'..','..', 'Brokers')

dotenv_path = os.path.join(BROKERS_DIR, '.env')
load_dotenv(dotenv_path)

# Import necessary modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Utils'))
import general_calc as gc


sys.path.append(BROKERS_DIR)
import place_order 


class SuppressOutput: 
    def __init__(self,suppress_stdout=False,suppress_stderr=False): 
        self.suppress_stdout = suppress_stdout 
        self.suppress_stderr = suppress_stderr 
        self._stdout = None 
        self._stderr = None
    def __enter__(self): 
        devnull = open(os.devnull, "w") 
        if self.suppress_stdout: 
            self._stdout = sys.stdout 
            sys.stdout = devnull        
        if self.suppress_stderr: 
            self._stderr = sys.stderr 
            sys.stderr = devnull 
    def __exit__(self, *args): 
        if self.suppress_stdout: 
            sys.stdout = self._stdout 
        if self.suppress_stderr: 
            sys.stderr = self._stderr


index = os.getenv('overnight_index')


def get_strikeprc():
    file_path = os.getenv('omkar_json_filepath')
    omkar_details = gc.read_json_file(file_path)
    kite = KiteConnect(api_key=omkar_details['zerodha']['api_key'])
    kite.set_access_token(omkar_details['zerodha']['access_token'])
    token = os.getenv('nifty_token')
    ltp_data = kite.ltp(token)  # Convert token to string
    ltp = ltp_data[token]['last_price']
    return gc.round_strike_prc(ltp,index)

def fetchLatestNiftyDaily(proxyServer=None):
    return yf.download(
            tickers="^NSEI",
            period='5d',
            interval='1d',
            proxy=proxyServer,
            progress=False,
            timeout=10
        )

def getNiftyModel(proxyServer=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    utils_dir = os.path.join(script_dir, 'Utils') 
    os.makedirs(utils_dir, exist_ok=True)

    files = [
        os.path.join(utils_dir, 'nifty_model_v2.h5'), 
        os.path.join(utils_dir, 'nifty_model_v2.pkl')
    ]
    urls = [
        "https://raw.github.com/pranjal-joshi/Screeni-py/new-features/src/ml/nifty_model_v2.h5",
        "https://raw.github.com/pranjal-joshi/Screeni-py/new-features/src/ml/nifty_model_v2.pkl"
    ]
    if os.path.isfile(files[0]) and os.path.isfile(files[1]):
        file_age = (time.time() - os.path.getmtime(files[0])) / 604800
        if file_age > 1:
            download = True
            os.remove(files[0])
            os.remove(files[1])
        else:
            download = False
    else:
        download = True
    if download:
        for file_url in urls:
            if proxyServer is not None:
                resp = requests.get(file_url, stream=True, proxies={'https': proxyServer})
            else:
                resp = requests.get(file_url, stream=True)
            if resp.status_code == 200:
                print("[+] Downloading AI model (v2) for Nifty predictions, Please Wait..")
                try:
                    chunksize = 1024 * 1024 * 1
                    filesize = int(int(resp.headers.get('content-length')) / chunksize)
                    filesize = 1 if not filesize else filesize
                    with open(os.path.join(utils_dir, file_url.split('/')[-1]), 'wb') as f:
                        dl = 0 
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                            if dl >= filesize:
                                print("[+] Download Complete!")
                except Exception as e:
                    print("[!] Download Error - " + str(e))
        time.sleep(3)
    model = keras.models.load_model(files[0])
    pkl = joblib.load(files[1])
    return model, pkl

def getNiftyPrediction(data, proxyServer):
    import warnings 
    warnings.filterwarnings("ignore")
    model, pkl = getNiftyModel(proxyServer=proxyServer)
    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
        data = data[pkl['columns']]
        ### v2 Preprocessing
        data['High'] = data['High'].pct_change() * 100
        data['Low'] = data['Low'].pct_change() * 100
        data['Open'] = data['Open'].pct_change() * 100
        data['Close'] = data['Close'].pct_change() * 100
        data = data.iloc[-1] 
        ###
        data = pkl['scaler'].transform([data])
        pred = model.predict(data)[0]
    if pred > 0.5:
        out = "BEARISH"
        sug = "Hold your Short position!"
    else:
        out = "BULLISH"
        sug = "Stay Bullish!"
    return out


strikeprc = get_strikeprc()

bull_strikeprc = strikeprc - 150
bear_strikeprc = strikeprc + 150

try:
    proxyServer = urllib.request.getproxies()['http']
except KeyError:
    proxyServer = ""

prediction = getNiftyPrediction(
                data=fetchLatestNiftyDaily(proxyServer=proxyServer), 
                proxyServer=proxyServer
            )
print(prediction)
option_type = 'CE' if prediction == 'BEARISH' else 'PE'
strikeprc = bear_strikeprc if prediction == 'BEARISH' else bull_strikeprc
transaction_type = 'SELL' if prediction == 'BEARISH' else 'BUY'

order_details_opt = {
    "base_symbol": index,
    "option_type": option_type,
    "strike_prc": strikeprc,
    "transaction":"BUY",
    "direction": prediction
}
order_details_future = {
    "base_symbol": index,
    "option_type": 'FUT',
    "strike_prc": 0,
    "transaction": transaction_type,
    "direction": prediction
}

orders_to_place = [
    ('Overnight_Options', order_details_opt),
    ('Overnight_Options', order_details_future)
]

for strategy, order_details in orders_to_place:
    place_order.place_order_for_broker(strategy, order_details,signal='Afternoon')
