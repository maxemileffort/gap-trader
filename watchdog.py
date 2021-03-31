import datetime, time, csv, threading, sys, subprocess
import glob
import os
from pathlib import Path

import pandas as pd
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL
from canceler import cancel_all
from scraper import scraper
from trader import daily_trader
from assessor import assess

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_BASE_URL)

count = 0
def start_test(count):
    cancel_all()
    if count < 1:
        count+=1
        symbols = ['AAPL', 'MSFT', 'HLX', 'AES', 'NI', 'CNP', 'BOXL', 'IBIO']

        for symbol in symbols:
            api.submit_order(
                symbol=symbol,
                qty='100',
                side='buy',
                type='market',
                time_in_force='gtc'
            )
    run_watchdog(0)

def kill_trade_or_not(symbol, current_price, qty):
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
        if float(current_price) <= float(stop_loss.iloc[0]):
            print("Kill trade.")
            kill_trade(symbol, qty, current_price)
            return True
        else:
            print("Not kill trade.")
            print("Current price still above stop_loss")
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
        print("new move stop df:")
        print(df)
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

def check_for_stop(symbol, new_stop, qty):
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
                    # if new price and old price are different, move the stop only if the new stop is greater than the old stop
                    if new_stop != float(row['stop_loss']) and new_stop > float(row['stop_loss']):
                        # "Move" stop (most times it just gets put in exact same spot)
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

def record_trade(result, price):
    print(result)
    symbol = result.symbol
    # filled_price = result.filled_avg_price
    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    df = pd.read_csv(location)

    filt = df['symbol'] == symbol
    df.loc[filt, 'actual_exit'] = price

    df.to_csv(location, index=False)

def kill_trade(symbol, qty, price):
    
    try:
        res = api.submit_order(
            symbol= symbol,
            qty = qty,
            side= "sell",
            type= "market",
            time_in_force= "gtc"
        )
        print("Killed trade")
        record_trade(res, price)
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

def check_long_trades():
    positions = api.list_positions()
    # print(orders)
    for trade in positions:
        # print("trade:")
        # print(trade)
        if trade.side == "long":
            symbol = trade.symbol
            qty = trade.qty
            entry_price = float(trade.avg_entry_price)
            exit_price = float(trade.avg_entry_price) * 2
            current_price = float(trade.current_price)
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
            print(f'symbol: {symbol} current price: {current_price} current sl: {stoploss} distance from sl: {distance_from_stoploss}')
            print(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade.unrealized_pl}')

            # check current trades to see if it's time for an exit
            killed_trade = kill_trade_or_not(symbol, current_price, qty)
            if killed_trade:
                continue # skip the rest of the checks
            else:
                pass
            # kill trade if it drops 7% below entry
            if percent_gain <= -7:
                kill_trade(symbol, qty, current_price)
            # cash in winners
            elif current_price >= exit_price:
                kill_trade(symbol, qty, current_price)
            # lock in free trades @ 5% gain (actually added 1% because who wants to give away ALL those profits)
            # elif percent_gain >= 5 and percent_gain < 10:
            #     check_for_stop(symbol, entry_price*1.01, qty)
            #     continue
            # # start a trailing stop of 7%
            # elif percent_gain >= 10 and distance_from_stoploss > 7:
            #     check_for_stop(symbol, round(current_price*0.93,2), qty)
            #     continue
            # start a trailing stop of 7%
            elif distance_from_stoploss > 7:
                check_for_stop(symbol, round(current_price*0.93,2), qty)
                continue
            # # lock in 15% gainers @ 10% gain
            # elif percent_gain >= 15 and percent_gain < 20:
            #     check_for_stop(symbol, round(entry_price*1.10,2), qty)
            #     continue
            # # lock in 20% gainers @ 15% gain
            # elif percent_gain >= 20 and percent_gain < 25:
            #     check_for_stop(symbol, round(entry_price*1.15,2), qty)
            #     continue
            # # and so on...
            # elif percent_gain >= 25 and percent_gain < 30:
            #     check_for_stop(symbol, round(entry_price*1.20,2), qty)
            #     continue
            # elif percent_gain >= 30 and percent_gain < 35:
            #     check_for_stop(symbol, round(entry_price*1.25,2), qty)
            #     continue
            # elif percent_gain >= 35 and percent_gain < 40:
            #     check_for_stop(symbol, round(entry_price*1.30,2), qty)
            #     continue
            # elif percent_gain >= 40 and percent_gain < 45:
            #     check_for_stop(symbol, round(entry_price*1.35,2), qty)
            #     continue
            # elif percent_gain >= 45 and percent_gain < 50:
            #     check_for_stop(symbol, round(entry_price*1.40,2), qty)
            #     continue
            # log that there isn't enough profit to move stop
            else:
                print(f"not enough gain to move stops for {symbol}.")
                continue
            
def rate_limiter(count):
    # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    print(f"Finished run number {count}. Starting next trade check.")

    # Figure out when the market will close so we can prepare to sell beforehand.
    slow_down = count % 135 # clock calls were ending the script prematurely so slowed them down
    if slow_down == 0:
        clock = api.get_clock()
        closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
        currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
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
    while count < 7500:
        count+=1
        tCLT = threading.Thread(target=check_long_trades)
        tCLT.start()
        tCLT.join()
        tRL = threading.Thread(target=rate_limiter(count))
        tRL.start()
        tRL.join()

if __name__ == "__main__":
    # run_watchdog(0)
    start_test(0)