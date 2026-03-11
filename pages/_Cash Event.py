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

# Load data (header row 5)
data = sheet.get_all_records(head=5)
df_ledger = pd.DataFrame(data)

# Ensure Amount column exists for numeric calculations
if "Amount" not in df_ledger.columns:
    df_ledger["Amount"] = pd.NA
else:
    df_ledger["Amount"] = pd.to_numeric(df_ledger["Amount"], errors="coerce")

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
        
#------------------------------------

# -----------------------------
# CASH FLOW INPUT PAGE
# -----------------------------
st.title("💰 Event Cash Flow Input")

# 1️⃣ Select Event
events = df_ledger["recipient_name"].dropna().unique().tolist()
selected_event = st.selectbox("Select Event", events)

df_event = df_ledger[df_ledger["recipient_name"] == selected_event].copy()

if df_event.empty:
    st.warning("No ledger rows exist for this event yet.")
    st.stop()

# 2️⃣ Pick Date that has missing money_in
# Find dates where Type=IN is missing for any account
all_accounts = df_event["status"].dropna().unique().tolist()
date_account_pairs = []

for d in df_event["date"].dropna().unique():
    df_day = df_event[df_event["date"] == d]
    for acc in all_accounts:
        if not ((df_day["status"] == acc) & (df_day["Type"] == "IN")).any():
            date_account_pairs.append(d)

if not date_account_pairs:
    st.success("✅ All dates have money_in recorded for all accounts.")
    st.stop()

next_date = sorted(pd.to_datetime(date_account_pairs, format="%d %b %y"))[0].strftime("%d %b %y")
st.write(f"Next date to input cash inflow: **{next_date}**")

# 3️⃣ Money In Form
st.subheader("Money In Entries")
money_in_dict = {}
for acc in all_accounts:
    # Check if this account already has money_in for this date
    df_check = df_event[(df_event["date"] == next_date) & (df_event["status"] == acc) & (df_event["Type"] == "IN")]
    if df_check.empty:
        money_in_dict[acc] = st.number_input(f"Money In - {acc}", min_value=0.0, value=0.0, step=1.0, format="%.2f")

# 4️⃣ Money Out Form
st.subheader("Money Out Entries (Optional)")
money_out_list = []
if st.checkbox("Add Money Out for this date"):
    num_out = st.number_input("How many money out entries?", min_value=1, max_value=10, value=1, step=1)
    for i in range(num_out):
        col1, col2, col3 = st.columns(3)
        with col1:
            acc = st.selectbox(f"Account for OUT #{i+1}", all_accounts, key=f"out_acc_{i}")
        with col2:
            amt = st.number_input(f"Amount OUT #{i+1}", min_value=0.0, value=0.0, step=1.0, format="%.2f", key=f"out_amt_{i}")
        with col3:
            category = st.text_input(f"Category OUT #{i+1}", value="Expense", key=f"out_cat_{i}")
        money_out_list.append({"status": acc, "Amount": amt, "Category": category})

# 5️⃣ Submit Button
if st.button("Submit Cash Flow"):

    rows_to_append = []

    timestamp = datetime.now().strftime("%d %b %H:%M")

    # Money In Rows
    for acc, amt in money_in_dict.items():
        if amt > 0:
            row = {
                "Timestamp": timestamp,
                "recipient_name": selected_event,
                "job_num": df_event["job_num"].iloc[0],
                "date": next_date,
                "status": acc,
                "Type": "IN",
                "Category": "Sales Event",
                "Amount": amt,
                "note": "",
                "username": st.session_state.get("username", "unknown")
            }
            rows_to_append.append(row)

    # Money Out Rows
    for out in money_out_list:
        if out["Amount"] > 0:
            row = {
                "Timestamp": timestamp,
                "recipient_name": selected_event,
                "job_num": df_event["job_num"].iloc[0],
                "date": next_date,
                "status": out["status"],
                "Type": "OUT",
                "Category": out["Category"],
                "Amount": out["Amount"],
                "note": "",
                "username": st.session_state.get("username", "unknown")
            }
            rows_to_append.append(row)

    if rows_to_append:
        df_new = pd.DataFrame(rows_to_append)

        # Append to Google Sheet dynamically (header row 5)
        sheet.append_rows(df_new.values.tolist())

        st.success(f"💾 {len(df_new)} cash flow entries recorded for {next_date}!")
    else:
        st.warning("No amounts entered to submit.")
