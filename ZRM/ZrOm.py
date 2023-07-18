import json
import csv
import os
import argparse

from csv import writer
from datetime import datetime
from kiteconnect import KiteConnect
from ZrOm_calc import get_option_tokens,get_zrm_users, get_expiry_dates
from place_order import *
from time import sleep

script_dir = os.path.dirname(os.path.abspath(__file__))
zerodha_omkar_filepath = os.path.join(script_dir, '..', 'Utils', 'users/omkar.json')
broker_filepath = os.path.join(script_dir, '..', 'Utils', 'broker.json')


# Parsing the base entry time to a format which can be compared with current time
base_entry_time = datetime.strptime("09:24:00", "%H:%M:%S").time()

users_to_trade = get_zrm_users(broker_filepath)
print(users_to_trade)

class Algo:
    base_entry_price = 0
    
    zone_width = 50
    quantity = 50
    is_trade_cycle_done = False
    long_entry = False
    short_entry = False
    long_entry_count = 0
    short_entry_count = 0
    order_book = []
    trade_cycle_count = 1
    open_order_counts = 0
    init_timer = None 
    one_print = False
    result_csv = ""

    def __init__(self, csv, zone_width,users):
        self.result_csv = csv
        self.zone_width = zone_width
        self.users = users

    def is_trade_complete(self):
        return self.is_trade_cycle_done

    # Same existing functions here
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

    def write_results_csv(self, file):
        with open(file, 'a') as f_object:
            # Pass this file object to csv.writer()
            # and get a writer object
            writer_object = writer(f_object)
            # Pass the list as an argument into
            # the writerow()
            for trans in self.order_book:
                row = [trans['trade_cycle'], trans['order_type'], trans['entry_point'], trans['entry_price'],
                       trans['entry_time'], trans['exit_time'], trans['exit_price'],
                       trans['exit_point'], trans['is_order_closed'], trans['quantity']]
                writer_object.writerow(row)
            # Close the file object
            f_object.close()

    str_prc = ""    

    def run(self, tick_price, tick_time):
        global str_prc
        expiry_date = get_expiry_dates()[0]
        # Check the base entry time constraint before entering the trades
        current_time = datetime.now().time()
        if current_time < base_entry_time:
            print("Waiting for base entry time")
            return

        # Rest of the existing 'run' function here
        if self.init_timer is None:            
            self.init_timer = datetime.now()
            
        elif ((datetime.fromtimestamp(tick_time)) - self.init_timer).total_seconds() >= 30:
            if self.one_print is False:
                print("#@# Base Entry Price is set to --> {}".format(tick_price))
                self.base_entry_price = tick_price
                self.one_print = True
                print("Base Entry Price is set to --> {}".format(self.base_entry_price))    
                # Place entry order here
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
                    #Squareoff ZrOm orders

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
                    
                    str_prc = round(tick_price/100)*100
                    tokens,trading_symbol,trading_symbol_aliceblue = get_option_tokens("BANKNIFTY",expiry_date,str_prc,"CE")
                    for brokers, users in self.users:
                        if brokers == "aliceblue":
                            order_id = place_aliceblue_order(trading_symbol_aliceblue,"BUY",point,q,str_prc,"BANKNIFTY",users)
                        elif brokers == "zerodha":
                            order_id = place_zerodha_order(trading_symbol,"BUY",point,q,str_prc,"BANKNIFTY",users)
                    # order_id = place_zerodha_order(trading_symbol,"BUY",point,q,str_prc,"BANKNIFTY")###################################################
                    # place CE orders here
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

                    print("str_prc",str_prc)
                    tokens,trading_symbol,trading_symbol_aliceblue = get_option_tokens("BANKNIFTY",expiry_date,str_prc,"PE")
                    for brokers, users in self.users:
                        if brokers == "aliceblue":
                            order_id = place_aliceblue_order(trading_symbol_aliceblue,"BUY",point,q,str_prc,"BANKNIFTY", users)
                        elif brokers == "zerodha":
                            order_id = place_zerodha_order(trading_symbol,"BUY",point,q,str_prc,"BANKNIFTY", users)
                    # order_id = place_zerodha_order(trading_symbol,"BUY",point,q,str_prc,"BANKNIFTY") ########################################################
                    # place PE orders here
                    self.add_item_order_book(self.trade_cycle_count, "Short", point, tick_price, m_time, "", "", "", False, q)
                    self.open_order_counts += 1
                    self.short_entry_count += 1
                    is_condition = True

                # Long exits logic
                if tick_price >= self.base_entry_price + self.zone_width and is_condition is False:
                    print("Closing first order.. ** With Profits")
                    is_condition = True
                    point = "P" + str(self.long_entry_count - 1)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    self.exit_all_open_orders(point, tick_price, m_time)
                    #Squareoff ZrOm orders

                # Short Exits
                if tick_price <= self.base_entry_price - (
                        self.zone_width * 2) and self.open_order_counts > 0 and is_condition is False:
                    print("Closing all exits orders.. ** With No Profits/Loss")
                    is_condition = True
                    point = "R" + str(self.short_entry_count - 1)
                    m_time = datetime.fromtimestamp(int(tick_time) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    self.exit_all_open_orders(point, tick_price, m_time)
                    #Squareoff ZrOm orders

            else:
                print("*********** Order Logs ************")
                print(json.dumps(self.order_book, indent=3))
                self.write_results_csv(self.result_csv)



def main(zone_width):
    order_open = False
    # Initialize KiteConnect object

    with open(zerodha_omkar_filepath) as json_file:
        data = json.load(json_file)
    api_key = data.get('zerodha', {}).get('api_key')
    access_token = data.get('zerodha', {}).get('access_token')
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # open the file in the write mode
    header = ['trace_cycle', 'order_type', 'entry_point', 'entry_price', 'entry_time', 'exit_time', 'exit_price', 'exit_point',
              'is_order_closed', 'quantity']
    file_path = os.getcwd()+"/cryptoticks_results_" + datetime.now().strftime("%Y_%m_%d-%H-%M-%S") + ".csv"
    with open(file_path, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    objalgo = Algo(file_path, zone_width,users_to_trade)

    while True:
        try:
            # Fetching ltp of the instrument
            nifty_token = 256265  # Nifty token
            bnf_token = 260105
            ltp_data = kite.ltp(bnf_token)
            tick_price = ltp_data[str(bnf_token)]['last_price']
            tick_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')  # Current time
            tick_time_obj = datetime.strptime(tick_time, '%d-%m-%Y %H:%M:%S')
            tick_time = tick_time_obj.timestamp()

            objalgo.run(tick_price, tick_time)

            # Check if trade cycle is complete
            if objalgo.is_trade_complete():
                print("Trade cycle completed. Exiting...")
                break

        except Exception as e:
            print("Error:", str(e))
        sleep(1)  # Interval between successive ltp checks

if __name__ == "__main__":
    main(zone_width=50)  # Set the desired zone width
