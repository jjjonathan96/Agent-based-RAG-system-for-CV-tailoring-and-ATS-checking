import streamlit as st
import openai
import pdfplumber
import datetime
import pymongo
from bson.objectid import ObjectId
from hashlib import sha256
import re
import stripe
from dotenv import load_dotenv
import os


load_dotenv()


# --- Stripe Setup ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# --- MongoDB Setup ---
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client["cv_tailoring"]
users_col = db["users"]
usage_col = db["usage"]

per_usage = 0.25

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
    return user.get("coin_balance", 0)

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
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional CV and cover letter assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1
    )
    return response.choices[0].message.content

def parse_response(response_text):
    match_score = re.search(r"Matching Score:\s*(\d+)", response_text)
    score = int(match_score.group(1)) if match_score else None
    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()] if missing_kw_block else []
    tailored_cv_block = re.search(r"Tailored CV:\s*(.*?)\nCover Letter:", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else ""
    cover_letter_block = re.search(r"Cover Letter:\s*(.*)", response_text, re.DOTALL)
    cover_letter = cover_letter_block.group(1).strip() if cover_letter_block else ""
    return score, missing_keywords, tailored_cv, cover_letter

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
    openai.api_key = st.text_input("Enter your OpenAI API Key", type="password")

    user_id = str(st.session_state.user["_id"])
    coin_balance = get_coin_balance(user_id)
    st.info(f"🪙 You have **{coin_balance} coins**")

    if coin_balance <= 0:
        st.warning("You have no coins left. Please purchase more to continue.")
        return

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
            result = tailor_full_cv(st.session_state["parsed_cv"], jd_input)
            score, missing_keywords, tailored_cv, cover_letter = parse_response(result)
            st.session_state["tailored_cv"] = tailored_cv
            st.session_state["cover_letter"] = cover_letter
            update_coin_balance(user_id, -per_usage)

    if st.session_state["tailored_cv"]:
        st.subheader("📊 Matching Score & Keyword Gap")
        st.write(f"**Score:** {score}/100")
        st.write(f"**Missing Keywords:** {', '.join(missing_keywords) if missing_keywords else 'None'}")

        st.subheader("📄 Tailored CV")
        st.text_area("Tailored CV Preview", value=st.session_state["tailored_cv"], height=500)

        st.subheader("✉️ Cover Letter")
        st.text_area("Cover Letter Preview", value=st.session_state["cover_letter"], height=400)

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
        success_url="https://yourdomain.com/success",  # Update these URLs
        cancel_url="https://yourdomain.com/cancel",
        metadata={"coin_amount": coin_amount, "user_email": user_email}
    )
    return session.url

# --- Subscription / Coins Page ---
def subscription_page():
    st.title("🪙 Coin Balance & Purchase")

    user = get_user_by_email(st.session_state.user["email"])
    coin_balance = user.get("coin_balance", 0)

    st.write(f"**Current Coin Balance:** {coin_balance} coins")
    st.write(f"Each tailored CV costs **{per_usage} coin ({per_usage}p)**")

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
