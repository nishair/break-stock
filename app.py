import streamlit as st
from db.schema import init_db
from services.alert_runner import start_alert_checker

st.set_page_config(page_title="Break Stock - Finance Dashboard", layout="wide")

init_db()
start_alert_checker()

st.sidebar.title("Finance Dashboard")
page = st.sidebar.radio(
    "Navigate",
    ["Portfolio", "Stock Analysis", "Budget", "Alerts", "Import"],
)

if page == "Portfolio":
    from pages.portfolio import render
    render()
elif page == "Stock Analysis":
    from pages.analysis import render
    render()
elif page == "Budget":
    from pages.budget import render
    render()
elif page == "Alerts":
    from pages.alerts import render
    render()
elif page == "Import":
    from pages.imports import render
    render()
