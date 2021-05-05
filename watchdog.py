import datetime, time, csv, threading, sys, subprocess
import glob
import os
from pathlib import Path
import logging
import math

import pandas as pd
from tda.orders.equities import equity_buy_limit, equity_buy_market, equity_sell_market
from tda.orders.common import OrderType

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID
from canceler import cancel_all
from scraper import scraper
from trader import daily_trader, create_order
from assessor import assess
from client_builder import build_client
from file_cleanup import cleanup_files
from webdriver_updater import get_updates

# set up logging to file - copied from https://docs.python.org/3/howto/logging-cookbook.html
_date = datetime.datetime.now()
local_date = _date.strftime("%x").replace("/", "_")
_file = Path(f'./logs/{local_date}-log.txt')
if _file.exists():
    pass
else:
    _file.touch()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=f'./logs/{local_date}-log.txt',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger().addHandler(console)

count = 0
def start_test(count):
    cancel_all('all')
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
    logging.info("Kill trade or not...")
    df = pd.read_csv(location)
    filt = df['symbol'] == symbol
    stop_loss = df.loc[filt, 'stop_loss']
    # logging.info(stop_loss)
    # logging.info(stop_loss.iloc[0])
    # if current_price is below stop, cancel orders and sell off position
    try:
        if order_type == "long" and float(current_price) <= float(stop_loss.iloc[0]):
            logging.info("Kill trade.")
            kill_trade(symbol, qty, current_price, order_type)
            return True
        elif order_type == "short" and float(current_price) >= float(stop_loss.iloc[0]):
            logging.info("Kill trade.")
            kill_trade(symbol, qty, current_price, order_type)
            return True
        else:
            logging.info("Not killing trade.")
            return False
    except:
        logging.info(f"Unexpected error checking stops: {sys.exc_info()}")
        pass

def move_stop(symbol, new_price, qty):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    # logging.info(symbol)
    # logging.info(new_price)

    # find monitor file
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"

    # import csv as dataframe
    df = pd.read_csv(location)
    # logging.info("initial move stop df:")
    # logging.info(df)

    # rewrite dataframe with new stop
    # use df.loc to do this. video: https://www.youtube.com/watch?v=DCDe29sIKcE&list=RDCMUCCezIgC97PvUuR4_gbFUs5g&index=5
    try:
        filt = df['symbol'] == symbol
        df.loc[filt, 'stop_loss'] = new_price
        logging.info(f"new stop loss for {symbol}: {new_price}")
    except:
        logging.info(f"Unexpected error moving stop: {sys.exc_info()}")
        logging.info("unchanged move stop df:")
        logging.info(df)

    # rewrite csv with new dataframe
    df.to_csv(location, index=False)

