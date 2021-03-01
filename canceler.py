# canceler 

import alpaca_trade_api as tradeapi

from settings import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_API_PAPER_BASE_URL, APCA_API_BASE_URL

api = tradeapi.REST(APCA_API_KEY_ID, APCA_API_SECRET_KEY, base_url=APCA_API_PAPER_BASE_URL)

def cancel_all():
    # cancel all open orders
    orders = api.list_orders(status="open")
    print("Canceling orders...")

    for order in orders:
        api.cancel_order(order.id)

    print("Orders canceled.")

    # close all trades    
    positions = api.list_positions()
    print("Closing positions...")
    for trade in positions:
        # submit sell order for the position
        try:
            api.submit_order(
                symbol=trade.symbol,
                qty=trade.qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
        # it might be a short position, so try a buy order
        except:
            api.submit_order(
                symbol=trade.symbol,
                qty=trade.qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
    print("All positions closed.")

if __name__ == "__main__":
    cancel_all()