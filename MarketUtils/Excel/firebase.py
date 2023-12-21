from firebase_admin import db
from firebase_admin import credentials, storage
import firebase_admin
import os, sys
from dotenv import load_dotenv

# Get the current working directory
DIR = os.getcwd()
sys.path.append(DIR)

ENV_PATH = os.path.join(DIR, '.env')
load_dotenv(ENV_PATH)

# Retrieve values from .env
firebase_credentials_path = os.getenv('firebase_credentials_path')
database_url = os.getenv('database_url')
storage_bucket = os.getenv('storage_bucket')

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': storage_bucket
    })
    
# Function to save file to Firebase Storage
def save_file_to_firebase(file_path, firebase_bucket_name):
    bucket = storage.bucket(firebase_bucket_name)

    # Create a blob for uploading the file
    blob = bucket.blob(os.path.basename(file_path))
    # Upload the file
    blob.upload_from_filename(file_path)
    print(f"File {file_path} uploaded to {firebase_bucket_name}.")