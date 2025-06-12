import streamlit as st
import openai
import pdfplumber
import tempfile
import re
from fpdf import FPDF
import unicodedata

# --- Streamlit Setup ---
st.set_page_config(page_title="One-Page AI CV Tailor", layout="wide")
st.title("📄 One-Page A4 AI CV Tailor")

openai.api_key = st.text_input("Enter OpenAI API Key", type="password")

# --- Extract Text ---
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())

# --- Clean Unicode ---
def clean_text(text):
    text = unicodedata.normalize("NFKD", text)
    return text.translate(str.maketrans({
        "•": "-", "–": "-", "—": "-", "“": "\"", "”": "\"", "’": "'", "…": "...",
    }))

# --- Trim to 1 A4 Page Approx. ---
def limit_text_to_lines(text, max_lines=75):
    lines = text.splitlines()
    return "\n".join(lines[:max_lines])

# --- Generate PDF ---
def convert_text_to_pdf(text):
    text = clean_text(text)
    text = limit_text_to_lines(text)  # ensure it fits A4

    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_font("Helvetica", size=10)

    height_used = 0
    max_height = 277  # max usable height on A4 in mm

    for line in text.split('\n'):
        line = line.strip()
        if line:
            h = 5
            if height_used + h > max_height:
                break
            pdf.multi_cell(0, h, line)
            height_used += h
        else:
            pdf.ln(3)
            height_used += 3

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

# --- Tailor CV ---
@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text):
    prompt = f"""
You are an expert CV writer. Tailor this CV to the Job Description.
Preserve tone and structure, but make it concise and ATS-optimized.
Ensure it fits **one A4 page**.

Return ONLY the tailored CV (no explanation).

CV:
{cv_text}

Job Description:
{jd_text}
"""
    response = openai.ChatCompletion.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": "You are a helpful career assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=1
    )
    return response.choices[0].message.content.strip()

# --- Streamlit Logic ---
if "cv_text" not in st.session_state:
    st.session_state["cv_text"] = None

if st.session_state["cv_text"] is None:
    uploaded_cv = st.file_uploader("Upload Your CV (PDF)", type=["pdf"])
    if uploaded_cv:
        with st.spinner("Extracting CV..."):
            st.session_state["cv_text"] = extract_text_from_pdf(uploaded_cv)
            st.success("✅ CV loaded.")
else:
    st.success("CV loaded.")
    if st.button("🔄 Reset CV"):
        st.session_state["cv_text"] = None
        st.experimental_rerun()

jd_input = st.text_area("Paste Job Description Below:")

if st.button("✂️ Tailor CV to One Page") and st.session_state["cv_text"] and jd_input:
    with st.spinner("Generating one-page CV..."):
        tailored_cv = tailor_full_cv(st.session_state["cv_text"], jd_input)
        pdf_path = convert_text_to_pdf(tailored_cv)

        st.subheader("📄 Tailored One-Page CV")
        st.text_area("Preview", tailored_cv, height=600)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download A4 PDF", f, file_name="tailored_cv_a4.pdf")
else:
    st.info("Upload a CV and paste job description to begin.")