# for take profit and stop losses
def create_exit(symbol, entry_price, stop_loss, take_profit, qty):
    # find monitor file, or create it
    _date = datetime.datetime.now()
    local_date = _date.strftime("%x").replace("/", "_")
    file_string = f"monitor-{local_date}.csv"
    location = f"./csv's/monitors/{file_string}"
    logging.info("Creating exit...")
    try:
        # import csv as dataframe
        df = pd.read_csv(location)
        # logging.info("create exit df:")
        # logging.info(df)
        # construct new row
        # append new row to df if it doesn't exist already
        try:
            # check df for entry
            locator = df.loc[df[symbol]]
            # logging.info("locator:")
            # logging.info(locator)
        except:
            # if it doesn't exist, return False and logging.info the error
            logging.info(f"Unexpected error creating exit: {sys.exc_info()}")
            locator = False
            pass
        if locator:
            # if an entry exists, don't do anything
            logging.info("entry exists")
        else:
            # otherwise, append the entire row
            row = [symbol, entry_price, stop_loss, take_profit, qty, '']
            # logging.info("row:")
            # logging.info(row)
            df.loc[len(df.index)] = row
        # save new df as csv
        # logging.info("new create exit df:")
        # logging.info(df)
        df.to_csv(location, index=False)
    except FileNotFoundError:
        # if it doesn't exist, create it and try to access it again
        logging.info("file not found, creating now.")
        Path(location).touch()
        with open(location, 'w', newline='') as csvfile:
            fieldnames = ['symbol', 'entry', 'stop_loss', 'take_profit', 'qty', "actual_exit"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        csvfile.close()
        logging.info("file created, trying to create exit again.")
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
            # logging.info("found monitor")
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["symbol"] == symbol:
                    # did find entry in monitor
                    # logging.info("found entry in monitor")
                    match = symbol        
                    break
                else:
                    # didn't find entry in monitor
                    # logging.info("did not find entry this time")
                    continue
        csvfile.close()
    except FileNotFoundError:
        logging.info("monitor file not found...")
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
    logging.info("checking stop")
    with open(location, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        match = ''
        for row in reader:
            # did find entry in monitor
            if row["symbol"] == symbol:
                match = symbol
                # logging.info(row)
                # check for matching stop order
                try:
                    # if new price and old price are different, for long trades, 
                    # move the stop only if the new stop is greater than the old stop
                    if order_type == "long" and new_stop != float(row['stop_loss']) and new_stop > float(row['stop_loss']):
                        # "Move" stop (most times it just gets put in exact same spot)
                        logging.info(f'Moving stop for {symbol} to {new_stop}')
                        move_stop(symbol, new_stop, qty)
                        break
                    elif order_type == "short" and new_stop != float(row['stop_loss']) and new_stop < float(row['stop_loss']):
                        logging.info(f'Moving stop for {symbol} to {new_stop}')
                        move_stop(symbol, new_stop, qty)
                        break
                    # if new price and old price match, do nothing
                    else:
                        logging.info("Stop in right place for now.")
                        break
                except:
                    logging.info(f"Unexpected error checking stop: {sys.exc_info()}")
                    pass
        # didn't find entry in monitor
        if match == '':
            logging.info("Problem finding stop.")
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
            logging.info("Killed trade")
            record_trade(symbol, price)
        else:
            client.place_order(
                    account_id=ACCOUNT_ID, 
                    order_spec=equity_buy_market(symbol, qty)
                )
            logging.info("Killed trade")
            record_trade(symbol, price)
    except:
        logging.info(f"Unexpected error killing trade: {sys.exc_info()}")
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
    # logging.info(orders)
    for trade in positions:
        # logging.info("trade:")
        # logging.info(trade)
        if trade["longQuantity"] > 0 and trade["longQuantity"] != trade["shortQuantity"]:
            symbol = trade["instrument"]["symbol"]
            if symbol == "MMDA1":
                continue
            qty = trade["longQuantity"]
            entry_price = float(trade["averagePrice"])
            exit_price = round(float(entry_price) * 1.2, 2)
            symbol_quote_obj = client.get_quote(symbol).json()[symbol]
            current_bid_price = round(float(symbol_quote_obj["bidPrice"]),2)
            current_ask_price = round(float(symbol_quote_obj["askPrice"]),2)
            current_price = round((current_ask_price + current_bid_price) / 2, 2)
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
            logging.info(f'symbol: {symbol} current price: {current_price} current sl: {stoploss} distance from sl: {distance_from_stoploss}%')
            logging.info(f'symbol: {symbol} entry price: {entry_price} percent gain: {percent_gain} profit/loss: {trade["currentDayProfitLoss"]}')

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
                create_order(client, symbol, current_price, qty, "long")
            # if a stock moves 5% it should be a free trade or a small gain, 
            # not a loss like with the trailing stop
            elif percent_gain >= 5 and percent_gain <= 7:
                check_for_stop(symbol=symbol, new_stop=round(entry_price*1.01,2), qty=qty, order_type="long")
                continue
            # start a trailing stop of 7%, that moves up 1% every time the trade moves up 1%
            elif distance_from_stoploss > 7 or math.isclose(distance_from_stoploss, 7.25, abs_tol=0.25):
                check_for_stop(symbol=symbol, new_stop=round(current_price*0.94,2), qty=qty, order_type="long")
                continue
            # log that there isn't enough profit to move stop
            else:
                logging.info(f"not enough gain to move stops for {symbol}.")
                continue

def check_short_trades(client):
    account_with_positions = client.get_account(account_id=ACCOUNT_ID, fields=client.Account.Fields.POSITIONS).json()["securitiesAccount"]
    try:
        positions = account_with_positions["positions"]
    except:
        positions = {}
    # logging.info(orders)
    for trade in positions:
        # logging.info("trade:")
        # logging.info(trade)
        if trade["shortQuantity"] > 0 and trade["longQuantity"] != trade["shortQuantity"]:
            symbol = trade["instrument"]["symbol"]
            if symbol == "MMDA1":
                continue
            qty = trade["shortQuantity"]
            entry_price = float(trade["averagePrice"])
            exit_price = float(entry_price) * 0.5
            symbol_quote_obj = client.get_quote(symbol).json()[symbol]
            current_bid_price = round(float(symbol_quote_obj["bidPrice"]),2)
            current_ask_price = round(float(symbol_quote_obj["askPrice"]),2)
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
            logging.info(f'symbol: {symbol} current price: {current_price} current sl: {stoploss} distance from sl: {distance_from_stoploss}%')
            logging.info(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade["currentDayProfitLoss"]}')

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
            elif distance_from_stoploss > 7.0:
                check_for_stop(symbol=symbol, new_stop=round(current_price*1.07,2), qty=qty, order_type="short")
                continue
            # log that there isn't enough profit to move stop
            else:
                logging.info(f"not enough gain to move stops for {symbol}.")
                continue

def rate_limiter(count):
    # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    logging.info(f"Finished run number {count}. Starting next trade check.")

    # Figure out when the market will close so we can prepare to sell beforehand.
    closingTime = time.mktime(datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0).timetuple())
    currTime = time.mktime(datetime.datetime.now().timetuple())
    timeToClose = closingTime - currTime

    # Close all positions when 10 minutes til market close.
    logging.info(f"timeToClose: {timeToClose}")
    if(timeToClose < (60 * 10)):
        logging.info("Market closing soon.  Closing positions.")
        date = datetime.datetime.now()
        local_date = date.strftime("%x")
        local_time = date.strftime("%X")
        cancel_all('all')
        logging.info(f"Finish time: {local_time} on {local_date}")
        # because script is started by local batch file, we want it to 
        # exit every day, so it closes the cmd prompt
        cleanup_files()
        get_updates()
        sys.exit()
    # slow down time between calls to 5 sec    
    else:
        logging.info("next check in 4...") 
        time.sleep(4) 

def rescan_stocks():
    # Lost $3k on a paper account due to this. 3/26/21
    # possibly fixed 4/28/21
    # return os.system("python control.py --rescan") # doesn't multi-thread
    return subprocess.Popen(["python", "control.py", "--rescan"])

def run_watchdog(count):
    # poor man's web socket
    while count < 6500:
        count+=1
        try:
            # run like normal on every check except for the ones at the 30 min marks
            # if count % 5 != 0 and count < 10:
            if count % 450 != 0:
                client = build_client()
                tCLT = threading.Thread(target=check_long_trades(client))
                tCLT.start()
                tCST = threading.Thread(target=check_short_trades(client))
                tCST.start()
                tCLT.join()
                tCST.join()
                tRL = threading.Thread(target=rate_limiter(count)) # this function has exit conditions
                tRL.start()
                tRL.join()
            # at every 30 min mark, rescan
            else: 
                rescan_stocks()
        except SystemExit:
            sys.exit()
        except KeyboardInterrupt:
            cancel_all('all')
            sys.exit()
        except:
            logging.info("something went wrong running process, probably connection timeout.")
            logging.info(f"Unexpected error: {sys.exc_info()}")
            pass

if __name__ == "__main__":
    # run_watchdog(0)
    start_test(0)