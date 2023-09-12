import json
import csv
import os
import argparse
from csv import writer
import time
from datetime import datetime
import pandas as pd
import psycopg2
import pandas.io.sql as sqlio

class Algo:
    base_entry_price = 0
    zone_width = 0
    quantity = 25
    is_trade_cycle_done = False
    long_entry = False
    short_entry = False
    long_entry_count = 0
    short_entry_count = 0
    order_book = []
    trade_cycle_count = 1
    open_order_counts = 0
    init_timer = None #int(time.perf_counter())
    one_print = False
    result_csv = ""

    def __init__(self, csv, zone_width):
        self.result_csv = csv
        self.zone_width = zone_width

    def reinit(self):
        self.base_entry_price = 0
        self.is_trade_cycle_done = False
        self.long_entry = False
        self.short_entry = False
        self.long_entry_count = 0
        self.short_entry_count = 0
        self.order_book = []
        self.open_order_counts = 0
        self.init_timer = None #int(time.perf_counter())
        self.one_print = False

    def write_results_csv(self, file):
        with open(file,'a', newline='',encoding='UTF8') as f_object:
            # Pass this file object to csv.writer() and get a writer object
            writer_object = writer(f_object)
            # Pass the list as an argument into the writerow()
            for trans in self.order_book:
                row = [trans['trade_cycle'], trans['order_type'], trans['entry_point'], trans['entry_price'],
                       trans['entry_time'], trans['exit_time'], trans['exit_price'],
                       trans['exit_point'], trans['is_order_closed'], trans['quantity']]
                writer_object.writerow(row)
            # Close the file object
            f_object.close()

    def add_item_order_book(self, trade_cycle, order_type, entry_point, entry_price, entry_time, exit_time, exit_price,
                            exit_point, is_order_closed, quantity):
        self.order_book.append(
            {
                "trade_cycle": trade_cycle,
                "order_type": order_type,
                "entry_point": entry_point,
                "entry_price": entry_price,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "exit_price": exit_price,
                "exit_point": exit_point,
                "is_order_closed": is_order_closed,
                "quantity": quantity
            }
        )

    def exit_all_open_orders(self, point, tick_price, tick_time):
        try:
            for idx, item in enumerate(self.order_book):
                if self.order_book[idx]["order_type"] == "long":
                    print("Placed long sell order (exits)")
                    print("Transaction Details - \n\t entry_price {0} \n\t exit_price {1}".
                          format(self.order_book[idx]["entry_price"], tick_price))

                else:
                    print("Placed short buy order (exits)")
                    print("Transaction Details - \n\t entry_price {0} \n\t exit_price {1}".
                          format(self.order_book[idx]["entry_price"], tick_price))
                self.order_book[idx]["exit_time"] = tick_time
                self.order_book[idx]["exit_price"] = tick_price
                self.order_book[idx]["exit_point"] = point
                self.order_book[idx]["is_order_closed"] = True
                self.open_order_counts -= 1
                self.is_trade_cycle_done = True
            self.trade_cycle_count += 1
        except:
            pass

    def run(self, tick_price, tick_time):
        if self.init_timer is None:
            self.init_timer = tick_time/1000
        elif (tick_time/1000) - self.init_timer >= 60:
            if self.one_print is False:
                print("#@# Base Entry Price is set to --> {}".format(tick_price))
                self.base_entry_price = tick_price
                self.one_print = True
            is_condition = False
            if self.is_trade_cycle_done is False:
                # Loss Exit consecutive 5 trade are happened, close all existing orders
                if tick_price <= (self.base_entry_price - self.zone_width) and \
                        self.short_entry_count == 2 and self.long_entry_count == 3 and is_condition is False:
                    print("Placed exits orders.. ** With Loss")
                    is_condition = True
                    point = "S" + str(self.short_entry_count)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    self.exit_all_open_orders(point, tick_price, m_time)

                # First base entry logic with below condition
                # This is to handle to do long buy when it touched short sell zone and come back base entry price
                if tick_price >= self.base_entry_price and self.long_entry_count == self.short_entry_count and is_condition is False:
                    print("Placed long buy Order at {} (Long Entry)".format(tick_price))
                    point = 'L' + str(self.long_entry_count)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    q = self.quantity
                    if point == 'L0':
                        q = self.quantity
                    elif point == 'L1':
                        q = self.quantity * 3
                    elif point == 'L2':
                        q = self.quantity * 12
                    self.add_item_order_book(self.trade_cycle_count, "Long", point, tick_price, m_time, "", "", "", False, q)
                    self.open_order_counts += 1
                    self.long_entry_count += 1
                    is_condition = True
                # Short Entry logic
                if tick_price <= (self.base_entry_price - self.zone_width) and \
                        (self.short_entry_count == (self.long_entry_count - 1)) and is_condition is False:
                    print("Placed short sell Order at {} (Short Entry)".format(tick_price))
                    point = 'S' + str(self.short_entry_count)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    q = self.quantity
                    if point == 'S0':
                        q = self.quantity * 2
                    elif point == 'S1':
                        q = self.quantity * 6
                    self.add_item_order_book(self.trade_cycle_count, "Short", point, tick_price, m_time, "", "", "", False, q)
                    self.open_order_counts += 1
                    self.short_entry_count += 1
                    is_condition = True

                # Long exits logic
                if tick_price >= self.base_entry_price + self.zone_width and is_condition is False:
                    print("Closing all exits orders.. ** With Profits**")
                    is_condition = True
                    point = "P" + str(self.long_entry_count - 1)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    self.exit_all_open_orders(point, tick_price, m_time)

                # Short Exits
                if tick_price <= self.base_entry_price - (
                        self.zone_width * 2) and self.open_order_counts > 0 and is_condition is False:
                    print("Closing all exits orders.. ** With No Profits/Loss")
                    is_condition = True
                    point = "R" + str(self.short_entry_count - 1)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    self.exit_all_open_orders(point, tick_price, m_time)

            else:
                print("*********** Order Logs ************")
                print(json.dumps(self.order_book, indent=3))
                self.write_results_csv(self.result_csv)
                self.reinit()

