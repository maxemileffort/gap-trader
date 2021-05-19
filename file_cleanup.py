import datetime, time, csv, threading, sys, subprocess
import glob
from pathlib import Path
import os
import shutil

folder_names = ["csv's/raw", "csv's/monitors", "csv's/reports", "csv's/trades", "csv's/watches"]

def get_date():
    date = datetime.datetime.now()
    local_date = date.strftime("%x").replace("/", "_")
    return local_date

def delete_logs():
    logs = glob.glob("./logs/*.txt")
    sorted_logs = sorted(logs, key=os.path.getctime)
    if len(sorted_logs) > 2:
        os.remove(sorted_logs[0])
        delete_logs()

def delete_old_folders():
    raw = glob.glob("./csv's/raw/*/")
    sorted_raw = sorted(raw, key=os.path.getctime)
    monitors = glob.glob("./csv's/monitors/*/")
    sorted_monitors = sorted(monitors, key=os.path.getctime)
    reports = glob.glob("./csv's/reports/*/")
    sorted_reports = sorted(reports, key=os.path.getctime)
    trades = glob.glob("./csv's/trades/*/")
    sorted_trades = sorted(trades, key=os.path.getctime)
    watches = glob.glob("./csv's/watches/*/")
    sorted_watches = sorted(watches, key=os.path.getctime)
    folders = [sorted_raw, sorted_monitors, sorted_reports, sorted_trades, sorted_watches]
    # print(folders)
    for folder in folders:
        print(len(folder))
        while len(folder) > 15:
            shutil.rmtree(folder[0], ignore_errors=True)
            folder.pop(0)

def cleanup_files():
    
    current_date = get_date()

    for folder in folder_names:
        try:
            os.mkdir(f"./{folder}/{current_date}")
        except:
            pass
        for file_ in glob.glob(f'./{folder}/*.csv'):
            if current_date in file_:
                # print(file_)
                just_file_name = file_.replace(f"./{folder}", "")
                # print(just_file_name)
                os.rename(file_, f'./{folder}/{current_date}/{just_file_name}')

    delete_logs()
    delete_old_folders()

if __name__ == "__main__":
    cleanup_files()
    # delete_old_folders()