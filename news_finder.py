# news catalyst finder

import requests, re, datetime, time, os
import threading
import lxml.html as lh
from lxml.html.clean import Cleaner

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from splinter import Browser
from random import seed, random, choice

from settings import CHROMEDRIVER_DIR

def news_finder(symbol):
    # define the location of the Chrome Driver - CHANGE THIS!!!!!
    executable_path = {'executable_path': CHROMEDRIVER_DIR}

    # Create a new instance of the browser, make sure we can see it (Headless = False)
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    browser = Browser('chrome', **executable_path, headless=False, incognito=True, options=options)

    # define the components to build a URL
    method = 'GET'
    url = f'https://www.seekingalpha.com/symbol/{symbol}'

    # build the URL and store it in a new variable
    p = requests.Request(method, url).prepare()
    myurl = p.url

    # go to the URL
    browser.visit(myurl)
    seed(1)
    time.sleep(random()+1)
    time.sleep(random()+1)
    try:
        browser.execute_script("var footer = document.querySelector('footer'); if(footer){footer.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
        browser.execute_script("var footer = document.querySelector('#footer'); if(footer){footer.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
        browser.execute_script("var footer = document.querySelector('.footer'); if(footer){footer.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
    except:
        # print("Error occurred triggering lazy loading: ", sys.exc_info())
        pass
    try:
        browser.execute_script("var header = document.querySelector('header'); if(header){header.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
        browser.execute_script("var header = document.querySelector('#header'); if(header){header.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
        browser.execute_script("var header = document.querySelector('.header'); if(header){header.scrollIntoView({behavior: 'smooth', block: 'end', inline: 'nearest'})};")
    except:
        # print("Error occurred triggering lazy loading: ", sys.exc_info())
        pass
    time.sleep(random()+random()*10+2)

    html = browser.html

    time.sleep(1)
    

    # create soup object out of cleaned html
    soup = BeautifulSoup(html, "lxml")

    news_text = soup.find("section", attrs={"data-test-id": "card-container-news"}).find("div", attrs={"data-test-id": "post-list"}).get_text()
    split_text = news_text.split(",")
    first_news_entry = split_text[0]
    # time.sleep(60*5)
    browser.quit()
    print(first_news_entry)

if __name__ == '__main__':
    news_finder("lhdx")