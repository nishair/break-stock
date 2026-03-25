import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services.market_data import get_history
from analysis.indicators import add_sma, add_ema, add_rsi, add_macd, add_bollinger_bands


def render():
    st.header("Stock Analysis Dashboard")

    # --- Controls ---
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        symbol = st.text_input("Stock Symbol", value="AAPL").upper()
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    with col3:
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    # Indicator toggles
    st.subheader("Indicators")
    col1, col2, col3, col4 = st.columns(4)
    show_sma = col1.checkbox("SMA (20/50/200)", value=True)
    show_ema = col2.checkbox("EMA (12/26)")
    show_bb = col3.checkbox("Bollinger Bands")
    show_macd = col4.checkbox("MACD")
    show_rsi = col1.checkbox("RSI")

    if not symbol:
        st.warning("Enter a stock symbol to begin.")
        return

    # --- Fetch Data ---
    with st.spinner(f"Fetching data for {symbol}..."):
        df = get_history(symbol, period=period, interval=interval)

    if df.empty:
        st.error(f"No data found for {symbol}. Check the symbol and try again.")
        return

    # --- Compute Indicators ---
    if show_sma:
        df = add_sma(df)
    if show_ema:
        df = add_ema(df)
    if show_bb:
        df = add_bollinger_bands(df)
    if show_rsi:
        df = add_rsi(df)
    if show_macd:
        df = add_macd(df)

    # --- Determine subplot layout ---
    extra_rows = []
    if show_rsi:
        extra_rows.append("RSI")
    if show_macd:
        extra_rows.append("MACD")

    row_count = 2 + len(extra_rows)  # candlestick + volume + extras
    row_heights = [0.5] + [0.15] + [0.35 / max(len(extra_rows), 1)] * len(extra_rows)
    if not extra_rows:
        row_heights = [0.7, 0.3]

    subtitles = [symbol, "Volume"] + extra_rows
    fig = make_subplots(
        rows=row_count,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=subtitles,
        row_heights=row_heights,
    )

    # --- Candlestick ---
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1, col=1,
    )

    # --- Overlays on candlestick ---
    colors = {"SMA_20": "#FF6B6B", "SMA_50": "#4ECDC4", "SMA_200": "#45B7D1",
              "EMA_12": "#FFA07A", "EMA_26": "#98D8C8"}

    for col_name, color in colors.items():
        if col_name in df.columns:
            fig.add_trace(
                go.Scatter(x=df["Date"], y=df[col_name], name=col_name,
                           line=dict(width=1, color=color)),
                row=1, col=1,
            )

    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["BB_Upper"], name="BB Upper",
                       line=dict(width=1, color="gray", dash="dash")),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["BB_Lower"], name="BB Lower",
                       line=dict(width=1, color="gray", dash="dash"),
                       fill="tonexty", fillcolor="rgba(128,128,128,0.1)"),
            row=1, col=1,
        )

    # --- Volume ---
    colors_vol = ["red" if row["Close"] < row["Open"] else "green" for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(x=df["Date"], y=df["Volume"], name="Volume",
               marker_color=colors_vol, showlegend=False),
        row=2, col=1,
    )

    # --- RSI ---
    current_extra_row = 3
    if show_rsi and "RSI" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["RSI"], name="RSI",
                       line=dict(color="#AB63FA", width=1)),
            row=current_extra_row, col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_extra_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_extra_row, col=1)
        current_extra_row += 1

    # --- MACD ---
    if show_macd and "MACD" in df.columns:
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["MACD"], name="MACD",
                       line=dict(color="#636EFA", width=1)),
            row=current_extra_row, col=1,
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["MACD_Signal"], name="Signal",
                       line=dict(color="#EF553B", width=1)),
            row=current_extra_row, col=1,
        )
        hist_colors = ["green" if v >= 0 else "red" for v in df["MACD_Hist"]]
        fig.add_trace(
            go.Bar(x=df["Date"], y=df["MACD_Hist"], name="MACD Hist",
                   marker_color=hist_colors, showlegend=False),
            row=current_extra_row, col=1,
        )

    # --- Layout ---
    fig.update_layout(
        height=200 + row_count * 200,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Quick Stats ---
    st.subheader("Quick Stats")
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest["Close"] - prev["Close"]
    change_pct = (change / prev["Close"]) * 100 if prev["Close"] != 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Close", f"${latest['Close']:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
    col2.metric("High", f"${latest['High']:.2f}")
    col3.metric("Low", f"${latest['Low']:.2f}")
    col4.metric("Volume", f"{int(latest['Volume']):,}")
