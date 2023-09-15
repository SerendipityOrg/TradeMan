import shutil
from pathlib import Path
import tempfile
import os
import re
import math
import io
from PIL import Image
import datetime
import base64
import pandas as pd
from firebase_admin import db
from firebase_admin import credentials, storage
import firebase_admin
import hashlib
import openpyxl
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import streamlit as st
from formats import format_value, format_stat_value, indian_format
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from script import display_performance_dashboard, table_style


# Initialize session_state if it doesn't exist
if 'client_data' not in st.session_state:
    st.session_state.client_data = {}

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
    # Initialize variables
data = []  # This will hold the Excel data

def login_admin(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Get a reference to the Firebase database
    ref = db.reference('/admin')

    # Check if the username and password match an existing admin
    existing_admins = ref.order_by_child('username').equal_to(username).get()

    if not existing_admins:
        return False
    else:
        for admin_id, admin_data in existing_admins.items():
            if admin_data.get('password') == hashed_password:
                return True
        return False

def get_weeks_for_month(month_number, year):
    first_day_of_month = datetime.date(year, month_number, 1)
    last_day_of_month = datetime.date(year, month_number + 1, 1) - datetime.timedelta(days=1)
    
    # Find the first Saturday of the month
    while first_day_of_month.weekday() != 5:
        first_day_of_month += datetime.timedelta(days=1)
    
    weeks = []
    while first_day_of_month <= last_day_of_month:
        end_day = first_day_of_month + datetime.timedelta(days=6)
        if end_day > last_day_of_month:
            end_day = last_day_of_month
        weeks.append((first_day_of_month.day, end_day.day))
        first_day_of_month += datetime.timedelta(days=7)
    
    return weeks

def update_client_data(client_name, updated_data):
    # Get a reference to the selected client's database
    selected_client_ref = db.reference(f"/clients/{client_name}")
    # Update the client data in the Firebase database
    selected_client_ref.update(updated_data)


def update_brokers_data(client_name, brokers_list_1, brokers_list_2):
    # Get a reference to the selected client's brokers list in the Firebase database
    selected_client_ref = db.reference(f"/clients/{client_name}")
    # Update the brokers list in the Firebase database
    selected_client_ref.update(
        {"Brokers list 1": brokers_list_1, "Brokers list 2": brokers_list_2})


def update_strategies_data(client_name, strategies_list):
    # Get a reference to the selected client's strategies list in the Firebase database
    selected_client_ref = db.reference(f"/clients/{client_name}/Strategy list")
    # Update the strategies list in the Firebase database
    selected_client_ref.set(strategies_list)


def update_profile_picture(selected_client_name, new_profile_picture):
    # Get a reference to the selected client's database
    selected_client_ref = db.reference(f"/clients/{selected_client_name}")

    # Save the uploaded file to a temporary location
    temp_dir = Path(tempfile.gettempdir())
    temp_file_path = temp_dir / new_profile_picture.name

    # Write the uploaded file's content to the temporary location
    with open(temp_file_path, 'wb') as out_file:
        shutil.copyfileobj(new_profile_picture, out_file)

    # Read the temporary file as bytes
    with open(temp_file_path, 'rb') as file:
        profile_picture_bytes = file.read()

    # Convert the image to base64
    profile_picture = base64.b64encode(profile_picture_bytes).decode('utf-8')

    # Update the profile picture in the Firebase database
    selected_client_ref.update({"Profile Picture": profile_picture})

    # Remove the temporary file
    temp_file_path.unlink()


def select_client():
    # Get a reference to the clients in the Firebase database
    client_ref = db.reference('/clients')
    
    # Retrieve the client data from the database
    client_data = client_ref.get()
    
    # If there's no client data, show a warning message
    if not client_data:
        st.sidebar.warning("No client data found.")
        return

    # Construct a list of client names, with a default 'Select' option
    client_names = ['Select'] + list(client_data.keys())

    # Modify the client names for display:
    # Replace underscores with spaces and capitalize each word
    formatted_client_names = [client_name.replace('_', ' ').title() for client_name in client_names]

    # Create a select box in the Streamlit sidebar to choose a client
    selected_client_name = st.sidebar.selectbox('Select a client', formatted_client_names)

    # If no client is selected, exit the function early
    if selected_client_name == 'Select':
        return

    # Convert the formatted client name back to its original format (with underscores and lowercase)
    original_selected_client_name = selected_client_name.replace(' ', '_').lower()

    # Check if the selected client name is a valid key in the retrieved client data
    if original_selected_client_name not in client_data:
        st.sidebar.warning("Selected client data not found.")
        return

    # Extract the data for the selected client
    selected_client = client_data[original_selected_client_name]

    # Show another select box for the user to choose between 'Profile' and 'Performance Dashboard'
    next_selection = st.sidebar.selectbox('Client Details', ['Profile', 'Performance Dashboard'])

    # Display the appropriate content based on the user's choice
    if next_selection == 'Profile':
        show_profile(selected_client, selected_client_name)

    elif next_selection == 'Performance Dashboard':
             # Convert the first letter of client_username to lowercase for file naming
        client_username = selected_client.get("Username", '')
        client_username = client_username[0].lower() + client_username[1:]
        excel_file_name = f"{client_username}.xlsx"  # Construct the Excel file name based on client's username
        # Call the function to display the performance dashboard, passing in both the client data and Excel file name
        display_performance_dashboard(selected_client,client_username, excel_file_name)

def show_profile(selected_client, selected_client_name):
    profile_picture = selected_client.get("Profile Picture")
    # Display the profile picture if available
    if profile_picture is not None:
        # Decode base64 string to bytes
        profile_picture_bytes = base64.b64decode(profile_picture)

        # Convert profile picture from bytes to PIL Image
        image = Image.open(io.BytesIO(profile_picture_bytes))

       # Convert the image to RGB
        image_rgb = image.convert("RGB")

        # Save the image in JPG format with reduced quality (adjust the quality value as needed)
        image_path = "profile_picture.jpg"
        # Adjust the quality value as needed
        image_rgb.save(image_path, "JPEG", quality=50)

        # Define CSS style to position the profile picture in the right top corner with some margin
        css_style = f"""
            <style>
                .profile-picture-container {{
                    position: absolute;
                    top: -90px;  /* Adjust the top value as needed */
                    right: 10px;
                    border: 2px solid #ccc;
                    border-radius: 50%;
                    overflow: hidden;
                }}
                .profile-picture-container img {{
                    width: 100px;
                    height: 100px;
                }}
            </style>
        """

        # Display the CSS style
        st.markdown(css_style, unsafe_allow_html=True)

        # Display the profile picture in a container with the defined CSS style
        st.markdown(f"""
            <div class="profile-picture-container">
                <img src="data:image/jpeg;base64,{base64.b64encode(profile_picture_bytes).decode('utf-8')}" alt="Profile Picture">
            </div>
        """, unsafe_allow_html=True)

        # Remove the saved image file
        os.remove(image_path)

        # Extract client data from the dictionary
        Name = selected_client.get("Name", "")
        Username = selected_client.get("Username", "")
        Email = selected_client.get("Email", "")
        Password = selected_client.get("Password", "")
        Phone_Number = selected_client.get("Phone Number", "")
        Date_of_Birth = selected_client.get("Date of Birth", "")
        Aadhar_Card_No = selected_client.get("Aadhar Card No", "")
        PAN_Card_No = selected_client.get("PAN Card No", "")
        Bank_Name = selected_client.get("Bank Name", "")
        Bank_Account_No = selected_client.get("Bank Account No", "")
        Brokers_list_1 = selected_client.get("Brokers list 1", [])
        Brokers_list_2 = selected_client.get("Brokers list 2", [])
        Strategy_list = selected_client.get("Strategy list", [])
        Comments = selected_client.get("Comments", "")
        Smart_Contract = selected_client.get("Smart Contract", "")

        # Create a DataFrame to display the client data in tabular form
        data = {
            "Field": ["Name", "Username", "Email", "Password", "Phone Number", "Date of Birth", "Aadhar Card No",
                      "PAN Card No", "Bank Name", "Bank Account No", "Comments", "Smart Contract"],
            "Value": [str(Name), str(Username), str(Email), str(Password), str(Phone_Number), str(Date_of_Birth),
                      str(Aadhar_Card_No), str(PAN_Card_No), str(
                          Bank_Name), str(Bank_Account_No), str(Comments),
                      str(Smart_Contract)]
        }
        df = pd.DataFrame(data)

        # Display the DataFrame as a table with CSS styling and remove index column
        st.markdown(table_style, unsafe_allow_html=True)
        st.write(df.to_html(index=False, escape=False), unsafe_allow_html=True)

        # Display the broker list in a separate table
        st.subheader("Brokers")
        st.write("Broker 1")
        if isinstance(Brokers_list_1, list) and len(Brokers_list_1) > 0:
            broker_1_data = {
                "Field": [],
                "Value": []
            }
            for broker_1 in Brokers_list_1:
                broker_name = broker_1.get("broker_name", "")
        # If broker_name is a list, extract the first element
            if isinstance(broker_name, list) and broker_name:
                broker_name = broker_name[0]

            broker_1_data["Field"].extend(["Broker Name", "User Name", "Password", "2FA",
                                           "TotpAuth", "ApiKey", "ApiSecret", "Active", "Capital", "Risk profile"])
            broker_1_data["Value"].extend([
                str(broker_name),  # Use the processed broker_name value here
                str(broker_1.get("user_name", "")),
                str(broker_1.get("password", "")),
                str(broker_1.get("two_fa", "")),
                str(broker_1.get("totp_auth", "")),
                str(broker_1.get("api_key", "")),
                str(broker_1.get("api_secret", "")),
                str(broker_1.get("active", False)),
                "{:.2f}".format(broker_1.get("capital", 0.00)),
                str(broker_1.get("risk_profile", ""))
            ])

            broker_1_df = pd.DataFrame(broker_1_data)

            # Convert the values in the DataFrame to strings
            broker_1_df = broker_1_df.astype(str)

            # Display the DataFrame as a table with CSS styling and remove index column
            st.markdown(table_style, unsafe_allow_html=True)
            st.write(broker_1_df.to_html(index=False, escape=False),
                     unsafe_allow_html=True)

            # Add some space between the table and "Broker 2"
            st.markdown("<br>", unsafe_allow_html=True)  # Add this line

        st.write("Broker 2")
        if isinstance(Brokers_list_2, list) and len(Brokers_list_2) > 0:
            broker_2_data = {
                "Field": [],
                "Value": []
            }
            for broker_2 in Brokers_list_2:
                broker_name = broker_2.get("broker_name", "")
        # If broker_name is a list, extract the first element
            if isinstance(broker_name, list) and broker_name:
                broker_name = broker_name[0]

            for broker_2 in Brokers_list_2:
                broker_2_data["Field"].extend(["Broker Name", "User Name", "Password", "2FA",
                                               "TotpAuth", "ApiKey", "ApiSecret", "Active", "Capital", "Risk profile"])
                broker_2_data["Value"].extend([
                    str(broker_2.get("user_name", "")),
                    str(broker_2.get("password", "")),
                    str(broker_2.get("two_fa", "")),
                    str(broker_2.get("totp_auth", "")),
                    str(broker_2.get("api_key", "")),
                    str(broker_2.get("api_secret", "")),
                    str(broker_2.get("active", False)),
                    "{:.2f}".format(broker_2.get("capital", 0.00)),
                    str(broker_2.get("risk_profile", ""))
                ])

            broker_2_df = pd.DataFrame(broker_2_data)

            # Convert the values in the DataFrame to strings
            broker_2_df = broker_2_df.astype(str)

            # Display the DataFrame as a table with CSS styling and remove index column
            st.markdown(table_style, unsafe_allow_html=True)
            st.write(broker_2_df.to_html(index=False, escape=False),
                     unsafe_allow_html=True)
        else:
            st.warning("No broker data available.")

        # Display the strategy list in a separate table
        st.subheader("Strategies")
        if isinstance(Strategy_list, list) and len(Strategy_list) > 0:
            strategy_data = {
                "Strategy Name": [],
                "Broker": [],
                "Percentage Allocated": []
            }
        for strategy in Strategy_list:
            strategy_name = strategy.get("strategy_name", "")
            broker = strategy.get("broker", "")

            for selected_strategy in strategy_name:
                for selected_broker in broker:
                    perc_allocated_key = f"strategy_perc_allocated_{selected_strategy}_{selected_broker}_0"
                    percentage_allocated = strategy.get(perc_allocated_key, "")

                    strategy_data["Strategy Name"].append(selected_strategy)
                    strategy_data["Broker"].append(selected_broker)
                    strategy_data["Percentage Allocated"].append(
                        percentage_allocated)

        strategy_df = pd.DataFrame(strategy_data)
        # Display the DataFrame as a table with CSS styling and remove index column
        st.markdown(table_style, unsafe_allow_html=True)
        st.write(strategy_df.to_html(index=False, escape=False),
                 unsafe_allow_html=True)

        # Add some space between the table and the 'Edit' button
        st.markdown("<br>", unsafe_allow_html=True)

        # Add 'Edit' button to switch to 'edit mode'
        if st.button('Edit'):
            st.session_state.edit_mode = True

        # In edit mode, display the editable fields
        if st.session_state.get('edit_mode', False):
            updated_data = {}  # Store the updated client data
            updated_brokers_list_1 = []  # Store the updated brokers list 1
            updated_brokers_list_2 = []  # Store the updated brokers list 2
            updated_strategies_list = []  # Store the updated strategies list

            for i in range(len(df)):
                field = df.at[i, 'Field']
                value = df.at[i, 'Value']
                new_value = st.text_input(
                    field, value=value, key=f"{selected_client_name}-{field}")
                updated_data[field] = new_value

            # Edit profile picture
            st.subheader("Profile Picture")
            # Display the profile picture if available
            if profile_picture is not None or st.session_state.get('edit_mode', False):
                # Decode base64 string to bytes
                if profile_picture is not None:
                    profile_picture_bytes = base64.b64decode(profile_picture)
                else:
                    profile_picture_bytes = b""

                # Convert profile picture from bytes to PIL Image
                image = Image.open(io.BytesIO(profile_picture_bytes))

                # Display the image using st.image
                st.image(image, caption="Profile Picture",
                         use_column_width=True)
            new_profile_picture = st.file_uploader(
                "Upload New Profile Picture", type=["jpg", "jpeg"])
            if new_profile_picture is not None:
                update_profile_picture(
                    selected_client_name, new_profile_picture)
                st.success('Profile picture updated successfully.')
            elif profile_picture is None:
                new_profile_picture = st.file_uploader(
                    "Upload New Profile Picture", type=["jpg", "jpeg"])
                if new_profile_picture is not None:
                    update_profile_picture(
                        selected_client_name, new_profile_picture)

            # Edit brokers list
            st.subheader("Brokers")
            st.write("Broker 1")
            if isinstance(Brokers_list_1, list) and len(Brokers_list_1) > 0:
                for i, broker_1 in enumerate(Brokers_list_1):
                    broker_1["broker_name"] = st.multiselect(
                        "Broker Name", ["Zerodha", "AliceBlue"], default=broker_1.get("broker_name", []),
                        key=f"broker_name_1_{i}")
                    broker_1["user_name"] = st.text_input(
                        "User Name:", key=f"user_name_1_{i}", value=broker_1.get("user_name", ""))
                    broker_1["password"] = st.text_input(
                        "Password:", key=f"password_1_{i}", value=broker_1.get("password", ""))
                    broker_1["two_fa"] = st.text_input(
                        "2FA:", key=f"two_fa_1_{i}", value=broker_1.get("two_fa", ""))
                    broker_1["totp_auth"] = st.text_input(
                        "TotpAuth:", key=f"totp_auth_1_{i}", value=broker_1.get("totp_auth", ""))
                    broker_1["api_key"] = st.text_input(
                        "ApiKey:", key=f"api_key_1_{i}", value=broker_1.get("api_key", ""))
                    broker_1["api_secret"] = st.text_input(
                        "ApiSecret:", key=f"api_secret_1_{i}", value=broker_1.get("api_secret", ""))
                    broker_1["active"] = st.checkbox(
                        "Active:", key=f"active_1_{i}", value=broker_1.get("active", False))
                    broker_1["capital"] = st.number_input(
                        "Capital:", key=f"capital_1_{i}", value=broker_1.get("capital", ""))
                    broker_1["risk_profile"] = st.text_input("Risk profile:", key=f"risk_profile_1_{i}",
                                                             value=broker_1.get("risk_profile", ""))
                    updated_brokers_list_1.append(broker_1)

            st.write("Broker 2")

            if isinstance(Brokers_list_2, list) and len(Brokers_list_2) > 0:
                for i, broker_2 in enumerate(Brokers_list_2):
                    broker_2["broker_name"] = st.multiselect(
                        "Broker Name", ["Zerodha", "AliceBlue"], default=broker_2.get("broker_name", []),
                        key=f"broker_name_2_{i}")
                    broker_2["user_name"] = st.text_input(
                        "User Name:", key=f"user_name_2_{i}", value=broker_2.get("user_name", ""))
                    broker_2["password"] = st.text_input(
                        "Password:", key=f"password_2_{i}", value=broker_2.get("password", ""))
                    broker_2["two_fa"] = st.text_input(
                        "2FA:", key=f"two_fa_2_{i}", value=broker_2.get("two_fa", ""))
                    broker_2["totp_auth"] = st.text_input(
                        "TotpAuth:", key=f"totp_auth_2_{i}", value=broker_2.get("totp_auth", ""))
                    broker_2["api_key"] = st.text_input(
                        "ApiKey:", key=f"api_key_2_{i}", value=broker_2.get("api_key", ""))
                    broker_2["api_secret"] = st.text_input(
                        "ApiSecret:", key=f"api_secret_2_{i}", value=broker_2.get("api_secret", ""))
                    broker_2["active"] = st.checkbox(
                        "Active:", key=f"active_2_{i}", value=broker_2.get("active", False))
                    broker_2["capital"] = st.number_input(
                        "Capital:", key=f"capital_2_{i}", value=broker_2.get("capital", ""))
                    broker_2["risk_profile"] = st.text_input("Risk profile:", key=f"risk_profile_2_{i}",
                                                             value=broker_2.get("risk_profile", ""))
                    updated_brokers_list_2.append(broker_2)

            # Edit strategies list
            st.subheader("Strategies")
            if isinstance(Strategy_list, list) and len(Strategy_list) > 0:
                for i, strategy in enumerate(Strategy_list):
                    strategy["strategy_name"] = st.multiselect(
                        f"Strategy Name {i+1}", ["AmiPy", "MP Wizard", "ZRM", "Overnight Options", "Screenipy Stocks"], default=strategy.get("strategy_name", []), key=f"strategy_name_{i}")
                    strategy["broker"] = st.multiselect(
                        f"Broker {i+1}", ["Zerodha", "AliceBlue"], default=strategy.get("broker", []), key=f"strategy_broker_{i}")
                    selected_strategies = strategy["strategy_name"]
                    selected_brokers = strategy["broker"]

                    for selected_strategy in selected_strategies:
                        for selected_broker_name in selected_brokers:
                            # Modify the key format here
                            perc_allocated_key = f"strategy_perc_allocated_{selected_strategy}_{selected_broker_name}_0"
                            # Retrieve the value using the updated key
                            percentage_allocated = strategy.get(
                                perc_allocated_key, "")
                            options = [f"{i/10:.1f}%" for i in range(0, 101)]
                            default_index = options.index(percentage_allocated)
                            selected_percentage_allocated = st.selectbox(
                                f"Percentage Allocated for {selected_strategy} and {selected_broker_name} (%):", options, index=default_index, key=f"strategy_perc_allocated_{selected_strategy}_{selected_broker_name}_{i}")
                            # Set the selected value
                            strategy[perc_allocated_key] = selected_percentage_allocated
                    updated_strategies_list.append(strategy)

            # Update the changes in the database when Update button is clicked
            if st.button('Update'):
                if updated_data or updated_brokers_list_1 or updated_brokers_list_2 or updated_strategies_list:
                    if updated_data:
                        update_client_data(selected_client_name, updated_data)
                    if updated_brokers_list_1 or updated_brokers_list_2:
                        update_brokers_data(
                            selected_client_name, updated_brokers_list_1, updated_brokers_list_2)
                    if updated_strategies_list:
                        update_strategies_data(
                            selected_client_name, updated_strategies_list)

                    st.success('Client details updated successfully.')
                st.session_state.edit_mode = False  # Switch out of edit mode

def login():

    username = st.text_input('Admin Username')
    password = st.text_input('Password', type='password')

    if st.button('Login'):
        if login_admin(username, password):
            st.session_state.login_successful = True
            st.experimental_rerun()
        else:
            st.error('Invalid username or password.')


def logout():
    st.session_state.login_successful = False


def main():
    if st.session_state.get('login_successful', False):
        # If the admin is logged in, show the client selection page
        select_client()
        if st.sidebar.button('Logout'):
            logout()
    else:
        # If the admin is not logged in, show the login page
        login()


if __name__ == '__main__':
    main()