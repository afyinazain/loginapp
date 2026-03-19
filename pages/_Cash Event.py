import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import read_sheet, get_client
import os
import json
from streamlit_calendar import calendar

# -----------------------------
# LOGIN CHECK
# -----------------------------

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()

if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()
    
client = get_client()

# Google Service Account
google_creds = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
}

# Cloudinary
cloudinary_config = {
    "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "api_key": os.getenv("CLOUDINARY_API_KEY"),
    "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
}

# -----------------------------
# PAGE TITLE
# -----------------------------

st.title("🎪 Event Cash Flow Management")

# -----------------------------
# CONNECT TO GOOGLE SHEET
# -----------------------------

SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
EVENTLIST_SHEET = "Event_List"
TXN_SHEET = "Event_Txn"
ACCOUNT_SHEET = "Event_Account"

username = st.session_state.user["username"]

# ---------------------------------
# LOAD EVENT LIST
# ---------------------------------

@st.cache_data(ttl=60)

def load_sheet(sheet):

    sheet = urllib.parse.quote(sheet)

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"

    df = pd.read_csv(url)

    df.columns = df.columns.str.strip()

    return df
    
df_list = load_sheet(EVENTLIST_SHEET)
df_accounts = load_sheet(ACCOUNT_SHEET)
df_txn = load_sheet(TXN_SHEET)


# -----------------------------
# SELECT EVENT
# -----------------------------
active_events = df_events[df_events["status"] == "active"]

if active_events.empty:
    st.info("No active events")
    st.stop()

selected_event = st.selectbox(
    "Select Event",
    active_events["event_name"]
)

event_row = active_events[
    active_events["event_name"] == selected_event
].iloc[0]

event_id = event_row["event_id"]

start_date = pd.to_datetime(event_row["start_date"]).date()
end_date = pd.to_datetime(event_row["end_date"]).date()

# -----------------------------
# LOAD ACCOUNTS
# -----------------------------
event_accounts = df_accounts[
    df_accounts["event_id"] == event_id
]["account_type"].tolist()

# -----------------------------
# PREPARE TRANSACTION DATA
# -----------------------------
df_txn["date"] = pd.to_datetime(df_txn["date"], errors="coerce")

event_txn = df_txn[df_txn["event_id"] == event_id]

daily = event_txn.groupby(["date", "type"])["amount"].sum().reset_index()

# -----------------------------
# GENERATE CALENDAR EVENTS
# -----------------------------
events = []

current = start_date

while current <= end_date:

    day_data = daily[daily["date"] == pd.to_datetime(current)]

    total_in = day_data[day_data["type"] == "IN"]["amount"].sum()
    total_out = day_data[day_data["type"] == "OUT"]["amount"].sum()

    title = selected_event

    if total_in > 0 or total_out > 0:
        title += f"\n💰 {total_in:,.0f} | 💸 {total_out:,.0f}"

    events.append({
        "title": title,
        "start": current.strftime("%Y-%m-%d"),
        "end": current.strftime("%Y-%m-%d")
    })

    current += timedelta(days=1)

calendar_event = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "height": 650
    }
)

selected_date = None

if calendar_event and "dateClick" in calendar_event:

    selected_date = datetime.strptime(
        calendar_event["dateClick"]["date"],
        "%Y-%m-%d"
    ).date()

# -----------------------------
# TRANSACTION ENTRY
# -----------------------------
if selected_date:

    st.subheader(f"Add Transaction ({selected_date})")

    with st.form("txn_form"):

        txn_type = st.selectbox(
            "Type",
            ["IN", "OUT"]
        )

        account = st.selectbox(
            "Account",
            event_accounts
        )

        category = st.text_input("Category")

        item = st.text_input("Item")

        amount = st.number_input(
            "Amount",
            min_value=0.0
        )

        submit_txn = st.form_submit_button("Save Transaction")

    if submit_txn:

        txn_id = "TXN" + datetime.now().strftime("%Y%m%d%H%M%S")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        txn_sheet = client.open_by_key(SHEET_ID).worksheet(EVENT_TXN)

        headers = txn_sheet.row_values(1)

        row_data = {
            "txn_id": txn_id,
            "timestamp": timestamp,
            "username": username,
            "event_id": event_id,
            "date": selected_date.strftime("%Y-%m-%d"),
            "account": account,
            "type": txn_type,
            "category": category,
            "item": item,
            "amount": amount,
            "receipt_url": ""
        }

        row = [row_data.get(col, "") for col in headers]

        txn_sheet.append_row(row, value_input_option="USER_ENTERED")

        st.success("Transaction Saved")

        st.cache_data.clear()

        st.rerun()

# -----------------------------
# LEDGER VIEW
# -----------------------------
st.subheader("Ledger")

ledger = event_txn.sort_values("date")

st.dataframe(ledger)

total_in = ledger[ledger["type"] == "IN"]["amount"].sum()
total_out = ledger[ledger["type"] == "OUT"]["amount"].sum()

st.metric("Total In", f"RM {total_in:,.2f}")
st.metric("Total Out", f"RM {total_out:,.2f}")
st.metric("Balance", f"RM {total_in-total_out:,.2f}")

