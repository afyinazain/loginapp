import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import read_sheet, get_client, append_row_by_header
import os
import json
from streamlit_calendar import calendar
import urllib.parse
import uuid
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


# -----------------------------
# PAGE TITLE
# -----------------------------

st.title("🎪 Event Cash Flow Management")

# -----------------------------
# CONNECT TO GOOGLE SHEET
# -----------------------------

SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
EVENTS_SHEET = "Event_List"
TXN_SHEET = "Event_Txn"
ACCOUNT_SHEET = "Event_Account"

if "show_event_form" not in st.session_state:
    st.session_state.show_event_form = False
# -----------------------------
# REGISTER EVENT FORM
# -----------------------------

if st.button("➕ Register New Event"):
    st.session_state.show_event_form = True
    
if st.session_state.show_event_form:

    with st.form("register_event_form"):
        st.subheader("Register New Event")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        created_by = st.session_state.user["username"]
        event_id = "EVT" + datetime.now().strftime("%Y%m%d%H%M%S")
        st.text_input("Event ID", value=event_id, disabled=True)
        st.text_input("Created By", value=created_by, disabled=True)
        
        event_name = st.text_input("Event Name")
        job_number = st.text_input("Job Number")
        event_type = st.selectbox("Event Type", ["MEGA ARENA", "FUN FEST"])
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        duration = (end_date - start_date).days + 1
        account_types = st.multiselect("Account Types", ["CASH", "QR BANK", "TNG", "BNK1", "BNK2", "BNK3"])
        status = "active"
    
        col1, col2 = st.columns(2)

        submit = col1.form_submit_button("✅ Register Event")
        cancel = col2.form_submit_button("❌ Cancel")

        if submit:
            if not event_name or not account_types:
                st.warning("Please fill all required fields and select at least one account type.")
            else:
                # Append using header-aware function
                append_row_by_header(
                    sheet_id=SHEET_ID, 
                    sheet_name=EVENTS_SHEET,
                    data = {
                        "event_id": event_id,
                        "timestamp": timestamp,
                        "created_by": created_by,
                        "event_name": event_name,
                        "job_number": job_number,
                        "event_type": event_type,
                        "start_date": start_date,
                        "end_date": end_date,
                        "duration": duration,
                        "account_types": ",".join(account_types),
                        "status": status
                    },
                    header_row=1
                )

                st.success(f"✅ Event '{event_name}' registered successfully!")

                st.session_state.show_event_form = False
                st.rerun()
        if cancel:
            st.session_state.show_event_form = False
            st.rerun()

# -----------------------------
# LOAD EVENTS
# -----------------------------
df_events = pd.DataFrame(read_sheet(SHEET_ID, EVENTS_SHEET))

# Filter active events
active_events = df_events[df_events["status"] == "active"]

if active_events.empty:
    st.info("No active events")
    st.stop()

# -----------------------------
# SELECT EVENT
# -----------------------------

selected_event = st.selectbox(
    "Select Event",
    ["-- Select Event --"] + active_events["event_name"].tolist(),
    index = 0,
    key="active_event"
)
if selected_event == "-- Select Event --":
    st.info("Please select an event to continue.")
    st.stop()

event_row = active_events[active_events["event_name"] == selected_event].iloc[0]
event_id = event_row["event_id"]
event_name = event_row["event_name"]
accounts_raw = event_row.get("account_types","")
event_accounts = [a.strip()
                  for a in str(accounts_raw).split(",")
                  if a.strip() != ""
                ]   

event_start = pd.to_datetime(event_row["start_date"]).date()
event_end = pd.to_datetime(event_row["end_date"]).date()
#-----------------------------------
events = []

current = event_start
while current <= event_end:

    events.append({
        "title": "Event Day",
        "start": current.strftime("%Y-%m-%d"),
        "end": current.strftime("%Y-%m-%d")
    })

    current += timedelta(days=1)


