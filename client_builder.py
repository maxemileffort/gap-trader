# client builder 
import atexit

import tda

from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID, CHROMEDRIVER_DIR1, CHROME_DIR

client_id = CONSUMER_KEY + "@AMER.OAUTHAP"
path_to_token = "./tokens/token.json"

def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.binary_location = CHROME_DIR
    driver = webdriver.Chrome(CHROMEDRIVER_DIR1, chrome_options=options)
    atexit.register(lambda: driver.quit())
    return driver

def build_client():
    client = tda.auth.easy_client(api_key=client_id, redirect_uri=CALLBACK_URL, token_path=path_to_token, webdriver_func=make_driver, asyncio=False)
    return client

if __name__ == "__main__":
    build_client()