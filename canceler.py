# canceler 
import sys
import json
import tda.orders.equities as equities

from client_builder import build_client
from settings import CALLBACK_URL, CONSUMER_KEY, ACCOUNT_ID

def cancel_all():
    errors = []
    client = build_client()
    # cancel all open orders
    try:
        orders = client.get_orders_by_path(account_id=ACCOUNT_ID, max_results=None, from_entered_datetime=None, to_entered_datetime=None, status=client.Order.Status.QUEUED, statuses=None).json()
        print("Canceling orders...")
        # orders = orders.json()
        for order in orders:
            order_id = order["orderId"]
            print(f"Order ID: {order_id}")
            client.cancel_order(order_id=order_id, account_id=ACCOUNT_ID)

        print("Orders canceled.")
    except:
        print("Unexpected error canceling orders:", sys.exc_info())
        errors.append(sys.exc_info())
        pass

    # close all trades   
    try:
        account_with_positions = client.get_account(account_id=ACCOUNT_ID, fields=client.Account.Fields.POSITIONS).json()["securitiesAccount"]
        try:
            positions = account_with_positions["positions"]
        except:
            positions = {}
        print("Closing positions...")
        if positions == {}:
            print("No positions to close.")
        else:
            for trade in positions:
                print(positions)
                # submit sell order for the position
                symbol = trade["instrument"]["symbol"]
                short_quantity = trade["shortQuantity"]
                long_quantity = trade["longQuantity"]
                try:
                    if long_quantity > 0:
                        client.place_order(
                            account_id=ACCOUNT_ID,
                            order_spec=equities.equity_sell_market(symbol, long_quantity)
                        )
                # it might be a short position, so try a buy order
                    elif short_quantity > 0:
                        client.place_order(
                            account_id=ACCOUNT_ID,
                            order_spec=equities.equity_buy_market(symbol, short_quantity)
                        )
                    else:
                        print("No trades to close.")
                        return
                except:
                    print("Unexpected error closing trades:", sys.exc_info())
                    errors.append(sys.exc_info())
                    pass
    except:
        print("Unexpected error closing trades:", sys.exc_info())
        errors.append(sys.exc_info())
        pass

    if len(errors) > 0:
        print("errors with closing orders and positions:")
        print(errors)
    else:
        print("All orders canceled and positions closed.")

if __name__ == "__main__":
    cancel_all()