# reporter

import datetime, time, csv, threading, sys
import glob
import os
from pathlib import Path

import pandas as pd
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

# find report file
_date = datetime.datetime.now()
local_date = _date.strftime("%x").replace("/", "_")
file_string = f"report-{local_date}.csv"
location = f"./csv's/reports/{file_string}"

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

def check_report(location):
    try:
        df = pd.read_csv(location)
    except:
        print("Unexpected error creating report:", sys.exc_info())
        df = ''
        pass

    return df

def analyze_trades():
    print("analyzing today's trades...")
    orders = api.list_orders(status="all")
    positions = api.list_positions()

    print(orders)
    print(positions)

report = check_report(location)

if not report:
    Path(location).touch()
    check_report(location)

analyze_trades()

