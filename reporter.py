# reporter

import datetime, time, csv, threading, sys
import glob
import os
from pathlib import Path

import pandas as pd

# find monitor file, or create it
_date = datetime.datetime.now()
local_date = _date.strftime("%x").replace("/", "_")
file_string = f"monitor-{local_date}.csv"
monitor_location = f"./csv's/monitors/{file_string}"
print("Finding today's trades...")
try:
    df = pd.read_csv(monitor_location)

    df.to_csv(monitor_location, index=False)
except:
    print("No monitor.")

# find report file
_date = datetime.datetime.now()
local_date = _date.strftime("%x").replace("/", "_")
file_string = f"report-{local_date}.csv"
location = f"./csv's/reports/{file_string}"

def check_report(location):
    try:
        df = pd.read_csv(location)
    except:
        print("Unexpected error checking report:", sys.exc_info())
        df = ''
        pass

    return df

def analyze_trades(df):
    print("analyzing today's trades...")


# Reporter Logic

report = check_report(location)

if report == '':
    Path(location).touch()
    report = check_report(location)

analyze_trades(report)

