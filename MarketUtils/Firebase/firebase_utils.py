import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from dotenv import load_dotenv
import os,sys

DIR_PATH = os.getcwd()
sys.path.append(DIR_PATH)

ENV_PATH = os.path.join(DIR_PATH, '.env')
load_dotenv(ENV_PATH)

cred_filepath = os.getenv('firebase_cred_filepath')

cred = credentials.Certificate(cred_filepath)
firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://trading-app-caf8e-default-rtdb.firebaseio.com/'
    })

def fetch_collection_data_firebase(collection):
    ref = db.reference(collection)
    data = ref.get()
    return data

def update_fields_firebase(collection,username,data):
    ref = db.reference(f'{collection}/{username}')
    ref.update(data)
