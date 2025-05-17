import streamlit as st
import pdfplumber
from fpdf import FPDF
import tempfile
import re

from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from transformers import pipeline


# Streamlit UI
st.set_page_config(page_title="AI CV Tailoring with Local LLM", layout="wide")
st.title("\U0001F916 AI CV Tailoring Tool using Local LLM")


# Load local LLM model once and cache it for speed
@st.cache_resource(show_spinner=True)
def load_local_llm():
    # Replace with your local model path or HF model name
    pipe = pipeline(
        "text-generation",
        model="decapoda-research/llama-7b-hf",  # or another compatible model you have
        max_length=1024,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.15,
        device=-1  # set to -1 for CPU, 0+ for GPU device index
    )
    llm = HuggingFacePipeline(pipeline=pipe)
    return llm

llm = load_local_llm()


# Prompt template for tailoring CV
prompt_template = """
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

prompt = PromptTemplate(
    input_variables=["cv_text", "jd_text"],
    template=prompt_template
)

chain = LLMChain(llm=llm, prompt=prompt)


# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())


# Call the local LLM chain
@st.cache_data(show_spinner=True)
def tailor_full_cv(cv_text, jd_text):
    return chain.run(cv_text=cv_text, jd_text=jd_text)


# Parse the LLM response to get score, keywords, and tailored CV
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


# Add missing keywords to the skills section of the CV
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


# Convert text to PDF
def convert_text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        # Replace unsupported characters
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, safe_line)
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name


# Session state for CV text
if "parsed_cv" not in st.session_state:
    st.session_state["parsed_cv"] = None

if st.session_state["parsed_cv"] is None:
    cv_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if cv_file:
        with st.spinner("Extracting text from your CV..."):
            st.session_state["parsed_cv"] = extract_text_from_pdf(cv_file)
            st.success("CV loaded and saved in memory.")
else:
    st.success("✅ CV is loaded.")
    if st.button("🔁 Reset CV"):
        st.session_state["parsed_cv"] = None
        st.experimental_rerun()

jd_input = st.text_area("Paste the Job Description here")
tailor_button = st.button("Tailor My Full CV")

if tailor_button and st.session_state["parsed_cv"] and jd_input:
    with st.spinner("Tailoring your CV..."):
        response = tailor_full_cv(st.session_state["parsed_cv"], jd_input)
        score, missing_keywords, tailored_cv = parse_response(response)
        tailored_cv_with_skills = add_missing_keywords_to_skills(tailored_cv, missing_keywords)

        st.subheader("\U0001F4CA Matching Score and Tailored CV")
        st.write(f"**Matching Score:** {score}")
        st.write(f"**Missing Keywords added to Skills:** {', '.join(missing_keywords) if missing_keywords else 'None'}")
        st.text_area("Tailored CV", value=tailored_cv_with_skills, height=900)

        pdf_path = convert_text_to_pdf(tailored_cv_with_skills)
        with open(pdf_path, "rb") as f:
            st.download_button("Download Tailored CV as PDF", f, file_name="tailored_cv.pdf")
else:
    st.info("Upload your CV and paste a job description to start tailoring.")

