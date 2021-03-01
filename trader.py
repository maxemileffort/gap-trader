# trader 

import csv
import glob
import os

import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

def daily_trader():
    list_of_files = glob.glob("./csv's/trades/*.csv") # * means all if need specific format then *.csv
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    most_recent_file = sorted_files[-1] # last file should be most recent one

    api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL) 
    # account = api.get_account()
    # print(account)
    # print(api.list_positions())

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
        pl = float(trade.unrealized_pl)
        if pl > 0:
            # submit sell order for the position
            api.submit_order(
                symbol=trade.symbol,
                qty=trade.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
    print("Profitable positions closed.")

    print("Getting account balance...")
    account = api.get_account()
    print(f"account: {account}")
    buying_power = account.buying_power
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
            entry_price = round(last + 0.25, 2)
            qty = int(round(investment_per_trade / entry_price, 0))
            print(f"qty is {qty}")
            volume = row['Volume'] # to be used later
            gap_up_percent = row['Gap Up%'] # to be used later
            sl_price = str(round(last * 0.9 - 0.01, 2))
            # sl_limit_price = str(round(last * 0.92 - 0.01, 2))
            # tp_limit_price = str(round(last * 2, 2))
            # print(f"Symbol: {symbol} target entry: {entry_price} Stop Loss price: {sl_price} tp_limit price: {tp_limit_price} Vol: {volume} Gap Up% {gap_up_percent}")
            print(f"Symbol: {symbol} target entry: {entry_price} Stop Loss price: {sl_price} Vol: {volume} Gap Up% {gap_up_percent}")

            try:
                # simple order
                api.submit_order(
                    symbol=symbol,
                    qty=str(qty),
                    side='buy',
                    type='stop',
                    stop_price=str(entry_price),
                    time_in_force='gtc',
                    order_class='simple'
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