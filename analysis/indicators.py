import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


def add_sma(df: pd.DataFrame, windows: list[int] = None) -> pd.DataFrame:
    if windows is None:
        windows = [20, 50, 200]
    for w in windows:
        if len(df) >= w:
            df[f"SMA_{w}"] = SMAIndicator(close=df["Close"], window=w).sma_indicator()
    return df


def add_ema(df: pd.DataFrame, windows: list[int] = None) -> pd.DataFrame:
    if windows is None:
        windows = [12, 26]
    for w in windows:
        if len(df) >= w:
            df[f"EMA_{w}"] = EMAIndicator(close=df["Close"], window=w).ema_indicator()
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    if len(df) >= window:
        df["RSI"] = RSIIndicator(close=df["Close"], window=window).rsi()
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) >= 26:
        macd = MACD(close=df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()
    return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, std: int = 2) -> pd.DataFrame:
    if len(df) >= window:
        bb = BollingerBands(close=df["Close"], window=window, window_dev=std)
        df["BB_Upper"] = bb.bollinger_hband()
        df["BB_Middle"] = bb.bollinger_mavg()
        df["BB_Lower"] = bb.bollinger_lband()
    return df
