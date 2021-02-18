# assessor 

import re, datetime, time, csv
import pandas as pd
from sites import urls
from scraper import scraper
import glob
import os

def get_date_and_time(str):
    date = datetime.datetime.now()
    local_date = date.strftime("%x").replace("/", "_")
    local_time = date.strftime("%X").replace(":", "")
    location_string = f"./csv's/{str}/{local_date}-{local_time}-stocks.csv"
    return location_string

def assess(str):
    if str == "prompt":
        scrape_first = input("Scrape first, y/n?   ")
    else:
        scrape_first = "n"

    if scrape_first == "y" or scrape_first == "Y" or scrape_first == "yes" or scrape_first == "Yes":
        scraper()
        time.sleep(50)
    else:
        pass

    # get 2 latest csv's from csv's directory
    list_of_files = glob.glob("./csv's/*.csv") # * means all if need specific format then *.csv
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    recent_gap_down = sorted_files[-1] # last file is gap downs, due to order in which they are scraped
    recent_gap_up = sorted_files[-2] # second to last will be gap ups

    gap_ups = []
    gap_downs = []

    # analyze gap ups first
    # trade these, as they have something working favorably for them
    # which others will also bank on
    # looking for gap up over 4%, volume over 200k, and last daily closing price under $10
    with open(recent_gap_up, newline='') as csvfile:
        stockreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        print("===== Gap Ups: =====")
        for row in stockreader:
            try:
                # grab variables
                symbol = row['Symbol']
                last = float(row['Last'])
                volume = int(float(row['Volume'].replace(",", "")))
                gap_up_percent = float(row['Gap Up%'].replace("%", ""))
                # check for criteria above
                if volume>=200000 and last<=10.0 and gap_up_percent>=4.0:
                    print(f"{symbol}: Last - {last}, Gap Up% - {gap_up_percent}, Volume - {volume}")
                    gap_ups.append([symbol, last, volume, gap_up_percent])
                else:
                    # don't fit criteria
                    print(f"Skipped {symbol}: Outside parameters.")
            except:
                # quick fix for random rows in csv
                print("Error")
                continue
    csvfile.close()

    location = get_date_and_time("trades")

    with open(location, 'w', newline='') as csvfile:
        fieldnames = ['Symbol', 'Last', 'Volume', 'Gap Up%']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for stock in gap_ups:
            writer.writerow({"Symbol": stock[0], "Last": stock[1], "Volume": stock[2], "Gap Up%": stock[3],})
    csvfile.close()

    #anazlyze gap downs
    # looking for something that had a high price and has fallen due to recent news
    # add to a watchlist to profit off of recovery
    with open(recent_gap_down, newline='') as csvfile:
        stockreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        print("===== Gap Downs: =====")
        for row in stockreader:
            try:
                symbol = row['Symbol']
                last = float(row['Last'])
                volume = int(float(row['Volume'].replace(",", "")))
                gap_down_percent = float(row['Gap Down%'].replace("%", ""))
                if volume>=200000 and last<=10.0:
                    print(f"{symbol}: Last - {last}, Gap Down% - {gap_down_percent}, Volume - {volume}")
                    gap_downs.append([symbol, last, volume, gap_down_percent])
                else:
                    print(f"Skipped {symbol}: Outside parameters.")
            except:
                print("Error")
                continue
    csvfile.close()

    location = get_date_and_time("watches")

    with open(location, 'w', newline='') as csvfile:
        fieldnames = ['Symbol', 'Last', 'Volume', 'Gap Down%']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for stock in gap_downs:
            writer.writerow({"Symbol": stock[0], "Last": stock[1], "Volume": stock[2], "Gap Down%": stock[3],})
    csvfile.close()

    # print("Gap Ups:")
    # print(gap_ups) # trade these
    # print("Gap Downs:")
    # print(gap_downs) # add to a watchlist

if __name__ == '__main__':
    # if this script is invoked from the command line, default to prompt scraping
    assess('prompt')


