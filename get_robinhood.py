import pandas as pd
import yfinance as yf
import sqlite3
from datetime import datetime

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

# Create tables for stock data and user transactions
cursor.execute('''
CREATE TABLE IF NOT EXISTS stock_data (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_transactions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    date TEXT,
    shares INTEGER,
    price REAL
)
''')

conn.commit()

def fetch_and_store_stock_data(symbol):
    # Fetch data from Yahoo Finance
    stock_data = yf.download(symbol, period='1mo', interval='1d')
    stock_data.reset_index(inplace=True)
    
    # Store data in the database
    for index, row in stock_data.iterrows():
        cursor.execute('''
        INSERT INTO stock_data (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, row['Date'].strftime('%Y-%m-%d'), row['Open'], row['High'],
              row['Low'], row['Close'], row['Volume']))
    conn.commit()

def record_user_buy(symbol, shares, price):
    # Record the user's transaction
    cursor.execute('''
    INSERT INTO user_transactions (symbol, date, shares, price)
    VALUES (?, ?, ?, ?)
    ''', (symbol, datetime.now().strftime('%Y-%m-%d'), shares, price))
    conn.commit()

def view_stock_data(symbol):
    # Fetch stock data for the given symbol
    cursor.execute('SELECT * FROM stock_data WHERE symbol = ?', (symbol,))
    rows = cursor.fetchall()
    
    if rows:
        print(f"\nStock Data for {symbol}:")
        for row in rows:
            print(row)
    else:
        print(f"No data found for symbol: {symbol}")

def view_user_transactions():
    # Fetch all user transactions
    cursor.execute('SELECT * FROM user_transactions')
    rows = cursor.fetchall()
    
    if rows:
        print("\nUser Transactions:")
        for row in rows:
            print(row)
    else:
        print("No user transactions found.")

# Example usage
if __name__ == "__main__":
    # Fetch and store stock data for a specific symbol
    stock_symbol = input("Enter stock symbol to fetch data: ")
    fetch_and_store_stock_data(stock_symbol)

    # Record a user transaction
    user_symbol = input("Enter stock symbol for your buy: ")
    shares = int(input("Enter number of shares bought: "))
    price = float(input("Enter price per share: "))
    record_user_buy(user_symbol, shares, price)

    # View the stored data
    view_stock_data(stock_symbol)  # View the stock data for the entered symbol
    view_user_transactions()  # View all user transactionsA

# Close the database connection
conn.close()