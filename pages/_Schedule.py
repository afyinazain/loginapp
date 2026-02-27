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

branch_list = ["All Branches"] + sorted(df["branch"].dropna().unique().tolist())

default_branch = 0  # Default to all branches


selected_branch = st.radio(
    "🏢 Select Branch",
    branch_list,
    index=default_branch,
    horizontal=True
)

if selected_branch == "All Branches":
    df_branch = df.copy()
else:
    df_branch = df[df["branch"] == selected_branch]
    

# ---------------------------------
# PREPARE EVENTS FOR CALENDAR
# ---------------------------------

branch_colors = {
    branch: color for branch, color in zip(
        df["branch"].unique(),
        ["#18c936", "#f39c12", "#3498db", "#9b59b6", "#e74c3c"]
    )
}

events = []


for _, row in df_branch.iterrows():
    # Skip rows without a delivery_date
    if pd.isna(row["delivery_date"]):
        continue

    # Safely get all fields, replacing NaN with empty string or 0
    item = str(row.get("item_1") if pd.notna(row.get("item_1")) else "")
    bil_jam = str(row.get("bil_jam") if pd.notna(row.get("bil_jam")) else "")
    quotation = str(row.get("invoice_num") if pd.notna(row.get("invoice_num")) else "")
    salesperson = str(row.get("salesperson") if pd.notna(row.get("salesperson")) else "")
    branch = str(row.get("branch") if pd.notna(row.get("branch")) else "Unknown")

    # Ensure total is a valid number
    total = row.get("total", 0)
    if pd.isna(total):
        total = 0.0
    total = float(total)

    # Assign color per branch
    color = branch_colors.get(branch, "#18c936")

    # Append the event
    event = {
        "title": f"{item} - {bil_jam}" if item or bil_jam else branch,
        "start": row["delivery_date"].strftime("%Y-%m-%d"),
        "end": row["delivery_date"].strftime("%Y-%m-%d"),
        "color": color,
        "extendedProps": {
            "quotation": quotation,
            "salesperson": salesperson,
            "total": total,
            "branch": branch
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
# -----------------------
# BRANCH COLOR GUIDE
# -----------------------
st.markdown("### 🏢 Branch Color Guide")
legend_html = "<div style='display:flex; flex-wrap:wrap; gap:10px;'>"

for branch, color in branch_colors.items():
    legend_html += f"""
    <div style='display:flex; align-items:center; gap:4px;'>
        <div style='width:20px; height:20px; background:{color}; border-radius:4px;'></div>
        <span>{branch}</span>
    </div>
    """

legend_html += "</div>"

st.markdown(legend_html, unsafe_allow_html=True)


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

st.subheader(f"📆 Schedule Grid for {selected_branch}")

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
                # Safely get fields
                item = str(event.get("item_1") if pd.notna(event.get("item_1")) else "")
                salesperson = str(event.get("salesperson") if pd.notna(event.get("salesperson")) else "")
                bil_jam = str(event.get("bil_jam") if pd.notna(event.get("bil_jam")) else "")
                branch = str(event.get("branch") if pd.notna(event.get("branch")) else "Unknown")

                # Get color per branch
                color = branch_colors.get(branch, "#18c936")

                st.markdown(
                    f"""
                    <div style="
                        background:{color};
                        padding:6px;
                        border-radius:6px;
                        font-size:12px;
                        margin-bottom:4px;
                        color:white;">
                        {item} - {bil_jam}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.write("—")



