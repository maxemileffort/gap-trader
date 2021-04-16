import datetime, time, csv, threading, sys, subprocess
import glob
import os
from pathlib import Path

import pandas as pd
from tda.orders.equities import equity_buy_limit, equity_buy_market, equity_sell_market
from tda.orders.common import OrderType

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID
from canceler import cancel_all
from scraper import scraper
from trader import daily_trader
from assessor import assess
from client_builder import build_client

count = 0
def start_test(count):
    cancel_all()
    client = build_client()
    if count < 1:
        count+=1
        symbols = ['CRBP', 'QD', 'WPG', 'ANY']

        for symbol in symbols:
            client.place_order(
                account_id=ACCOUNT_ID, 
                order_spec=equity_buy_market(symbol, 5)
            )

        time.sleep(10)

        for symbol in symbols:
            client.place_order(
                account_id=ACCOUNT_ID, 
                order_spec=equity_sell_market(symbol, 5)
            )
    run_watchdog(0)

def kill_trade_or_not(symbol, current_price, qty, order_type):
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # import csv as dataframe
    print("Kill trade or not...")
    df = pd.read_csv(location)
    filt = df['symbol'] == symbol
    stop_loss = df.loc[filt, 'stop_loss']
    # print(stop_loss)
    # print(stop_loss.iloc[0])
    # if current_price is below stop, cancel orders and sell off position
    try:
        if order_type == "long" and float(current_price) <= float(stop_loss.iloc[0]):
            print("Kill trade.")
            kill_trade(symbol, qty, current_price, order_type)
            return True
        elif order_type == "short" and float(current_price) >= float(stop_loss.iloc[0]):
            print("Kill trade.")
            kill_trade(symbol, qty, current_price, order_type)
            return True
        else:
            print("Not killing trade.")
            print("Current price still away from stop_loss")
            return False
    except:
        print("Unexpected error checking stops:", sys.exc_info())
        pass

def move_stop(symbol, new_price, qty):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    # print(symbol)
    # print(new_price)

    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # import csv as dataframe
    df = pd.read_csv(location)
    # print("initial move stop df:")
    # print(df)

    # rewrite dataframe with new stop
    # use df.loc to do this. video: https://www.youtube.com/watch?v=DCDe29sIKcE&list=RDCMUCCezIgC97PvUuR4_gbFUs5g&index=5
    try:
        filt = df['symbol'] == symbol
        df.loc[filt, 'stop_loss'] = new_price
        print(f"new stop loss for {symbol}: {new_price}")
    except:
        print("Unexpected error moving stop:", sys.exc_info())
        print("unchanged move stop df:")
        print(df)

    # rewrite csv with new dataframe
    df.to_csv(location, index=False)

