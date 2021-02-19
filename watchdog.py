# watcher 

import re, datetime, time, csv
import glob
import os

import requests
import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

# symbols = ['AAPL', 'MSFT', 'HLX']

# for symbol in symbols:
#     api.submit_order(
#         symbol=symbol,
#         qty='100',
#         side='buy',
#         type='market',
#         time_in_force='gtc'
#     )

def move_stop(symbol, new_price, orders):
    # search orders list for orders that are sell stop orders with matching symbols, 
    # as that is the stop loss, and move price up to new price
    for order in orders:
        if order.symbol == symbol and order.side == 'sell' and order.type == 'stop':
            print("found a matching symbol")
            print(order)
            # grab order id
            order_id = order.id
            # send to url
            url = f"{APCA_API_PAPER_BASE_URL}/v2/orders/{order_id}"
            payload = {'stop_price': str(new_price)}
            r = requests.patch(url, payload)
            print(r.response)
        else:
            print("no matches found")

def watchdog():
    positions = api.list_positions()
    orders = api.list_orders()

    # print(positions)
    for trade in positions:
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
            move_stop(symbol, round(entry_price*0.9, 2), orders)
            print(f"not enough gain to move stops for {symbol}.")            
    