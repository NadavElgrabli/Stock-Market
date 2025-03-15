# Stock Market Assignment - Simulabs

## Overview

This project implements a small stock exchange system where traders can place buy and sell orders for various stocks. Stock prices are updated based on two factors:

1. **Periodic Market Events**: External events affect the stock prices at fixed intervals.
2. **Trading Activity**: The price of a stock is updated whenever a buy and sell order is matched and a trade is completed.

The system provides a set of API endpoints for managing stocks, traders, and trading operations. It is designed to work through HTTP requests and can be tested via Swagger UI at `http://127.0.0.1:8000/docs`.

## Key Features

- **Stock Management**: Handles stock data such as current price, amount, and transactions.
- **Trader Management**: Handles trader data, including cash balance, holdings, and open orders.
- **Trading Operations**: Allows placing and canceling buy and sell orders.
- **Transaction Recording**: Updates stock prices based on trade execution and market events.

## Key API Endpoints

- **POST /place_buy_order**: Place a buy order for a stock.
- **POST /place_sell_order**: Place a sell order for a stock.
- **DELETE /cancel_buy_order**: Cancel a buy order.
- **DELETE /cancel_sell_order**: Cancel a sell order.
- **GET /stocks**: Get all current stock data.
- **GET /stock/{stock_id}**: Get stock data by stock ID, including open buy/sell orders and the last 10 transactions.
- **GET /traders**: Get all trader data.
- **GET /trader-names**: Get a list of all trader names.
- **GET /trader/{trader_id}**: Get trader details by ID, including open orders, holdings, and cash balance.
- **GET /get_last_transactions/{trader_id}**: Get the last 8 transactions made by a specific trader.

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- FastAPI
- Uvicorn

### Installation Steps

1. Clone this repository to your local machine.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server using Uvicorn:
   ```bash
   uvicorn backend.main:app --reload
   ```
4. Open your browser and navigate to http://127.0.0.1:8000/docs to access the Swagger UI for testing the API.

## Usage

You can interact with the system via the API endpoints mentioned above. Here's a brief description of how to use some of the key operations:

- **Place Buy Order**:  
  Use the `POST /place_buy_order` endpoint to place a buy order for a specific stock.

- **Place Sell Order**:  
  Use the `POST /place_sell_order` endpoint to place a sell order for a specific stock.

- **Cancel Orders**:  
  Use `DELETE /cancel_buy_order` to cancel a buy order and `DELETE /cancel_sell_order` to cancel a sell order.

- **Get Stock Data**:  
  Use `GET /stocks` to retrieve all current stock data.  
  Use `GET /stock/{stock_id}` to get detailed information for a specific stock, including open orders and the last 10 transactions.

- **Get Trader Data**:  
  Use `GET /traders` to get a list of all traders.  
  Use `GET /trader/{trader_id}` to get detailed information about a specific trader, including open orders, holdings, and cash balance.

You can test and interact with these endpoints through the [Swagger UI](http://127.0.0.1:8000/docs).

## Additional Notes

- The system uses an in-memory database to store stock and trader information.
- The stock price is updated periodically based on external market events and trading activities.
- A trader cannot have both a buy and sell order for the same stock at the same time.
- Initially, all stocks are owned by the stock market itself, which acts as a trader. The stock market lists all stocks for sale at the prices defined in the JSON file. These sell orders automatically update whenever stock prices change due to external market events. Buyers initially must purchase their first stocks from the stock market itself.
- Random market events occur every minute to simulate real-world factors such as financial reports, news articles, or product launches. These events affect stock prices dynamically. The algorithm behind this works as follows:
  - Every minute, a market event is triggered that either increases or decreases stock prices.
  - A **market trend** is randomly chosen to be either positive or negative (`+1` for good news, `-1` for bad news).
  - An **impact factor** is randomly determined between **1% and 5%** to define the magnitude of change.
  - The stock price is then adjusted based on these factors, creating a simulated market that reacts to external forces in an unpredictable way.
- When a trader places a **buy order**, the system searches for all available **sell orders** for the requested stock that match the buyer's price or are listed for a lower price. The trader automatically purchases from the seller offering the best price (i.e., the lowest sell price available).
- Similarly, when a trader places a **sell order**, the system looks for all **buy orders** where traders are willing to pay the listed price or higher. The stock is then sold to the buyer willing to pay the highest price.
- This order-matching mechanism ensures that trades are executed efficiently, following a **best price priority** model:
  - Buy orders are matched to the **cheapest** available sell order.
  - Sell orders are matched to the **highest** available buy order.
- This is implemented in the system using sorting mechanisms:
  - **Buy orders** are sorted from highest to lowest price to ensure that sellers get the best possible deal.
  - **Sell orders** are sorted from lowest to highest price to ensure that buyers purchase at the most favorable price.
- **Reserved Funds Mechanism**:
  - When a trader places a buy order, the required funds are **reserved** from their account to ensure they have enough money to complete the purchase.
  - If the buy order is successfully executed, the reserved funds are used to complete the transaction.
  - If the order is canceled or unmatched, the reserved funds are released back to the trader’s balance.
  - This prevents traders from placing buy orders they cannot afford and ensures smooth trading operations.

## Points to Consider

### Using an in-memory database instead of a real database:

- The current implementation stores stock and trader data in memory, meaning all data is lost when the system shuts down.
- A proper **relational database (PostgreSQL, MySQL)** or **NoSQL database (MongoDB, Redis)** would have allowed for persistent storage, better scalability, and the ability to analyze historical trading data.
- A real database would also help prevent data corruption and enable concurrent user access more efficiently.

### Stock price updates based on transactions:

- In the current system, whenever a trade is completed, the stock price updates to match the transaction price.
- However, this approach can be **exploited**—a trader could intentionally buy a stock at a high price and then sell it at a significantly lower price to crash the stock’s value. This feature can be canceled to prevent such manipulation by commenting out lines: 119, 158, 244, 286 in `backend/main.py`.
- Future improvements could refine stock price updates by incorporating trade volume, historical trends, and market activity for a more realistic approach.
