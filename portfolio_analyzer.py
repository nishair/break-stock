"""Portfolio optimization and fundamental analysis module."""

import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

class PortfolioAnalyzer:
    """Portfolio analysis with fundamental metrics and optimization."""
    def __init__(self):
        self.conn = sqlite3.connect('portfolio_analysis.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_recommendations (
            id INTEGER PRIMARY KEY,
            date TEXT,
            portfolio_composition TEXT,
            expected_return REAL,
            risk_level REAL,
            sharpe_ratio REAL,
            diversification_score REAL
        )
        ''')
        self.conn.commit()

    def get_fundamental_data(self, symbol):
        """Retrieve fundamental financial data for a stock symbol."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            fundamentals = {
                'pe_ratio': info.get('forwardPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'roe': info.get('returnOnEquity', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'profit_margin': info.get('profitMargins', 0),
                'market_cap': info.get('marketCap', 0),
                'dividend_yield': info.get('dividendYield', 0) or 0,
                'beta': info.get('beta', 1),
                'sector': info.get('sector', 'Unknown')
            }
            return fundamentals
        except Exception:  # pylint: disable=broad-except
            return None

    def calculate_fundamental_score(self, fundamentals):
        """Calculate fundamental analysis score based on financial metrics."""
        if not fundamentals:
            return 0

        score = 0

        if fundamentals['pe_ratio'] and 10 <= fundamentals['pe_ratio'] <= 25:
            score += 1
        elif fundamentals['pe_ratio'] and fundamentals['pe_ratio'] < 10:
            score += 2

        if fundamentals['pb_ratio'] and fundamentals['pb_ratio'] < 3:
            score += 1

        if fundamentals['debt_to_equity'] and fundamentals['debt_to_equity'] < 50:
            score += 1

        if fundamentals['roe'] and fundamentals['roe'] > 0.15:
            score += 2
        elif fundamentals['roe'] and fundamentals['roe'] > 0.10:
            score += 1

        if fundamentals['revenue_growth'] and fundamentals['revenue_growth'] > 0.10:
            score += 2
        elif fundamentals['revenue_growth'] and fundamentals['revenue_growth'] > 0.05:
            score += 1

        if fundamentals['profit_margin'] and fundamentals['profit_margin'] > 0.20:
            score += 2
        elif fundamentals['profit_margin'] and fundamentals['profit_margin'] > 0.10:
            score += 1

        if fundamentals['dividend_yield'] > 0.02:
            score += 1

        return score

    def calculate_portfolio_metrics(self, symbols, weights=None):
        """Calculate portfolio risk, return, and diversification metrics."""
        if weights is None:
            weights = [1/len(symbols)] * len(symbols)

        if len(weights) != len(symbols):
            weights = [1/len(symbols)] * len(symbols)

        returns_data = []
        fundamentals_data = []

        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1y')
                if not hist.empty:
                    returns = hist['Close'].pct_change().dropna()
                    returns_data.append(returns)

                    fundamentals = self.get_fundamental_data(symbol)
                    fundamentals_data.append(fundamentals)
            except Exception:  # pylint: disable=broad-except
                continue

        if not returns_data:
            return None

        returns_df = pd.concat(returns_data, axis=1, keys=symbols[:len(returns_data)])
        returns_df = returns_df.dropna()

        if returns_df.empty:
            return None

        portfolio_returns = (returns_df * weights[:len(returns_data)]).sum(axis=1)

        expected_return = portfolio_returns.mean() * 252
        portfolio_risk = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = expected_return / portfolio_risk if portfolio_risk > 0 else 0

        correlation_matrix = returns_df.corr()
        avg_correlation = correlation_matrix.values[
            np.triu_indices_from(correlation_matrix.values, k=1)].mean()
        diversification_score = max(0, 1 - avg_correlation)

        sectors = set()
        avg_fundamental_score = 0
        for fund in fundamentals_data:
            if fund:
                sectors.add(fund.get('sector', 'Unknown'))
                avg_fundamental_score += self.calculate_fundamental_score(fund)

        avg_fundamental_score /= len(fundamentals_data) if fundamentals_data else 1
        sector_diversification = len(sectors) / len(symbols)

        total_diversification = (diversification_score + sector_diversification) / 2

        return {
            'expected_return': expected_return,
            'risk': portfolio_risk,
            'sharpe_ratio': sharpe_ratio,
            'diversification_score': total_diversification,
            'fundamental_score': avg_fundamental_score,
            'num_sectors': len(sectors)
        }

    def optimize_portfolio(self, symbols, investment_amount=10000,
                          risk_tolerance='moderate'):
        """Optimize portfolio allocation based on risk tolerance and metrics."""
        risk_multipliers = {
            'conservative': 0.8,
            'moderate': 1.0,
            'aggressive': 1.3
        }

        multiplier = risk_multipliers.get(risk_tolerance, 1.0)

        stock_scores = []
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1y')
                if hist.empty:
                    continue

                returns = hist['Close'].pct_change().dropna()
                sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

                fundamentals = self.get_fundamental_data(symbol)
                fund_score = self.calculate_fundamental_score(fundamentals)

                total_score = (sharpe * multiplier + fund_score) / 2

                stock_scores.append({
                    'symbol': symbol,
                    'score': total_score,
                    'price': hist['Close'].iloc[-1],
                    'fundamentals': fundamentals
                })
            except Exception:  # pylint: disable=broad-except
                continue

        stock_scores.sort(key=lambda x: x['score'], reverse=True)

        selected_stocks = stock_scores[:8]

        total_score = sum(s['score'] for s in selected_stocks)

        allocations = []
        total_allocated = 0

        for stock in selected_stocks:
            if stock['score'] > 0 and total_score > 0:
                weight = stock['score'] / total_score
                allocation = investment_amount * weight * 0.9
                shares = int(allocation / stock['price'])
                actual_allocation = shares * stock['price']

                allocations.append({
                    'symbol': stock['symbol'],
                    'shares': shares,
                    'allocation': actual_allocation,
                    'weight': weight,
                    'price': stock['price'],
                    'fundamentals': stock['fundamentals']
                })
                total_allocated += actual_allocation

        portfolio_composition = ', '.join(
            f"{a['symbol']}:{a['weight']:.1%}" for a in allocations)

        symbols_list = [a['symbol'] for a in allocations]
        weights_list = [a['weight'] for a in allocations]

        metrics = self.calculate_portfolio_metrics(symbols_list, weights_list)

        self.cursor.execute('''
        INSERT INTO portfolio_recommendations
        (date, portfolio_composition, expected_return, risk_level,
         sharpe_ratio, diversification_score)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d'), portfolio_composition,
              metrics['expected_return'] if metrics else 0,
              metrics['risk'] if metrics else 0,
              metrics['sharpe_ratio'] if metrics else 0,
              metrics['diversification_score'] if metrics else 0))
        self.conn.commit()

        return allocations, total_allocated, metrics

    def print_portfolio_recommendation(self, allocations, total_allocated,
                                      metrics, investment_amount):
        """Print formatted portfolio recommendation with metrics."""
        print("\n=== OPTIMIZED PORTFOLIO RECOMMENDATION ===")
        print(f"Investment Amount: ${investment_amount:,}")
        print(f"Total Allocated: ${total_allocated:,.0f}")
        print(f"Cash Reserve: ${investment_amount - total_allocated:,.0f}")

        if metrics:
            print("\nPortfolio Metrics:")
            print(f"Expected Annual Return: {metrics['expected_return']*100:.1f}%")
            print(f"Annual Risk (Volatility): {metrics['risk']*100:.1f}%")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"Diversification Score: {metrics['diversification_score']*100:.1f}%")
            print(f"Sectors Represented: {metrics['num_sectors']}")

        print("\nStock Allocations:")
        for i, stock in enumerate(allocations, 1):
            fund = stock['fundamentals']
            print(f"{i}. {stock['symbol']} - ${stock['allocation']:,.0f} ({stock['weight']*100:.1f}%)")
            print(f"   Shares: {stock['shares']} @ ${stock['price']:.2f}")
            if fund:
                pe_ratio = fund.get('pe_ratio', 'N/A')
                roe = fund.get('roe', 0) * 100 if fund.get('roe') else 'N/A'
                sector = fund.get('sector', 'N/A')
                print(f"   P/E: {pe_ratio} | ROE: {roe}% | Sector: {sector}")
            print()

def main():
    """Main function for portfolio optimization interface."""
    analyzer = PortfolioAnalyzer()

    print("=== PORTFOLIO OPTIMIZATION SYSTEM ===")

    investment_amount = float(input("Enter investment amount ($): ") or "10000")

    risk_tolerance = input("Risk tolerance (conservative/moderate/aggressive) [moderate]: ").lower() or "moderate"

    custom_stocks = input("Enter stock symbols (comma-separated) or "
                         "press Enter for default selection: ")

    if custom_stocks.strip():
        symbols = [s.strip().upper() for s in custom_stocks.split(',')]
    else:
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM',
                  'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'NFLX', 'CRM']

    print(f"\nOptimizing portfolio with {len(symbols)} stocks...")
    print("This may take a moment as we analyze fundamentals and "
          "technical indicators...")

    allocations, total_allocated, metrics = analyzer.optimize_portfolio(
        symbols, investment_amount, risk_tolerance)

    analyzer.print_portfolio_recommendation(
        allocations, total_allocated, metrics, investment_amount)


if __name__ == '__main__':
    main()