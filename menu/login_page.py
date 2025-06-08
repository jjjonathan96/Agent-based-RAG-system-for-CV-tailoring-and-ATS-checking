import streamlit as st
from .auth_helper import create_users_table, register_user, verify_user

def login_screen():
    st.title("🔐 Login to AI Job Assistant")
    create_users_table()

    menu = ["Login", "Signup"]
    choice = st.selectbox("Choose action", menu)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Welcome " + username)
            else:
                st.error("Invalid username or password")

    elif choice == "Signup":
        if st.button("Create Account"):
            if register_user(username, password):
                st.success("Account created! You can now log in.")
            else:
                st.warning("Username already exists.")
