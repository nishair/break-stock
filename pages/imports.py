import streamlit as st
import pandas as pd
from services.google_sheets import fetch_sheet_as_dataframe, parse_investments
from models.imports import import_investments, clear_all_transactions


def render():
    st.header("Import from Google Sheets")

    st.markdown("""
    **How to use:**
    1. Open your Google Sheet
    2. Click **Share** → **Anyone with the link** → **Viewer**
    3. Copy the URL and paste it below
    """)

    sheet_url = st.text_input(
        "Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit#gid=0",
    )

    if sheet_url and st.button("Fetch Sheet"):
        with st.spinner("Fetching data from Google Sheets..."):
            try:
                df = fetch_sheet_as_dataframe(sheet_url)
                st.session_state["imported_df"] = df
                st.session_state["imported_url"] = sheet_url
                st.success(f"Fetched {len(df)} rows")
            except Exception as e:
                st.error(f"Failed to fetch sheet: {e}")
                return

    # Show fetched data
    if "imported_df" in st.session_state:
        df = st.session_state["imported_df"]

        st.subheader("Raw Sheet Data")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)
        st.caption(f"Showing first 20 of {len(df)} rows")

        # Parse investments
        st.subheader("Parsed Investments")
        investments = parse_investments(df)

        if investments:
            preview = pd.DataFrame(investments)
            st.dataframe(preview, use_container_width=True, hide_index=True)
            st.caption(f"{len(investments)} investments found")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Import to Portfolio", type="primary"):
                    with st.spinner("Importing investments... This may take a few minutes (fetching live prices)"):
                        results = import_investments(investments)
                        st.success(
                            f"Imported: {results['imported']} | "
                            f"Skipped: {results['skipped']} | "
                            f"Errors: {len(results['errors'])}"
                        )
                        if results["errors"]:
                            with st.expander("View Errors"):
                                for err in results["errors"]:
                                    st.text(err)

            with col2:
                if st.button("Clear All Transactions First"):
                    clear_all_transactions()
                    st.warning("All existing transactions cleared.")
        else:
            st.warning("No valid investments found. Check that your sheet has the expected columns.")
