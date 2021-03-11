# watcher 

import datetime, time, csv, threading, sys
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

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

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

def kill_trade_or_not(symbol, current_price, qty, orders):
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
            kill_trade(orders, symbol, qty)
        else:
            print("Not kill trade.")
            print("Current price still above stop_loss")
    except:
        print("Unexpected error checking stops:", sys.exc_info())
        pass

def move_stop(symbol, new_price, qty):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    print(symbol)
    print(new_price)

    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # import csv as dataframe
    df = pd.read_csv(location)
    print("move stop df:")
    print(df)

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
            row = [symbol, entry_price, stop_loss, take_profit, qty]
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
            fieldnames = ['symbol', 'entry', 'stop_loss', 'take_profit', 'qty']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        csvfile.close()
        print("file created, trying to create exit again.")
        create_exit(symbol, entry_price, stop_loss, take_profit, qty)

    
def check_for_exit(symbol):
    # WORKING as of 2/26/21
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

def kill_trade(orders, symbol, qty):
    # WORKING
    # first remove pending orders related to symbol
    for order in orders:
        # print(f"kill trade order: {order}")
        if symbol == order.symbol:
            try:
                api.cancel_order(order.id)
                print("Orders killed.")
            except:
                print("something went wrong closing orders.")
                print("Unexpected error:", sys.exc_info())
                pass
    # then end the trade
    try:
        api.submit_order(
            symbol= symbol,
            qty = qty,
            side= "sell",
            type= "market",
            time_in_force= "gtc"
        )
        print("Killed trade")
    except:
        print("something went wrong killing trade.")
        print("Unexpected error:", sys.exc_info())
        pass

def check_long_trades():
    positions = api.list_positions()
    orders = api.list_orders()
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
            print(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade.unrealized_pl}')
            # first make sure tp is set up
            print("checking for exit")
            # first check, on script start up. They should all return false, which leads to creation of the stops and tp's.
            # The rest of the checks are checking to see if the stops are in acceptable ranges for the amount of profit in trade. 
            # "Continue" lines are important for preventing stops from moving backwards
            check = check_for_exit(symbol)
            # if the exits don't exist, create them
            if check != True:
                create_exit(symbol, entry_price, round(entry_price*.9, 2), round(exit_price, 2), qty)
            # check current trades to see if it's time for an exit
            kill_trade_or_not(symbol, current_price, qty, orders)
            # kill trade if it drops 10% below entry
            if percent_gain < -10:
                kill_trade(orders, symbol, qty)
                # WORKING up to this point
            # lock in free trades @ 5% gain
            elif percent_gain >= 5 and percent_gain < 10:
                check_for_stop(symbol, entry_price, qty)
                continue
            # lock in 10% gainers @ 5% gain
            elif percent_gain >= 10 and percent_gain < 15:
                check_for_stop(symbol, round(entry_price*1.05,2), qty)
                continue
            # lock in 15% gainers @ 10% gain
            elif percent_gain >= 15 and percent_gain < 20:
                check_for_stop(symbol, round(entry_price*1.10,2), qty)
                continue
            # lock in 20% gainers @ 15% gain
            elif percent_gain >= 20 and percent_gain < 25:
                check_for_stop(symbol, round(entry_price*1.15,2), qty)
                continue
            # and so on...
            elif percent_gain >= 25 and percent_gain < 30:
                check_for_stop(symbol, round(entry_price*1.20,2), qty)
                continue
            elif percent_gain >= 30 and percent_gain < 35:
                check_for_stop(symbol, round(entry_price*1.25,2), qty)
                continue
            elif percent_gain >= 35 and percent_gain < 40:
                check_for_stop(symbol, round(entry_price*1.30,2), qty)
                continue
            elif percent_gain >= 40 and percent_gain < 45:
                check_for_stop(symbol, round(entry_price*1.35,2), qty)
                continue
            elif percent_gain >= 45 and percent_gain < 50:
                check_for_stop(symbol, round(entry_price*1.40,2), qty)
                continue
            # log that there isn't enough profit to move stop
            else:
                print(f"not enough gain to move stops for {symbol}.")
                continue
            
def rate_limiter(count):
    # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    print(f"Finished run number {count}. Starting next trade check.")

    # Figure out when the market will close so we can prepare to sell beforehand.
    slow_down = count % 200 # clock calls were ending the script prematurely so slowed them down
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
        # because script is started by local batch file, we want it to exit every day
        sys.exit()
    # slow down time between calls to 5 sec    
    else:
        print("next check in 5...") 
        time.sleep(5) 

def run_watchdog(count):
    # poor man's web socket
    while count < 15000:
        count+=1
        tCLT = threading.Thread(target=check_long_trades)
        tCLT.start()
        tCLT.join()
        tRL = threading.Thread(target=rate_limiter(count))
        tRL.start()
        tRL.join()
        # recheck the stocks in the first 15 minutes to make sure things haven't changed too drastically
        # potential to mess up currently profitable trades
        if count == 180:
            # cancel open orders and then repeat the process
            print("rescanning stocks.")
            api.cancel_all_orders()
            scraper()
            assess('skip')
            daily_trader()

if __name__ == "__main__":
    # run_watchdog(0)
    start_test(0)