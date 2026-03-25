import pandas as pd
from db.connection import get_connection


def add_category(name: str, cat_type: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO budget_categories (name, type) VALUES (?, ?)",
            (name, cat_type),
        )


def get_categories(cat_type: str = None) -> list[dict]:
    with get_connection() as conn:
        if cat_type:
            rows = conn.execute(
                "SELECT id, name, type FROM budget_categories WHERE type = ? ORDER BY name",
                (cat_type,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, type FROM budget_categories ORDER BY type, name"
            ).fetchall()
    return [dict(row) for row in rows]


def add_entry(category_id: int, amount: float, date: str, description: str = ""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO budget_entries (category_id, amount, date, description) VALUES (?, ?, ?, ?)",
            (category_id, amount, date, description),
        )


def delete_entry(entry_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM budget_entries WHERE id = ?", (entry_id,))


def get_entries(start_date: str = None, end_date: str = None, category_id: int = None) -> pd.DataFrame:
    with get_connection() as conn:
        query = """
            SELECT e.id, c.name as category, c.type, e.amount, e.date, e.description
            FROM budget_entries e
            JOIN budget_categories c ON e.category_id = c.id
            WHERE 1=1
        """
        params = []
        if start_date:
            query += " AND e.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND e.date <= ?"
            params.append(end_date)
        if category_id:
            query += " AND e.category_id = ?"
            params.append(category_id)
        query += " ORDER BY e.date DESC"
        rows = conn.execute(query, params).fetchall()

    if not rows:
        return pd.DataFrame(columns=["ID", "Category", "Type", "Amount", "Date", "Description"])
    return pd.DataFrame(rows, columns=["ID", "Category", "Type", "Amount", "Date", "Description"])


def get_monthly_summary(year: int, month: int) -> dict:
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT c.name, c.type, SUM(e.amount) as total
            FROM budget_entries e
            JOIN budget_categories c ON e.category_id = c.id
            WHERE e.date >= ? AND e.date < ?
            GROUP BY c.id
            ORDER BY c.type, total DESC
        """, (start, end)).fetchall()

    income = []
    expenses = []
    total_income = 0
    total_expenses = 0

    for row in rows:
        entry = {"category": row["name"], "total": row["total"]}
        if row["type"] == "income":
            income.append(entry)
            total_income += row["total"]
        else:
            expenses.append(entry)
            total_expenses += row["total"]

    return {
        "income": income,
        "expenses": expenses,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net": total_income - total_expenses,
    }


def seed_default_categories():
    defaults = [
        ("Salary", "income"),
        ("Freelance", "income"),
        ("Investments", "income"),
        ("Other Income", "income"),
        ("Rent/Mortgage", "expense"),
        ("Groceries", "expense"),
        ("Utilities", "expense"),
        ("Transportation", "expense"),
        ("Dining Out", "expense"),
        ("Entertainment", "expense"),
        ("Healthcare", "expense"),
        ("Shopping", "expense"),
        ("Subscriptions", "expense"),
        ("Other Expense", "expense"),
    ]
    for name, cat_type in defaults:
        add_category(name, cat_type)