def main(zone_width):
    order_open = False

    # open the file in the write mode
    header = ['trace_cycle', 'order_type', 'entry_point', 'entry_price', 'entry_time', 'exit_time', 'exit_price', 'exit_point',
              'is_order_closed', 'quantity']
    file_path = os.getcwd()+"/call_option_results_" + datetime.now().strftime("%Y_%m_%d-%H-%M-%S") + ".csv"
    with open(file_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
    
    objalgo = Algo(file_path, zone_width)
    
def add_pnl_column(input_csv):
    margin_per_lot = 40000/25
    df = pd.read_csv(input_csv)
    df['PnL'] = df.apply(lambda row: (row['exit_price'] - row['entry_price']) * row['quantity'] if row['order_type'] == 'Long' else (row['entry_price'] - row['exit_price']) * row['quantity'], axis=1)
    df['Margin Used'] = df.apply(lambda row: row['entry_price'] * row['quantity'] if row['order_type'] == 'Long' else margin_per_lot * row['quantity'], axis=1)
    
    # if df['Margin Used'] is same between two rows

    
    # print net sum of df['PnL'] column
    print('Net PnL for this period:',df['PnL'].sum())
    
    df.to_csv(input_csv, index=False)
   
def process_csv_data(file_path, zone_width,tokenName):
    header = ['trace_cycle', 'order_type', 'entry_point', 'entry_price', 'entry_time', 'exit_time', 'exit_price',
              'exit_point', 'is_order_closed', 'quantity']
    results_file_path = os.getcwd() + "/test_" + datetime.now().strftime("%Y_%m_%d-%H-%M-%S") + ".csv"
    
    with open(results_file_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
    
    df = pd.read_csv(file_path)
    algo = Algo(results_file_path, zone_width)

    for index, row in df.iterrows():
        tick_price = row['close']
        tick_time = pd.Timestamp(row['date']).timestamp() * 1000
        algo.run(float(tick_price), tick_time)
        
    add_pnl_column(results_file_path)
    
def process_tsdb_data(token, zone_width):
    connection = psycopg2.connect(
        dbname="ohlc_token",
        user="postgres",
        password="K@nnada123",
        host="localhost",
        port="5432"
    )
    
    header = ['trace_cycle', 'order_type', 'entry_point', 'entry_price', 'entry_time', 'exit_time', 'exit_price',
              'exit_point', 'is_order_closed', 'quantity']
    results_file_path = os.getcwd() + "/test_" + datetime.now().strftime("%Y_%m_%d-%H-%M-%S") + ".csv"
    
    with open(results_file_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
    
    table_name = 'ohlc_' + str(token)

    with connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'Asia/Kolkata';")
        query = f"SELECT * FROM {table_name};"
        df = sqlio.read_sql_query(query, connection)
  
    algo = Algo(results_file_path, zone_width)

    for index, row in df.iterrows():
        tick_price = row['close']
        tick_time = pd.Timestamp(row['date']).timestamp() * 1000
        algo.run(float(tick_price), tick_time)
        
    add_pnl_column(results_file_path)

    
if __name__ == "__main__":

    from datetime import timedelta, date, datetime
    cmdLineParser = argparse.ArgumentParser("ZRMticks Trade Engine - ")
    cmdLineParser.add_argument("-m", "--mode", action="store", type=str,
                               dest="mode", default="H",
                               help="The IP to get IB Gateway connection")
    cmdLineParser.add_argument("-sd", "--startdate", action="store", type=str,
                               dest="startdate", default=date.today().strftime("%d-%m-%Y"),
                               help="Date (dd-mm-yyyy) For eg: 20-01-2022")
    cmdLineParser.add_argument("-ed", "--enddate", action="store", type=str,
                               dest="enddate", default=date.today().strftime("%d-%m-%Y"),
                               help="Date (dd-mm-yyyy) For eg: 20-01-2022")
    cmdLineParser.add_argument("-zw", "--zonewidth", action="store", type=int,
                               dest="zonewidth", default=25,
                               help="Movement zone width For eg: 25")
    args = cmdLineParser.parse_args()

    def date_range(date1, date2):
        for n in range(int((date2 - date1).days) + 2):
            yield date1 + timedelta(n)
       
    if args.mode == 'CSV':
        csv_file_path = r'ohlc_256265.csv'
        
        # tokenName = everything after ohlc_
        tokenName = csv_file_path.split('_')[1].split('.')[0]
        
        # prinT
        print('tokenName :',tokenName)
        
        process_csv_data(csv_file_path, args.zonewidth,tokenName)
        
    elif args.mode == 'DB':
                
        tokens = [10333442, 10333698, 10333954, 10334210, 10334466, 10334722, 10334978, 10335490, 10335746, 10336002, 10336258, 10336514, 10336770, 10337026, 10337282, 10337538, 10337794, 10338306, 10338562, 10339074, 10339330, 10339842, 10340610, 10340866, 10341122, 10342914, 10343426, 10343682, 10343938, 10344194, 10344450, 10345218, 10345986, 10346242, 10347522, 10347778, 10348290, 10349570, 10349826, 10350338, 10350594, 10351874]
        
        for token in tokens:
            process_tsdb_data(token, args.zonewidth)
        
    else:
        main(args.zonewidth)