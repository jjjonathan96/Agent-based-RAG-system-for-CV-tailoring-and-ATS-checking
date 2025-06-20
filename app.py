import streamlit as st
import openai
import pdfplumber
import datetime
import pymongo
from bson.objectid import ObjectId
from hashlib import sha256

from fpdf import FPDF
import tempfile
import re

import stripe
from dotenv import load_dotenv
import os
import base64

score, missing_keywords, tailored_cv, cover_letter = 0, '', '', ''

# --- Load environment variables ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
model=os.getenv("MODEL")
open_ai_key = os.getenv("OPENAI_API_KEY")
# --- Stripe Setup ---
stripe.api_key = STRIPE_SECRET_KEY

# --- MongoDB Setup ---
client = pymongo.MongoClient(MONGO_URI)
db = client["cv_tailoring"]
users_col = db["users"]
usage_col = db["usage"]

# --- Global Config ---
per_usage = 0.25  # 25p per tailored application

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.parsed_cv = None
    st.session_state.tailored_cv = ""
    st.session_state.cover_letter = ""
    st.session_state.page = "Login"

# --- Helper Functions ---

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def get_user_by_email(email):
    return users_col.find_one({"email": email})

def authenticate(email, password):
    user = get_user_by_email(email)
    if user and user["password"] == hash_password(password):
        return get_user_by_email(email)
    return None

def update_coin_balance(user_id, coins):
    users_col.update_one({"_id": ObjectId(user_id)}, {"$inc": {"coin_balance": coins}})

def get_coin_balance(user_id):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    return round(user.get("coin_balance", 0), 2)

def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text):
    prompt = f"""
You are an expert career assistant. Perform the following:
1. Compare the CV and Job Description and calculate a matching score (0-100).
2. List important keywords from the Job Description that are missing in the CV.
3. Rewrite the full CV to tailor it to the Job Description and only change in work experience; maximum three lines. Retain original Education and Contact sections.
4. Write a concise, ATS-optimized cover letter for the job.
Return format:
---
Matching Score: <number>
Missing Keywords:
- keyword1
Tailored CV:
<tailored>
Cover Letter:
<letter>
---
CV:
{cv_text}
Job Description:
{jd_text}
"""
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional CV and cover letter assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1
    )
    return response.choices[0].message.content
# --- Parse GPT Response ---
def parse_response(response_text):
    
    match_score = re.search(r"Matching Score:\s*(\d+)", response_text)
    score = int(match_score.group(1)) if match_score else None

    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = []
    if missing_kw_block:
        missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()]

    tailored_cv_block = re.search(r"Tailored CV:\s*(.*?)\nCover Letter:", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else ""

    cover_letter_block = re.search(r"Cover Letter:\s*(.*)", response_text, re.DOTALL)
    cover_letter_temp = cover_letter_block.group(1).strip() if cover_letter_block else ""
    cover_letter = " ".join(cover_letter_temp.split('?'))
    return score, missing_keywords, tailored_cv, cover_letter

# --- Improve Skills Section ---
def add_missing_keywords_to_skills(cv_text, missing_keywords):
    skills_section_pattern = re.compile(r"(Skills[:\n]+)(.*?)(\n\n|$)", re.DOTALL | re.IGNORECASE)

    def replacer(match):
        skills_header = match.group(1)
        skills_content = match.group(2).strip()
        current_skills = set(re.split(r",|\n", skills_content))
        updated_skills = current_skills.union(set(missing_keywords))
        return f"{skills_header}{', '.join(sorted(updated_skills))}\n\n"

    if skills_section_pattern.search(cv_text):
        return skills_section_pattern.sub(replacer, cv_text)
    else:
        return cv_text.strip() + "\n\nSkills:\n" + ", ".join(sorted(set(missing_keywords))) + "\n"
# clean unicode
def clean_text_for_pdf(text):
    replacements = {
        "—": "-",
        "–": "-",
        "“": "\"",
        "”": "\"",
        "’": "'",
        "•": "-",
        "…": "...",
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2003": " ",  # em space ← ADD THIS LINE
        "\u2002": " ",  # en space (optional)
        "\u2009":" ",
        "\u200a":" ",
        "\u2502":" ",
        "\u2010":" ",
        "\u00a0": " ",  # non-breaking space (optional)
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text


# --- Create PDF from Text ---
def convert_text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=11)
    line_height = pdf.font_size * 2
    text = clean_text_for_pdf(text)
    for line in text.split('\n'):
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, line_height, safe_line)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

