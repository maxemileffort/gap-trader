# trader 

import csv
import glob
import os
import sys
import datetime

from tda.orders.equities import equity_buy_limit, equity_sell_limit, equity_sell_short_limit
from tda.orders.common import OrderType

from client_builder import build_client
from canceler import cancel_all

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID

def create_order(client, symbol, entry_price, qty, order_type):
    if order_type == "short":
        try:
            client.place_order(
                account_id=ACCOUNT_ID,
                order_spec=equity_sell_short_limit(symbol, qty, entry_price).set_order_type(OrderType.STOP).clear_price().set_stop_price(entry_price)
            )
        except:
            print(f"something went wrong creating short sell order: {sys.exc_info()}")
            pass
    elif order_type == "long":
        try:
            client.place_order(
                account_id=ACCOUNT_ID,
                order_spec=equity_buy_limit(symbol, qty, entry_price).set_order_type(OrderType.STOP).clear_price().set_stop_price(entry_price)
            )
        except:
            print(f"something went wrong creating order: {sys.exc_info()}")
            pass

def check_for_trade(symbol):
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"
    # check for entry by symbol
    with open(location, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # did find entry in monitor
            if row["symbol"] == symbol:
                return True
            else:
                return False
    csvfile.close()

def daily_trader(str_):
    list_of_files = glob.glob("./csv's/trades/*.csv") 
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    most_recent_file = sorted_files[-1] # last file should be most recent one

    client = build_client()

    # if str_ == "initial":
    # cancel all open orders
    cancel_all('orders')
    # else:
        # it's a re-run, so don't cancel orders
        # pass

    
    print("Getting account balance...")
    account = client.get_account(account_id=ACCOUNT_ID).json()["securitiesAccount"]
    
    # print(f"account: {account}")
    # choose between account["currentBalances"][totalCash] for cash accounts, 
    # or account["currentBalances"]["buyingPower"]
    if account["type"] == "CASH":
        # plan to use a cash account to avoid PDT rule, so need to spread the 
        # trades over 3 days to allow cash to settle. Also, using this 
        # number to automatically calculate qty of shares for each trade
        buying_power = account["currentBalances"]["totalCash"]
    else:
        # later, when using a margin account, this becomes 
        # a part of the risk management strategy
        buying_power = account["currentBalances"]["buyingPower"]
    
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
            quote = client.get_quote(symbol)
            bid = quote.json()[symbol]["bidPrice"]
            ask = quote.json()[symbol]["askPrice"]
            avg_price = round((bid + ask) / 2, 2)
            trade_check = check_for_trade(symbol)

            if not trade_check:
                pass
            else:
                continue
            # if the price has moved down more than 35 cents, avg + 0.35 will be lower than last, and try to short the stock
            if avg_price + 0.35 < last: 
                order_type = "short"
                entry_price = round(last - 0.45, 2)
                sl_price = str(round(entry_price * 1.07, 2))
            # otherwise, price is stable or moving up, so make a long order
            else: 
                order_type = "long"
                entry_price = round(last + 0.30, 2)
                sl_price = str(round(entry_price * 0.93, 2))
            qty = int(round(investment_per_trade / entry_price, 0))
            print(f"qty is {qty}")
            if entry_price == 0 or qty == 0:
                continue
            volume = row['Volume'] # to be used later
            gap_up_percent = row['Gap Up%'] # to be used later
            
            print(f"Symbol: {symbol} side: {order_type} target entry: {entry_price} Stop Loss price: {sl_price}")
            print(f"Symbol: {symbol} Vol: {volume} Gap Up% {gap_up_percent}")
            
            try:
                create_order(client, symbol, entry_price, qty, order_type)
                order_num+=1
            except Exception as err:
                print(f"Error with {symbol}: {err}")
                error_num+=1
                pass
        print(f"{entries} Entries found.")
        print(f"{order_num} Orders created.")
        print(f"{error_num} Errors encountered.")
    csvfile.close()

if __name__ == '__main__':
    daily_trader('initial')