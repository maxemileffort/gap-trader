import datetime, time, csv, threading, sys, subprocess
import glob
from pathlib import Path
import os

folder_names = ["csv's", "csv's/monitors", "csv's/reports", "csv's/trades", "csv's/watches"]

def get_date():
    date = datetime.datetime.now()
    local_date = date.strftime("%x").replace("/", "_")
    return local_date

def cleanup_files():
    
    current_date = get_date()

    for folder in folder_names:
        try:
            os.mkdir(f"./{folder}/{current_date}")
        except:
            pass
        for file_ in glob.glob(f'./{folder}/*.csv'):
            if current_date in file_:
                print(file_)
                just_file_name = file_.replace(f"./{folder}", "")
                print(just_file_name)
                os.rename(file_, f'./{folder}/{current_date}{just_file_name}')


if __name__ == "__main__":
    cleanup_files()