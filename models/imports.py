from db.connection import get_connection
from services.market_data import get_current_price


def import_investments(investments: list[dict]) -> dict:
    """Import parsed investment records into the database.

    For each investment, we store a buy transaction. Since the sheet gives us
    total dollars invested (not per-share price and shares), we calculate:
    - current_price from yfinance (or fall back to current_value if unavailable)
    - shares = current_value / current_price
    - cost_per_share = initial_investment / shares

    Returns summary of import results.
    """
    imported = 0
    skipped = 0
    errors = []

    with get_connection() as conn:
        for inv in investments:
            symbol = inv["symbol"]
            initial = inv["initial_investment"]
            current_val = inv["current_value"]
            date = inv["date"] or "2024-01-01"
            dividend = inv.get("dividend", 0)

            if initial <= 0:
                skipped += 1
                continue

            # Try to get current price to calculate shares
            live_price = get_current_price(symbol)

            if live_price and live_price > 0:
                shares = current_val / live_price if current_val > 0 else initial / live_price
                cost_per_share = initial / shares if shares > 0 else initial
            elif current_val > 0 and initial > 0:
                # Fallback: assume 1 "unit" with total cost
                shares = 1.0
                cost_per_share = initial
            else:
                skipped += 1
                continue

            try:
                # Check if transaction already exists for this symbol+date
                existing = conn.execute(
                    "SELECT id FROM user_transactions WHERE symbol = ? AND date = ? AND price = ?",
                    (symbol.upper(), date, round(cost_per_share, 4)),
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                conn.execute(
                    """
                    INSERT INTO user_transactions (symbol, date, transaction_type, shares, price)
                    VALUES (?, ?, 'buy', ?, ?)
                    """,
                    (symbol.upper(), date, round(shares, 6), round(cost_per_share, 4)),
                )

                # Record dividend as a separate note (store in description-less budget entry if > 0)
                imported += 1
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")

    return {"imported": imported, "skipped": skipped, "errors": errors}


def clear_all_transactions():
    """Remove all transactions (for re-import)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM user_transactions")
