import streamlit as st
import plotly.graph_objects as go
from models.portfolio import (
    get_accounts,
    record_transaction,
    get_transactions,
    get_holdings,
    get_portfolio_summary,
    delete_transaction,
)


def render():
    st.header("Portfolio Tracker")

    # --- Account Filter ---
    accounts = get_accounts()
    account_options = ["All Accounts"] + accounts
    selected_account = st.sidebar.selectbox("Account", account_options)
    account_filter = None if selected_account == "All Accounts" else selected_account

    # --- Add Transaction ---
    with st.expander("Add Transaction", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            symbol = st.text_input("Symbol", placeholder="AAPL").upper()
        with col2:
            txn_type = st.selectbox("Type", ["buy", "sell"])
        with col3:
            shares = st.number_input("Shares", min_value=0.0001, value=1.0, step=1.0)
        with col4:
            price = st.number_input("Price per Share", min_value=0.01, value=100.0, step=0.01)
        with col5:
            txn_account = st.selectbox("Account", accounts if accounts else ["default"])

        if st.button("Record Transaction"):
            if symbol:
                record_transaction(symbol, shares, price, txn_type, txn_account)
                st.success(f"Recorded {txn_type} of {shares} shares of {symbol} at ${price:.2f} in {txn_account}")
                st.rerun()
            else:
                st.error("Please enter a stock symbol.")

    # --- Portfolio Summary ---
    summary = get_portfolio_summary(account_filter)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"${summary['total_value']:,.2f}")
    col2.metric("Total Cost Basis", f"${summary['total_cost']:,.2f}")
    gain_loss = summary["total_gain_loss"]
    col3.metric(
        "Total Gain/Loss",
        f"${gain_loss:,.2f}",
        delta=f"${gain_loss:,.2f}",
        delta_color="normal",
    )

    # --- Holdings Table ---
    st.subheader(f"Holdings — {selected_account}")
    holdings = get_holdings(account_filter)
    if not holdings.empty:
        st.dataframe(
            holdings.sort_values("Market Value", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg Cost": st.column_config.NumberColumn(format="$%.2f"),
                "Current Price": st.column_config.NumberColumn(format="$%.2f"),
                "Market Value": st.column_config.NumberColumn(format="$%.2f"),
                "Gain/Loss": st.column_config.NumberColumn(format="$%.2f"),
                "Gain/Loss %": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        # --- Holdings Pie Chart ---
        # Show top 20 by market value for readability
        top = holdings.nlargest(20, "Market Value")
        fig = go.Figure(data=[go.Pie(
            labels=top["Symbol"],
            values=top["Market Value"],
            hole=0.4,
        )])
        fig.update_layout(title_text=f"Top 20 Holdings — {selected_account}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No holdings yet. Add a transaction above to get started.")

    # --- Transaction History ---
    st.subheader("Transaction History")
    transactions = get_transactions(account_filter)
    if not transactions.empty:
        st.dataframe(
            transactions.head(50),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
            },
        )
        st.caption(f"Showing first 50 of {len(transactions)} transactions")

        # Delete transaction
        with st.expander("Delete a Transaction"):
            txn_id = st.number_input("Transaction ID to delete", min_value=1, step=1)
            if st.button("Delete Transaction"):
                delete_transaction(txn_id)
                st.success(f"Deleted transaction #{txn_id}")
                st.rerun()
    else:
        st.info("No transactions recorded yet.")
