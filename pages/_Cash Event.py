import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_sheet


# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

# Check if user is admin
if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()
    
st.title("🎪 Event Cash Flow Management")

# ----------------------------
# LOAD DATA
# ----------------------------

GLIDE_SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
INVOICE_SHEET_NAME = "InvoiceList"

data = read_sheet(
    sheet_id=GLIDE_SHEET_ID,
    sheet_name=INVOICE_SHEET_NAME,
    header_row=7
)

df = pd.DataFrame(data)

# -----------------------
# EVENT SELECTION
# -----------------------

st.subheader("Event Selection")

col1, col2 = st.columns(2)

with col1:
    event_name = st.text_input("Event Name")

with col2:
    start_date = st.date_input("Event Start Date")
    end_date = st.date_input("Event End Date")

# -----------------------
# CASH ENTRY FORM
# -----------------------

st.divider()
st.subheader("Add Transaction")

col1, col2, col3 = st.columns(3)

with col1:
    flow_type = st.selectbox(
        "Type",
        ["IN","OUT"]
    )

with col2:
    category = st.selectbox(
        "Category",
        ["Ticket","Food","Staff","Rental","Equipment","Marketing","Other"]
    )

with col3:
    amount = st.number_input(
        "Amount (RM)",
        min_value=0.0,
        step=1.0
    )

description = st.text_input("Description")

recorded_by = st.text_input("Recorded By")

if st.button("Submit Transaction"):

    new_data = {
        "timestamp": datetime.now(),
        "event_name": event_name,
        "event_date": event_date,
        "category": category,
        "type": flow_type,
        "description": description,
        "amount": amount,
        "recorded_by": recorded_by
    }

    df_new = pd.DataFrame([new_data])

    df_updated = pd.concat([df, df_new], ignore_index=True)

    conn.update(
        worksheet="Event_Cashflow",
        data=df_updated
    )

    st.success("Transaction recorded successfully!")

    st.rerun()

# -----------------------
# FILTER DATA
# -----------------------

filtered = df[
    (df["event_name"] == event_name) &
    (df["event_date"] == str(event_date))
]

# -----------------------
# SUMMARY
# -----------------------

st.divider()
st.subheader("Financial Summary")

total_in = filtered[filtered["type"]=="IN"]["amount"].sum()
total_out = filtered[filtered["type"]=="OUT"]["amount"].sum()

balance = total_in - total_out

col1, col2, col3 = st.columns(3)

col1.metric("Money In", f"RM {total_in:,.2f}")
col2.metric("Money Out", f"RM {total_out:,.2f}")
col3.metric("Balance", f"RM {balance:,.2f}")

# -----------------------
# TRANSACTION TABLE
# -----------------------

st.divider()
st.subheader("Transaction List")

st.dataframe(
    filtered.sort_values("timestamp", ascending=False),
    use_container_width=True
)

# -----------------------
# EXPENSE CHART
# -----------------------

st.divider()
st.subheader("Expense by Category")

expense = filtered[filtered["type"]=="OUT"]

if not expense.empty:

    chart = expense.groupby("category")["amount"].sum()

    st.bar_chart(chart)
