import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
from PIL import Image
import io
import os
import base64

table_style = """
<style>
table.dataframe {
    border-collapse: collapse;
    width: 100%;
}

table.dataframe th,
table.dataframe td {
    border: 1px solid black;
    padding: 8px;
    text-align: left; /* Align text to the left */
}

table.dataframe th {
    background-color: #f2f2f2;
}

table.dataframe tr:nth-child(even) {
    background-color: #f2f2f2;
}

table.dataframe tr:hover {
    background-color: #ddd;
}
</style>
"""
# Check if Firebase app is already initialized
if not firebase_admin._apps:
    # Initialize Firebase app
    cred = credentials.Certificate("credentials.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://trading-app-caf8e-default-rtdb.firebaseio.com'
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
            show_profile(client_data)
        else:
            st.warning("No client data available.")
    elif selected == "Performance Dashboard":
        show_performance_dashboard()
    elif selected == "Logout":
        logout()
        st.experimental_rerun()


def show_profile(client_data):
    profile_picture = client_data.get("Profile Picture")
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
                    top: -40px;  /* Adjust the top value as needed */
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

    pd.options.display.float_format = '{:,.2f}'.format
    # Set the title for the Streamlit app
    st.markdown("<h3 style='color: darkblue'>Profile</h3>",
                unsafe_allow_html=True)

    # Extract client data from the dictionary
    Name = client_data.get("Name", "")
    Username = client_data.get("Username", "")
    Email = client_data.get("Email", "")
    Password = client_data.get("Password", "")
    Phone_Number = client_data.get("Phone Number", "")
    Date_of_Birth = client_data.get("Date of Birth", "")
    Aadhar_Card_No = client_data.get("Aadhar Card No", "")
    PAN_Card_No = client_data.get("PAN Card No", "")
    Bank_Name = client_data.get("Bank Name", "")
    Bank_Account_No = client_data.get("Bank Account No", "")
    Brokers_list_1 = client_data.get("Brokers list 1", [])
    Brokers_list_2 = client_data.get("Brokers list 2", [])
    Strategy_list = client_data.get("Strategy list", [])
    Comments = client_data.get("Comments", "")
    Smart_Contract = client_data.get("Smart Contract", "")

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

    # Display the broker list in vertical tabular form
    st.subheader("Brokers")
    st.write("Broker 1")
    if isinstance(Brokers_list_1, list) and len(Brokers_list_1) > 0:
        broker_1_data = {
            "Field": [],
            "Value": []
        }
        for broker_1 in Brokers_list_1:
            broker_1_data["Field"].extend(["Broker Name", "User Name", "Password", "2FA",
                                           "TotpAuth", "ApiKey", "ApiSecret", "Active", "Capital", "Risk profile"])
            broker_1_data["Value"].extend([
                str(broker_1.get("broker_name", [""])[0]),
                str(broker_1.get("user_name", "")),
                str(broker_1.get("password", "")),
                str(broker_1.get("two_fa", "")),
                str(broker_1.get("totp_auth", "")),
                str(broker_1.get("api_key", "")),
                str(broker_1.get("api_secret", "")),
                str(broker_1.get("active", "")),
                "{:.2f}".format(broker_1.get("capital", 0.00)),
                str(broker_1.get("risk_profile", ""))
            ])

        broker_1_df = pd.DataFrame(broker_1_data)
        # Display the DataFrame as a table with CSS styling and remove index column
        st.markdown(table_style, unsafe_allow_html=True)
        st.write(broker_1_df.to_html(index=False, escape=False),
                 unsafe_allow_html=True)

        # Add some space between the table and "Broker 2"
        st.markdown("<br>", unsafe_allow_html=True)  # Add this line
    else:
        st.warning("No broker data available.")

    st.write("Broker 2")
    if isinstance(Brokers_list_2, list) and len(Brokers_list_2) > 0:
        broker_2_data = {
            "Field": [],
            "Value": []
        }
        for broker_2 in Brokers_list_2:
            broker_2_data["Field"].extend(["Broker Name", "User Name", "Password", "2FA",
                                           "TotpAuth", "ApiKey", "ApiSecret", "Active", "Capital", "Risk profile"])
            broker_2_data["Value"].extend([
                str(broker_2.get("broker_name", [""])[0]),
                str(broker_2.get("user_name", "")),
                str(broker_2.get("password", "")),
                str(broker_2.get("two_fa", "")),
                str(broker_2.get("totp_auth", "")),
                str(broker_2.get("api_key", "")),
                str(broker_2.get("api_secret", "")),
                str(broker_2.get("active", "")),
                "{:.2f}".format(broker_2.get("capital", 0.00)),
                str(broker_2.get("risk_profile", ""))
            ])

        broker_2_df = pd.DataFrame(broker_2_data)
        # Display the DataFrame as a table with CSS styling and remove index column
        st.markdown(table_style, unsafe_allow_html=True)
        st.write(broker_2_df.to_html(index=False, escape=False),
                 unsafe_allow_html=True)
    else:
        st.warning("No broker data available.")

     # Display the strategy list in vertical tabular form
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


def logout():
    # Reset session state variables
    session_state.logged_in = False
    session_state.client_data = None


def show_performance_dashboard():
    # Set the title for the Streamlit app
    st.markdown("<h3 style='color: darkblue'>Performance Dashboard</h3>",
                unsafe_allow_html=True)
