
import streamlit as st
from utils.sheets import read_sheet
import pandas as pd
from datetime import datetime, timedelta


# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

# Check if user is admin
if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()

INVOICE_SHEET_ID = "1zAey2gr64Gjc7299BzEDAEJ4dLqd3HIvOIpnXDufddQ"
SHEET_NAME = "OrderList"

st.title("📊 Admin Dashboard")

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

# Clean data
df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
df["outstanding_payment"] = pd.to_numeric(df["outstanding_payment"], errors="coerce").fillna(0)
df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")
df["doc_date"] = pd.to_datetime(df["doc_date"], errors="coerce")

# Only invoices
df = df[df["TYPE"] == "INV-R"]

today = pd.Timestamp.today()

# ----------------------------
# KPI METRICS
# ----------------------------

month_start = today.replace(day=1)

orders_month = df[df["delivery_date"] >= month_start]
sales_month = orders_month["total"].sum()

outstanding = df["outstanding_payment"].sum()

upcoming = df[
    (df["delivery_date"] >= today) &
    (df["delivery_date"] <= today + timedelta(days=7))
]

col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Orders This Month", len(orders_month))
col2.metric("💰 Sales This Month", f"RM {sales_month:,.0f}")
col3.metric("⚠️ Outstanding Balance", f"RM {outstanding:,.0f}")
col4.metric("📅 Rentals Next 7 Days", len(upcoming))

st.divider()

# ----------------------------
# UPCOMING RENTALS
# ----------------------------

st.subheader("📅 Upcoming Rentals (Next 7 Days)")

upcoming_table = upcoming[
    ["delivery_date", "branch", "item_1", "nama_pelanggan", "salesperson"]
].sort_values("delivery_date")

st.dataframe(upcoming_table, use_container_width=True)

st.divider()

# ----------------------------
# BRANCH PERFORMANCE
# ----------------------------

st.subheader("🏢 Branch Performance")

branch_sales = (df.groupby("branch")["total"].sum().sort_values(ascending=False))

st.bar_chart(branch_sales)

st.divider()

# ----------------------------
# SALESPERSON PERFORMANCE (Last 6 Months by Delivery Month)
# ----------------------------

st.subheader("👤 Salesperson Performance (Last 6 Months)")

# Remove rows without delivery_date
df_sales = df[df["delivery_date"].notna()].copy()

# Convert delivery_date to month
df_sales["month"] = df_sales["delivery_date"].dt.to_period("M")

# Get latest 6 months
latest_month = df_sales["month"].max()
last_6_months = [latest_month - i for i in range(5, -1, -1)]

df_sales = df_sales[df_sales["month"].isin(last_6_months)]

# Group by month + salesperson
salesperson_monthly = (
    df_sales.groupby(["month", "salesperson"])["total"]
    .sum()
    .reset_index()
)

# Pivot table so each salesperson becomes a line
chart_data = salesperson_monthly.pivot(
    index="month",
    columns="salesperson",
    values="total"
).fillna(0)

# Convert month to readable format
chart_data.index = chart_data.index.astype(str)

# Line chart
st.line_chart(chart_data, use_container_width=True)

# ----------------------------
# OUTSTANDING PAYMENTS
# ----------------------------

st.subheader("⚠️ Outstanding Payments")

unpaid = df[df["outstanding_payment"] > 0]

unpaid_table = unpaid[
    [
        "invoice_num",
        "salesperson",
        "branch",
        "total",
        "outstanding_payment",
        "delivery_date"
    ]
].sort_values("delivery_date")

st.dataframe(unpaid_table, use_container_width=True)

st.divider()

# ----------------------------
# MONTHLY SALES TREND
# ----------------------------

st.subheader("📈 Monthly Revenue Trend")

df["month"] = df["doc_date"].dt.to_period("M").astype(str)

monthly_sales = (
    df.groupby("month")["total"]
    .sum()
)

st.line_chart(monthly_sales)






