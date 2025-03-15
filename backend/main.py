from fastapi import FastAPI, HTTPException
from .database import load_data, stocks_db, traders_db
from .models import Order, Transaction
import asyncio
from .database import update_stock_prices
from .helpers import reserve_funds, create_buy_order, find_matching_sell_orders, fetch_and_validate_buy_order, create_and_update_transaction_in_buy_order, update_buyer_funds_and_holdings, fetch_and_validate_sell_order, create_sell_order, find_matching_buy_orders, create_and_update_transaction_in_sell_order, adjust_balances

app = FastAPI()

# Load data on startup
load_data()

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(update_stock_prices())  

@app.get("/stocks")
def get_stocks():
    return list(stocks_db.values())

@app.get("/stock/{stock_id}")
def get_stock_by_id(stock_id: str):
    # Fetch stock from in-memory database
    stock = stocks_db.get(stock_id)
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Create response with stock details, open orders, and last 10 transactions
    stock_data = {
        "id": stock.id,
        "name": stock.name,
        "current_price": stock.current_price,
        "amount": stock.amount,
        "open_orders": stock.open_orders,
        "transactions": stock.transactions[-10:],  # Last 10 transactions
    }
    return stock_data


@app.get("/traders")
def get_traders():
    return list(traders_db.values())

@app.get("/trader-names")
def get_trader_names():
    return {"trader_names": [trader.name for trader in traders_db.values()]}

@app.get("/trader/{trader_id}")
def get_trader_details(trader_id: str):
    trader = traders_db.get(trader_id)
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")

    return {
        "name": trader.name,
        "money": trader.money,
        "holdings": trader.holdings,
        "buy_orders": list(trader.buy_orders.values()),
        "sell_orders": list(trader.sell_orders.values()),
    }


@app.get("/get_last_transactions/{trader_id}")
def get_last_transactions(trader_id: str):
    trader = traders_db.get(trader_id)
    
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found.")
    
    # Fetch the last 8 transactions, if fewer transactions are available, return all of them
    last_transactions = trader.transactions[-8:]
    
    return {"trader_id": trader_id, "last_transactions": last_transactions}

