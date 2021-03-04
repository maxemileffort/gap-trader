# reporter

import datetime, time, csv, threading, sys
import glob
import os
from pathlib import Path

import pandas as pd

# find report file
_date = datetime.datetime.now()
local_date = _date.strftime("%x").replace("/", "_")
file_string = f"report-{local_date}.csv"
location = f"./csv's/reports/{file_string}"

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

report = check_report(location)

if not report:
    Path(location).touch()
    check_report(location)

analyze_trades()

