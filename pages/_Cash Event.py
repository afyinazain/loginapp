import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_sheet
import gspread
from google.oauth2.service_account import Credentials
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
EVENTLIST_SHEET = "Event List"
CASHFLOW_SHEET = "Cashflow Event"
username = st.session_state.user
# ---------------------------------
# LOAD EVENT LIST
# ---------------------------------

@st.cache_data(ttl=60)
def load_events():

    url = "https://docs.google.com/spreadsheets/d/1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A/edit?gid=635875008#gid=635875008"

    df = pd.read_csv(url)

    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    return df


df_event = load_events()

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

            new_row = pd.DataFrame([{

                "timestamp": timestamp,
                "pic": username,
                "event_name": event_name,
                "event_type": event_type,
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
                "account_type": ",".join(account_type),
                "status": "active"

            }])

            st.success("Event Registered")

            # HERE you will append to sheet using your Google API method
