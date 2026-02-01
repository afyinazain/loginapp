import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import get_client, read_sheet, append_row_by_header, generate_invoice_number

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

user = st.session_state.user

# ----------------------------
# User Profile Tab - Quotations
# ----------------------------

INVOICE_SHEET_ID = "1zAey2gr64Gjc7299BzEDAEJ4dLqd3HIvOIpnXDufddQ"
SHEET_NAME = "OrderList"

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access your profile.")
    st.stop()

user_name = st.session_state.user["username"]
st.title(f"👤 {user_name}'s Quotation List")

# ----------------------------
# LOAD DATA
# ----------------------------
data = read_sheet(
    sheet_id=INVOICE_SHEET_ID,
    sheet_name=SHEET_NAME,
    header_row=1
)
df = pd.DataFrame(data)

df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce")

quotations = df[
    (df["salesperson"] == user_name) &
    (df["type_status"] == "Quotation")
]

if quotations.empty:
    st.info("No active quotations.")
    st.stop()

# ----------------------------
# POPUP DIALOG
# ----------------------------
@st.dialog("✅ Confirm Quotation")
def confirm_dialog(row):

    st.write(f"**Quotation:** {row['quotation_num']}")
    st.write(f"**Total:** RM {float(row['total']):.2f}")

    proof = st.file_uploader(
        "Upload payment proof",
        type=["png", "jpg", "jpeg"]
    )

    invoice_num = generate_invoice_number()
    st.write(invoice_num)
    print(df.columns)
    print(df.head(5))

    if st.button("🚀 Submit Confirmation"):
        if not proof:
            st.error("Please upload payment proof")
            return

        
        


        client = get_client()
        ws = client.open_by_key(INVOICE_SHEET_ID).worksheet(SHEET_NAME)

        cell = ws.find(row["quotation_num"])
        sheet_row = cell.row

        ws.update_cell(sheet_row, df.columns.get_loc("type_status") + 1, "Invoice")
        ws.update_cell(sheet_row, df.columns.get_loc("invoice_num") + 1, invoice_num)
        ws.update_cell(sheet_row, df.columns.get_loc("proof_attached") + 1, proof.name)

        st.success(f"🎉 Invoice {invoice_num} created")
        st.rerun()

# ----------------------------
# CARD VIEW
# ----------------------------
for _, row in quotations.iterrows():

    expired = (
        pd.notna(row["expiry_date"]) and
        datetime.today() > row["expiry_date"]
    )

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### 🧾 {row['quotation_num']}")
            st.write(f"**Total:** RM {float(row['total']):.2f}")
            st.write(
                f"**Expiry:** {row['expiry_date'].date() if pd.notna(row['expiry_date']) else '—'}"
            )
            st.write("**Status:** Quotation")

            if expired:
                st.error("❌ Expired")

        with col2:
            if not expired:
                if st.button(
                    "Confirm",
                    key=f"confirm_btn_{row['quotation_num']}"
                ):
                    confirm_dialog(row)