def convert_text_to_pdf_one_page(text):
    pdf = FPDF(format='A4')
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=False)  # no page breaks

    pdf.set_font("Arial", size=10)
    line_height = pdf.font_size * 1.5
    max_height = 277  # approx usable height on A4 in mm (297 - margins)

    y_start = pdf.get_y()
    height_used = 0

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            # small vertical gap for empty lines
            height_used += line_height * 0.5
            if height_used > max_height:
                break
            pdf.ln(line_height * 0.5)
            continue

        # Detect section headings (simple heuristic: all uppercase or ends with ':')
        if line.isupper() or line.endswith(":"):
            pdf.set_font("Arial", "B", 10)
        else:
            pdf.set_font("Arial", size=10)

        # Estimate if this line fits
        if height_used + line_height > max_height:
            break

        # Write the line with wrapping
        pdf.multi_cell(0, line_height, line)
        height_used += line_height

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name
# --- Registration ---
def register():
    st.title("📝 Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")
    if st.button("Register"):
        if not email or not password:
            st.error("Please enter email and password.")
            return
        if get_user_by_email(email):
            st.error("Email already registered.")
        else:
            users_col.insert_one({
                "email": email,
                "password": hash_password(password),
                "plan": "free",
                "coin_balance": 0,
                "created": datetime.datetime.utcnow()
            })
            st.success("Registered successfully! You can now login.")
            st.session_state.page = "Login"
            st.rerun()

