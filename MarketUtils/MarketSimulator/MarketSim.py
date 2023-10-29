import pandas as pd
import time
import datetime

# Load the csv file
df = pd.read_csv('nifty_50.csv')

# Convert the date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort the dataframe by date
df = df.sort_values('date')

# The time difference in seconds between each row (in real world, it's 60 seconds)
time_difference = 60

# The speed of simulation (5x speed)
simulation_speed = 5

# The actual sleep time in seconds between each row
sleep_time = time_difference / simulation_speed

# Iterate over each row in the dataframe
for index, row in df.iterrows():
    # Print the row data
    print(row)

    # Sleep for the required time
    time.sleep(sleep_time)
