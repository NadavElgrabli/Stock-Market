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
- Initially, all stocks are owned by the stock exchange, so sell orders are created at the stock price defined in the JSON file.
#   S t o c k - M a r k e t  
 