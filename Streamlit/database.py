import pyrebase
import json

# Firebase Configuration
with open('credentials.json') as f:
    config = json.load(f)

firebase = pyrebase.initialize_app(config)
db = firebase.database()

def add_client_to_db(user_id, name, email):
    client_data = {
        "name": name,
        "email": email
    }
    db.child("clients").child(user_id).set(client_data)
    return True

def fetch_client_data(user_id):
    client_data = db.child("clients").child(user_id).get().val()
    return client_data if client_data else None
