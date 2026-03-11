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

df_event = df_ledger[df_ledger["recipient_name"] == selected_event]
df_event["date_dt"] = pd.to_datetime(df_event["date"], format="%d %b %y")
start_date = df_event["date_dt"].min()
end_date = df_event["date_dt"].max()

date_range = pd.date_range(start_date, end_date)

st.subheader("Event Cash Calendar")

cols = st.columns(7)

for i, d in enumerate(date_range):

    df_day = df_event[df_event["date_dt"] == d]

    label = d.strftime("%d %b")

    txn_text = ""

    if not df_day.empty:

        for _, row in df_day.iterrows():

            if pd.notna(row["money_in"]) and row["money_in"] != "":
                txn_text += f"\n+ {row['item']} RM{float(row['money_in']):.2f}"

            if pd.notna(row["money_out"]) and row["money_out"] != "":
                txn_text += f"\n- {row['item']} RM{float(row['money_out']):.2f}"

    full_label = label + txn_text

    with cols[i % 7]:

        if st.button(full_label, key=f"day_{i}"):

            st.session_state["selected_cash_date"] = d

if "selected_cash_date" in st.session_state:

    selected_date = st.session_state["selected_cash_date"]

    st.subheader(f"Cash Entry : {selected_date.strftime('%d %b %Y')}")

accounts = df_event["status"].dropna().unique()

money_in_data = {}

for acc in accounts:
    money_in_data[acc] = st.number_input(
        f"Money In - {acc}",
        min_value=0.0,
        step=1.0
    )

st.subheader("Money Out")

out_account = st.selectbox("Account", accounts)

out_amount = st.number_input("Amount Out", min_value=0.0)

out_note = st.text_input("Note")

if st.button("Save Transaction"):

    rows = []

    timestamp = datetime.now().strftime("%d %b %H:%M")

    for acc, amt in money_in_data.items():

        if amt > 0:

            rows.append([
                timestamp,
                selected_event,
                df_event["job_num"].iloc[0],
                selected_date.strftime("%d %b %y"),
                acc,
                "Sales",
                "Sales Event",
                amt,
                "",
                "",
                st.session_state.get("username","unknown")
            ])

    if out_amount > 0:

        rows.append([
            timestamp,
            selected_event,
            df_event["job_num"].iloc[0],
            selected_date.strftime("%d %b %y"),
            out_account,
            "Expense",
            "Expense",
            "",
            out_amount,
            out_note,
            st.session_state.get("username","unknown")
        ])

    sheet.append_rows(rows)

    st.success("Transaction recorded.")





