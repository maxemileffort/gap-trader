import glob
import os
import re
from shutil import move, copyfile
import sys
import time
import zipfile

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from splinter import Browser

# these will need to be setup manually the first go around
from settings import CHROMEDRIVER_DIR1, CHROMEDRIVER_DIR2, DL_DIR

def get_version_links(href):
    return href and re.compile("chromedriver.storage.googleapis.com").search(href)

def get_html(url):
    r = requests.get(url)
    html = r.text
    return html

def get_updates():
    soup = BeautifulSoup(get_html('https://chromedriver.chromium.org/downloads'), 'lxml')

    version_links = soup.find_all(href=get_version_links)

    # print(version_links[0]['href'])
    # print(version_links[1]['href'])
    # print(version_links[2]['href'])

    dl_link0 = version_links[0]['href']
    dl_link1 = version_links[1]['href']
    dl_link2 = version_links[2]['href']

    dl_links = [dl_link0, dl_link1, dl_link2]

    # download new versions
    count = 1
    for link in dl_links:
        executable_path = {'executable_path': CHROMEDRIVER_DIR2}
        options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory" : "./chromedrivers",
            "download.directory_upgrade": "true",
            "download.prompt_for_download": "false",
            "disable-popup-blocking": "true"
        }
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", prefs)
        try:
            browser = Browser('chrome', **executable_path, headless=False, incognito=True, options=options)
            browser.visit(link)
        except:
            executable_path = {'executable_path': CHROMEDRIVER_DIR1}
            browser = Browser('chrome', **executable_path, headless=False, incognito=True, options=options)
            browser.visit(link)

        time.sleep(1.5)
        dl_button = browser.links.find_by_partial_href('chromedriver_win32.zip')
        time.sleep(1)
        dl_button.click()
        time.sleep(5)

        browser.quit()
        time.sleep(1)

        download_path = DL_DIR
        new_path = os.getcwd()
        old_file_name = download_path+'/chromedriver_win32.zip'
        new_file_name = new_path+f'/chromedrivers/chromedriver_win32-{count}.zip'
        move(old_file_name, new_file_name)
        time.sleep(1)
        count += 1

    # remove old versions
    list_of_files = [glob.glob("./chromedrivers/1/*.exe")]
    list_of_files.append(glob.glob("./chromedrivers/2/*.exe")) 
    list_of_files.append(glob.glob("./chromedrivers/3/*.exe")) 
    for file_ in list_of_files:
        try:
            os.remove(file_[0])
        except:
            pass

    # unzip and remove zips
    list_of_files = glob.glob("./chromedrivers/*.zip") 
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    # print(sorted_files)
    count = 1
    for file_ in sorted_files:
        with zipfile.ZipFile(file_, 'r') as zip_ref:
            zip_ref.extractall(f"./chromedrivers/{count}/")
            count += 1
        try:
            os.remove(file_)
        except:
            pass

if __name__ == "__main__":
    get_updates()