# canceler 

import re, datetime, time, csv
import glob
import os

import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

list_of_files = glob.glob("./csv's/trades/*.csv") # * means all if need specific format then *.csv
sorted_files = sorted(list_of_files, key=os.path.getctime)
most_recent_file = list_of_files[-1] # last file should be most recent one

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL) 
account = api.get_account()
print(account)
print(api.list_positions())

# cancel all open orders
orders = api.list_orders(status="open")
print("Canceling orders...")

for order in orders:
    api.cancel_order(order.id)

print("Orders canceled.")

# close all trades    
positions = api.list_positions()
print("Closing positions...")
for trade in positions:
    # submit sell order for the position
    api.submit_order(
        symbol=trade["symbol"],
        qty=trade["qty"],
        side='sell',
        type='market',
        time_in_force='gtc'
    )
print("All positions closed.")