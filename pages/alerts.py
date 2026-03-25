import streamlit as st
import pandas as pd
from models.alerts import create_alert, get_alerts, delete_alert
from services.alert_runner import start_alert_checker, check_all_alerts, is_running
from config import ALERT_CHECK_INTERVAL_MINUTES


def render():
    st.header("Price Alerts")

    # Start background checker
    start_alert_checker()

    # Status
    status = "Running" if is_running() else "Stopped"
    st.caption(f"Alert checker: {status} (checks every {ALERT_CHECK_INTERVAL_MINUTES} min)")

    if st.button("Check Alerts Now"):
        with st.spinner("Checking prices..."):
            check_all_alerts()
        st.success("Alert check complete.")
        st.rerun()

    # --- Create Alert ---
    with st.expander("Create New Alert", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            symbol = st.text_input("Symbol", placeholder="AAPL").upper()
        with col2:
            target_price = st.number_input("Target Price ($)", min_value=0.01, value=150.0, step=1.0)
        with col3:
            direction = st.selectbox("Trigger When Price Goes", ["above", "below"])

        if st.button("Create Alert"):
            if symbol:
                create_alert(symbol, target_price, direction)
                st.success(f"Alert created: {symbol} {direction} ${target_price:.2f}")
                st.rerun()
            else:
                st.error("Please enter a symbol.")

    # --- Active Alerts ---
    st.subheader("Active Alerts")
    active = get_alerts(active_only=True)
    if not active.empty:
        st.dataframe(
            active,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Target Price": st.column_config.NumberColumn(format="$%.2f"),
            },
        )
        with st.expander("Delete an Alert"):
            alert_id = st.number_input("Alert ID to delete", min_value=1, step=1)
            if st.button("Delete Alert"):
                delete_alert(alert_id)
                st.success(f"Deleted alert #{alert_id}")
                st.rerun()
    else:
        st.info("No active alerts.")

    # --- Alert History ---
    st.subheader("Alert History")
    all_alerts = get_alerts(active_only=False)
    triggered = all_alerts[all_alerts.get("Active", pd.Series()) == 0] if "Active" in all_alerts.columns else all_alerts.iloc[0:0]
    if not triggered.empty:
        st.dataframe(triggered, use_container_width=True, hide_index=True)
    else:
        st.info("No triggered alerts yet.")
