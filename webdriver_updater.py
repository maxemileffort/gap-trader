import sys
import re

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


def get_version_links(href):
    return href and re.compile("chromedriver.storage.googleapis.com").search(href)

def get_html(url):
    # url = 'https://chromedriver.chromium.org/downloads'
    r = requests.get(url)
    html = r.text
    return html

soup = BeautifulSoup(get_html('https://chromedriver.chromium.org/downloads'), 'lxml')

version_links = soup.find_all(href=get_version_links)

# print(version_links[0]['href'])
# print(version_links[1]['href'])
# print(version_links[2]['href'])

dl_link0 = get_html(version_links[0]['href'])
dl_link1 = get_html(version_links[1]['href'])
dl_link2 = get_html(version_links[2]['href'])

soup = BeautifulSoup(dl_link0, 'lxml')
print(soup)
