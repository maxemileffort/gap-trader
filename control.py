# control
import time
from scraper import scraper
from trader import daily_trader
from assessor import assess

option_string = ('What would you like to do? (Pick a number)\n 1. Scrape Data Only\n 2. Assess Data Only\n 3. Trade Only\n 4. Scrape and Assess\n 5. Assess and Trade\n 6.Scrape, Assess, and Trade\n 7. Exit\n Pick a number.')

def present_selection():
    print(option_string)
    choice = input("Make a selection:   ")
    eval_choice(choice)

def eval_choice(choice):
    if choice == '1': # scrape only
        scraper()
        print("working...")
        time.sleep(40)
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
        time.sleep(40)
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
        time.sleep(40)
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
    elif choice == '7': # exit
        pass
    else: # fat finger or something
        print('try again dummy.')
        present_selection()

present_selection()      