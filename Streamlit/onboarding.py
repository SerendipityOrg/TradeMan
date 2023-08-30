import streamlit as st
from datetime import date, datetime
from PIL import Image
from pymongo import MongoClient
import os
import io


# Connect to MongoDB
MONGO_URL = os.environ.get("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["TrademanUserProfile"]
clients_collection = db["Clients"]

def onboarding_page(*args, **kwargs):
    # Check if the 'brokers' key exists in the session state, otherwise initialize it
    if 'brokers' not in st.session_state:
        st.session_state.brokers = []

    # Check if the 'strategies' key exists in the session state, otherwise initialize it
    if 'strategies' not in st.session_state:
        st.session_state.strategies = []

    # Set the title for the Streamlit app
    st.title("Client Onboarding")

    # Take inputs for client information
    name = st.text_input("Name:")
    dob = st.date_input("Date of Birth:", min_value=date(1950, 1, 1))
    dob = datetime.combine(dob, datetime.min.time())  # Convert date to datetime
    phone = st.text_input("Phone Number:")
    email = st.text_input("Email:")
    aadhar = st.text_input("Aadhar Card No:")
    pan = st.text_input("Pan Card No:")
    bank_account = st.text_input("Bank Account No:")
    profile_picture = st.file_uploader("Profile Picture", type=["png", "jpg", "jpeg"])

    # Add a header for the brokers section
    st.subheader("Brokers")

    # Add a button to allow addition of new broker details
    add_broker = st.button("Add Broker")
    if add_broker:
        # Only add a new broker field if the last one is filled
        if len(st.session_state.brokers) == 0 or any(st.session_state.brokers[-1].values()):
            st.session_state.brokers.append({})

    # Create dynamic input fields for broker information
    for i, broker in enumerate(st.session_state.brokers):
        broker_name = st.selectbox("Broker Name", ["Zerodha", "AliceBlue"], key=f"broker_name_{i}")
        broker["broker_name"] = broker_name

        # Rest of the broker fields
        broker["user_name"] = st.text_input("User Name:", key=f"user_name_{i}")
        broker["password"] = st.text_input("Password:", key=f"password_{i}")
        broker["two_fa"] = st.text_input("2FA:", key=f"two_fa_{i}")
        broker["totp_auth"] = st.text_input("TotpAuth:", key=f"totp_auth_{i}")
        broker["api_key"] = st.text_input("ApiKey:", key=f"api_key_{i}")
        broker["api_secret"] = st.text_input("ApiSecret:", key=f"api_secret_{i}")
        broker["active"] = st.checkbox("Active:", key=f"active_{i}")
        broker["capital"] = st.number_input("Capital:", key=f"capital_{i}")
        broker["risk_profile"] = st.text_input("Risk profile:", key=f"risk_profile_{i}")

    # Add a header for the strategies section
    st.subheader("Strategies Subscribed")

    # Add a button to allow addition of new strategy details
    add_strategy = st.button("Add Strategy")
    if add_strategy:
        # Only add a new strategy field if the last one is filled
        if len(st.session_state.strategies) == 0 or any(st.session_state.strategies[-1].values()):
            st.session_state.strategies.append({})

    # Create dynamic input fields for strategy information
    for i, strategy in enumerate(st.session_state.strategies):
        strategy["strategy_name"] = st.multiselect("Strategy Name", ["SMA"], key=f"strategy_name_{i}")
        strategy["broker"] = st.multiselect("Broker", ["Zerodha", "AliceBlue"], key=f"strategy_broker_name_{i}")
        strategy["perc_allocated"] = st.selectbox("Percentage Allocated (%):", options=[f"{i}%" for i in range(1, 101)], key=f"strategy_perc_allocated_{i}")

    # Take input for comments
    comments = st.text_area("Comments:")

    # Add a submit button
    submit = st.button("Submit")

    # Check if the submit button is clicked
    if submit:
        # Check if all the fields are filled before submitting
        if name and dob and phone and email and aadhar and pan and bank_account and st.session_state.brokers and st.session_state.strategies:
            # Create a dictionary with all the client data
            client_data = {
                "name": name,
                "dob": dob,
                "phone": phone,
                "email": email,
                "aadhar": aadhar,
                "pan": pan,
                "bank_account": bank_account,
                "brokers": st.session_state.brokers,
                "strategies_subscribed": st.session_state.strategies,
                "comments": comments
            }

            # Save the uploaded profile picture as binary data if it exists
            if profile_picture is not None:
                # Open the image using PIL
                image = Image.open(profile_picture)

                # Convert the image to JPEG format
                image = image.convert("JPEG")

                # Create a BytesIO object to hold the image data
                image_bytes = io.BytesIO()

                # Save the image to the BytesIO object in JPEG format
                image.save(image_bytes, format="JPEG")

                # Get the image bytes as a bytearray
                image_bytearray = image_bytes.getvalue()

                # Assign the image bytearray to the client dictionary
                client_data["profile_picture"] = image_bytearray

            # Add the client to the database
            clients_data_collection.insert_one(client_data)

            # Show a success message
            st.success("Client added successfully!")
        else:
            # If not all fields are filled, show an error message
            unfilled_fields = []
            if not name:
                unfilled_fields.append("Name")
            if not dob:
                unfilled_fields.append("Date of Birth")
            if not phone:
                unfilled_fields.append("Phone Number")
            if not email:
                unfilled_fields.append("Email")
            if not aadhar:
                unfilled_fields.append("Aadhar Card No")
            if not pan:
                unfilled_fields.append("Pan Card No")
            if not bank_account:
                unfilled_fields.append("Bank Account No")
            if not st.session_state.brokers:
                unfilled_fields.append("Brokers")
            if not st.session_state.strategies:
                unfilled_fields.append("Strategies Subscribed")

            error_message = "Please fill the following fields: " + ", ".join(unfilled_fields)
            st.error(error_message)


if __name__ == "__main__":
    onboarding_page()
