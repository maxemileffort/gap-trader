# shorter

import re, datetime, time, csv
import glob
import os

import requests
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

# get latest csv from watches directory
list_of_files = glob.glob("./csv's/watches/*.csv") 
sorted_files = sorted(list_of_files, key=os.path.getctime)
recent_gap_down = sorted_files[-1] # last file is most recent, which will be the stocks that are dropping

# go through each row and poll for if symbol is shortable
shortables = []
with open(recent_gap_down, newline='') as csvfile:
    stockreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    
    for row in stockreader:
        try:
            # grab variables
            symbol = row['Symbol']
            last = float(row['Last'])
            # calculate entry
            entry = round(last - 0.30, 2)
            data = api.get_asset(symbol)
            if data.shortable == True:
                shortables.append([symbol, last, entry])
            else:
                continue
        except:
            print("something went wrong")
csvfile.close()

print(shortables)

for stock in shortables:
    print(f"creating short order for {stock[0]}")
    api.submit_order(
        symbol=stock[0],
        qty=100,
        side='sell',
        type='stop',
        stop_price=stock[2],
        time_in_force='gtc',
        order_class='simple'
    )