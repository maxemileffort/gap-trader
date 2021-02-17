# trader 

import re, datetime, time, csv
import glob
import os

import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL, CHROMEDRIVER_DIR

list_of_files = glob.glob("./csv's/trades/*.csv") # * means all if need specific format then *.csv
sorted_files = sorted(list_of_files, key=os.path.getctime)
most_recent_file = list_of_files[-1] # last file should be most recent one

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url='https://paper-api.alpaca.markets') # or use ENV Vars shown below
account = api.get_account()
print(account)
print(api.list_positions())