# trader 

import re, datetime, time, csv
import glob
import os

import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

list_of_files = glob.glob("./csv's/trades/*.csv") # * means all if need specific format then *.csv
sorted_files = sorted(list_of_files, key=os.path.getctime)
most_recent_file = list_of_files[-1] # last file should be most recent one

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL) 
account = api.get_account()
print(account)
print(api.list_positions())

# cancel all open orders
orders = api.list_orders(status="open")
print("Canceling orders...")

for order in orders:
    api.cancel_order(order.id)

print("Orders canceled.")

# close all profitable trades    
positions = api.list_positions()
print("Closing profitable positions...")
for trade in positions:
    pl = float(trade["unrealized_pl"])
    if pl > 0:
        # submit sell order for the position
        api.submit_order(
            symbol=trade["symbol"],
            qty=trade["qty"],
            side='sell',
            type='market',
            time_in_force='gtc'
        )
print("Profitable positions closed.")

# create orders from most recent gap up analysis
with open(most_recent_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    print("Creating orders...")
    
    order_num = 0
    error_num = 0
    entries = 0
    for row in reader:
        entries+=1
        symbol = row['Symbol']
        last = float(row['Last'])
        limit_price = str(last + 0.25)
        volume = row['Volume']
        gap_up_percent = row['Gap Up%']
        stop_price = str(round(last * 0.93 - 0.01, 2))
        sl_limit_price = str(round(last * 0.92 - 0.01, 2))
        tp_limit_price = str(round(last * 1.20, 2))
        print(f"Symbol: {symbol} Stop price: {stop_price} sl_limit price: {sl_limit_price} tp_limit price: {tp_limit_price}")

        # try:
        api.submit_order(
            symbol=symbol,
            qty=100,
            side='buy',
            type='limit',
            limit_price=limit_price,
            time_in_force='gtc',
            order_class='bracket',
            stop_loss={'stop_price': stop_price,
                    'limit_price':  sl_limit_price},
            take_profit={'limit_price': tp_limit_price}
        )
        order_num+=1
        # except:
        #     print(f"Error with {symbol}")
        #     error_num+=1
        #     pass
    print(f"{entries} Entries found.")
    print(f"{order_num} Orders created.")
    print(f"{error_num} Errors encountered.")
csvfile.close()
        