# for take profit and stop losses
def create_exit(symbol, entry_price, stop_loss, take_profit, qty):
    # find monitor file, or create it
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"
    print("Creating exit...")
    try:
        # import csv as dataframe
        df = pd.read_csv(location)
        # print("create exit df:")
        # print(df)
        # construct new row
        # append new row to df if it doesn't exist already
        try:
            # check df for entry
            locator = df.loc[df[symbol]]
            # print("locator:")
            # print(locator)
        except:
            # if it doesn't exist, return False and print the error
            print("Unexpected error creating exit:", sys.exc_info())
            locator = False
            pass
        if locator:
            # if an entry exists, don't do anything
            print("entry exists")
        else:
            # otherwise, append the entire row
            row = [symbol, entry_price, stop_loss, take_profit, qty, '']
            # print("row:")
            # print(row)
            df.loc[len(df.index)] = row
        # save new df as csv
        # print("new create exit df:")
        # print(df)
        df.to_csv(location, index=False)
    except FileNotFoundError:
        # if it doesn't exist, create it and try to access it again
        print("file not found, creating now.")
        Path(location).touch()
        with open(location, 'w', newline='') as csvfile:
            fieldnames = ['symbol', 'entry', 'stop_loss', 'take_profit', 'qty', "actual_exit"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        csvfile.close()
        print("file created, trying to create exit again.")
        create_exit(symbol, entry_price, stop_loss, take_profit, qty)

    
def check_for_exit(symbol):
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"
    # check for entry by symbol
    match = ''
    try:
        with open(location, 'r', newline='') as csvfile:
            # print("found monitor")
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["symbol"] == symbol:
                    # did find entry in monitor
                    # print("found entry in monitor")
                    match = symbol        
                    break
                else:
                    # didn't find entry in monitor
                    # print("did not find entry this time")
                    continue
        csvfile.close()
    except FileNotFoundError:
        print("monitor file not found...")
        return False
    
    if match:
        return True
    else:
        return False

def check_for_stop(symbol, new_stop, qty, order_type):
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # check for entry by symbol
    print("checking stop")
    with open(location, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        match = ''
        for row in reader:
            # did find entry in monitor
            if row["symbol"] == symbol:
                match = symbol
                # print(row)
                # check for matching stop order
                try:
                    # if new price and old price are different, for long trades, 
                    # move the stop only if the new stop is greater than the old stop
                    if order_type == "long" and new_stop != float(row['stop_loss']) and new_stop > float(row['stop_loss']):
                        # "Move" stop (most times it just gets put in exact same spot)
                        print(f'Moving stop for {symbol} to {new_stop}')
                        move_stop(symbol, new_stop, qty)
                        break
                    elif order_type == "short" and new_stop != float(row['stop_loss']) and new_stop < float(row['stop_loss']):
                        print(f'Moving stop for {symbol} to {new_stop}')
                        move_stop(symbol, new_stop, qty)
                        break
                    # if new price and old price match, do nothing
                    else:
                        print("Stop in right place for now.")
                        break
                except:
                    print("Unexpected error checking stop:", sys.exc_info())
                    pass
        # didn't find entry in monitor
        if match == '':
            print("Problem finding stop.")
    csvfile.close()

def record_trade(symbol, price):
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    df = pd.read_csv(location)

    filt = df['symbol'] == symbol
    df.loc[filt, 'actual_exit'] = price

    df.to_csv(location, index=False)

def kill_trade(symbol, qty, price, order_type):
    client = build_client()
    try:
        if order_type == "long":
            client.place_order(
                    account_id=ACCOUNT_ID, 
                    order_spec=equity_sell_market(symbol, qty)
                )
            print("Killed trade")
            record_trade(symbol, price)
        else:
            client.place_order(
                    account_id=ACCOUNT_ID, 
                    order_spec=equity_buy_market(symbol, qty)
                )
            print("Killed trade")
            record_trade(symbol, price)
    except:
        print("something went wrong killing trade.")
        print("Unexpected error:", sys.exc_info())
        pass

def grab_current_stoploss(symbol):
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"
    sl = ''
    with open(location, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # did find entry in monitor
            if row["symbol"] == symbol:
                sl = row["stop_loss"]
    csvfile.close()
    return float(sl)

def check_long_trades(client):
    
    account_with_positions = client.get_account(account_id=ACCOUNT_ID, fields=client.Account.Fields.POSITIONS).json()["securitiesAccount"]
    try:
        positions = account_with_positions["positions"]
    except:
        positions = {}
    # print(orders)
    for trade in positions:
        # print("trade:")
        # print(trade)
        if trade["longQuantity"] > 0 and trade["longQuantity"] != trade["shortQuantity"]:
            symbol = trade["instrument"]["symbol"]
            if symbol == "MMDA1":
                continue
            qty = trade["longQuantity"]
            entry_price = float(trade["averagePrice"])
            exit_price = float(entry_price) * 2
            # print(f"test: {test}")
            current_bid_price = round(float(client.get_quote(symbol).json()[symbol]["bidPrice"]),2)
            current_ask_price = round(float(client.get_quote(symbol).json()[symbol]["askPrice"]),2)
            current_price = (current_ask_price + current_bid_price) / 2
            percent_gain = round((current_price - entry_price) / entry_price * 100, 2)
            # first check, on script start up. They should all return false, which leads to creation of the stops and tp's.
            # The rest of the checks make sure stop loss is trailing. 
            # "Continue" lines are important for speeding up the process of checking stops for multiple stocks
            check = check_for_exit(symbol)
            # if the exits don't exist, create them
            if check != True:
                create_exit(symbol, entry_price, round(entry_price*.93, 2), round(exit_price, 2), qty)

            stoploss = grab_current_stoploss(symbol) # only used for moving stop losses
            distance_from_stoploss = round((current_price - stoploss) / stoploss * 100, 2)
            print(f'symbol: {symbol} current price: {current_price} current sl: {stoploss} distance from sl: {distance_from_stoploss}%')
            print(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade["currentDayProfitLoss"]}')

            # check current trades to see if it's time for an exit
            killed_trade = kill_trade_or_not(symbol, current_price, qty, 'long')
            if killed_trade:
                continue # skip the rest of the checks
            else:
                pass
            # kill trade if it drops 7% below entry
            if percent_gain <= -7:
                kill_trade(symbol, qty, current_price, "long")
            # cash in winners
            elif current_price >= exit_price:
                kill_trade(symbol, qty, current_price, "long")
            # start a trailing stop of 7%
            elif distance_from_stoploss > 7:
                check_for_stop(symbol=symbol, new_stop=round(current_price*0.93,2), qty=qty, order_type="long")
                continue
            # log that there isn't enough profit to move stop
            else:
                print(f"not enough gain to move stops for {symbol}.")
                continue

def check_short_trades(client):
    account_with_positions = client.get_account(account_id=ACCOUNT_ID, fields=client.Account.Fields.POSITIONS).json()["securitiesAccount"]
    try:
        positions = account_with_positions["positions"]
    except:
        positions = {}
    # print(orders)
    for trade in positions:
        # print("trade:")
        # print(trade)
        if trade["shortQuantity"] > 0 and trade["longQuantity"] != trade["shortQuantity"]:
            symbol = trade["instrument"]["symbol"]
            if symbol == "MMDA1":
                continue
            qty = trade["shortQuantity"]
            entry_price = float(trade["averagePrice"])
            exit_price = float(entry_price) * 0.5
            # print(f"test: {test}")
            current_bid_price = round(float(client.get_quote(symbol).json()[symbol]["bidPrice"]),2)
            current_ask_price = round(float(client.get_quote(symbol).json()[symbol]["askPrice"]),2)
            current_price = (current_ask_price + current_bid_price) / 2
            percent_gain = round((entry_price - current_price) / entry_price * 100, 2)
            # first check, on script start up. They should all return false, which leads to creation of the stops and tp's.
            # The rest of the checks make sure stop loss is trailing. 
            # "Continue" lines are important for speeding up the process of checking stops for multiple stocks
            check = check_for_exit(symbol)
            # if the exits don't exist, create them
            if check != True:
                create_exit(symbol, entry_price, round(entry_price*1.07, 2), round(exit_price, 2), qty)

            stoploss = grab_current_stoploss(symbol) # only used for moving stop losses
            distance_from_stoploss = round((current_price - stoploss) / stoploss * 100, 2)
            print(f'symbol: {symbol} current price: {current_price} current sl: {stoploss} distance from sl: {distance_from_stoploss}%')
            print(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade["currentDayProfitLoss"]}')

            # check current trades to see if it's time for an exit
            killed_trade = kill_trade_or_not(symbol, current_price, qty, "short")
            if killed_trade:
                continue # skip the rest of the checks
            else:
                pass
             # kill trade if it drops 7% below entry
            if percent_gain <= -7:
                kill_trade(symbol, qty, current_price, "short")
            # cash in winners
            elif current_price >= exit_price:
                kill_trade(symbol, qty, current_price, "short")
            # start a trailing stop of 7%
            elif distance_from_stoploss > 7:
                check_for_stop(symbol=symbol, new_stop=round(current_price*1.07,2), qty=qty, order_type="short")
                continue
            # log that there isn't enough profit to move stop
            else:
                print(f"not enough gain to move stops for {symbol}.")
                continue


def rate_limiter(count):
    # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    print(f"Finished run number {count}. Starting next trade check.")

    # Figure out when the market will close so we can prepare to sell beforehand.
    slow_down = count % 120 # clock calls were ending the script prematurely so slowed them down
    if slow_down == 0:
        closingTime = time.mktime(datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0).timetuple())
        currTime = time.mktime(datetime.datetime.now().timetuple())
        timeToClose = closingTime - currTime
    else:
        timeToClose = 1200

    # Close all positions when 15 minutes til market close.
    if(timeToClose < (60 * 10)):
        print("Market closing soon.  Closing positions.")
        date = datetime.datetime.now()
        local_date = date.strftime("%x")
        local_time = date.strftime("%X")
        cancel_all()
        print(f"Finish time: {local_time} on {local_date}")
        # because script is started by local batch file, we want it to 
        # exit every day, so it closes the cmd prompt
        sys.exit()
    # slow down time between calls to 5 sec    
    else:
        print("next check in 4...") 
        time.sleep(4) 

def rebuild_monitor():
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # check if the monitor exists, and if it does, blank it out
    try:
        with open(location, 'w', newline='') as csvfile:
            fieldnames = ['symbol', 'entry', 'stop_loss', 'take_profit', 'qty']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        csvfile.close()
    # if it doesn't exist, then don't worry about it
    except:
        pass

def rescan_stocks():
    # Lost $3k on a paper account due to this. 3/26/21
    # first, clear the monitor file, or else the rescan will 
    # repeatedly enter and exit trades
    rebuild_monitor()
    # rescan, assess, and trade
    subprocess.Popen(["python", "control.py", "--rescan"])

def run_watchdog(count):
    # poor man's web socket
    while count < 6500:
        count+=1
        try:
            client = build_client()
            tCLT = threading.Thread(target=check_long_trades(client))
            tCLT.start()
            tCST = threading.Thread(target=check_short_trades(client))
            tCST.start()
            tCLT.join()
            tCST.join()
            tRL = threading.Thread(target=rate_limiter(count))
            tRL.start()
            tRL.join()
        except SystemExit:
            sys.exit()
        except KeyboardInterrupt:
            sys.exit()
        except:
            print("something went wrong running process, probably connection timeout.")
            print("Unexpected error:", sys.exc_info())
            pass

if __name__ == "__main__":
    # run_watchdog(0)
    start_test(0)