import streamlit as st
import pandas as pd
from auth import authenticate
from datetime import date
from datetime import datetime
from datetime import timedelta
from streamlit_calendar import calendar

st.set_page_config(page_title="Soopa App", layout="wide")

st.title("🎈 Soopa Rental System")


if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
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

    st.warning("Please log in to check schedule and availability")
    st.subheader("🔐 Login")

    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("ID", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome {user['name']}")
                st.rerun()
            else:
                st.error("Invalid ID")

else:
        
    st.success(f"Hi {st.session_state.user['name']}! We Are Happy To Have You Here")
    

    st.markdown("---")
    st.subheader("Quick Actions")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📅 View Schedule"):
            st.switch_page("pages/_Schedule.py")
            
    with col2:
        if st.button("📝 Submit Order"):
            st.switch_page("pages/_New Order.py")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()
