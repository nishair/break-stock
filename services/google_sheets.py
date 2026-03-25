import re
import pandas as pd
import requests


def extract_sheet_id(url_or_id: str) -> str:
    """Extract the Google Sheet ID from a URL or return as-is if already an ID."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def extract_gid(url: str) -> str:
    """Extract gid parameter from URL, default to 0."""
    match = re.search(r"gid=(\d+)", url)
    return match.group(1) if match else "0"


def fetch_sheet_as_dataframe(url_or_id: str) -> pd.DataFrame:
    """Fetch a publicly shared Google Sheet as a pandas DataFrame.

    The sheet must be shared with 'Anyone with the link can view'.
    """
    sheet_id = extract_sheet_id(url_or_id)
    gid = extract_gid(url_or_id) if "/" in url_or_id else "0"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    response = requests.get(csv_url, timeout=30)
    response.raise_for_status()

    from io import StringIO
    csv_text = response.text

    # Read without any header to inspect all rows as data
    raw = pd.read_csv(StringIO(csv_text), header=None)

    # Find the real header row by looking for known column keywords
    header_keywords = {"investment name", "initial investment", "current rate", "profit/loss", "percent"}
    header_row = 0
    for idx in range(min(10, len(raw))):
        row_values = {str(v).strip().lower() for v in raw.iloc[idx] if pd.notna(v)}
        if len(row_values & header_keywords) >= 3:
            header_row = idx
            break

    # Use the detected row as column names and skip everything above it
    df = pd.read_csv(StringIO(csv_text), header=header_row)

    # Clean up column names
    df.columns = [str(c).strip() if pd.notna(c) else f"col_{i}" for i, c in enumerate(df.columns)]

    return df


def parse_investments(df: pd.DataFrame) -> list[dict]:
    """Parse the investment sheet into a list of investment records.

    Expected columns (flexible matching):
    - investment name / symbol
    - initial investment
    - current rate
    - profit/loss
    - percent
    - When invested last?
    - Dividend?
    - Verdict?
    """
    # Normalize column names
    col_map = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if "investment name" in col_lower or col_lower == "symbol":
            col_map["symbol"] = col
        elif "initial investment" in col_lower:
            col_map["initial_investment"] = col
        elif "current rate" in col_lower:
            col_map["current_value"] = col
        elif col_lower in ("profit/loss", "profit loss"):
            col_map["profit_loss"] = col
        elif col_lower == "percent":
            col_map["percent"] = col
        elif "when invested" in col_lower or "date" in col_lower:
            col_map["date"] = col
        elif "dividend" in col_lower and "actual" not in col_lower:
            col_map["dividend"] = col
        elif "actual" in col_lower:
            col_map["actual_pnl"] = col
        elif "verdict" in col_lower:
            col_map["verdict"] = col

    investments = []
    for _, row in df.iterrows():
        symbol = str(row.get(col_map.get("symbol", ""), "")).strip()
        if not symbol or symbol == "nan" or symbol == "":
            continue

        # Skip non-investment rows (headers, totals, metadata)
        skip_keywords = [
            "total", "last updated", "eps update", "current rate updated",
            "initial investment updated", "dividend updated", "where to invest",
            "verdict", "treasury direct", "sell list", "vote on", "add the new",
            "srp", "hsa review", "lowest", "lower", "low", "4th lowest", "5th",
            "max", "2nd", "3rd", "4th", "5", "6", "7", "8", "9", "10",
        ]
        if symbol.lower() in skip_keywords or any(kw in symbol.lower() for kw in ["updated", "update", "invest", "done"]):
            continue

        initial = _parse_number(row.get(col_map.get("initial_investment", ""), 0))
        current = _parse_number(row.get(col_map.get("current_value", ""), 0))
        pnl = _parse_number(row.get(col_map.get("profit_loss", ""), 0))
        pct = _parse_number(row.get(col_map.get("percent", ""), 0))
        date = str(row.get(col_map.get("date", ""), "")).strip()
        dividend = _parse_number(row.get(col_map.get("dividend", ""), 0))
        verdict = str(row.get(col_map.get("verdict", ""), "")).strip()

        if initial == 0 and current == 0:
            continue

        investments.append({
            "symbol": symbol,
            "initial_investment": initial,
            "current_value": current,
            "profit_loss": pnl,
            "percent": pct,
            "date": _normalize_date(date),
            "dividend": dividend,
            "verdict": verdict if verdict != "nan" else "",
        })

    return investments


def _parse_number(val) -> float:
    """Parse a number from various formats."""
    if pd.isna(val):
        return 0.0
    try:
        s = str(val).strip().replace(",", "").replace("$", "").replace("%", "")
        if s in ("", "nan", "#DIV/0!", "-"):
            return 0.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _normalize_date(date_str: str) -> str:
    """Try to normalize various date formats to YYYY-MM-DD."""
    if not date_str or date_str == "nan":
        return ""

    date_str = date_str.strip()

    # Try common formats
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%m/%d"):
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, fmt)
            # If year is missing (format %m/%d), assume current year
            if fmt == "%m/%d":
                dt = dt.replace(year=datetime.now().year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try parsing "09/26" style (MM/YY)
    parts = date_str.split("/")
    if len(parts) == 2:
        try:
            month = int(parts[0])
            year_part = int(parts[1])
            if year_part < 100:
                year_part += 2000
            from datetime import datetime
            return datetime(year_part, month, 1).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return date_str
