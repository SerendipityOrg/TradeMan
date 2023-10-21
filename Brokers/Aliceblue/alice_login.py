from pya3 import *
from Crypto import Random
from Crypto.Cipher import AES
import base64
import hashlib
import json
import requests
import pyotp


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
    
def login_in_aliceblue(user_details):
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

    return alice_session_id