# --- Login ---
def login():
    st.title("🔐 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if not email or not password:
            st.error("Please enter email and password.")
            return
        user = authenticate(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.page = "CV Tailoring"
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

# --- Main App ---
def main_app():
    st.title("🤖 AI CV + Cover Letter Tailoring Tool")
    #openai.api_key = st.text_input("Enter your OpenAI API Key", type="password")
    openai.api_key = open_ai_key

    user_id = str(st.session_state.user["_id"])
    coin_balance = get_coin_balance(user_id)
    st.info(f"🪙 You have **{coin_balance:.2f} coins**")

    if coin_balance < per_usage:
        st.warning(f"You need at least {per_usage} coins to tailor a CV. Please buy more.")
        return

    # --- Session Setup ---
    if "parsed_cv" not in st.session_state:
        st.session_state["parsed_cv"] = None
    if "tailored_cv" not in st.session_state:
        st.session_state["tailored_cv"] = ""
    if "cover_letter" not in st.session_state:
        st.session_state["cover_letter"] = ""

# --- Upload CV ---
    if st.session_state["parsed_cv"] is None:
        cv_file = st.file_uploader("Upload CV (PDF)", type=["pdf"])
        if cv_file:
            st.session_state["parsed_cv"] = extract_text_from_pdf(cv_file)
            st.success("✅ CV extracted.")
    else:
        st.success("✅ CV already loaded.")
        if st.button("🔁 Reset CV"):
            st.session_state["parsed_cv"] = None
            st.session_state["tailored_cv"] = ""
            st.session_state["cover_letter"] = ""
            st.rerun()

    jd_input = st.text_area("Paste the Job Description here", height=400)

    if st.button("✨ Tailor My CV & Cover Letter") and st.session_state["parsed_cv"] and jd_input:
        with st.spinner("Processing with GPT..."):
            global score, missing_keywords, tailored_cv, cover_letter
            result = tailor_full_cv(st.session_state["parsed_cv"], jd_input)
            score, missing_keywords, tailored_cv, cover_letter = parse_response(result)
            tailored_cv = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

            st.session_state["tailored_cv"] = tailored_cv
            st.session_state["cover_letter"] = cover_letter
            update_coin_balance(user_id, -per_usage)

    
    # --- Show Results ---
    if st.session_state["tailored_cv"]:
        st.subheader("📊 Matching Score & Keyword Gap")
        st.write(f"**Score:** {score}/100")
        st.write(f"**Missing Keywords:** {', '.join(missing_keywords) if missing_keywords else 'None'}")

        st.subheader("📄 Tailored CV")
        st.text_area("Tailored CV Preview", value=st.session_state["tailored_cv"], height=500)
        #pdf_cv = convert_text_to_pdf(st.session_state["tailored_cv"])
        pdf_cv = convert_text_to_pdf_one_page(clean_text_for_pdf(st.session_state["tailored_cv"]))
        with open(pdf_cv, "rb") as f:
            st.download_button("⬇️ Download Tailored CV (PDF)", f.read(), file_name="tailored_cv.pdf", mime="application/pdf")

        st.subheader("✉️ Cover Letter")
        st.text_area("Cover Letter Preview", value=st.session_state["cover_letter"], height=400)
        pdf_cl = convert_text_to_pdf(st.session_state["cover_letter"])
        with open(pdf_cl, "rb") as f:
            st.download_button("⬇️ Download Cover Letter (PDF)", f.read(), file_name="cover_letter.pdf", mime="application/pdf")
    # --- Stripe Checkout ---
def create_coin_checkout_session(user_email, coin_amount, price_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        mode="payment",
        customer_email=user_email,
        success_url="https://yourdomain.com/success",  # Update to your actual domain
        cancel_url="https://yourdomain.com/cancel",
        metadata={"coin_amount": coin_amount, "user_email": user_email}
    )
    return session.url

# --- Subscription / Coins Page ---
def subscription_page():
    st.title("🪙 Coin Balance & Purchase")

    user = get_user_by_email(st.session_state.user["email"])
    coin_balance = user.get("coin_balance", 0)

    st.write(f"**Current Coin Balance:** {coin_balance:.2f} coins")
    st.write(f"Each tailored CV costs **{per_usage} coin ({int(per_usage*100)}p)**")

    coin_options = {
        "5 Coins (£5)": ("price_1RbAfbQRsS5klTttxZc43Adm", 5),
        "10 Coins (£10)": ("price_1RbAgMQRsS5klTttVwsvybig", 10),
        "20 Coins (£20)": ("price_1RbAhMQRsS5klTttcdhVKVrL", 20)
    }

    selected = st.selectbox("Select Coin Package", list(coin_options.keys()))

    if st.button("Buy Coins"):
        price_id, coins = coin_options[selected]
        checkout_url = create_coin_checkout_session(user["email"], coins, price_id)
        st.markdown(f"[Click here to pay and receive {coins} coins]({checkout_url})", unsafe_allow_html=True)

# --- Logout ---
def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.parsed_cv = None
    st.session_state.tailored_cv = ""
    st.session_state.cover_letter = ""
    st.session_state.page = "Login"
    st.rerun()

# --- Page Router ---
def app_router():
    if st.session_state.logged_in:
        page = st.sidebar.selectbox("Select Page", ["CV Tailoring", "Subscription", "Logout"])
    else:
        page = st.sidebar.selectbox("Select Page", ["Login", "Register"])

    st.session_state.page = page

    if not st.session_state.logged_in:
        if page == "Login":
            login()
        elif page == "Register":
            register()
    else:
        if page == "CV Tailoring":
            main_app()
        elif page == "Subscription":
            subscription_page()
        elif page == "Logout":
            logout()

# --- Run App ---
app_router()
