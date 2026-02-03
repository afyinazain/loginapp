import hashlib
import pandas as pd
import streamlit as st

USER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mPk6ebxFF9HnRfcpYNOtb07VeBD-4eSe1rkc-jxLcmU/export?format=csv&gid=2102286431"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def load_users():
    return pd.read_csv(USER_SHEET_URL)

def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)

    match = users[
        (users["username"] == username) &
        (users["password_hash"] == hashed)
    ]

    if not match.empty:
        return match.iloc[0].to_dict()

    return None

from utils.sheets import get_gsheet
from utils.hashing import verify_password

def login(email, password):
    ws = get_gsheet("users")
    users = ws.get_all_records()

    for u in users:
        if u["email"] == email and u["status"] == "active":
            if verify_password(password, u["password_hash"]):
                st.session_state.user = u
                return True
    return False

def require_login():
    if "user" not in st.session_state:
        st.switch_page("pages/_Login.py")


