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

@st.cache_data(ttl=60)

# -----------------------------
# REGISTER EVENT FORM
# -----------------------------
if st.button("➕ Register New Event")

    with st.form("register_event_form"):
        st.subheader("Register New Event")
        event_name = st.text_input("Event Name")
        job_number = st.text_input("Job Number")
        event_type = st.selectbox("Event Type", ["MEGA ARENA", "FUN FEST"])
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        account_types = st.multiselect("Account Types", ["CASH", "QR BANK", "TNG", "BNK1", "BNK2", "BNK3"])
        username = st.session_state.user["username"]
    
        submit = st.form_submit_button("Save Event")

        if submit:
            if not event_name or not account_types:
                st.warning("Please fill all required fields and select at least one account type.")
            else:
                duration = (end_date - start_date).days + 1
                event_id = "EVT" + datetime.now().strftime("%Y%m%d%H%M%S")
                # Prepare data dict based on your sheet headers
                data = {
                    "event_id": event_id,
                    "timestamp": datetime.now(),
                    "created_by": username,
                    "event_name": event_name,
                    "job_number": job_number,
                    "event_type": event_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration": duration,
                    "account_types": ",".join(account_types),
                    "status": "active"
                }

                # Append using header-aware function
                append_row_by_header(SHEET_ID, EVENT_SHEET, data)

                st.success(f"✅ Event '{event_name}' registered successfully!")

                # Optionally, reload active events if needed
                st.experimental_rerun()




# -----------------------------
# SELECT EVENT
# -----------------------------
active_events = df_events[df_events["status"] == "active"]

if active_events.empty:
    st.info("No active events")
    st.stop()

selected_event = st.selectbox(
    "Select Event",
    active_events["event_name"],
    key="active_event"
)


event_row = active_events[
    active_events["event_name"] == selected_event
].iloc[0]

event_id = event_row["event_id"]

start_date = pd.to_datetime(event_row["start_date"]).date()
end_date = pd.to_datetime(event_row["end_date"]).date()
