#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from get_data import StockAnalyzer
from portfolio_analyzer import PortfolioAnalyzer
import yfinance as yf

class InvestmentAdvisor:
    def __init__(self):
        self.stock_analyzer = StockAnalyzer()
        self.portfolio_analyzer = PortfolioAnalyzer()

    def comprehensive_analysis(self):
        print("=" * 60)
        print("      COMPREHENSIVE INVESTMENT ANALYSIS SYSTEM")
        print("=" * 60)

        while True:
            print("\nSelect Analysis Type:")
            print("1. Quick Stock Analysis (Top 10 stocks)")
            print("2. Custom Stock Analysis")
            print("3. Portfolio Optimization")
            print("4. Sector Analysis")
            print("5. Risk Assessment")
            print("6. Exit")

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == '1':
                self.quick_stock_analysis()
            elif choice == '2':
                self.custom_stock_analysis()
            elif choice == '3':
                self.portfolio_optimization()
            elif choice == '4':
                self.sector_analysis()
            elif choice == '5':
                self.risk_assessment()
            elif choice == '6':
                print("Thank you for using the Investment Advisor!")
                break
            else:
                print("Invalid choice. Please try again.")

    def quick_stock_analysis(self):
        print("\n" + "="*50)
        print("QUICK STOCK ANALYSIS - TOP PERFORMERS")
        print("="*50)

        top_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD', 'CRM']
        investment_amount = float(input("Enter investment amount ($10,000): ") or "10000")

        recommendations = self.stock_analyzer.get_investment_recommendations(top_stocks, investment_amount)

    def custom_stock_analysis(self):
        print("\n" + "="*50)
        print("CUSTOM STOCK ANALYSIS")
        print("="*50)

        symbols_input = input("Enter stock symbols (comma-separated): ")
        if not symbols_input.strip():
            print("No symbols entered.")
            return

        symbols = [s.strip().upper() for s in symbols_input.split(',')]
        investment_amount = float(input("Enter investment amount ($10,000): ") or "10000")

        print(f"\nAnalyzing {len(symbols)} stocks...")
        recommendations = self.stock_analyzer.get_investment_recommendations(symbols, investment_amount)

        print("\nDetailed Analysis:")
        for stock in recommendations[:5]:
            print(f"\n--- {stock['symbol']} DETAILED ANALYSIS ---")
            fundamentals = self.portfolio_analyzer.get_fundamental_data(stock['symbol'])
            if fundamentals:
                print(f"P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}")
                print(f"P/B Ratio: {fundamentals.get('pb_ratio', 'N/A')}")
                print(f"ROE: {fundamentals.get('roe', 0)*100:.1f}%" if fundamentals.get('roe') else "ROE: N/A")
                print(f"Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}")
                print(f"Revenue Growth: {fundamentals.get('revenue_growth', 0)*100:.1f}%" if fundamentals.get('revenue_growth') else "Revenue Growth: N/A")
                print(f"Sector: {fundamentals.get('sector', 'N/A')}")
                print(f"Market Cap: ${fundamentals.get('market_cap', 0):,.0f}" if fundamentals.get('market_cap') else "Market Cap: N/A")

    def portfolio_optimization(self):
        print("\n" + "="*50)
        print("PORTFOLIO OPTIMIZATION")
        print("="*50)

        investment_amount = float(input("Enter investment amount ($10,000): ") or "10000")
        risk_tolerance = input("Risk tolerance (conservative/moderate/aggressive) [moderate]: ").lower() or "moderate"

        custom_stocks = input("Enter stock symbols (comma-separated) or press Enter for diversified selection: ")

        if custom_stocks.strip():
            symbols = [s.strip().upper() for s in custom_stocks.split(',')]
        else:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM',
                      'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'NFLX', 'CRM']

        print(f"\nOptimizing portfolio with {len(symbols)} stocks for {risk_tolerance} risk profile...")

        allocations, total_allocated, metrics = self.portfolio_analyzer.optimize_portfolio(
            symbols, investment_amount, risk_tolerance)

        self.portfolio_analyzer.print_portfolio_recommendation(
            allocations, total_allocated, metrics, investment_amount)

    def sector_analysis(self):
        print("\n" + "="*50)
        print("SECTOR ANALYSIS")
        print("="*50)

        sectors = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'CRM'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO'],
            'Financial': ['JPM', 'V', 'MA', 'BAC', 'WFC'],
            'Consumer': ['AMZN', 'HD', 'PG', 'KO', 'PEP'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG'],
            'Industrial': ['BA', 'CAT', 'GE', 'MMM']
        }

        print("Available sectors:")
        for i, sector in enumerate(sectors.keys(), 1):
            print(f"{i}. {sector}")

        choice = input("\nSelect sector number or 'all' for comprehensive analysis: ").strip()

        if choice.lower() == 'all':
            print("\nComprehensive Sector Analysis:")
            for sector_name, stocks in sectors.items():
                print(f"\n--- {sector_name.upper()} SECTOR ---")
                avg_scores = []
                for symbol in stocks:
                    analysis = self.stock_analyzer.analyze_stock(symbol)
                    if analysis:
                        avg_scores.append(analysis['score'])
                        print(f"{symbol}: {analysis['recommendation']} (Score: {analysis['score']})")

                if avg_scores:
                    print(f"Sector Average Score: {sum(avg_scores)/len(avg_scores):.1f}")
        else:
            try:
                sector_idx = int(choice) - 1
                sector_name = list(sectors.keys())[sector_idx]
                stocks = sectors[sector_name]

                print(f"\n--- {sector_name.upper()} SECTOR ANALYSIS ---")
                investment_amount = float(input("Enter investment amount for this sector ($5,000): ") or "5000")

                recommendations = self.stock_analyzer.get_investment_recommendations(stocks, investment_amount)
            except (ValueError, IndexError):
                print("Invalid sector selection.")

    def risk_assessment(self):
        print("\n" + "="*50)
        print("RISK ASSESSMENT")
        print("="*50)

        symbols_input = input("Enter stock symbols for risk assessment (comma-separated): ")
        if not symbols_input.strip():
            print("No symbols entered.")
            return

        symbols = [s.strip().upper() for s in symbols_input.split(',')]

        print(f"\nRisk Assessment for {len(symbols)} stocks:")
        print("-" * 60)

        high_risk = []
        medium_risk = []
        low_risk = []

        for symbol in symbols:
            analysis = self.stock_analyzer.analyze_stock(symbol)
            fundamentals = self.portfolio_analyzer.get_fundamental_data(symbol)

            if analysis and fundamentals:
                volatility = analysis['volatility']
                beta = fundamentals.get('beta', 1)

                risk_score = 0
                if volatility > 60:
                    risk_score += 2
                elif volatility > 30:
                    risk_score += 1

                if beta > 1.5:
                    risk_score += 2
                elif beta > 1.2:
                    risk_score += 1

                if fundamentals.get('debt_to_equity', 0) > 100:
                    risk_score += 1

                print(f"{symbol}:")
                print(f"  Volatility: {volatility:.1f}%")
                print(f"  Beta: {beta:.2f}")
                print(f"  Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}")

                if risk_score >= 4:
                    risk_level = "HIGH RISK"
                    high_risk.append(symbol)
                elif risk_score >= 2:
                    risk_level = "MEDIUM RISK"
                    medium_risk.append(symbol)
                else:
                    risk_level = "LOW RISK"
                    low_risk.append(symbol)

                print(f"  Risk Level: {risk_level}")
                print()

        print("RISK SUMMARY:")
        print(f"High Risk Stocks: {', '.join(high_risk) if high_risk else 'None'}")
        print(f"Medium Risk Stocks: {', '.join(medium_risk) if medium_risk else 'None'}")
        print(f"Low Risk Stocks: {', '.join(low_risk) if low_risk else 'None'}")

def main():
    advisor = InvestmentAdvisor()
    advisor.comprehensive_analysis()

if __name__ == '__main__':
    main()