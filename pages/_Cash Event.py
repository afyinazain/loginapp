import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_sheet
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# LOGIN CHECK
# -----------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()

if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()

# -----------------------------
# PAGE TITLE
# -----------------------------
st.title("🎪 Event Cash Flow Management")

# -----------------------------
# GOOGLE AUTH
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# -----------------------------
# CONNECT TO GOOGLE SHEET
# -----------------------------
SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
SHEET_NAME = "Cash Event"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Read header in row 5
data = sheet.get_all_records(head=5)
df_existing = pd.DataFrame(data)

# -----------------------------
# SHOW BUTTON TO OPEN LEDGER FORM
# -----------------------------
    
with st.expander("📝 Event Ledger Generator", expanded=True):
    event_name = st.text_input("Event Name")
    job_num = st.text_input("Job Number")

    username = st.session_state.user["username"]

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    accounts = st.multiselect(
        "Select Account Types",
        ["CASH", "QR", "TNG", "BANK1"]
    )

    if st.button("Generate Ledger"):
        if event_name == "" or job_num == "" or username == "":
            st.warning("Please fill Event Name, Job Number and Username")
            st.stop()

        if len(accounts) == 0:
            st.warning("Select at least one account type")
            st.stop()

        # Create date range
        dates = pd.date_range(start_date, end_date)

        rows = []
        for d in dates:
            for acc in accounts:
                row = {
                    "Timestamp": datetime.now().strftime("%d %b"),
                    "print": "",
                    "date": d.strftime("%d %b %y"),
                    "month": d.strftime("%y %m"),
                    "account_name": "cash4",
                    "item": "Sales",
                    "category": "Sales Event",
                    "folio": "",
                    "note": "",
                    "money_in": "",
                    "money_out": "",
                    "receipt": "",
                    "status": acc,
                    "job_num": job_num,
                    "recipient_name": event_name,
                    "tin_num": "",
                    "username": username
                }
                rows.append(row)

        df_new = pd.DataFrame(rows).fillna("")

        # Check duplicates
        if not df_existing.empty:
            duplicate = df_existing[df_existing["job_num"] == job_num]
            if not duplicate.empty:
                st.error("Ledger for this job number already exists.")
                st.stop()

        # Append to Google Sheet
        sheet.append_rows(df_new.values.tolist())

        st.success(f"{len(df_new)} rows successfully generated!")
        st.dataframe(df_new)
