from fastapi import HTTPException
from .models import Trader, Stock, Order, Transaction
import datetime


def get_trader_and_stock(trader_id: str, stock_id: str, traders_db: dict, stocks_db: dict):
    """Fetches the trader and stock objects by their IDs."""
    trader = traders_db.get(trader_id)
    stock = stocks_db.get(stock_id)
    
    if not trader or not stock:
        raise HTTPException(status_code=404, detail="Trader or stock not found.")
    
    return trader, stock


def check_existing_sell_order(trader: Trader, stock_id: str):
    """Checks if the trader has a sell order for the same stock."""
    if stock_id in trader.sell_orders.keys():
        raise HTTPException(status_code=400, detail="Cannot place a buy order while having a sell order for the same stock.")


def validate_amount(amount: int):
    """Validates that the amount is positive."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive.")


def validate_available_money(trader: Trader, price: float, amount: int):
    """Validates if the trader has enough available money (excluding reserved funds)."""
    total_cost = price * amount
    available_money = trader.money - trader.reserved_funds
    if available_money < total_cost:
        raise HTTPException(status_code=400, detail="Not enough money to place the buy order.")
    

def fetch_and_validate_buy_order(trader_id: str, stock_id: str, price: float, amount: int, traders_db: dict, stocks_db: dict):
    """Fetch trader and stock, then validate order constraints."""
    trader, stock = get_trader_and_stock(trader_id, stock_id, traders_db, stocks_db)

    check_existing_sell_order(trader, stock_id)
    validate_amount(amount)
    validate_available_money(trader, price, amount)

    return trader, stock

def check_existing_buy_order(trader: Trader, stock_id: str):
    """Checks if the trader has a buy order for the same stock."""
    if stock_id in trader.buy_orders.keys():
        raise HTTPException(status_code=400, detail="Cannot place a buy order while having a buy order for the same stock.")


def validate_available_stock(trader: Trader, stock_id: str, amount: int):
    """Validates if the trader has enough available stock to sell."""
    if trader.holdings.get(stock_id, 0) < amount:
        raise HTTPException(status_code=400, detail="Not enough stock to place the sell order.")
    
def fetch_and_validate_sell_order(trader_id: str, stock_id: str, price: float, amount: int, traders_db: dict, stocks_db: dict):
    """Fetch trader and stock, then validate order constraints."""
    trader, stock = get_trader_and_stock(trader_id, stock_id, traders_db, stocks_db)

    check_existing_buy_order(trader, stock_id)
    validate_amount(amount)
    validate_available_stock(trader, stock_id, amount)

    return trader, stock


def reserve_funds(trader: Trader, price: float, amount: int):
    """Reserves the funds for the buy order."""
    total_cost = price * amount
    trader.reserved_funds += total_cost

def create_buy_order(trader_id: str, stock_id: str, price: float, amount: int):
    """Creates and returns a new buy order."""
    order_id = f"{trader_id}-{stock_id}-BUY"
    return Order(id=order_id, trader_id=trader_id, stock_id=stock_id, order_type="BUY", price=price, amount=amount)

def create_sell_order(trader_id: str, stock_id: str, price: float, amount: int):
    """Creates and returns a new sell order."""
    order_id = f"{trader_id}-{stock_id}-SELL"
    return Order(id=order_id, trader_id=trader_id, stock_id=stock_id, order_type="SELL", price=price, amount=amount)

def find_matching_sell_orders(stock_id: str, price: float, traders_db: dict):
    matched_orders = []
    for seller in traders_db.values():
        sell_order = seller.sell_orders.get(stock_id)
        if sell_order and sell_order.price <= price:
            matched_orders.append((sell_order, seller))

    # Sort matched sell orders by price (lowest to highest)
    return sorted(matched_orders, key=lambda x: x[0].price)

def find_matching_buy_orders(stock_id: str, price: float, traders_db: dict):
    """Finds and returns a sorted list of matching buy orders."""
    matched_buy_orders = [
        (buyer.buy_orders[stock_id], buyer)
        for buyer in traders_db.values()
        if stock_id in buyer.buy_orders and buyer.buy_orders[stock_id].price >= price
    ]

    # Sort matched buy orders by price (highest to lowest)
    matched_buy_orders.sort(key=lambda x: x[0].price, reverse=True)
    
    return matched_buy_orders


def create_and_update_transaction_in_buy_order(trader, seller, stock_id, sell_order, trade_cost, amount, stock):
    """Creates a transaction and updates buyer, seller, and stock transaction histories."""
    timestamp = datetime.datetime.now()

    transaction = Transaction(
        id=f"{stock_id}_{timestamp}",
        buyer_id=trader.id,
        buyer_name=trader.name,
        seller_id=seller.id,
        seller_name=seller.name,
        stock_id=stock_id,
        price=sell_order.price,
        amount=amount,
        total=trade_cost
    )

    # Add transaction to buyer's, seller's, and stock's transaction history
    trader.transactions.append(transaction)
    seller.transactions.append(transaction)
    stock.transactions.append(transaction)  


def create_and_update_transaction_in_sell_order(trader, buyer, stock, stock_id, buy_order, amount, trade_cost):
    """Creates a transaction and updates the seller's, buyer's, and stock's history."""
    
    # Generate a timestamp
    timestamp = datetime.datetime.now()
    
    # Create a new transaction
    transaction = Transaction(
        id=f"{stock_id}_{timestamp}",
        buyer_id=buyer.id,
        buyer_name=buyer.name,
        seller_id=trader.id,
        seller_name=trader.name,
        stock_id=stock_id,
        price=buy_order.price,
        amount=amount,  
        total=trade_cost
    )

    # Add transaction to seller's, buyer's, and stock's history
    trader.transactions.append(transaction)
    buyer.transactions.append(transaction)
    stock.transactions.append(transaction)



def update_buyer_funds_and_holdings(trader, stock_id, trade_cost, amount):
    trader.reserved_funds -= trade_cost
    trader.money -= trade_cost
    trader.holdings[stock_id] = trader.holdings.get(stock_id, 0) + amount

def adjust_balances(buyer, trader, trade_cost):
    """Adjusts balances for the buyer and trader after a transaction."""
    buyer.reserved_funds -= trade_cost
    buyer.money -= trade_cost
    trader.money += trade_cost