# ---------------------------------
# REGISTER EVENT POPUP
# ---------------------------------

if st.button("➕ Register Event"):

    with st.form("register_event"):

        st.subheader("Register New Event")

        event_name = st.text_input("Event Name")

        job_number = st.text_input("Job Number")

        event_type = st.selectbox(
            "Event Type",
            ["MEGA ARENA", "FUN FEST"]
        )

        start_date = st.date_input("Start Date")

        end_date = st.date_input("End Date")

        duration = (end_date - start_date).days + 1

        account_type = st.multiselect(
            "Account Type",
            ["CASH", "QR BANK", "TNG", "BNK1", "BNK2", "BNK3"]
        )

        submit = st.form_submit_button("Save Event")

        if submit:

            timestamp = datetime.now()

            sheet = client.open_by_key(SHEET_ID).worksheet(EVENTLIST_SHEET)

            sheet.append_row([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                username,
                event_name,
                event_type,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                duration,
                ",".join(account_type),
                "active"
            ])

            st.success("✅ Event Registered")

            st.cache_data.clear()
            st.rerun()


active_events = df_event[df_event["status"] == "active"]

if active_events.empty:
    st.info("No active events found. Please register an event first.")
    st.stop()

selected_event = st.selectbox(
    "Select Event",
    active_events["event_name"].dropna().unique()
)

event_rows = active_events[active_events["event_name"] == selected_event]

if event_rows.empty:
    st.warning("Event not found.")
    st.stop()

event_row = event_rows.iloc[0]

start_date = event_row["start_date"]
end_date = event_row["end_date"]
job_number = event_row["job_number"] if "job_number" in event_row else ""

st.markdown("""
<style>

.fc-event-title {
    white-space: pre-line;
    font-size: 11px;
}

</style>
""", unsafe_allow_html=True)




import urllib.parse

@st.cache_data(ttl=60)
def load_cashflow():

    sheet_name = urllib.parse.quote(CASHFLOW_SHEET)

    url1 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    df1 = pd.read_csv(url1)

    df1.columns = df1.columns.str.strip()
   
    if "date" in df1.columns:
        df1["date"] = pd.to_datetime(df1["date"], errors="coerce")

    return df1


df_cash = load_cashflow()

# ---------------------------------
# FILTER CASHFLOW FOR SELECTED EVENT
# ---------------------------------

event_cash = df_cash[df_cash["account_name"] == selected_event].copy()


# Convert numeric columns safely
event_cash["money_in"] = pd.to_numeric(event_cash["money_in"], errors="coerce").fillna(0)
event_cash["money_out"] = pd.to_numeric(event_cash["money_out"], errors="coerce").fillna(0)

# Group by date
daily_cash = event_cash.groupby("date").agg(
    total_in=("money_in", "sum"),
    total_out=("money_out", "sum")
).reset_index()

events = []

current = start_date

while current <= end_date:

    day_in = 0
    day_out = 0

    row = daily_cash[daily_cash["date"] == pd.to_datetime(current)]

    if not row.empty:
        day_in = float(row["total_in"].values[0])
        day_out = float(row["total_out"].values[0])

    title = f"{selected_event}"

    if day_in > 0 or day_out > 0:
        title += f"\n💰 {day_in:,.0f} | 💸 {day_out:,.0f}"

    events.append({
        "title": title,
        "start": current.strftime("%Y-%m-%d"),
        "end": current.strftime("%Y-%m-%d"),
        "color": "#18c936"
    })

    current += timedelta(days=1)

calendar_options = {
    "initialView": "dayGridMonth",
    "height": 650,
    "selectable": True
}

calendar_event = calendar(
    events=events,
    options=calendar_options
)

selected_date = None
if calendar_event and hasattr(calendar_event, "dateClick"):
    clicked = calendar_event.dateClick()  # call the method
    selected_date_str = clicked["date"]
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()


df_cash["date_only"] = pd.to_datetime(df_cash["date"]).dt.date

transactions = df_cash[df_cash["date_only"] == selected_date]

if selected_date:
    st.subheader(f"Transactions for {selected_date}")
    st.markdown("### 💰 Money In")
    
    with st.form("money_in_form"):

        amount = st.number_input("Amount RM", min_value=0.0)

        item = st.selectbox("Item", ["Ticket Sales", "Petty Cash", "Other"])

        category = st.selectbox("Category", ["Sales", "Cash Injection"])

        account = st.selectbox(
            "Account Type",
            ["CASH", "QR BANK", "TNG", "BNK1", "BNK2", "BNK3"]
        )

        receipt = st.file_uploader("Upload Receipt")

        submit_in = st.form_submit_button("Add Money In")

    st.markdown("### 💸 Money Out")
    
    with st.form("money_out_form"):

        amount = st.number_input("Amount RM ", min_value=0.0)

        item = st.selectbox("Expense Item",
            ["Purchase","Petrol","Diesel","Land Rental"]
        )

        category = st.selectbox("Category",
            ["Expense","Operational"]
        )

        account = st.selectbox(
            "Account Type",
            ["CASH","QR BANK","TNG","BNK1","BNK2","BNK3"]
        )

        receipt = st.file_uploader("Receipt")

        submit_out = st.form_submit_button("Add Money Out")
