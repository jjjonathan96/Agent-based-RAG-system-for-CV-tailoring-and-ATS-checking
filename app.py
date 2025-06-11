import streamlit as st
import openai
import pdfplumber
from fpdf import FPDF
import tempfile
import re

# Streamlit UI setup
st.set_page_config(page_title="AI CV Tailoring", layout="wide")
st.title("🤖 AI CV Tailoring Tool")

# OpenAI API Key input
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")
if openai_api_key:
    openai.api_key = openai_api_key

# Extract text from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

# Tailoring function
@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text):
    prompt = f"""
You are an expert career assistant. Perform the following tasks:
1. From the job description, extract:
   - Role
   - Requirements
   - Visa Status
   - Salary
   - Location
   - About Company
2. Compare the CV and Job Description and calculate a matching score (0–100) based on ATS relevance.
3. List important keywords from the job description missing in the CV.
4. Rewrite the full CV tailored to the job description. Only modify the two work experience entries by adding 2–3 lines each.
5. Write a one-page cover letter.

Return in this exact format:
---
Extract Job description:
- Role: ...
- Requirements: ...
- Visa Status: ...
- Salary: ...
- Location: ...
- About Company: ...

Matching Score: <number>

Missing Keywords:
- keyword1
- keyword2
...

Tailored CV:
<your tailored CV>

Cover Letter:
<your cover letter>
---
CV:
{cv_text}

Job Description:
{jd_text.strip()}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful and professional career assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# Response parsing
def parse_response(response_text):
    score = int(re.search(r"Matching Score:\s*(\d+)", response_text).group(1)) if "Matching Score:" in response_text else None

    job_description_block = re.search(r"Extract Job description:\s*(.*?)Matching Score:", response_text, re.DOTALL)
    job_description = job_description_block.group(1).strip() if job_description_block else ""

    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()] if missing_kw_block else []

    tailored_cv_block = re.search(r"Tailored CV:\s*(.*?)Cover Letter:", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else ""

    cover_letter_block = re.search(r"Cover Letter:\s*(.*)", response_text, re.DOTALL)
    cover_letter = cover_letter_block.group(1).strip() if cover_letter_block else ""

    return score, missing_keywords, tailored_cv, cover_letter, job_description

# Add missing keywords to skills section
def add_missing_keywords_to_skills(cv_text, missing_keywords):
    pattern = re.compile(r"(Skills[:\n]+)(.*?)(\n\n|$)", re.DOTALL | re.IGNORECASE)

    def replacer(match):
        header = match.group(1)
        content = match.group(2).strip()
        current = set(re.split(r",|\n", content))
        updated = current.union(missing_keywords)
        return f"{header}{', '.join(sorted(updated))}\n\n"

    if pattern.search(cv_text):
        return pattern.sub(replacer, cv_text)
    else:
        return cv_text.strip() + "\n\nSkills:\n" + ", ".join(sorted(set(missing_keywords))) + "\n"

# Convert text to downloadable PDF
def convert_text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=12)
    line_height = pdf.font_size * 2

    for line in text.split('\n'):
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, line_height, safe_line)

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name

# CV memory management
if "parsed_cv" not in st.session_state:
    st.session_state["parsed_cv"] = None

# Upload and store CV
if st.session_state["parsed_cv"] is None:
    cv_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if cv_file:
        with st.spinner("Reading your CV..."):
            st.session_state["parsed_cv"] = extract_text_from_pdf(cv_file)
            st.success("CV loaded and saved in memory.")
else:
    st.success("✅ CV is already loaded.")
    if st.button("🔁 Reset CV"):
        st.session_state["parsed_cv"] = None
        st.experimental_rerun()

# Job description input
jd_input = st.text_area("Paste the Job Description here")
tailor_button = st.button("Tailor My Full CV")

# Tailor and display results
if tailor_button and st.session_state["parsed_cv"] and jd_input and openai_api_key:
    with st.spinner("Processing..."):
        try:
            result = tailor_full_cv(st.session_state["parsed_cv"], jd_input)

            # DEBUG: Show raw model response
            # st.subheader("🔍 Raw OpenAI Response")
            # st.text_area("Model Output", value=result, height=300)

            score, missing_keywords, tailored_cv, cover_letter, job_description = parse_response(result)
            tailored_cv_with_skills = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

            st.subheader("📊 Matching Score & Tailored CV")
            st.markdown(f"**Matching Score:** {score}")
            st.markdown(f"**Missing Keywords added to Skills:** {', '.join(missing_keywords) if missing_keywords else 'None'}")

            st.subheader("📄 Job")
            st.text_area("Job", value=job_description, height=300)

            st.subheader("📄 Tailored CV")
            st.text_area("Tailored CV", value=tailored_cv_with_skills, height=400)

            st.subheader("📨 Cover Letter")
            st.text_area("Cover Letter", value=cover_letter, height=400)

            pdf_path = convert_text_to_pdf(tailored_cv_with_skills)
            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download Tailored CV as PDF", f, file_name="tailored_cv.pdf")

        except Exception as e:
            st.error(f"❌ Error: {e}")
else:
    st.info("Upload your CV, enter your OpenAI API key, and paste a job description to begin.")
