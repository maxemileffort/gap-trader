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
APCA_API_KEY_ID = <your key>
APCA_API_SECRET_KEY = <your secret key>
APCA_API_BASE_URL = https://api.alpaca.markets 
APCA_API_PAPER_BASE_URL = https://paper-api.alpaca.markets 
```
