# scraper 

import requests, re, datetime, time, os
import threading
import lxml.html as lh
from lxml.html.clean import Cleaner
import pandas as pd

from splinter import Browser
from selenium import webdriver
from random import seed, random, choice

from sites import urls
from settings import CHROMEDRIVER_DIR1, CHROMEDRIVER_DIR2

def get_gaps(url):
    date = datetime.datetime.now()
    local_date = date.strftime("%x").replace("/", "_")
    local_time = date.strftime("%X").replace(":", "")
    location_string = f"./csv's/{local_date}-{local_time}-stocks.csv"

    # define the location of the Chrome Driver - CHANGE THIS!!!!!
    executable_path = {'executable_path': CHROMEDRIVER_DIR2}

    # Create a new instance of the browser, make sure we can see it (Headless = False)
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # define the components to build a URL
    method = 'GET'

    # build the URL and store it in a new variable
    p = requests.Request(method, url).prepare()
    myurl = p.url

    # go to the URL
    try:
        browser = Browser('chrome', **executable_path, headless=False, incognito=True, options=options)
        browser.visit(myurl)
    except:
        # if chrome auto updates and opening a browser fails, 
        # try a different webdriver version
        executable_path = {'executable_path': CHROMEDRIVER_DIR1}
        browser = Browser('chrome', **executable_path, headless=False, incognito=True, options=options)
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
    
    retries = 0
    while retries < 5:
        try:
            browser.find_by_css('.show-all')[1].click()
            break
        except:
            print("element doesn't exist.")
            time.sleep(5)
            retries += 1
            pass

    # add a little randomness to using the page
    time.sleep(random()+random()*10+5)

    html = browser.html

    browser.quit()

    # print(html)

    doc = lh.fromstring(html)

    # remove ads and other scripts
    cleaner = Cleaner(page_structure=False, links=False)
    doc = cleaner.clean_html(html)

    doc = lh.fromstring(doc)
    # print(doc)

    th_elements = doc.xpath('//th')
    # print([len(T) for T in th_elements[:12]])
    tr_elements = doc.xpath('//tr')
    # print([len(T) for T in tr_elements[:50]])

    #Create empty list
    col=[]
    x=0
    #For each row, store each first element (header) and an empty list
    for d in th_elements:
        x+=1
        name=d.text_content().strip()
        # print(f"{i}:{name}")
        col.append((name,[]))

    for j in range(1,len(tr_elements)):
        #T is our j'th row
        T=tr_elements[j]
        # print(f"length of T: {len(T)}")
        
        #If row is not of size 12, the //tr data is not from our table or it's the wrong data
        if len(T)!=12:
            continue
        
        #i is the index of our column
        i=0
        
        #Iterate through each element of the row
        for t in T.iterchildren():
            try:
                data=t.text_content().strip()
                # print(data) 
            except:
                data=""
                # print(data) 
            #Check if row is empty
            if i>0:
            #Convert any numerical value to integers
                try:
                    data=int(data)
                except:
                    pass
            #Append the data to the empty list of the i'th column
            # print(f"i: {i}")
            col[i][1].append(data)
            #Increment i for the next column
            i+=1

    Dict={title:column for (title,column) in col}
    df=pd.DataFrame(Dict)

    try:
        df = df.drop(columns=['Links', 'Name', 'Time', 'Low'])
    except:
        pass

    print("from scraper.py:")
    print(df.head())
    # print(df.dtypes)

    df.to_csv(path_or_buf=location_string)

    return 

def scraper():
    for link in urls:
        get_gaps(link)
        time.sleep(1)

if __name__ == '__main__':
    scraper()