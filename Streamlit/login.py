import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
from PIL import Image
import io
import os
import base64
import datetime
from script import show_profile
from dotenv import load_dotenv
from streamlit_calendar import calendar
from firebase_admin import storage
from streamlit_option_menu import option_menu
from script import display_performance_dashboard,table_style
from formats import format_value, format_stat_value, indian_format


# Load environment variables from .env file
load_dotenv()

# Retrieve values from .env
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
database_url = os.getenv('DATABASE_URL')
storage_bucket = os.getenv('STORAGE_BUCKET')

# Initialize Firebase app
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': storage_bucket
    })

# Create a SessionState class to manage session state variables
class SessionState:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# Create a session state variable
session_state = SessionState(logged_in=False, client_data=None)


def login_page():
    # If the user is not logged in, show the login form
    if not session_state.logged_in:
        # Take inputs for login information
        username = st.text_input(
            "Email or Phone Number:", key="user_email_input")
        password = st.text_input(
            "Password:", type="password", key="user_Password_input")

        # Add a login button
        login = st.button("Login")

        # Check if the login button is clicked
        if login:
            # Fetch data from Firebase Realtime Database to verify the credentials
            try:
                # Get a reference to the 'clients' node in the database
                ref = db.reference('clients')

                # Fetch all clients data
                clients = ref.get()

                # Go through each client and check if the credentials match
                for client_id, client_data in clients.items():
                    if (client_data.get("Email") == username or client_data.get("Phone Number") == username) and client_data.get("Password") == password:
                        # If credentials match, show a success message and break the loop
                        session_state.logged_in = True
                        session_state.client_data = client_data
                        st.experimental_rerun()
                        break
                else:
                    # If no matching credentials are found, show an error message
                    st.error("Invalid username or password.")
            except Exception as e:
                # Show an error message if there's an exception
                st.error("Failed to fetch data: " + str(e))
    else:
        # If the user is already logged in, show the other contents
        show_app_contents()


def show_app_contents():
    # Create a container for the horizontal menu
    menu_container = st.container()

    # Add the horizontal menu to the container
    with menu_container:
        selected = st.sidebar.selectbox(
            "Select",
            ("Profile", "Performance Dashboard", "Logout"),
        )

      # Show the respective content based on the selected option
    if selected == "Profile":
        client_data = session_state.client_data
        if client_data is not None:
            show_profile(client_data,)
        else:
            st.warning("No client data available.")
    elif selected == "Performance Dashboard":
        display_for_login(session_state.client_data)  # Modified this line to use display_for_login
    elif selected == "Logout":
        logout()
        st.experimental_rerun()


def display_for_login(client_data):
    if client_data:  # Check if client_data is not None before processing
        client_username = client_data.get("Username", '')
        client_username = client_username[0].lower() + client_username[1:]
        excel_file_name = f"{client_username}.xlsx"
        display_performance_dashboard(client_data, client_username, excel_file_name)
    else:
        st.warning("No client data available.")



def logout():
    # Reset session state variables
    session_state.logged_in = False
    session_state.client_data = None