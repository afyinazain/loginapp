import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import read_sheet, get_client
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
    
df_events = load_sheet(EVENTLIST_SHEET)
df_accounts = load_sheet(ACCOUNT_SHEET)
df_txn = load_sheet(TXN_SHEET)

if st.button("➕ Register Event"):
    st.session_state.show_event_form = True


# -----------------------------
# EVENT FORM
# -----------------------------
if st.session_state.get("show_event_form", False):

    with st.form("event_form"):

        st.subheader("Register New Event")

        event_name = st.text_input("Event Name")

        job_number = st.text_input("Job Number")

        event_type = st.selectbox(
            "Event Type",
            ["FUN FEST", "MEGA ARENA"],
            key="event_type"
        )

        start_date = st.date_input("Start Date")

        end_date = st.date_input("End Date")

        submit = st.form_submit_button("Save Event")

        if submit:

            duration = (end_date - start_date).days + 1

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            event_id = "EVT" + datetime.now().strftime("%Y%m%d%H%M%S")

            # Connect to sheet
            sheet = client.open_by_key(SHEET_ID).worksheet(EVENTLIST_SHEET)

            # Get headers from row 1
            headers = sheet.row_values(1)

            # Create dictionary mapped to headers
            row_data = {
                "event_id": event_id,
                "timestamp": timestamp,
                "username": username,
                "event_name": event_name,
                "job_number": job_number,
                "event_type": event_type,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "duration": duration,
                "status": "active"
            }

            # Reorder according to sheet headers
            row = [row_data.get(col, "") for col in headers]

            # Append row
            sheet.append_row(row, value_input_option="USER_ENTERED")

            st.success("✅ Event Registered")

            st.session_state.show_event_form = False

            st.rerun()
            
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
