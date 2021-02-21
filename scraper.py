# scraper 

import requests, re, datetime, time
import lxml.html as lh
from lxml.html.clean import Cleaner
import pandas as pd

from splinter import Browser
from random import seed, random

from sites import urls
from settings import CHROMEDRIVER_DIR

def get_gaps(url):
    date = datetime.datetime.now()
    local_date = date.strftime("%x").replace("/", "_")
    local_time = date.strftime("%X").replace(":", "")
    location_string = f"./csv's/{local_date}-{local_time}-stocks.csv"

    # define the location of the Chrome Driver - CHANGE THIS!!!!!
    executable_path = {'executable_path': CHROMEDRIVER_DIR}

    # Create a new instance of the browser, make sure we can see it (Headless = False)
    browser = Browser('chrome', **executable_path, headless=False)

    # define the components to build a URL
    method = 'GET'

    # build the URL and store it in a new variable
    p = requests.Request(method, url).prepare()
    myurl = p.url

    # go to the URL
    browser.visit(myurl)
    seed(1)
    time.sleep(random()+1)
    browser.driver.set_window_size(1524, 1024)
    time.sleep(random()+1)
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random()+1)
    try:
        browser.find_by_css('.show-all')[1].click()
    except:
        print("element doesn't exist.")
        pass

    time.sleep(random()+10)

    html = browser.html

    browser.quit()

    # print(html)

    doc = lh.fromstring(html)

    cleaner = Cleaner(page_structure=False, links=False)
    doc = cleaner.clean_html(html)

    doc = lh.fromstring(doc)
    # print(doc)

    th_elements = doc.xpath('//th')
    # print([len(T) for T in th_elements[:12]])
    tr_elements = doc.xpath('//tr')
    # print([len(T) for T in tr_elements[:50]])

    # print(th_elements)
    # print(tr_elements)

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
            print(f"i: {i}")
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
    print(df.dtypes)

    df.to_csv(path_or_buf=location_string)

    return 

def scraper():
    for link in urls:
        get_gaps(link)
        time.sleep(1)

if __name__ == '__main__':
    scraper()