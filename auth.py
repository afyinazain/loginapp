import streamlit as st
import hashlib
import pandas as pd


USER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mPk6ebxFF9HnRfcpYNOtb07VeBD-4eSe1rkc-jxLcmU/export?format=csv&gid=2102286431"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    return pd.read_csv(USER_SHEET_URL)


def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)

    match = users[
        (users["username"] == username)
        & (users["password_hash"] == hashed) 
        & (users["status"] == "active")
    ]

    if not match.empty:
        return match.iloc[0].to_dict()

    return None


def require_login():
    if "user" not in st.session_state:
        st.switch_page("pages/_Login.py")

