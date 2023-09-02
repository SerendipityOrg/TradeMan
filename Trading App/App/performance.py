# Import required libraries
import firebase_admin
from firebase_admin import credentials, storage
from datetime import timedelta
import openpyxl
import requests
import zipfile

# Initialize Firebase with credentials and database/storage details
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://trading-app-caf8e-default-rtdb.firebaseio.com',
    'storageBucket': 'gs://trading-app-caf8e.appspot.com'
})

# Reference the Excel file in Firebase Storage
bucket = storage.bucket()
# Replace {username} with the actual username
blob = bucket.blob('/clientsexcel/brijesh.xlsx')

# Generate a signed URL to download the Excel file
url = blob.generate_signed_url(timedelta(seconds=300), method='GET')

# Download the Excel file using the signed URL
response = requests.get(url)

# Check if the download was successful (HTTP status code 200)
if response.status_code == 200:
    # Save the downloaded content as an Excel file
    with open('local-excel-file.xlsx', 'wb') as f:
        f.write(response.content)
else:
    print("Failed to download the file.")
    exit(1)  # Exit the script if download fails

# Try to read the Excel file
try:
    # Load the workbook and select the active sheet
    wb = openpyxl.load_workbook('local-excel-file.xlsx')
    sheet = wb.active

    # Create an empty list to store the rows
    data = []

    # Loop through each row in the sheet to read specific columns
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=1, max_col=11):
        strategy = row[0].value  # Strategy is in the 1st column
        index = row[1].value     # Index is in the 2nd column
        date = row[3].value      # Date is in the 4th column
        pnl = row[10].value      # PnL is in the 11th column

        # Append the row data to the list
        data.append([strategy, index, date, pnl])

    # Print the retrieved data
    for record in data:
        print(record)

except zipfile.BadZipFile:
    print("File is not a valid Excel file.")
