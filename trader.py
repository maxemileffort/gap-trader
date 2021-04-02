# trader 

import csv
import glob
import os
import sys

from tda.orders.equities import equity_buy_limit
from tda.orders.common import Duration, Session, OrderType

from client_builder import build_client
from canceler import cancel_all

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID

def daily_trader():
    list_of_files = glob.glob("./csv's/trades/*.csv") 
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    most_recent_file = sorted_files[-1] # last file should be most recent one

    client = build_client()

    # cancel all open orders
    cancel_all()

    # close all profitable trades 
    print("Getting account balance...")
    # SUBSTITUTE
    account = client.get_account(account_id=ACCOUNT_ID).json()["securitiesAccount"]
    
    print(f"account: {account}")
    # choose between account["currentBalances"][totalCash] for cash accounts, or account["currentBalances"]["buyingPower"]
    if account["type"] == "CASH":
        buying_power = account["currentBalances"]["totalCash"]
    else:
        buying_power = account["currentBalances"]["buyingPower"]
    # plan to use a cash account to avoid PDT rule, so need to spread the 
    # trades over 3 days to allow cash to settle. Also, using this 
    # number to automatically calculate qty of shares for each trade
    daily_investment = round(float(buying_power) / 3, 2)
    print(daily_investment)
    

    # count rows
    with open(most_recent_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        print("Counting trades...")
        num_of_trades = len(list(reader))
    csvfile.close()

    # create orders from most recent gap up analysis
    with open(most_recent_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        print("Creating orders...")
        investment_per_trade = round(daily_investment / num_of_trades, 2)
        order_num = 0
        error_num = 0
        entries = 0
        print(f"Num of trades is {num_of_trades}")
        print(f"inv per trade is {investment_per_trade}")

        for row in reader:
            entries+=1
            symbol = row['Symbol']
            last = float(row['Last'])
            entry_price = round(last + 0.30, 2)
            qty = int(round(investment_per_trade / entry_price, 0))
            print(f"qty is {qty}")
            volume = row['Volume'] # to be used later
            gap_up_percent = row['Gap Up%'] # to be used later
            sl_price = str(round(entry_price * 0.9, 2))
            # sl_limit_price = str(round(last * 0.92 - 0.01, 2))
            # tp_limit_price = str(round(last * 2, 2))
            # print(f"Symbol: {symbol} target entry: {entry_price} Stop Loss price: {sl_price} tp_limit price: {tp_limit_price} Vol: {volume} Gap Up% {gap_up_percent}")
            print(f"Symbol: {symbol} target entry: {entry_price} Stop Loss price: {sl_price} Vol: {volume} Gap Up% {gap_up_percent}")
            
            try:
                # simple order
                client.place_order(
                   account_id=ACCOUNT_ID,
                   order_spec=equity_buy_limit(symbol, qty, entry).set_order_type(OrderType.STOP)
                )
                order_num+=1
            except:
                print(f"Error with {symbol}")
                error_num+=1
                pass
        print(f"{entries} Entries found.")
        print(f"{order_num} Orders created.")
        print(f"{error_num} Errors encountered.")
    csvfile.close()

if __name__ == '__main__':
    daily_trader()