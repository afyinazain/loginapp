
import streamlit as st

# Check if user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("❌ You must log in first to access this page.")
    st.stop()  # stops the rest of the page from running

# Check if user is admin
if st.session_state.user.get("role") != "admin":
    st.error("🚫 You do not have permission to access this page.")
    st.stop()


st.title("🎈 Admin Dashboard")