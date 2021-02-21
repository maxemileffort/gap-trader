# watcher 

import re, datetime, time, csv
import glob
import os

import requests
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

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
    check_long_trades(0, 10)

def move_stop(symbol, new_price, orders):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    print(symbol)
    print(new_price)
    for order in orders:
        if order.symbol == symbol and order.side == 'sell' and order.type == 'stop':
            print("found a matching order")
            print(order)
            # grab order id
            order_id = order.id
            # send to url
            url = f"{APCA_API_PAPER_BASE_URL}/v2/orders/{order_id}"
            payload = {'stop_price': str(new_price)}
            r = requests.patch(url, payload)
            print(r.response)
        else:
            print("no stop found!")

def check_for_stop(symbol, stop, orders):
    match = ''            
    for order in orders:
        if order.symbol == symbol and order.side == 'sell' and order.type == 'stop':
            # check for matching stop order
            match = symbol
            break
    print(f"match: {match}")
    # if there isn't a matching stop order, create one        
    if match == '':
        print("creating stop")
        create_stop(symbol, stop, orders)

def create_stop(symbol, stop_price, orders):
    try:
        api.submit_order(
            symbol=symbol,
            qty=100,
            side='sell',
            type='stop',
            stop_price=stop_price,
            time_in_force='gtc',
            order_class='simple'
        )
    except:
        pass

def check_long_trades(count, runs):
    positions = api.list_positions()
    orders = api.list_orders()
    # print(orders)
    for trade in positions:
        print("trade:")
        print(trade)
        if trade.side == "long":
            symbol = trade.symbol
            entry_price = float(trade.avg_entry_price)
            current_price = float(trade.current_price)
            percent_gain = round((current_price - entry_price) / entry_price * 100, 2)
            print(f'symbol: {symbol} percent gain: {percent_gain} profit/loss: {trade.unrealized_pl}')
            # lock in 25% gainers @ 20% gain
            if percent_gain > 25:
                move_stop(symbol, round(entry_price*1.20,2), orders)
                continue
            # lock in 20% gainers @ 15% gain
            elif percent_gain > 20:
                move_stop(symbol, round(entry_price*1.15,2), orders)
                continue
            # lock in 15% gainers @ 10% gain
            elif percent_gain > 15:
                move_stop(symbol, round(entry_price*1.10,2), orders)
                continue
            # lock in 10% gainers @ 5% gain
            elif percent_gain > 10:
                move_stop(symbol, round(entry_price*1.05,2), orders)
                continue
            # lock in free trades @ 5% gain
            elif percent_gain > 5:
                move_stop(symbol, entry_price, orders)
                continue
            # make sure there's a stop in place
            else:
                print(f"not enough gain to move stops for {symbol}.")
                check_for_stop(symbol, round(entry_price*0.9, 2), orders)            
                create_stop(symbol, round(entry_price*0.9, 2), orders)
                continue
    
    time.sleep(4) # rate limit on API of 200 request per min, so this keeps the position and order calls down to about 30 per min, leaving room for modifying stops.
    
    # poor man's "websocket"
    count+=1
    if count < runs:
        print(f"Finished run {count} of {runs} runs. Starting next trade check.")
        check_long_trades(count, runs)
    else:
        date = datetime.datetime.now()
        local_date = date.strftime("%x")
        local_time = date.strftime("%X")
        print(f"Finish time: {local_time} on {local_date}")

if __name__ == "__main__":
    start_test(count)