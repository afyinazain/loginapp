import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
from datetime import timedelta
from streamlit_calendar import calendar
import re

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

st.set_page_config(
    page_title="Soopa Rental Schedule",
    layout="wide"
)

st.title("🎈 Soopa Balloon Rental Schedule")



st.write("Check availability for each date first before submit the order. Click on the date to check")

# Load data
@st.cache_data(ttl=30)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A/export?format=csv&gid=1912796754"
    df = pd.read_csv(url, header=6)
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")
    return df

# Filter only INV-R
df = load_data()
df = df[df["TYPE"] == "INV-R"]
#--------------------------------------------------




# first calendar-------- Build events list --------
events = []
for _, row in df.iterrows():
    delivery_date = row.get("delivery_date")

    # 🚨 Skip rows with no valid date
    if pd.isna(delivery_date):
        continue

    start_date = (
        delivery_date.strftime("%Y-%m-%d")
        if pd.notna(delivery_date)
        else None
    )
        
    events.append({
        "title": f"{row['item_1']} ({row['invoice_num']})",
        "start": row["delivery_date"].strftime("%Y-%m-%d"),
        "end": row["delivery_date"].strftime("%Y-%m-%d"),
        # optional: set colors etc
        "backgroundColor": "#4caf50",
        "borderColor": "#4caf50",
        "textColor": "#ffffff",
    })

# -------- Calendar config --------
calendar_options = {
    "initialView": "dayGridMonth",       # month view
    "headerToolbar": {
    
    },
    "selectable": True,                  # allow selection
    "editable": False,                   # not editable for now
}

# -------- Render calendar --------
if events:
    cal_state = calendar(
        events=events,
        options=calendar_options,
        key="schedule_calendar"
    )
else:
    st.info("No events to show this month.")

# -------- Show clicked details (optional) --------

if cal_state and "eventClick" in cal_state:
    ev = cal_state["eventClick"]["event"]
    st.markdown(f"### 📌 Selected event: {ev['title']}")
    st.write("🗓 Date:", ev["start"])


#capture clicked date
selected_cal_date = None

if cal_state and cal_state.get("dateClick"):
    clicked = cal_state["dateClick"]["date"]
    
    selected_cal_date = ( pd.to_datetime(clicked, utc=True) .tz_convert("Asia/Kuala_Lumpur") .date() )


#convert it
if selected_cal_date:
    #filter data for that date
    daily_df = df[df["delivery_date"].dt.date == selected_cal_date]
else:
    daily_df = pd.DataFrame()


#------------------------------------------------
# section 2 - Available items logic
st.markdown("""
<style>
.availability-grid {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.section-box {
    border-radius: 10px;
    padding: 10px;
    background: rgba(255,255,255,0.05);
    flex: 1;
    min-width: 160px;
}

.section-title {
    font-weight: 700;
    margin-bottom: 8px;
    text-align: center;
}

.items-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.item-card {
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12px;
    text-align: center;
    font-weight: 600;
}

.available {
    background: #1b5e20;
    color: #a5d6a7;
}

.booked {
    background: #b71c1c;
    color: #ffcdd2;
}
</style>
""", unsafe_allow_html=True)

    # Define inventory

INVENTORY = [
    "BANANA",
    "HIPPO",
    "THOMAS",
    "BOAT",
    "TWISTER",
    "BBALL",
    "LITTLEBALL",
    "DOLPHIN",
    "ARIEL",
    "UNICORN",
    "FROZEN",
    "SPIDER",
    "CANDY",
    "HULK",
    "RACING",
    "COURT",
    "GATOR",
    "PRINCESS",
    "HOTWHEEL",
    "BUILDER",
    "ATLANTICA",
    "MARVEL",
    "CROCC",
    "POSEIDON",
    "PLAYLAND",
    "ISLAND",
    "RAMBO",
    "UNIVERSE",
    "MEGALODON",
    "TORNADO",
    "MINI SPONGEBOB",
    "MINI TRANSFORMERS",
    "MINI MAZE",
    "SPARROW",
    "TROPICANA",
    "SPONGEBOB",
    "TRANSFORMERS",
    "MAZE HOUSE",
    "DOMINION",
    "MICKEY"
]    


    
# Parsing logic
def extract_products(text):
    if not isinstance(text, str):
        return set()

    text = text.upper()

    found = set()
    for product in INVENTORY:
        if product in text:
            found.add(product)
    
    return found

# 
if daily_df.empty:
    st.info("No schedule for this date.")
else:

    # 2️⃣ Availability inside an expander that opens automatically
    booked_items = set()
    for text in daily_df['item_1'].fillna(''):
        booked_items.update(extract_products(text))

    available_items = [i for i in INVENTORY if i not in booked_items]
    unavailable_items = [i for i in INVENTORY if i in booked_items]

    available_html = "".join(f"<div class='item-card available'>{item}</div>" for item in available_items)
    booked_html = "".join(f"<div class='item-card booked'>{item}</div>" for item in unavailable_items)

    with st.expander("📦 Availability for the Day", expanded=True):
        st.markdown(f"""
        <div class="availability-grid">
            <div class="section-box">
                <div class="section-title">❌ Booked</div>
                <div class="items-grid">{booked_html or "<div style='opacity:.6'>None</div>"}</div>
            </div>
            <div class="section-box">
                <div class="section-title">✅ Available</div>
                <div class="items-grid">{available_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # refresh button
    st.write("Refresh data to keep up to date")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
    
    # show schedule

    st.subheader("📋 Schedule of the Day")
    for _, row in daily_df.iterrows():
        st.markdown(f"""
        <div style="
            padding:12px;
            margin-bottom:10px;
            border-left:5px solid #2196F3;
            background:rgba(255,255,255,0.05);
            border-radius:8px;
        ">
            <b>Customer:</b> {row['nama_pelanggan']}<br>
            <b>Product:</b> {row['item_1']}<br>
            <b>Location:</b> {row['branch']}<br>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------
# -----------------------------------------------------------

