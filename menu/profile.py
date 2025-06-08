# profile_helper.py

import streamlit as st
import pdfplumber
import re
from .db import *

COUNTRIES = [
    "United Kingdom", "United States", "Canada", "India", "Germany",
    "France", "Australia", "Netherlands", "Singapore", "United Arab Emirates"
]

# --- Extract basic info from CV text
def extract_profile_info(text):
    name = text.split('\n')[0].strip()
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone = re.search(r"\+?\d[\d \-\(\)]{7,}", text)
    linkedin = re.search(r"(https?://)?(www\.)?linkedin\.com/[^\s]+", text)
    github = re.search(r"(https?://)?(www\.)?github\.com/[^\s]+", text)

    return {
        "name": name,
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "linkedin": linkedin.group(0) if linkedin else "",
        "github": github.group(0) if github else ""
    }

def show_profile_tab():
    st.header("0. Profile Setup")

    init_profile_db()
    db_data = load_profile_from_db()

    uploaded_cv = st.file_uploader("Upload Your CV (PDF only)", type="pdf")
    extracted = {"name": "", "email": "", "phone": "", "linkedin": "", "github": ""}
    if uploaded_cv:
        with pdfplumber.open(uploaded_cv) as pdf:
            text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        extracted = extract_profile_info(text)
        st.success("Extracted details from CV")

    name = st.text_input("Full Name", value=extracted["name"] or db_data.get("name", ""))
    email = st.text_input("Email", value=extracted["email"] or db_data.get("email", ""))
    phone = st.text_input("Phone Number", value=extracted["phone"] or db_data.get("phone", ""))
    linkedin = st.text_input("LinkedIn URL", value=extracted["linkedin"] or db_data.get("linkedin", ""))
    github = st.text_input("GitHub URL", value=extracted["github"] or db_data.get("github", ""))
    country = st.selectbox("Country", COUNTRIES, index=COUNTRIES.index(db_data.get("country", "United Kingdom")))

    if st.button("Save Profile"):
        save_profile_to_db(name, email, phone, linkedin, github, country)
        st.success("✅ Profile saved to database")

    return {
        "name": name, "email": email, "phone": phone,
        "linkedin": linkedin, "github": github, "country": country
    }
