import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date
from models.budget import (
    add_category,
    get_categories,
    add_entry,
    get_entries,
    get_monthly_summary,
    delete_entry,
    seed_default_categories,
)


def render():
    st.header("Budget Tracker")

    # Seed defaults if no categories exist
    if not get_categories():
        seed_default_categories()

    # --- Add Entry ---
    with st.expander("Add Income/Expense", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            entry_type = st.selectbox("Type", ["expense", "income"])
        with col2:
            entry_date = st.date_input("Date", value=date.today())

        categories = get_categories(entry_type)
        cat_names = [c["name"] for c in categories]
        cat_ids = {c["name"]: c["id"] for c in categories}

        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            if cat_names:
                selected_cat = st.selectbox("Category", cat_names)
            else:
                st.warning("No categories found. Add one below.")
                selected_cat = None
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.01, value=50.0, step=1.0)
        with col3:
            description = st.text_input("Description (optional)")

        if st.button("Add Entry"):
            if selected_cat:
                add_entry(cat_ids[selected_cat], amount, entry_date.strftime("%Y-%m-%d"), description)
                st.success(f"Added ${amount:.2f} {entry_type} - {selected_cat}")
                st.rerun()

    # --- Add Category ---
    with st.expander("Manage Categories"):
        col1, col2 = st.columns(2)
        with col1:
            new_cat_name = st.text_input("New Category Name")
        with col2:
            new_cat_type = st.selectbox("Category Type", ["expense", "income"], key="new_cat_type")
        if st.button("Add Category"):
            if new_cat_name:
                add_category(new_cat_name, new_cat_type)
                st.success(f"Added category: {new_cat_name}")
                st.rerun()

    # --- Monthly Summary ---
    st.subheader("Monthly Summary")
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
    with col2:
        selected_month = st.number_input("Month", min_value=1, max_value=12, value=datetime.now().month)

    summary = get_monthly_summary(int(selected_year), int(selected_month))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${summary['total_income']:,.2f}")
    col2.metric("Total Expenses", f"${summary['total_expenses']:,.2f}")
    net = summary["net"]
    col3.metric("Net Savings", f"${net:,.2f}", delta=f"${net:,.2f}", delta_color="normal")

    # --- Expense Breakdown Chart ---
    if summary["expenses"]:
        fig = go.Figure(data=[go.Pie(
            labels=[e["category"] for e in summary["expenses"]],
            values=[e["total"] for e in summary["expenses"]],
            hole=0.4,
        )])
        fig.update_layout(title_text="Expense Breakdown")
        st.plotly_chart(fig, use_container_width=True)

    # --- Income vs Expenses Bar Chart ---
    if summary["total_income"] > 0 or summary["total_expenses"] > 0:
        fig = go.Figure(data=[
            go.Bar(name="Income", x=["Summary"], y=[summary["total_income"]], marker_color="green"),
            go.Bar(name="Expenses", x=["Summary"], y=[summary["total_expenses"]], marker_color="red"),
        ])
        fig.update_layout(title_text="Income vs Expenses", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    # --- Recent Entries ---
    st.subheader("Recent Entries")
    entries = get_entries(
        start_date=f"{int(selected_year)}-{int(selected_month):02d}-01",
        end_date=f"{int(selected_year)}-{int(selected_month):02d}-31",
    )
    if not entries.empty:
        st.dataframe(
            entries,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="$%.2f"),
            },
        )
        with st.expander("Delete an Entry"):
            entry_id = st.number_input("Entry ID to delete", min_value=1, step=1)
            if st.button("Delete Entry"):
                delete_entry(entry_id)
                st.success(f"Deleted entry #{entry_id}")
                st.rerun()
    else:
        st.info("No entries for this month.")
