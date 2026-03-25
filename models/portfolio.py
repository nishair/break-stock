import pandas as pd
from datetime import datetime
from db.connection import get_connection
from services.market_data import get_current_price


def get_accounts() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT account FROM user_transactions ORDER BY account"
        ).fetchall()
    return [row["account"] for row in rows]


def record_transaction(symbol: str, shares: float, price: float, txn_type: str = "buy", account: str = "default"):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_transactions (symbol, date, transaction_type, shares, price, account)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (symbol.upper(), datetime.now().strftime("%Y-%m-%d"), txn_type, shares, price, account),
        )


def get_transactions(account: str = None) -> pd.DataFrame:
    with get_connection() as conn:
        if account:
            rows = conn.execute(
                "SELECT id, symbol, date, transaction_type, shares, price, account FROM user_transactions WHERE account = ? ORDER BY date DESC",
                (account,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, symbol, date, transaction_type, shares, price, account FROM user_transactions ORDER BY date DESC"
            ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["ID", "Symbol", "Date", "Type", "Shares", "Price", "Account"])
    return pd.DataFrame(rows, columns=["ID", "Symbol", "Date", "Type", "Shares", "Price", "Account"])


def get_holdings(account: str = None) -> pd.DataFrame:
    with get_connection() as conn:
        where = "WHERE account = ?" if account else ""
        params = (account,) if account else ()
        rows = conn.execute(f"""
            SELECT symbol,
                   SUM(CASE WHEN transaction_type = 'buy' THEN shares ELSE -shares END) as total_shares,
                   SUM(CASE WHEN transaction_type = 'buy' THEN shares * price ELSE 0 END) as total_cost,
                   SUM(CASE WHEN transaction_type = 'buy' THEN shares ELSE 0 END) as total_bought
            FROM user_transactions
            {where}
            GROUP BY symbol
            HAVING total_shares > 0
        """, params).fetchall()

    if not rows:
        return pd.DataFrame(columns=["Symbol", "Shares", "Avg Cost", "Current Price", "Market Value", "Gain/Loss", "Gain/Loss %"])

    holdings = []
    for row in rows:
        symbol = row["symbol"]
        shares = row["total_shares"]
        avg_cost = row["total_cost"] / row["total_bought"] if row["total_bought"] > 0 else 0
        current_price = get_current_price(symbol) or 0

        market_value = shares * current_price
        cost_basis = shares * avg_cost
        gain_loss = market_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0

        holdings.append({
            "Symbol": symbol,
            "Shares": round(shares, 4),
            "Avg Cost": round(avg_cost, 2),
            "Current Price": round(current_price, 2),
            "Market Value": round(market_value, 2),
            "Gain/Loss": round(gain_loss, 2),
            "Gain/Loss %": round(gain_loss_pct, 2),
        })

    return pd.DataFrame(holdings)


def get_portfolio_summary(account: str = None) -> dict:
    holdings = get_holdings(account)
    if holdings.empty:
        return {"total_value": 0, "total_gain_loss": 0, "total_cost": 0}
    total_value = holdings["Market Value"].sum()
    total_cost = (holdings["Shares"] * holdings["Avg Cost"]).sum()
    return {
        "total_value": round(total_value, 2),
        "total_gain_loss": round(total_value - total_cost, 2),
        "total_cost": round(total_cost, 2),
    }


def delete_transaction(txn_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM user_transactions WHERE id = ?", (txn_id,))
