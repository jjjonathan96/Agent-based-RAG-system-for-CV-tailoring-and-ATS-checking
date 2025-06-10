import streamlit as st
import openai
import pdfplumber
from fpdf import FPDF
import tempfile
import re
import difflib
import requests
from bs4 import BeautifulSoup

# --- Helper functions ---

def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        texts = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)

def get_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
        return text
    except Exception as e:
        return f"Error fetching or parsing URL: {e}"

@st.cache_data(show_spinner=False)
def tailor_full_cv(cv_text, jd_text, temperature):
    prompt = f"""
You are an expert ATS CV tailoring assistant. Perform the following:
1. Compare the CV and Job Description and calculate a matching score (0-100) based on ATS relevance.
2. Compare the CV how ATS friendly score (0-100).
3. List important keywords from the Job Description missing in the CV.
4. Tailor the CV by changing 2-3 lines in work experience and projects to better match the Job Description, preserving structure, tone, and formatting. Use STAR method for experience changes and make tailored experience come first, then original.
5. Write a one-page cover letter starting clearly with 'Cover Letter:'.

Return the response in this format:
---
Matching Score: <number>

Missing Keywords:
- keyword1
- keyword2
...

Tailored CV:
<full tailored CV>

Cover Letter:
<cover letter text>
---
CV:
""" + cv_text + """

Job Description:
""" + jd_text + """
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful and professional career assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content

def parse_response(response_text):
    match_score = re.search(r"Matching Score:\s*(\d+)", response_text)
    score = int(match_score.group(1)) if match_score else None

    missing_kw_block = re.search(r"Missing Keywords:\s*((?:- .*\n)+)", response_text)
    missing_keywords = []
    if missing_kw_block:
        missing_keywords = [line.strip("- ").strip() for line in missing_kw_block.group(1).splitlines()]

    tailored_cv_block = re.search(r"Tailored CV:\s*(.*?)Cover Letter:", response_text, re.DOTALL)
    tailored_cv = tailored_cv_block.group(1).strip() if tailored_cv_block else ""

    cover_letter_block = re.search(r"Cover Letter:\s*(.*)", response_text, re.DOTALL)
    cover_letter = cover_letter_block.group(1).strip() if cover_letter_block else ""

    return score, missing_keywords, tailored_cv, cover_letter

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

def generate_diff_html(original, tailored):
    original_lines = original.strip().splitlines()
    tailored_lines = tailored.strip().splitlines()
    diff = difflib.ndiff(original_lines, tailored_lines)
    html_diff = ""
    for line in diff:
        if line.startswith("- "):
            html_diff += f"<div style='background-color:#ffe6e6;'>❌ {line[2:]}</div>"
        elif line.startswith("+ "):
            html_diff += f"<div style='background-color:#e6ffe6;'>✅ {line[2:]}</div>"
        elif line.startswith("  "):
            html_diff += f"<div style='color:#666;'>{line[2:]}</div>"
    return html_diff
