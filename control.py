# control
import time, datetime, getopt, sys, threading

from scraper import scraper
from trader import daily_trader
from assessor import assess
from watchdog import run_watchdog
from setup_folders import setup_folders

import tda
from client_builder import build_client

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID

option_string = ('What would you like to do? (Pick a number)\n 1. Scrape Data Only\n' 
                ' 2. Assess Data Only\n 3. Trade Only\n 4. Scrape and Assess\n 5. Assess and Trade\n' 
                ' 6. Scrape, Assess, and Trade\n 7. Start Watchdog\n 8. All 4\n 9. Exit\n Pick a number.')

# automate starting entire script
def await_market_open(num):
    setup_folders()
    num += 1
    if num > 4:
        print("market not opening today")
        return
    print("checking time...")
    client = build_client()
    today = datetime.date.today()
    clock = client.get_hours_for_single_market(market=client.Markets.EQUITY, date=today).json()["equity"]["EQ"]
    # print(clock)
    
    # app starts right at 9:30 est from scheduler
    # if it's a trading day, start the app
    if clock["isOpen"] == True:
        opening_time = time.mktime(datetime.datetime.now().replace(hour=8, minute=30, second=0, microsecond=0).timetuple())
        curr_time = time.mktime(datetime.datetime.now().timetuple())
        market_open_check = curr_time - opening_time
        print(f"market_open_check: {market_open_check}")
        if (market_open_check <= 5*60):
            print(f"Market open, sleeping for {market_open_check} min then beginning process.")
            time.sleep(60*market_open_check)
        print("Beginning process.")
        scraper()           #
        assess('skip')      #
        time.sleep(1)       # This whole process (from scrape to starting watchdog) takes about 2-5 minutes
        daily_trader()      # so there's also inherently a delay between market open and when the app 
        time.sleep(1)       # starts trading
        run_watchdog(0)     #
    else:
        print("market not open today.")
        sys.exit()

def present_selection():
    setup_folders()
    print(option_string)
    choice = input("Make a selection:   ")
    eval_choice(choice)

def eval_choice(choice):
    if choice == '1': # scrape only
        print("working...")
        scraper()
        print("done scraping.")
        present_selection()
    elif choice == '2': # assess only
        assess('skip')
        time.sleep(2)
        print("Files created.")
        present_selection()
    elif choice == '3': # trade only
        print("creating orders...")
        daily_trader()
        time.sleep(8)
        print("Orders created.")
        present_selection()
    elif choice == '4': # scrape and assess
        scraper()
        print("working...")
        time.sleep(10)
        print("almost done...")
        time.sleep(10)
        print("done scraping.")
        print("creating assessment...")
        assess('skip')
        time.sleep(2)
        print("Files created.")
        present_selection()
    elif choice == '5': # assess and trade
        print("creating assessment...")
        assess('skip')
        time.sleep(2)
        print("Files created.")
        print("creating orders...")
        daily_trader()
        time.sleep(8)
        print("Orders created.")
        present_selection()
    elif choice == '6': # all 3
        scraper()
        print("working...")
        time.sleep(10)
        print("almost done...")
        time.sleep(10)
        print("done scraping.")
        print("creating assessment...")
        assess('skip')
        time.sleep(2)
        print("Files created.")
        print("creating orders...")
        daily_trader()
        time.sleep(8)
        print("Orders created.")
        present_selection()
    elif choice == '7': # watchdog
        print("Starting watchdog...")
        time.sleep(1)
        run_watchdog(0)
    elif choice == '8': # runs all 3 after waiting for market to open, then begins watchdog
        await_market_open(0)
    elif choice == '9': # exit
        sys.exit()
    else: # fat finger or something
        print('try again dummy.')
        present_selection()

# Get full command-line arguments
full_cmd_arguments = sys.argv

# Keep all but the first
argument_list = full_cmd_arguments[1:]

short_options = "12345678"
long_options = ["scrape", "assess", "trade", "s-and-a", "a-and-t", "s-a-and-t", "watch", 'auto']

try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    # Output error, and return with an error code
    print (str(err))
    present_selection()

# Evaluate given options
for current_argument, current_value in arguments:
    if current_argument in ("-1", "--scrape"):
        eval_choice('1')
    elif current_argument in ("-2", "--assess"):
        eval_choice('2')
    elif current_argument in ("-3", "--trade"):
        eval_choice('3')
    elif current_argument in ("-4", "--s-and-a"):
        eval_choice('4')
    elif current_argument in ("-5", "--a-and-t"):
        eval_choice('5')
    elif current_argument in ("-6", "--s-a-and-t"):
        eval_choice('6')
    elif current_argument in ("-7", "--watch"):
        eval_choice('7')
    elif current_argument in ("-8", "--auto"):
        eval_choice('8')
    else:
        present_selection()

if __name__ == "__main__":
    present_selection()