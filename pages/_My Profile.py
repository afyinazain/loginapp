import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.sheets import upload_to_cloudinary, get_client, read_sheet, append_row_by_header, generate_invoice_number

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

user = st.session_state.user

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="dbxmliyzr",
    api_key="157236951965868",
    api_secret="4_GPqScoK-9rup4Eb_GS1fbxgjs"
)

# ----------------------------
# User Profile Tab - Quotations
# ----------------------------

INVOICE_SHEET_ID = "1zAey2gr64Gjc7299BzEDAEJ4dLqd3HIvOIpnXDufddQ"
SHEET_NAME = "OrderList"

GLIDE_SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
INVOICE_SHEET_NAME = "InvoiceList"

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access your profile.")
    st.stop()

user_name = st.session_state.user["username"]

# ----------------------------
# LOAD DATA
# ----------------------------
data = read_sheet(
    sheet_id=INVOICE_SHEET_ID,
    sheet_name=SHEET_NAME,
    header_row=1
)
df = pd.DataFrame(data)



st.write(f"### ✅ My Order List")
st.write(f"This List Shows Orders With Pending Payment Only")
data_inv = read_sheet(
    sheet_id=GLIDE_SHEET_ID,
    sheet_name=INVOICE_SHEET_NAME,
    header_row=7
)

df_inv = pd.DataFrame(data_inv)

df_inv["lookup_pivot3"] = pd.to_numeric(
    df_inv["lookup_pivot3"],
    errors="coerce"
)


invoices = df_inv[
    (df_inv["salesperson"] == user_name) &
    (df_inv["type_status"] == "Invoice") &
    (df_inv["lookup_pivot3"] > 0)
]

if invoices.empty:
    st.info("No orders.")





for _, row in invoices.iterrows():
    
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### 🧾 {row['item_1']} - {row['branch']} ({row['delivery_date']})")
            st.write(f"**Total:** RM {float(row['total']):.2f}")
        with col2:
            st.link_button("WhatsApp", row["wa_link"])
        

