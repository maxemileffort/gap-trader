# Algo Trader 

## general workflow 

scraper scrapes gaps into csv -> assessor evaluates based on criteria ->
trader makes trades from the stocks passing criteria -> watcher exits trades systematically

## first

setup virtual environment (note: this is for cmd on Windows)

`python3 -m venv trading-env && trading-env\Scripts\activate.bat`

if changing to a different environment:

`deactivate && path-to-new-env\Scripts\activate.bat`

run 

`pip install -r requirements.txt`

## second

create a `.env` file and add your api key and secret key:

```
CHROMEDRIVER_DIR=<path to chromedriver>
CHROME_DIR=<path to chrome>
CALLBACK_URL=<exactly what is on your app that you created>
CONSUMER_KEY=<your consumer key>
ACCOUNT_ID=<your numerical account number>
```
