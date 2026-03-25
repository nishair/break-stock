import yfinance as yf
import pandas as pd


def get_current_price(symbol: str) -> float | None:
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.info.get("currentPrice") or ticker.info.get("regularMarketPrice")
        if price:
            return float(price)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None


def get_history(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        data.reset_index(inplace=True)
        return data
    except Exception:
        return pd.DataFrame()


def get_history_range(symbol: str, start: str, end: str) -> pd.DataFrame:
    try:
        data = yf.download(symbol, start=start, end=end, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        data.reset_index(inplace=True)
        return data
    except Exception:
        return pd.DataFrame()