@app.post("/place_buy_order")
def place_buy_order(trader_id: str, stock_id: str, price: float, amount: int):
    # Fetch trader and stock and validate constraints
    trader, stock = fetch_and_validate_buy_order(trader_id, stock_id, price, amount, traders_db, stocks_db)

    # Reserve funds and create the buy order
    reserve_funds(trader, price, amount)
    buy_order = create_buy_order(trader_id, stock_id, price, amount)
    
    # Get matched sell orders
    matched_sell_orders = find_matching_sell_orders(stock_id, price, traders_db)

    if matched_sell_orders:
        for sell_order, seller in matched_sell_orders:
            if sell_order.amount < amount:
                # Full match, buyer purchases all shares from this sell order (E.g., buyer wants 10, seller has 5)
                amount -= sell_order.amount
                trade_cost = sell_order.amount * sell_order.price
                
                # Deduct from reserved funds and actual money, and update the buyer's holdings
                update_buyer_funds_and_holdings(trader, stock_id, trade_cost, sell_order.amount)

                # Update the seller's money and holdings
                seller.money += trade_cost
                seller.holdings[stock_id] = seller.holdings.get(stock_id, 0) - sell_order.amount

                # Create transaction and update buyer, seller, and stock transaction histories
                create_and_update_transaction_in_buy_order(trader, seller, stock_id, sell_order, trade_cost, sell_order.amount, stock)

                # Remove stock holdings for seller if they become zero
                if seller.holdings[stock_id] == 0:
                    del seller.holdings[stock_id]

                # Remove the completed sell order from stock's open orders 
                if sell_order in stock.open_orders:
                    stock.open_orders.remove(sell_order)

                # Sell order is fully completed, remove the completed sell order from the seller's open orders
                sell_order.amount = 0  
                seller.sell_orders.pop(stock_id, None)

                # Update the seller in database and update stock price to the transaction price
                traders_db[seller.id] = seller
                stocks_db[stock_id].current_price = sell_order.price
            else:
                # Partial match, buyer buys only what they need (E.g., buyer wants 10 or less, seller has 10)
                trade_cost = amount * sell_order.price
                
                # Deduct from buyer's reserved funds and actual money and update the buyer's holdings
                update_buyer_funds_and_holdings(trader, stock_id, trade_cost, amount)

                if sell_order.amount - amount == 0:
                    # Remove the sell order since it's fully executed
                    seller.sell_orders.pop(stock_id, None)
                    # Remove the sell order from stock's open orders 
                    if sell_order in stock.open_orders:
                        stock.open_orders.remove(sell_order)
                
                # Update sell order amount
                sell_order.amount -= amount

                # Update the seller's money and holdings
                seller.money += trade_cost
                seller.holdings[stock_id] = seller.holdings.get(stock_id, 0) - amount 
                 
                # Remove stock holdings for seller if they become zero
                if seller.holdings[stock_id] == 0:
                    del seller.holdings[stock_id]              
                
                # Create transaction and update buyer, seller, and stock transaction histories
                create_and_update_transaction_in_buy_order(trader, seller, stock_id, sell_order, trade_cost, amount, stock)

                # Remove the buy order since it's fully fulfilled
                amount = 0  # Order fully filled
                trader.buy_orders.pop(stock_id, None)

                # Remove the buy order from stock's open orders 
                if buy_order in stock.open_orders:
                    stock.open_orders.remove(buy_order)

                # Update the seller in database and Update stock price to the transaction price
                traders_db[seller.id] = seller
                stocks_db[stock_id].current_price = sell_order.price
                break
        
        # If there are still shares left in the buy order, place it as an active buy order
        if amount > 0:
            buy_order.amount = amount       
            trader.buy_orders[stock_id] = buy_order
            # Add the buy order to the stock's open orders
            stock.open_orders.append(buy_order)
    else:
        # No matching sell orders, place the buy order for future matching and add the buy order to the stock's open orders
        trader.buy_orders[stock_id] = buy_order
        stock.open_orders.append(buy_order)
    
    # After the transaction, clear the reserved funds to zero if the buy order was completely fulfilled
    if amount == 0:
        trader.reserved_funds = 0

    # Update the buyer in the database
    traders_db[trader.id] = trader
    return {"message": "Buy order processed successfully", "buy_order": buy_order}


# 2. Cancel a Buy Order
@app.delete("/cancel_buy_order")
def cancel_buy_order(trader_id: str, stock_id: str):
    trader = traders_db.get(trader_id)
    
    if not trader or stock_id not in trader.buy_orders:
        raise HTTPException(status_code=404, detail="Buy order not found.")
    
    # Retrieve the buy order and release the reserved funds
    order = trader.buy_orders.pop(stock_id)
    total_cost = order.price * order.amount
    trader.reserved_funds -= total_cost  

    # Update the trader in the database
    traders_db[trader.id] = trader

    # Remove the buy order from the stock's open orders 
    stock = stocks_db.get(stock_id)
    if order in stock.open_orders:
        stock.open_orders.remove(order)
    
    return {"message": "Buy order cancelled successfully", "order": order}  


