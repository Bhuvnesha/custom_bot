import streamlit as st
from auth import create_user, verify_user

# ---------- Login / Signup Page ----------
def login_signup_page():
    st.title("🔑 User Login")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = verify_user(username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"Welcome back, {username} 👋")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Sign Up")
        new_user = st.text_input("New Username", key="signup_user")
        new_pass = st.text_input("New Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            if create_user(new_user, new_pass):
                st.success("✅ Account created! Please login.")
            else:
                st.error("⚠️ Username already exists")
