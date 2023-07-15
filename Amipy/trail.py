from kiteconnect import KiteConnect
import datetime

kite = KiteConnect(api_key="6b0dp5ussukmo67h",access_token="lYa6IRWuhTQJhokb3TCUouecGOaXpftk")

# ltp_data = kite.ltp([260105,256265])
# ltp = ltp_data['last_price']
# print(ltp_data)
def get_previous_dates(num_dates):
    dates = []
    current_date = datetime.date.today()

    while len(dates) < num_dates:
        current_date -= datetime.timedelta(days=1)

        if current_date.weekday() >= 5 or current_date in holidays:
            continue

        dates.append(current_date.strftime("%Y-%m-%d"))

    return dates

# List of holidays
holidays = [
    datetime.date(2023, 1, 26),
    datetime.date(2023, 3, 7),
    datetime.date(2023, 3, 30),
    datetime.date(2023, 4, 4),
    datetime.date(2023, 4, 7),
    datetime.date(2023, 4, 14),
    datetime.date(2023, 4, 22),
    datetime.date(2023, 5, 1),
    datetime.date(2023, 6, 28),
    datetime.date(2023, 8, 15),
    datetime.date(2023, 9, 19),
    datetime.date(2023, 10, 2),
    datetime.date(2023, 10, 24),
    datetime.date(2023, 11, 14),
    datetime.date(2023, 11, 27),
    datetime.date(2023, 12, 25)
]

previous_dates = get_previous_dates(5)
tokens = [260105,256265,257801]
for token in tokens:
    data = kite.historical_data(instrument_token=token, from_date=previous_dates[-1], to_date=previous_dates[0], interval="day")

    # Calculate range for each day and find average range
    ranges = [d['high'] - d['low'] for d in data]
    average_range = sum(ranges) / len(ranges)

    print("Average range for {} is {}".format(token, average_range))

# today = kite.historical_data(260105,"2023-07-13 09:15:00","2023-07-13 10:10:00","hour")
# print(today)
# ltp_data = kite.ltp([260105,256265])
# ltp = ltp_data['last_price']
# print(ltp_data)