url_i = "https://docs.google.com/spreadsheets/d/1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A/export?format=csv&gid=2133205329"
    df_inventory = pd.read_csv(url_i)

    df_inventory.columns = df_inventory.columns.str.strip().str.lower()

    # safe boolean conversion
    df_inventory["active"] = (
        df_inventory["active"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    df_inventory = df_inventory[df_inventory["active"]]

    # clean fields
    df_inventory["branch"] = df_inventory["branch"].astype(str).str.strip()
    df_inventory["product_name"] = df_inventory["product_name"].astype(str).str.strip().str.upper()

    return df_inventory

df_inventory = load_inventory()
df = load_data()
df = df[df["TYPE"] == "INV-R"]

active_branch_list = (
    df_inventory["branch"]
    .dropna()
    .unique()
    .tolist()
)

active_branch_list.sort()

all_inventory = df_inventory["product_name"].unique().tolist()

# Parsing logic
def extract_products(text,inventory_list):
    if not isinstance(text, str):
        return set()

    text = text.upper()

    found = set()
    return {p for p in inventory_list if p in text}

booked_items_all = set()

for text in daily_df['item_1'].fillna(''):
    booked_items_all.update(extract_products(text, all_inventory))

def get_available_all():
    return [i for i in all_inventory if i not in booked_items_all]

def get_available_by_branch(branch):
    branch_inventory = df_inventory[
        df_inventory["branch"] == branch
    ]["product_name"].tolist()

    daily_branch_df = daily_df[
        daily_df["branch"] == branch
    ]

    booked = set()
    for text in daily_branch_df["item_1"].fillna(""):
        booked.update(
            extract_products(text, branch_inventory)
        )

    return [i for i in branch_inventory if i not in booked]


available_items_all = [i for i in all_inventory if i not in booked_items_all]
unavailable_items_all = [i for i in all_inventory if i in booked_items_all]

----
            
    #----------------
st.divider()
st.write(f"### ⌛️ My Active Quotation List")
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

    

    all_rows = read_sheet(
    sheet_id=GLIDE_SHEET_ID,
    sheet_name=INVOICE_SHEET_NAME,
    header_row=7
    )

    df2 = pd.DataFrame(all_rows)


    st.caption(f"🔍 Check Before Confirm")
    doc_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delivery_date = st.date_input(
        "Delivery Date",
        value=pd.to_datetime(row.get("delivery_date", datetime.today())).date()
        )
    nama_pelanggan = st.text_input("Nama Penuh Pelanggan", value=row.get("nama_pelanggan", ""))
    no_tel = st.text_input("No. Tel / Whatsapp", value=row.get("no_tel", ""))
    no_tin = st.text_input("Alamat / No TIN / No IC / Email", value=row.get("no_tin", ""))
    nama_tempat = st.text_input("Nama Tempat (Cth: KL, Hulu Langat, KB, dll)", value=row.get("nama_tempat",""))
    link_location = st.text_input("Location URL (Maps/Waze)",value=row.get("link_location", ""))
    branch = st.selectbox("Branch", active_branch_list)

    branch_inventory = df_inventory[df_inventory["branch"] == branch]["product_name"].tolist()
    daily_branch_df = daily_df[daily_df["branch"] == branch]

    booked_branch_items = set()
    for text in daily_branch_df['item_1'].fillna(''):
        booked_branch_items.update(extract_products(text, branch_inventory))

    available_branch_items = [
        i for i in branch_inventory if i not in booked_branch_items
    ]

    available_branch_items1 = get_available_by_branch(branch)

    item_1 = st.multiselect(
    "Item 1",
    available_branch_items1,
    placeholder="Choose available item"
    )


    
    
    harga_1 = st.number_input("Harga 1", value=float(row.get("harga_1", 0)))
    item_2 = st.text_input("Item 2", value=row.get("item_2", ""))
    harga_2 = st.number_input("Harga 2", value=float(row.get("harga_2", 0)))
    item_3 = st.text_input("Item 3", value=row.get("item_3", ""))
    harga_3 = st.number_input("Harga 3", value=float(row.get("harga_3", 0)))
    bil_jam = st.text_input("Durasi",value=row.get("bil_jam",""))
    subtotal = harga_1+harga_2+harga_3
    st.write(f"Subtotal: RM{subtotal:.2f}")
    
    tax = st.number_input("Tax (SST)", value=float(row.get("tax", 0)))
    total = subtotal + tax
            
    st.markdown("### 💰 Price Breakdown")
    
    st.write(f"Subtotal: RM{subtotal:.2f}")
    st.write(f"Tax (SST): RM{tax:.2f}")
    st.write(f"Total Amount: RM{total:.2f}")

    invoice_num = generate_invoice_number(df)
    st.write(f'Invoice Number For This Order : {invoice_num}')

    if st.button("🚀 Submit Confirmation"):
        if not proof or not link_location:
            st.error("Please upload payment proof and location link")
            return


        image_url = upload_to_cloudinary(
            proof,
            f"{row['quotation_num']}_{proof.name}"
        )

        client = get_client()

        ws1 = client.open_by_key(INVOICE_SHEET_ID).worksheet(SHEET_NAME)
        ws2 = client.open_by_key(GLIDE_SHEET_ID).worksheet(INVOICE_SHEET_NAME)

        cell = ws1.find(row["quotation_num"])
        sheet_row1 = cell.row

        # Update fields
        ws1.update_cell(sheet_row1, df.columns.get_loc("type_status") + 1, "Invoice")
        ws1.update_cell(sheet_row1, df.columns.get_loc("invoice_num") + 1, invoice_num)

        ws1.update_cell(sheet_row1, df.columns.get_loc("proof_attached") + 1, image_url)

        ws1.update_cell(sheet_row1, df.columns.get_loc("Tick") + 1, "")
        ws1.update_cell(sheet_row1, df.columns.get_loc("nama_pelanggan") + 1, nama_pelanggan)
        ws1.update_cell(sheet_row1, df.columns.get_loc("no_tel") + 1, no_tel)
        ws1.update_cell(sheet_row1, df.columns.get_loc("no_tin") + 1, no_tin)
        ws1.update_cell(sheet_row1, df.columns.get_loc("link_location") + 1, link_location)
        ws1.update_cell(sheet_row1, df.columns.get_loc("doc_date") + 1, doc_date)
        ws1.update_cell(sheet_row1, df.columns.get_loc("delivery_date") + 1, delivery_date.strftime("%Y-%m-%d"))
        ws1.update_cell(sheet_row1, df.columns.get_loc("item_1") + 1, item_1)
        ws1.update_cell(sheet_row1, df.columns.get_loc("item_2") + 1, item_2)
        ws1.update_cell(sheet_row1, df.columns.get_loc("item_3") + 1, item_3)
        ws1.update_cell(sheet_row1, df.columns.get_loc("harga_1") + 1, harga_1)
        ws1.update_cell(sheet_row1, df.columns.get_loc("harga_2") + 1, harga_2)
        ws1.update_cell(sheet_row1, df.columns.get_loc("harga_3") + 1, harga_3)
        ws1.update_cell(sheet_row1, df.columns.get_loc("subtotal") + 1, subtotal)
        ws1.update_cell(sheet_row1, df.columns.get_loc("tax") + 1, tax)
        ws1.update_cell(sheet_row1, df.columns.get_loc("total") + 1, total)
        ws1.update_cell(sheet_row1, df.columns.get_loc("nama_tempat") + 1, nama_tempat)
        ws1.update_cell(sheet_row1, df.columns.get_loc("bil_jam") + 1, bil_jam)


        cell2 = ws2.find(row["quotation_num"])
        sheet_row2 = cell2.row

        # Update fields
        ws2.update_cell(sheet_row2, df2.columns.get_loc("type_status") + 1, "Invoice")
        ws2.update_cell(sheet_row2, df2.columns.get_loc("invoice_num") + 1, invoice_num)

        ws2.update_cell(sheet_row2, df2.columns.get_loc("proof_attached") + 1, image_url)

        ws2.update_cell(sheet_row2, df2.columns.get_loc("Tick") + 1, "")
        ws2.update_cell(sheet_row2, df2.columns.get_loc("nama_pelanggan") + 1, nama_pelanggan)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("no_tel") + 1, no_tel)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("no_tin") + 1, no_tin)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("link_location") + 1, link_location)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("doc_date") + 1, doc_date)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("delivery_date") + 1, delivery_date.strftime("%Y-%m-%d"))
        ws2.update_cell(sheet_row2, df2.columns.get_loc("item_1") + 1, item_1)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("item_2") + 1, item_2)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("item_3") + 1, item_3)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("harga_1") + 1, harga_1)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("harga_2") + 1, harga_2)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("harga_3") + 1, harga_3)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("subtotal") + 1, subtotal)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("tax") + 1, tax)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("total") + 1, total)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("nama_tempat") + 1, nama_tempat)
        ws2.update_cell(sheet_row2, df2.columns.get_loc("bil_jam") + 1, bil_jam)

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
            st.markdown(f"### 🧾 {row['item_1']} - {row['branch']} ({row['delivery_date']})")
            st.write(f"**Total:** RM {float(row['total']):.2f}")
            
            if expired:
                st.error("❌ Expired")

        with col2:
            st.link_button("WhatsApp", row["wa_link"])
            if not expired:
                if st.button(
                    "Confirm",
                    key=f"confirm_btn_{row['quotation_num']}"
                ):
                    confirm_dialog(row)
                    










