import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_sheet
import gspread
from google.oauth2.service_account import Credentials

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

# Check if user is admin
if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()
    
st.title("🎪 Event Cash Flow Management")

st.title("Event Ledger Generator")

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

data = sheet.get_all_records()
df_existing = pd.DataFrame(data)

# -----------------------------
# EVENT CREATION UI
# -----------------------------

st.subheader("Create Event Ledger")

event_name = st.text_input("Event Name")
job_num = st.text_input("Job Number")

username = st.session_state.get("username", "unknown")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Start Date")

with col2:
    end_date = st.date_input("End Date")

accounts = st.multiselect(
    "Select Account Types",
    ["CASH", "QR", "TNG", "BANK1"]
)

st.divider()

# -----------------------------
# GENERATE LEDGER
# -----------------------------

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
                "recipient_name": "",
                "tin_num": "",
                "username": username
            }

            rows.append(row)

    df_new = pd.DataFrame(rows)

    # -----------------------------
    # CHECK DUPLICATE EVENT
    # -----------------------------

    if not df_existing.empty:

        duplicate = df_existing[
            df_existing["job_num"] == job_num
        ]

        if not duplicate.empty:
            st.error("Ledger for this job number already exists.")
            st.stop()

    # -----------------------------
    # APPEND TO GOOGLE SHEET
    # -----------------------------

    updated = pd.concat([df_existing, df_new], ignore_index=True)

    sheet.update(
        [updated.columns.values.tolist()] + updated.values.tolist()
    )

    st.success(f"{len(df_new)} rows successfully generated!")

    st.dataframe(df_new)
