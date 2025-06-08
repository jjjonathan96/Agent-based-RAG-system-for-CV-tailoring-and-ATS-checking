# AI Job Assistant Agent - Starter Template

# Structure:
# 1. RAG-based CV Tailoring
# 2. Cover Letter Writing
# 3. Job Searching
# 4. Interview Q&A Generator
# 5. ATS Checker
# 6. Job Alert Notifier
# 7. Application Tracker

import streamlit as st
import sqlite3
from pathlib import Path
import streamlit.components.v1 as components

from menu.login_page import login_screen
from menu.profile import show_profile_tab


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()


# === Setup ===
st.set_page_config(page_title="AI Job Assistant", layout="wide")
st.title("\U0001F916 AI Job Assistant Agent")


# === Top Tab Navigation ===
tabs = st.tabs([
                "Job Search",
                "Recommended Jobs",
                "Match Job Score",
                "RAG Cv tailoring",
                "Cover Letter",
                "Interview Q&A Generator",
                "ATS Checker",
                "Job Alerts",
                "Application Tracker",
                "Chat",
                "Profile"])

# === Database for Application Tracking ===
def init_db():
    conn = sqlite3.connect("applications.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company TEXT, role TEXT, date_applied TEXT,
                  status TEXT, interview_date TEXT, notes TEXT)''')
    conn.commit()
    conn.close()

init_db()

# === Feature Pages ===
with tabs[0]:
    st.header("1. Job Search")
    varFiltersCg = []  # Placeholder for filters logic, keyword extraction etc.
    # Upload CV & JD
    # Extract keywords & match
    # RAG agent logic here

with tabs[1]:
    st.header("2. Recommended Jobs")

with tabs[2]:
    st.header("3. Match job score")

with tabs[3]:
    st.header("4. RAG Cv tailoring")
    # Use tailored CV + JD to generate cover letter

with tabs[4]:
    st.header("5.Cover Letter ")
    # Scrape or use job APIs
    # Filter + keyword search

with tabs[5]:
    st.header("6. Interview Q&A Generator")
    # Input: Tailored CV + JD
    # Output: Q&A pairs from LLM

with tabs[6]:
    st.header("7. ATS Checker")
    # Highlight keyword matches/mismatches
    # Display ATS match score

with tabs[7]:
    st.header("8. Job Alert Notifier")
    # Email or WhatsApp integration using Twilio / SMTP
    # Schedule daily alert with matched jobs

with tabs[8]:
    st.header("9. Application Tracker")

with tabs[9]:
    st.header("10. Chat")

with tabs[10]:
    st.header("11. Profile")
    show_profile_tab()
   