calendar_result = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "initialDate": event_start.strftime("%Y-%m-%d"),
        "height": 400,
        "headerToolbar": False,   # disables top navigation buttons
        "dayMaxEvents": True,
        "editable": False,
        "selectable": False,
        "fixedWeekCount": True,    # ensures all event dates fit in the month view
        "navLinks": False,
        "eventStartEditable": False,
        "eventDurationEditable": False
    }
)

# -----------------------------
# INITIALIZE
# -----------------------------
if "txn_data" not in st.session_state:
    st.session_state.txn_data = {}  # current form values
#-------------------------------------------------
#--------------form---------------------
#-------------------------------------------------
# -----------------------------
# PAGE TITLE
# -----------------------------

st.title("💰 Event Cash Flow")

if "show_txn_form" not in st.session_state:
    st.session_state.show_txn_form = True

with st.expander("Submit Transactions", expanded=st.session_state.show_txn_form):
    # Date input
    st.session_state.txn_data["date"] = st.date_input(
        "Transaction Date",
        value=st.session_state.txn_data.get("date", event_start),
        min_value=event_start,
        max_value=event_end,
        key="txn_date"
    )

    st.write(f"Transactions will be recorded for: **{st.session_state.txn_date}**")
    st.markdown("---")

    # Two-column layout
    col1, col2 = st.columns(2)

    with col1:
        type = st.selectbox(
            "Type",
            ["-- Select Type --","IN", "OUT"],
            key="txn_type"
        )

        if type == "IN":

            items = st.selectbox(
                "Items",
                ["-- Select Item --","Sales", "Petty Cash", "Others"],
                key=f"txn_items"
            )

            category = st.selectbox(
            "Category",
            ["-- Select Category --","Sales Event", "Petty Cash"],
            key=f"txn_category"
        )
        else:
            items = st.selectbox(
                "Items",
                ["-- Select Item --","Expenses Event", "Petty Cash", "Others"],
                key=f"txn_items"
            )

            category = st.selectbox(
                "Category",
                [   
                    "-- Select Category --",
                    "Petrol/Diesel",
                    "Land Rental",
                    "Utilities",
                    "Purchase - tools/equipment",
                    "Accommodation",
                    "Others"
                ],
                key=f"txn_category"
            )


    with col2:
        amount = st.number_input(
            "Amount (RM)",
            step=10,
            key="txn_amount"
        )

        for_account = st.selectbox(
            "For Account",
            ["-- Select Account --"] + event_accounts,
            index=0,
            key="txn_account"
        )

        receipt = st.file_uploader(
            "Receipt",
            type=["jpg","png","jpeg"],
            key="txn_receipt"
        )
    st.markdown("---")
    if st.button("✅ Submit Transaction"):
        if type == "-- Select Type --" or items == "-- Select Item --" or category == "-- Select Category --" or for_account == "-- Select Account --":
            st.warning("⚠ Please complete all fields before submitting.")
            st.stop()
        # --- Prepare data to append ---
        txn_id = str(uuid.uuid4())[:10]
        data = {
            "txn_id": txn_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_id": event_id,
            "account_name": selected_event,
            "username":st.session_state.user["username"],
            "date": st.session_state.txn_data["date"].strftime("%Y-%m-%d"),
            "type": type,
            "item": items,
            "category": category,
            "amount": amount,
            "for_account": for_account,
            "receipt": receipt.name if st.session_state.txn_data.get("receipt") else ""
        }

        # --- Append to Google Sheet ---
        append_row_by_header(
            sheet_id=SHEET_ID,
            sheet_name=TXN_SHEET,
            data=data,
            header_row=1
        )
        
        st.success(f"✅ Transaction ** ({type}) RM{amount} ** submitted! ")
        st.session_state.txn_data = {}
        # delete widget states
        for key in [
            "txn_date",
            "txn_type",
            "txn_items",
            "txn_category",
            "txn_amount",
            "txn_account",
            "txn_receipt"
        ]:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state.show_txn_form = False
        
        




