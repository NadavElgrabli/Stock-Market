import json
from .models import Trader, Stock, Order
import random
import asyncio

# In-memory database
stocks_db = {}
traders_db = {}

# Load data from JSON file
def load_data():
    global stocks_db, traders_db
    with open("BurseJson.json", "r") as file:
        data = json.load(file)

        # Clear existing data while maintaining reference
        stocks_db.clear()
        traders_db.clear()

        stocks_db.update({
            stock["id"]: Stock(
                id=stock["id"], 
                name=stock["name"], 
                current_price=stock["currentPrice"], 
                amount=stock["amount"]
            ) for stock in data["shares"]
        })

        traders_db.update({
            trader["id"]: Trader(
                id=trader["id"], 
                name=trader["name"], 
                money=trader["money"]
            ) 
            for trader in data["traders"]
        })
        
        # Create the "Stock Market" trader
        stock_market = Trader(
            id="0", 
            name="Stock Market", 
            money=0.0,  
            holdings={stock_id: stock.amount for stock_id, stock in stocks_db.items()}, 
            sell_orders={
                stock_id: Order(
                    id=f"order_{stock_id}",
                    trader_id="0",
                    stock_id=stock_id,
                    order_type="SELL",
                    price=stock.current_price,
                    amount=stock.amount
                )
                for stock_id, stock in stocks_db.items()
            }
        )

        # Add the stock market trader to traders_db
        traders_db["0"] = stock_market

# Initialize data at startup
load_data()

async def update_stock_prices():
    while True:
        
        for stock in stocks_db.values():
            old_price = stock.current_price
            
            # Introduce a dynamic market impact factor
            market_trend = random.choice([-1, 1])  # Simulate good/bad news
            impact_factor = random.uniform(0.01, 0.05)  # 1% to 5% change
            
            # Calculate new price with more market influence
            price_change = market_trend * impact_factor * stock.current_price
            stock.current_price = max(1, round(old_price + price_change, 2))  

        # Update the stock market's sell orders to match the new stock prices
        stock_market = traders_db["0"]

        # Update each sell order to reflect the new price
        for stock_id, sell_order in stock_market.sell_orders.items():
            stock = stocks_db.get(stock_id)
            if stock:
                sell_order.price = stock.current_price  # Update the price to the current stock price
                    
        await asyncio.sleep(60)  
