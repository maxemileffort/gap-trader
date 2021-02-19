# control
import time, getopt, sys
from scraper import scraper
from trader import daily_trader
from assessor import assess
from watchdog import watchdog

option_string = ('What would you like to do? (Pick a number)\n 1. Scrape Data Only\n' 
                ' 2. Assess Data Only\n 3. Trade Only\n 4. Scrape and Assess\n 5. Assess and Trade\n' 
                ' 6. Scrape, Assess, and Trade\n 7. Start Watchdog\n 8. Exit\n Pick a number.')

def present_selection():
    print(option_string)
    choice = input("Make a selection:   ")
    eval_choice(choice)

def eval_choice(choice):
    if choice == '1': # scrape only
        scraper()
        print("working...")
        time.sleep(10)
        print("almost done...")
        time.sleep(10)
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
        watchdog()
    elif choice == '8': # exit
        pass
    else: # fat finger or something
        print('try again dummy.')
        present_selection()

# Get full command-line arguments
full_cmd_arguments = sys.argv

# Keep all but the first
argument_list = full_cmd_arguments[1:]

short_options = "123456"
long_options = ["scrape", "assess", "trade", "s-and-a", "a-and-t", "s-a-and-t"]

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
    else:
        present_selection()

if __name__ == "__main__":
    present_selection()