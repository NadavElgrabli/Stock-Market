from pydantic import BaseModel
from typing import Dict, List

# Stock model representing the stock data
class Stock(BaseModel):
    id: str
    name: str
    current_price: float
    amount: int
    open_orders: List['Order'] = []  # Active buy/sell orders
    transactions: List['Transaction'] = []  # Last 10 completed transactions


# Order model representing a buy or sell order
class Order(BaseModel):
    id: str
    trader_id: str
    stock_id: str
    order_type: str  # "BUY" or "SELL" 
    price: float
    amount: int


class Transaction(BaseModel):
    id: str # Unique transaction ID: f"{stock_id}_{timestamp}"
    buyer_id: str
    buyer_name: str
    seller_id: str
    seller_name: str
    stock_id: str
    price: float
    amount: int
    total: float  # price * amount

# Trader model representing the trader data
class Trader(BaseModel):
    id: str
    name: str
    money: float
    reserved_funds: float = 0.0  # track funds reserved for buy orders
    holdings: Dict[str, int] = {}  # Mapping stock_id to quantity of shares owned
    buy_orders: Dict[str, 'Order'] = {}  # Mapping stock_id to buy orders
    sell_orders: Dict[str, 'Order'] = {}  # Mapping stock_id to sell orders
    transactions: List['Transaction'] = []  # List of transactions



