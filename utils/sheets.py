import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import timedelta, datetime, date
import re

import os
import json

# Google Service Account
google_creds = {
    "type": "service_account",
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
}


# -----------------------------
# SCOPES for Google Sheets & Drive
# -----------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# -----------------------------
# Helper function: authorize client
# -----------------------------

def get_client():
    """
    Returns a gspread client authorized via Railway environment variables.
    """
    # Reconstruct the service account JSON from environment variables
    service_account_info = {
        "type": "service_account",
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID", ""),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL", "")
    }

    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client
    
# -----------------------------
# Append a row to a sheet
# -----------------------------

def append_row_by_header(sheet_id: str, sheet_name: str, data: dict, header_row: int = 1):
    """
    Append a row to a Google Sheet tab.
    
    Args:
        sheet_id (str): The Google Sheet ID
        sheet_name (str): Tab name in the spreadsheet
        row (list): List of values to append
    """
    client = get_client()
    ws = client.open_by_key(sheet_id).worksheet(sheet_name)

    headers = ws.row_values(header_row)

    # Initialize row with empty strings
    row = [""]*len(headers)

    

    for key, value in data.items():
        if key in headers:
            idx = headers.index(key)
            # Convert date or other non-string values to string
            if isinstance(value, (datetime, date)):
                value = value.strftime("%Y-%m-%d")
            row[idx] = value
        else:
            print(f"Warning: '{key}' not found in sheet headers.")

    ws.append_row(row, value_input_option="USER_ENTERED")

# -----------------------------
# Read all rows from a sheet
# -----------------------------

@st.cache_data(ttl=10)  # cache for 10 seconds
def read_sheet(sheet_id: str, sheet_name: str, header_row: int = 1):
    client = get_client()
    ws = client.open_by_key(sheet_id).worksheet(sheet_name)

    values = ws.get_all_values()

    headers = values[header_row - 1]
    data_rows = values[header_row:]

    clean_headers = []
    for i, h in enumerate(headers):
        if h.strip() == "":
            clean_headers.append(f"_col_{i}")  # dummy column name
        else:
            clean_headers.append(h)

    records = []
    for row in data_rows:
        record = dict(zip(clean_headers, row))
        records.append(record)

    return records


from datetime import datetime

def generate_quotation_number(sheet_id, sheet_name="OrderList", prefix="Q-"):
    # 1️⃣ Get current year and month
    now = datetime.now()
    year = now.strftime("%y")    # last 2 digits
    month = now.strftime("%m")   # 2-digit month
    base = f"{prefix}{year}{month}"  # e.g., "Q-2601"

    # 2️⃣ Read existing quotation numbers
    data = read_sheet(sheet_id, sheet_name)  # your read_sheet function returns list of dict
    running_numbers = []

    for row in data:
        qnum = row.get("quotation_num", "")  # make sure your column is named ""
        if qnum.startswith(base):
            # extract last 3 digits
            running_numbers.append(int(qnum[-3:]))

    # 3️⃣ Determine next running number
    if running_numbers:
        next_run = max(running_numbers) + 1
    else:
        next_run = 1

    # 4️⃣ Format 3-digit running number
    run_str = f"{next_run:03d}"

    # 5️⃣ Final quotation number
    return f"{base}{run_str}"

from datetime import datetime
import pandas as pd



def generate_invoice_number1() -> str:


    SHEET_ID = "1qw_0cW4ipW5eYh1_sqUyvZdIcjmYXLcsS4J6Y4NoU6A"
    SHEET_NAME = "InvoiceList"

    today = datetime.today()
    prefix = "R"
    yy = today.strftime("%y")
    mm = today.strftime("%m")

    base = f"{prefix}-{yy}{mm}"  # R-2601

    all_orders = read_sheet(
        sheet_id=SHEET_ID,
        sheet_name=SHEET_NAME,
        header_row=1
    )

    df = pd.DataFrame(all_orders)

    if "invoice_num" not in df.columns:
        return f"{base}001"

    # 🔒 Clean data
    df = df[df["invoice_num"].notna()]
    df = df[df["invoice_num"].str.startswith(base)]

    if df.empty:
        next_run = 1
    else:
        # 🔑 Extract last 3 digits safely
        df["run"] = df["invoice_num"].str[-3:].astype(int)
        next_run = df["run"].max() + 1

    return f"{base}{next_run:03d}"

#----test----




def generate_invoice_number(df):
    INVOICE_COL = "invoice_num"
    now = datetime.now()
    yy = now.strftime("%y")   # e.g. 25
    mm = now.strftime("%m")   # e.g. 09

    pattern = rf"^R-{yy}{mm}(\d{{3}})$"

    running_numbers = []

    for inv in df[INVOICE_COL].dropna():
        inv = str(inv).strip()
        match = re.match(pattern, inv)
        if match:
            running_numbers.append(int(match.group(1)))

    next_running = max(running_numbers) + 1 if running_numbers else 1

    return f"R-{yy}{mm}{next_running:03d}"

# ------------------------------------------------
import cloudinary
import cloudinary.uploader

# Cloudinary
cloudinary_config = {
    "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "api_key": os.getenv("CLOUDINARY_API_KEY"),
    "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
}


def upload_to_cloudinary(file, file_name):
    result = cloudinary.uploader.upload(
        file,
        public_id=file_name,
        folder="deposit_proofs"
    )
    return result["secure_url"]

