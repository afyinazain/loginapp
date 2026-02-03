import streamlit as st
import pandas as pd
from auth import authenticate
from datetime import date
from datetime import datetime
from datetime import timedelta
from streamlit_calendar import calendar

from utils.sheets import append_row_by_header, generate_quotation_number


# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()
    

# Date selector
selected_date = st.date_input(
    "Select date",
    value=date.today()
)

# TRIGGER DIALOG
# ----------------------------




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

#convert it
if selected_date:
    #filter data for that date
    daily_df = df[df["delivery_date"].dt.date == selected_date]
else:
    daily_df = pd.DataFrame()


# Drop point prices
DROP_POINT_PRICES = {
    "Kelantan": 50,
    "Nilai": 80,
    "Kulai": 50,
    "Johor":100
}

ACTIVE_BRANCH = ("Nilai", "Kulai", "Pasir Puteh","Peringat")

#-------DEFINE SHEET ID'S---------
INVOICE_SHEET_ID = "1zAey2gr64Gjc7299BzEDAEJ4dLqd3HIvOIpnXDufddQ" #form2
SCHEDULE_SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A" #auditsoopaglide

# ----------------------------
# POPUP ORDER FORM
# ----------------------------

@st.dialog("📝 New Rental Order")
def order_popup():
    st.caption(f"📅 Date: {selected_date}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quotation_num = generate_quotation_number(INVOICE_SHEET_ID)
    st.text_input("Quotation Number", value=quotation_num, disabled=True)
    salesperson = st.text_input("Salesperson",value=st.session_state.user["username"])
    email = st.text_input("Documents will be sent to this address",value=st.session_state.user["email_address"],disabled=True)
    nama_pelanggan = st.text_input("Nama Penuh Pelanggan")
    delivery_date = st.date_input("Delivery Date",value=selected_date)
    expiry_date = datetime.today() + timedelta(days=5)
    item_1 = st.text_input("Item 1")
    harga_1 = st.number_input("Harga 1",step=10)
    item_2 = st.selectbox("Lokasi Penghantaran", list(DROP_POINT_PRICES.keys()))
    harga_2 = st.number_input("Caj Penghantaran",value=DROP_POINT_PRICES.get(item_2, 0),step=10)
    item_3 = st.text_input("Item 3")
    harga_3 = st.number_input("Harga 3",step=10)
    branch = st.selectbox("Lokasi Penghantaran", ACTIVE_BRANCH)

    subtotal = harga_1 + harga_2 + harga_3
    st.write(f"Subtotal: RM{subtotal:.2f}")

    tax_on = st.checkbox("Apply SST 8%", value=True)

    if tax_on:
        tax = round(subtotal * 0.08, 2)
    else:
        tax = 0


    
    total = subtotal + tax
            
    st.markdown("### 💰 Price Breakdown")
    
    st.write(f"Subtotal: RM{subtotal:.2f}")
    st.write(f"Tax (SST): RM{tax:.2f}")
    st.write(f"Total Amount: RM{total:.2f}")

    delivery_date_str = delivery_date.strftime("%Y-%m-%d")
    col1, col2 = st.columns(2)    

    if col1.button("✅ Submit Quotation"):
        if not item_1 or not delivery_date:
            st.error("Please fill all required fields")
        else:
                # Save to Google Sheets

               # For the invoice sheet
            append_row_by_header(
                sheet_id=INVOICE_SHEET_ID,
                sheet_name="OrderList",  # replace with the actual sheet/tab name
                data={"quotation_num": quotation_num,
                    "invoice_num": quotation_num,
                    "timestamp": timestamp,
                    "nama_pelanggan": nama_pelanggan,
                    "salesperson": salesperson,
                    "email": email,
                    "delivery_date": delivery_date_str,
                    "item_1": item_1,
                    "harga_1": harga_1,
                    "item_2": f"Penghantaran ke {item_2}",
                    "harga_2": harga_2,
                    "item_3": item_3,
                    "harga_3": harga_3,
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": total,
                    "type_status": "Quotation",
                    "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                    "branch": branch
                },
                header_row=1
            )

            append_row_by_header(
                sheet_id=SCHEDULE_SHEET_ID,
                sheet_name="InvoiceList",  # replace with the actual sheet/tab name
                data={"quotation_num": quotation_num,
                    "invoice_num": quotation_num,
                    "timestamp": timestamp,
                    "nama_pelanggan": nama_pelanggan,
                    "salesperson": salesperson,
                    "delivery_date": delivery_date_str,
                    "item_1": item_1,
                    "harga_1": harga_1,
                    "item_2": f"Penghantaran ke {item_2}",
                    "harga_2": harga_2,
                    "item_3": item_3,
                    "harga_3": harga_3,
                    "subtotal": subtotal,
                    "tax": tax,
                    "total": total,
                    "TYPE": "INV-R",
                    "branch": branch
                },
                header_row=7
            )
            st.success("Order submitted successfully")
            st.switch_page("pages/_My Profile.py")
            st.rerun()

    if col2.button("❌ Cancel"):
        st.rerun()

       
if st.button("📝 New Order"):
    order_popup()  # this will open the dialog    


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

# ----------------------------
# Availability + Click Logic
# ----------------------------

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

if "show_popup" not in st.session_state:
    st.session_state.show_popup = False


booked_items = set()
for text in daily_df['item_1'].fillna(''):
    booked_items.update(extract_products(text))

available_items = [i for i in INVENTORY if i not in booked_items]
unavailable_items = [i for i in INVENTORY if i in booked_items]

# session state for selected product
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

with st.expander("📦 Availability for the Day", expanded=True):

    col1, col2 = st.columns(2)

    # ❌ BOOKED
    with col1:
        st.markdown("### ❌ Booked")
        for item in unavailable_items:
            st.button(
                item,
                key=f"booked_{item}",
                disabled=True
            )

    # ✅ AVAILABLE (CLICKABLE)
    with col2:
        st.markdown("### ✅ Available")
        for item in available_items:
               if st.code(item, language="", line_numbers=False):
                st.session_state.selected_product = item
                # Option 1: Show in a text box with a copy button


                # ----------------------------



