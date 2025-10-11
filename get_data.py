
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class StockAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect('stock_analysis.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_analysis (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            date TEXT,
            price REAL,
            rsi REAL,
            macd REAL,
            signal REAL,
            sma_20 REAL,
            sma_50 REAL,
            volume_ratio REAL,
            volatility REAL,
            recommendation TEXT,
            score REAL
        )
        ''')
        self.conn.commit()

    def calculate_rsi(self, prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line

    def calculate_volatility(self, prices, window=20):
        returns = prices.pct_change()
        volatility = returns.rolling(window=window).std() * np.sqrt(252)
        return volatility

    def analyze_stock(self, symbol, period='1y'):
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)

        if data.empty:
            return None

        data['RSI'] = self.calculate_rsi(data['Close'])
        data['MACD'], data['Signal'] = self.calculate_macd(data['Close'])
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=20).mean()
        data['Volatility'] = self.calculate_volatility(data['Close'])

        latest = data.iloc[-1]

        score = 0
        recommendations = []

        if latest['RSI'] < 30:
            score += 2
            recommendations.append("Oversold (RSI < 30)")
        elif latest['RSI'] > 70:
            score -= 2
            recommendations.append("Overbought (RSI > 70)")

        if latest['MACD'] > latest['Signal']:
            score += 1
            recommendations.append("Bullish MACD signal")
        else:
            score -= 1
            recommendations.append("Bearish MACD signal")

        if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
            score += 2
            recommendations.append("Strong uptrend")
        elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
            score -= 2
            recommendations.append("Strong downtrend")

        if latest['Volume_Ratio'] > 1.5:
            score += 1
            recommendations.append("High volume activity")

        if latest['Volatility'] < 0.3:
            score += 1
            recommendations.append("Low volatility (stable)")
        elif latest['Volatility'] > 0.6:
            score -= 1
            recommendations.append("High volatility (risky)")

        if score >= 3:
            recommendation = "STRONG BUY"
        elif score >= 1:
            recommendation = "BUY"
        elif score >= -1:
            recommendation = "HOLD"
        elif score >= -3:
            recommendation = "SELL"
        else:
            recommendation = "STRONG SELL"

        self.cursor.execute('''
        INSERT INTO stock_analysis (symbol, date, price, rsi, macd, signal, sma_20, sma_50,
                                  volume_ratio, volatility, recommendation, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, datetime.now().strftime('%Y-%m-%d'), latest['Close'], latest['RSI'],
              latest['MACD'], latest['Signal'], latest['SMA_20'], latest['SMA_50'],
              latest['Volume_Ratio'], latest['Volatility'], recommendation, score))
        self.conn.commit()

        return {
            'symbol': symbol,
            'current_price': latest['Close'],
            'recommendation': recommendation,
            'score': score,
            'analysis': recommendations,
            'rsi': latest['RSI'],
            'macd': latest['MACD'],
            'volatility': latest['Volatility'],
            'trend': 'Uptrend' if latest['Close'] > latest['SMA_20'] else 'Downtrend'
        }

    def get_investment_recommendations(self, symbols, investment_amount=10000):
        results = []
        for symbol in symbols:
            analysis = self.analyze_stock(symbol)
            if analysis:
                results.append(analysis)

        results.sort(key=lambda x: x['score'], reverse=True)

        print(f"\n=== INVESTMENT RECOMMENDATIONS (${investment_amount:,}) ===\n")

        total_allocation = 0
        for i, stock in enumerate(results[:5]):
            if stock['recommendation'] in ['STRONG BUY', 'BUY']:
                weight = max(0.1, (6 - i) / 15)
                allocation = investment_amount * weight
                shares = int(allocation / stock['current_price'])

                print(f"{i+1}. {stock['symbol']} - {stock['recommendation']}")
                print(f"   Price: ${stock['current_price']:.2f}")
                print(f"   Score: {stock['score']}")
                print(f"   Allocation: ${allocation:,.0f} ({weight*100:.1f}%)")
                print(f"   Shares: {shares}")
                print(f"   RSI: {stock['rsi']:.1f}")
                print(f"   Trend: {stock['trend']}")
                print(f"   Volatility: {stock['volatility']:.1f}%")
                print(f"   Analysis: {', '.join(stock['analysis'][:3])}")
                print()

                total_allocation += allocation

        print(f"Total Allocated: ${total_allocation:,.0f}")
        print(f"Cash Reserve: ${investment_amount - total_allocation:,.0f}")

        return results

def main():
    analyzer = StockAnalyzer()

    top_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'CRM']

    print("Analyzing top stocks for investment opportunities...")
    recommendations = analyzer.get_investment_recommendations(top_stocks)

    user_symbols = input("\nEnter additional stock symbols to analyze (comma-separated, or press Enter to skip): ")
    if user_symbols.strip():
        user_list = [s.strip().upper() for s in user_symbols.split(',')]
        user_recommendations = analyzer.get_investment_recommendations(user_list)

if __name__ == '__main__':
    main()
