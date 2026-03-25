import pandas as pd
from db.connection import get_connection
from services.market_data import get_history


def fetch_and_store(symbol: str, period: str = "1mo"):
    data = get_history(symbol, period=period)
    if data.empty:
        return

    with get_connection() as conn:
        for _, row in data.iterrows():
            conn.execute(
                """
                INSERT OR REPLACE INTO stock_data (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol.upper(),
                    pd.Timestamp(row["Date"]).strftime("%Y-%m-%d"),
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                ),
            )


def get_stock_history(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    with get_connection() as conn:
        query = "SELECT date, open, high, low, close, volume FROM stock_data WHERE symbol = ?"
        params = [symbol.upper()]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date"
        rows = conn.execute(query, params).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df
