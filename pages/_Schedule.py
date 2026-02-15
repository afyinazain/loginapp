import re

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

# ---------------------------------
# AUTH CHECK
# ---------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()

st.title("📅 Rental Schedule")

# ---------------------------------
# LOAD DATA
# ---------------------------------
@st.cache_data(ttl=60)
def load_schedule_data():
    url = "https://docs.google.com/spreadsheets/d/1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A/export?format=csv&gid=1912796754"
    df = pd.read_csv(url, header=6)

    df.columns = df.columns.str.strip()
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")

    # Filter only rental invoices
    df = df[df["TYPE"] == "INV-R"]

    return df

df = load_schedule_data()

# ---------------------------------
# BRANCH FILTER
# ---------------------------------
branch_list = sorted(df["branch"].dropna().unique().tolist())

selected_branch = st.selectbox(
    "🏢 Select Branch",
    branch_list
)

# Filter by branch
df_branch = df[df["branch"] == selected_branch]

# ---------------------------------
# PREPARE EVENTS FOR CALENDAR
# ---------------------------------
events = []

for _, row in df_branch.iterrows():

    if pd.notna(row["delivery_date"]):

        events = []

for _, row in df_branch.iterrows():

    if pd.notna(row["delivery_date"]):

        item = str(row.get("item_1", "") or "")
        customer = str(row.get("nama_pelanggan", "") or "")
        quotation = str(row.get("quotation_num", "") or "")
        salesperson = str(row.get("salesperson", "") or "")

        total = row.get("total", 0)
        if pd.isna(total):
            total = 0

        event = {
            "title": f"{item} - {quotation}",
            "start": row["delivery_date"].strftime("%Y-%m-%d"),
            "end": row["delivery_date"].strftime("%Y-%m-%d"),
            "color": "#18c936",
            "extendedProps": {
                "quotation": quotation,
                "salesperson": salesperson,
                "total": float(total)
            }
        }

        events.append(event)


# ---------------------------------
# CALENDAR OPTIONS
# ---------------------------------
calendar_options = {
    "initialView": "dayGridMonth",
    "height": 650,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
}

# ---------------------------------
# DISPLAY CALENDAR
# ---------------------------------
st.subheader(f"📆 Schedule for {selected_branch}")

calendar_event = calendar(
    events=events,
    options=calendar_options
)

# ---------------------------------
# EVENT CLICK DETAILS
# ---------------------------------
if calendar_event and "eventClick" in calendar_event:
    event_data = calendar_event["eventClick"]["event"]

    st.markdown("### 📋 Event Details")

    st.write("🧾 Quotation:", event_data["extendedProps"]["quotation"])
    st.write("👤 Salesperson:", event_data["extendedProps"]["salesperson"])
    st.write("💰 Total:", event_data["extendedProps"]["total"])



