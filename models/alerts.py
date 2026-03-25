import pandas as pd
from datetime import datetime
from db.connection import get_connection


def create_alert(symbol: str, target_price: float, direction: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO price_alerts (symbol, target_price, direction, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
            """,
            (symbol.upper(), target_price, direction, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def get_alerts(active_only: bool = True) -> pd.DataFrame:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT id, symbol, target_price, direction, created_at FROM price_alerts WHERE is_active = 1 ORDER BY created_at DESC"
            ).fetchall()
            cols = ["ID", "Symbol", "Target Price", "Direction", "Created"]
        else:
            rows = conn.execute(
                "SELECT id, symbol, target_price, direction, is_active, created_at, triggered_at FROM price_alerts ORDER BY created_at DESC"
            ).fetchall()
            cols = ["ID", "Symbol", "Target Price", "Direction", "Active", "Created", "Triggered"]

    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows, columns=cols)


def trigger_alert(alert_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE price_alerts SET is_active = 0, triggered_at = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), alert_id),
        )


def delete_alert(alert_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))


def get_active_alerts_raw() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, symbol, target_price, direction FROM price_alerts WHERE is_active = 1"
        ).fetchall()
    return [dict(row) for row in rows]
