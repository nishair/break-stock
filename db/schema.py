from db.connection import get_connection


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(symbol, date)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                transaction_type TEXT NOT NULL DEFAULT 'buy',
                shares REAL NOT NULL,
                price REAL NOT NULL,
                account TEXT NOT NULL DEFAULT 'default'
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (category_id) REFERENCES budget_categories(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                target_price REAL NOT NULL,
                direction TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                triggered_at TEXT
            )
        """)

    _migrate_user_transactions()


def _migrate_user_transactions():
    """Migrate old user_transactions table if it lacks new columns."""
    with get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(user_transactions)")
        columns = {row["name"] for row in cursor.fetchall()}

        if "account" not in columns:
            conn.execute("ALTER TABLE user_transactions ADD COLUMN account TEXT NOT NULL DEFAULT 'default'")

        if "transaction_type" not in columns:
            conn.execute("""
                CREATE TABLE user_transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    transaction_type TEXT NOT NULL DEFAULT 'buy',
                    shares REAL NOT NULL,
                    price REAL NOT NULL
                )
            """)
            conn.execute("""
                INSERT INTO user_transactions_new (id, symbol, date, transaction_type, shares, price)
                SELECT id, symbol, date, 'buy', shares, price FROM user_transactions
            """)
            conn.execute("DROP TABLE user_transactions")
            conn.execute("ALTER TABLE user_transactions_new RENAME TO user_transactions")
