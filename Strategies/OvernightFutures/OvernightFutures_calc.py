import yfinance as yf
import os
import time
import requests
import numpy as np
import keras
import joblib
import sys


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
        out = "Bearish"
        sug = "Hold your Short position!"
    else:
        out = "Bullish"
        sug = "Stay Bullish!"
    return out