@app.post("/place_sell_order")
def place_sell_order(trader_id: str, stock_id: str, price: float, amount: int):
    # Fetch trader and stock and validate constraints
    trader, stock = fetch_and_validate_sell_order(trader_id, stock_id, price, amount, traders_db, stocks_db)
    
    # Create the sell order
    sell_order = create_sell_order(trader_id, stock_id, price, amount)

    # Find matching buy orders
    matched_buy_orders = find_matching_buy_orders(stock_id, price, traders_db)
    
    if matched_buy_orders:
        for buy_order, buyer in matched_buy_orders:

            if buy_order.amount < amount:
                # Seller sells part of what he has (e.g., buyer wants 10, seller has 15)
                amount -= buy_order.amount
                trade_cost = buy_order.amount * buy_order.price
                
                # Update the seller's and buyer's holdings
                buyer.holdings[stock_id] = buyer.holdings.get(stock_id, 0) + buy_order.amount
                trader.holdings[stock_id] -= buy_order.amount

                # Adjust balances
                adjust_balances(trader, buyer, trade_cost)
                
                # create transaction and update the seller's, buyer's, and stock's history
                create_and_update_transaction_in_sell_order(trader, buyer, stock, stock_id, buy_order, buy_order.amount, trade_cost)

                # Remove the open buy order (which is now closed) from the stock's open orders
                if buy_order in stock.open_orders:
                    stock.open_orders.remove(buy_order)

                # Remove completed buy order, and update buyer in the database
                buy_order.amount = 0
                buyer.buy_orders.pop(stock_id, None)
                traders_db[buyer.id] = buyer

                # Update stock price to the transaction price
                stocks_db[stock_id].current_price = buy_order.price

            else:
                # Seller sells everything he has (e.g., buyer wants 10, seller has 10 or less)
                trade_cost = amount * buy_order.price
                
                # Update holdings
                buyer.holdings[stock_id] = buyer.holdings.get(stock_id, 0) + amount
                trader.holdings[stock_id] -= amount
                
                # Adjust balances
                adjust_balances(trader, buyer, trade_cost)

                # Remove stock entry if holdings become zero
                if trader.holdings[stock_id] == 0:
                    del trader.holdings[stock_id]

                if buy_order.amount - amount == 0:
                    # Remove the buy order since it's fully executed
                    buyer.buy_orders.pop(stock_id, None)   
                    # Remove the buy order from stock's open orders
                    if buy_order in stock.open_orders:
                        stock.open_orders.remove(buy_order)

                # Update buy order amount
                buy_order.amount -= amount

                # Create transaction and update the seller's, buyer's, and stock's history
                create_and_update_transaction_in_sell_order(trader, buyer, stock, stock_id, buy_order, amount, trade_cost)

                # Remove the sell order since it's fully executed
                amount = 0  # Order fully filled
                trader.sell_orders.pop(stock_id, None)

                # Remove the sell order from stock's open orders 
                if sell_order in stock.open_orders:
                    stock.open_orders.remove(sell_order)

                # Update buyer in database
                traders_db[buyer.id] = buyer

                # Update stock price to the transaction price
                stocks_db[stock_id].current_price = buy_order.price
                break

        # If there's any stock left unsold, keep it as an active sell order
        if amount > 0:
            sell_order.amount = amount       
            trader.sell_orders[stock_id] = sell_order

            # Add the sell order to the stock's open orders
            stock.open_orders.append(sell_order)
    else:
        # No matching buy orders, place the sell order for future matching and add the sell order to the stock's open orders
        trader.sell_orders[stock_id] = sell_order
        stock.open_orders.append(sell_order)
    
    # Update the seller in the database
    traders_db[trader.id] = trader
    return {"message": "Sell order processed successfully", "sell_order": sell_order}


@app.delete("/cancel_sell_order")
def cancel_sell_order(trader_id: str, stock_id: str):
    trader = traders_db.get(trader_id)

    if not trader or stock_id not in trader.sell_orders:
        raise HTTPException(status_code=404, detail="Sell order not found.")

    # Remove the sell order
    sell_order = trader.sell_orders.pop(stock_id)

    # Update the seller in the database
    traders_db[trader.id] = trader

    # Remove the sell order from the stock's open orders
    stock = stocks_db.get(stock_id)
    if sell_order in stock.open_orders:
        stock.open_orders.remove(sell_order)

    return {"message": "Sell order cancelled successfully", "order": sell_order}

