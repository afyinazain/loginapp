import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
EVENTLIST_SHEET = "Event_List"
CASHFLOW_SHEET = "Cashflow_Event"
username = st.session_state.user["username"]
# ---------------------------------
# LOAD EVENT LIST
# ---------------------------------

@st.cache_data(ttl=60)
def load_events():

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={EVENTLIST_SHEET}"
    df = pd.read_csv(url)

    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    return df


df_event = load_events()

@st.cache_data(ttl=60)
def load_cashflow():

    url1 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={CASHFLOW_SHEET}"

    df1 = pd.read_csv(url1)

    if "date" in df1.columns:
        df1["date"] = pd.to_datetime(df1["date"])

    return df1

df_cashflow = load_cashflow()

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

events = []

current = start_date

while current <= end_date:

    events.append({
        "title": selected_event,
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

@st.cache_data(ttl=60)
def load_cashflow():

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={CASHFLOW_SHEET}"

    df = pd.read_csv(url)

    df["date"] = pd.to_datetime(df["date"])

    return df


df_cash = load_cashflow()

if calendar_event and "dateClick" in calendar_event:

    selected_date = calendar_event["dateClick"]["date"]

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
