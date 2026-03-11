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
        
#------------------------------------

# Load existing ledger
data = sheet.get_all_records(head=5)
df_ledger = pd.DataFrame(data)

# Make sure money_in column is numeric for checking
df_ledger["money_in"] = pd.to_numeric(df_ledger["money_in"], errors="coerce")
df_ledger["money_out"] = pd.to_numeric(df_ledger["money_out"], errors="coerce")

st.subheader("💰 Cash Flow Input")

# Get list of registered events
events = df_ledger["recipient_name"].dropna().unique().tolist()

selected_event = st.selectbox("Select Event", events)

# Filter rows for this event
df_event = df_ledger[df_ledger["recipient_name"] == selected_event].copy()

st.info("Edit `money_in` and `money_out` directly below. Changes will update the existing ledger rows.")

# Only keep rows where money_in is empty
df_pending = df_event[df_event["money_in"].isna() | (df_event["money_in"] == "")]

if df_pending.empty:
    st.info("All dates for this event already have money recorded.")
    st.stop()

# Take the earliest date
df_pending["date_dt"] = pd.to_datetime(df_pending["date"], format="%d %b %y")
next_row = df_pending.sort_values("date_dt").iloc[0]
next_date = next_row["date"]

st.write(f"Next date to record cash flow: **{next_date}**")

# Use Streamlit data editor for inline editing
edited_df = st.data_editor(
    df_event,
    num_rows="dynamic",
    use_container_width=True
)

col1, col2 = st.columns(2)
with col1:
    money_in = st.number_input("Money In (RM)", value=0.0, step=1.0, format="%.2f")
with col2:
    money_out = st.number_input("Money Out (RM)", value=0.0, step=1.0, format="%.2f")

# Update button
if st.button("Update Ledger"):
    headers = sheet.row_values(5)  # header row
    for idx, row in edited_df.iterrows():
        # Find row index in Google Sheet
        df_index = df_ledger.index[df_ledger["date"] == row["date"]][0]
        sheet_row_index = df_index + 6  # +6 because header is row 5

        # Update money_in and money_out dynamically
        money_in_col = headers.index("money_in") + 1
        money_out_col = headers.index("money_out") + 1

        sheet.update_cell(sheet_row_index, money_in_col, row["money_in"])
        sheet.update_cell(sheet_row_index, money_out_col, row["money_out"])

    st.success("💾 Ledger updated successfully!")
