import streamlit as st
import openai
import pdfplumber
import tempfile
import re
from pdfdocument.document import PDFDocument

# Streamlit UI
st.set_page_config(page_title="AI CV Tailoring", layout="wide")
st.title("\U0001F916 AI CV Tailoring Tool")

# Set OpenAI API key
openai.api_key = st.text_input("Enter your OpenAI API Key", type="password")

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        texts = [page.extract_text() for page in pdf.pages if page.extract_text()]
        return "\n".join(texts)

# Function to tailor full CV and extract ATS insights
@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text):
    prompt = f"""
You are an expert career assistant. Perform the following:
1. Compare the CV and Job Description and calculate a matching score (0-100) based on ATS relevance.
2. List important keywords from the Job Description missing in the CV.
3. Rewrite the full CV to tailor it to the Job Description while preserving its structure, tone, and formatting.

Return the response in this format:
---
Matching Score: <number>

Missing Keywords:
- keyword1
- keyword2
...

Tailored CV:
<full tailored CV>
---

CV:
{cv_text}

Job Description:
{jd_text}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful and professional career assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

def parse_response(response_text):
    match_score = re.search(r"Matching Score:\s*(\d+)", response_text)
    score = int(match_score.group(1)) if match_score else None

    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = []
    if missing_kw_block:
        missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()]

    tailored_cv_block = re.search(r"Tailored CV:\s*(.*)", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else response_text

    return score, missing_keywords, tailored_cv

def add_missing_keywords_to_skills(cv_text, missing_keywords):
    skills_section_pattern = re.compile(r"(Skills[:\n]+)(.*?)(\n\n|$)", re.DOTALL | re.IGNORECASE)

    def replacer(match):
        skills_header = match.group(1)
        skills_content = match.group(2).strip()

        current_skills = set(s.strip() for s in re.split(r",|\n", skills_content) if s.strip())
        updated_skills = current_skills.union(set(missing_keywords))

        new_skills_text = ", ".join(sorted(updated_skills))
        return f"{skills_header}{new_skills_text}\n\n"

    if skills_section_pattern.search(cv_text):
        return skills_section_pattern.sub(replacer, cv_text)
    else:
        return cv_text.strip() + "\n\nSkills:\n" + ", ".join(sorted(set(missing_keywords))) + "\n"

# Improved PDF conversion with spacing after headings and paragraphs
def convert_text_to_pdf(text):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = PDFDocument(temp_pdf.name)
    pdf.init_report()

    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Add paragraph for every line (avoid empty lines)
        pdf.p(stripped if stripped else " ")

        # Add extra space after headings (assumed uppercase lines)
        if stripped.isupper() and stripped != "":
            pdf.p("")  # add blank paragraph for spacing
            pdf.p("")
        # Add extra space after bullet points if next line is empty or heading
        if stripped.startswith("•"):
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line == "" or next_line.isupper():
                    pdf.p("")

    pdf.generate()
    return temp_pdf.name

# Initialize session state for CV text
if "parsed_cv" not in st.session_state:
    st.session_state["parsed_cv"] = None

# Upload CV only if not loaded yet
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

# Job Description input
jd_input = st.text_area("Paste the Job Description here")
tailor_button = st.button("Tailor My Full CV")

# Process tailoring request
if tailor_button and st.session_state["parsed_cv"] and jd_input:
    with st.spinner("Processing..."):
        result = tailor_full_cv(st.session_state["parsed_cv"], jd_input)
        score, missing_keywords, tailored_cv = parse_response(result)
        tailored_cv_with_skills = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

        st.subheader("\U0001F4CA Matching Score and Tailored Full CV with Missing Keywords added to Skills")
        st.write(f"**Matching Score:** {score}")
        st.write(f"**Missing Keywords added to Skills:** {', '.join(missing_keywords) if missing_keywords else 'None'}")
        st.text_area("Tailored CV", value=tailored_cv_with_skills, height=900)

        pdf_path = convert_text_to_pdf(tailored_cv_with_skills)
        with open(pdf_path, "rb") as f:
            st.download_button("Download Tailored CV as PDF", f, file_name="tailored_cv.pdf")
else:
    st.info("Upload your CV and paste a job description to begin.")
