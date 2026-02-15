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

default_branch = branch_list.index(st.session_state.user["branch"]) \
    if st.session_state.user.get("branch") in branch_list else 0

selected_branch = st.radio(
    "🏢 Select Branch",
    branch_list,
    index=default_branch,
    horizontal=True
)


# Filter by branch
df_branch = df[df["branch"] == selected_branch]

# ---------------------------------
# PREPARE EVENTS FOR CALENDAR
# ---------------------------------
events = []

for _, row in df_branch.iterrows():

    if pd.notna(row["delivery_date"]):

        item = str(row.get("item_1", "") or "")
        bil_jam = str(row.get("bil_jam", "") or "")
        quotation = str(row.get("invoice_num", "") or "")
        salesperson = str(row.get("salesperson", "") or "")

        total = row.get("total", 0)
        if pd.isna(total):
            total = 0

        event = {
            "title": f"{item} - {bil_jam}",
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

st.markdown("""
<style>

/* Force 3 columns layout */
.fc .fc-daygrid-body {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 6px;
}

/* Make each day card look like a box */
.fc .fc-daygrid-day {
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 4px;
    min-height: 110px;
}

/* Hide weekday header row */
.fc .fc-col-header {
    display: none !important;
}

/* Adjust event text size for mobile */
.fc-event {
    font-size: 10px;
    padding: 2px;
}

/* Smaller day number */
.fc .fc-daygrid-day-number {
    font-size: 12px;
}

/* Better mobile toolbar */
.fc .fc-toolbar-title {
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------
# CALENDAR OPTIONS
# ---------------------------------
calendar_options = {
    "initialView": "dayGridMonth",
    "height": 650,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": ""
    }
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


import calendar as cal
from datetime import date

st.subheader(f"📆 Schedule for {selected_branch}")

today = datetime.today()
year = today.year
month = today.month

# Get all dates in this month
month_dates = cal.monthcalendar(year, month)

# Flatten and remove zeros
flat_dates = [day for week in month_dates for day in week if day != 0]

# Convert events into dictionary by date
events_by_date = {}

for _, row in df_branch.iterrows():
    if pd.notna(row["delivery_date"]):
        d = row["delivery_date"].date()
        events_by_date.setdefault(d, []).append(row)

# Display 3-column grid
cols = st.columns(3)

for i, day in enumerate(flat_dates):
    current_date = date(year, month, day)

    with cols[i % 3]:
        st.markdown(f"### {day}")

        if current_date in events_by_date:
            for event in events_by_date[current_date]:
                item = str(event.get("item_1", ""))
                bil_jam = str(event.get("bil_jam", ""))

                st.markdown(
                    f"""
                    <div style="
                        background:#18c936;
                        padding:6px;
                        border-radius:6px;
                        font-size:12px;
                        margin-bottom:4px;">
                        {item} - {bil_jam}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("—")