# -----------------------------
# SHOW TODAY'S ACTIVITY FROM GOOGLE SHEET
# -----------------------------
st.subheader("📋 Today's Transactions")

try:
    df_txn = pd.DataFrame(read_sheet(SHEET_ID, TXN_SHEET))
    if not df_txn.empty:
        # Normalize column names
        df_txn.columns = [c.strip() for c in df_txn.columns]

        if "date" not in df_txn.columns:
            st.warning("⚠ 'date' column not found in sheet. Check your sheet headers.")
        else:
            today_str = datetime.today().strftime("%Y-%m-%d")
            # Convert all dates to string
            df_txn["date"] = df_txn["date"].astype(str)
            df_today = df_txn[df_txn["date"] == today_str]

            if df_today.empty:
                st.info("No transactions recorded today yet.")
            else:
                for _, txn in df_today.iterrows():
                    st.markdown(
                        f"- **{txn.get('type','')}** | {txn.get('items','')} | {txn.get('category','')} | RM {txn.get('amount','')} | Account: {txn.get('for_account','')}"
                    )
    else:
        st.info("No transactions recorded yet.")
except Exception as e:
    st.error(f"Error fetching transactions: {e}")

import plotly.express as px

# -----------------------------
# BAR CHART OF TRANSACTIONS PER EVENT DATE
# -----------------------------
st.subheader(f"📊 Transactions Summary for {event_name}")

# Get all event dates
event_dates = []
current = event_start
while current <= event_end:
    event_dates.append(current)
    current += timedelta(days=1)

# Load transactions for this event
try:
    df_txn = pd.DataFrame(read_sheet(SHEET_ID, TXN_SHEET))
    df_txn.columns = [c.strip() for c in df_txn.columns]  # normalize
    df_txn["date"] = pd.to_datetime(df_txn["date"], errors="coerce").dt.date
    df_txn["amount"] = pd.to_numeric(df_txn["amount"], errors="coerce").fillna(0)
    df_event_txn = df_txn[df_txn["event_id"] == event_id]
except:
    df_event_txn = pd.DataFrame(columns=["date", "amount"])

# Prepare summary data
summary = []
for day in event_dates:
    total = df_event_txn[df_event_txn["date"] == day]["amount"].sum()
    summary.append({"date": day.strftime("%Y-%m-%d"), "total_amount": total})

df_summary = pd.DataFrame(summary)

# Plot bar chart
fig = px.bar(
    df_summary,
    x="date",
    y="total_amount",
    text="total_amount",
    labels={"date": "Event Date", "total_amount": "Total Transaction (RM)"},
    title=f"Total Transactions per Day for {event_name}"
)
fig.update_traces(textposition="outside")
fig.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# EVENT TRANSACTION SUMMARY TABLE
# -----------------------------
st.subheader(f"📋 Transaction Summary for {event_name}")

# Get all event dates
event_dates = []
current = event_start
while current <= event_end:
    event_dates.append(current)
    current += timedelta(days=1)

# Load transactions for this event
df_txn = pd.DataFrame(read_sheet(SHEET_ID, TXN_SHEET))
if not df_txn.empty:
    df_txn.columns = [c.strip() for c in df_txn.columns]  # normalize
    df_txn["date"] = pd.to_datetime(df_txn["date"], errors="coerce").dt.date
    df_txn["amount"] = pd.to_numeric(df_txn["amount"], errors="coerce").fillna(0)
    df_event_txn = df_txn[df_txn["event_id"] == event_id]
else:
    df_event_txn = pd.DataFrame(columns=["date", "amount"])

# Prepare summary data
summary = []
for day in event_dates:
    day_txn = df_event_txn[df_event_txn["date"] == day]
    summary.append({
        "Date": day.strftime("%Y-%m-%d"),
        "Total Transactions": len(day_txn),
        "Total Amount (RM)": day_txn["amount"].sum()
    })

df_summary = pd.DataFrame(summary)

# Show the summary table
st.dataframe(df_summary)
