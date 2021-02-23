# watcher 

import re, datetime, time, csv
import glob
import os

import requests
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL
from canceler import cancel_all

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

count = 0
def start_test(count):
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
    check_long_trades(0)

def move_stop(symbol, new_price, orders, qty):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    print(symbol)
    print(new_price)
    for order in orders:
        if order.symbol == symbol and order.side == 'sell' and order.type == 'stop':
            # print("found a matching order")
            # print(order)
            # grab order id
            order_id = order.id
            # delete old stop
            delete_stop(order_id)
            # create new stop
            create_stop(symbol, new_price, qty)
            print(f"stop moved for {symbol}")

def delete_stop(order_id):
    api.cancel_order(order_id)

# for stop loss
def create_stop(symbol, stop_price, qty):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='stop',
            stop_price=stop_price,
            time_in_force='gtc',
            order_class='simple'
        )
    except:
        pass

# for take profit
def create_exit(symbol, limit_price, qty):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='limit',
            limit_price=limit_price,
            time_in_force='gtc',
            order_class='simple'
        )
    except:
        pass

def check_for_exit(symbol, exit_price, orders, qty):
    match = ''
    for order in orders:
        if order.symbol == symbol and order.side == 'sell' and order.type == 'limit':
            # check for matching limit order
            match = symbol
            print(f"found tp for: {symbol}.")
            break
    # if we can't find one, create it
    if match == '':
        print("No TP found. Creating one.")
        create_exit(symbol, exit_price, qty)

def check_for_stop(symbol, stop, orders, qty):
    match = ''            
    for order in orders:
        # check for matching stop order
        if order.symbol == symbol and order.side == 'sell' and order.type == 'stop':
            match = symbol
            print(f"found stop for: {match}. Putting it in the right place...")
            # if new price and old price are different, move the stop
            if stop != float(order.stop_price):
                # "Move" stop (most times it just gets put in exact same spot)
                move_stop(symbol, stop, orders, qty)
                break
            # if new price and old price match, do nothing
            else:
                print("Stop in right place for now.")
                continue
    # if there isn't a matching stop order, create one        
    if match == '':
        print("no stop found! creating one instead.")
        create_stop(symbol, stop, qty)

def check_long_trades(count):
    # poor man's "websocket"
    count+=1

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
            check_for_exit(symbol, exit_price, orders, qty)
            # lock in free trades @ 5% gain
            if percent_gain >= 5 and percent_gain < 10:
                check_for_stop(symbol, entry_price, orders, qty)
                continue
            # lock in 10% gainers @ 5% gain
            elif percent_gain >= 10 and percent_gain < 15:
                check_for_stop(symbol, round(entry_price*1.05,2), orders, qty)
                continue
            # lock in 15% gainers @ 10% gain
            elif percent_gain >= 15 and percent_gain < 20:
                check_for_stop(symbol, round(entry_price*1.10,2), orders, qty)
                continue
            # lock in 20% gainers @ 15% gain
            elif percent_gain >= 20 and percent_gain < 25:
                check_for_stop(symbol, round(entry_price*1.15,2), orders, qty)
                continue
            # and so on...
            elif percent_gain >= 25 and percent_gain < 30:
                check_for_stop(symbol, round(entry_price*1.20,2), orders, qty)
                continue
            elif percent_gain >= 30 and percent_gain < 35:
                check_for_stop(symbol, round(entry_price*1.25,2), orders, qty)
                continue
            elif percent_gain >= 35 and percent_gain < 40:
                check_for_stop(symbol, round(entry_price*1.30,2), orders, qty)
                continue
            elif percent_gain >= 40 and percent_gain < 45:
                check_for_stop(symbol, round(entry_price*1.35,2), orders, qty)
                continue
            elif percent_gain >= 45 and percent_gain < 50:
                check_for_stop(symbol, round(entry_price*1.40,2), orders, qty)
                continue
            # make sure there's a stop in place
            else:
                print(f"not enough gain to move stops for {symbol}.")
                check_for_stop(symbol, round(entry_price*0.9, 2), orders, qty)
                continue
            
    rate_limiter(count)
    
    
def rate_limiter(count):
    # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    print(f"Finished run number {count}. Starting next trade check.")

    # Figure out when the market will close so we can prepare to sell beforehand.
    clock = api.get_clock()
    closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
    currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
    timeToClose = closingTime - currTime

    # Close all positions when 15 minutes til market close.
    if(timeToClose < (60 * 15)):
        print("Market closing soon.  Closing positions.")
        date = datetime.datetime.now()
        local_date = date.strftime("%x")
        local_time = date.strftime("%X")
        cancel_all()
        print(f"Finish time: {local_time} on {local_date}")
    # slow down time between calls to 5 sec    
    else:
        time.sleep(2) 
        print("next check in 3...") 
        time.sleep(1)
        print("2...") 
        time.sleep(1) 
        print("1...") 
        time.sleep(1) 
        check_long_trades(count)

if __name__ == "__main__":
    start_test(count)