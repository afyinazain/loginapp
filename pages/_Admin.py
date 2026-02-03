
import streamlit as st
from utils.sheets import read_sheet
import pandas as pd
from streamlit_copy_to_clipboard import st_copy_to_clipboard



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

GLIDE_SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
INVOICE_SHEET_NAME = "InvoiceList"

st.title("🎈 Admin Dashboard")

data = read_sheet(
    sheet_id=INVOICE_SHEET_ID,
    sheet_name=SHEET_NAME,
    header_row=1
)
df = pd.DataFrame(data)

all_quotation = df[
    (df["type_status"] == "Invoice")
]

if all_quotation.empty:
    st.info("No active quotations.")

st.write(f"### All Active Quotation")
for _, row in all_quotation.iterrows():
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### 🧾 {row['item_1']} - {row['branch']} ({row['delivery_date']})")
            st.write(f"**Total:** RM {float(row['total']):.2f}")
            st.write(f'Salesperson :{row['salesperson']}')
        
