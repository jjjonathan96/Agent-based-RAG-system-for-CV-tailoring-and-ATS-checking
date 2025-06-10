import pdfplumber, tempfile, re, difflib, requests
from fpdf import FPDF
from bs4 import BeautifulSoup
import openai
import streamlit as st

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
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        return "\n\n".join(p.get_text(strip=True) for p in soup.find_all('p'))
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
        temperature=temperature,
    )
    return response.choices[0].message.content

def parse_response(response_text):
    score = int(re.search(r"Matching Score:\s*(\d+)", response_text).group(1))
    keywords = re.findall(r"- (.+)", re.search(r"Missing Keywords:(.*?)Tailored CV:", response_text, re.DOTALL).group(1))
    cv = re.search(r"Tailored CV:(.*?)Cover Letter:", response_text, re.DOTALL).group(1).strip()
    letter = re.search(r"Cover Letter:(.*)", response_text, re.DOTALL).group(1).strip()
    return score, keywords, cv, letter

def add_missing_keywords_to_skills(cv_text, keywords):
    pattern = re.compile(r"(Skills[:\n]+)(.*?)(\n\n|$)", re.IGNORECASE | re.DOTALL)
    def replacer(m):
        existing = set(re.split(r",|\n", m.group(2)))
        updated = ", ".join(sorted(existing.union(keywords)))
        return f"{m.group(1)}{updated}\n\n"
    return pattern.sub(replacer, cv_text) if pattern.search(cv_text) else f"{cv_text}\n\nSkills:\n{', '.join(sorted(set(keywords)))}\n"

def convert_text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

def generate_diff_html(original, tailored):
    diff = difflib.ndiff(original.strip().splitlines(), tailored.strip().splitlines())
    return "".join(
        f"<div style='background-color:#ffe6e6;'>❌ {line[2:]}</div>" if line.startswith("- ") else
        f"<div style='background-color:#e6ffe6;'>✅ {line[2:]}</div>" if line.startswith("+ ") else
        f"<div style='color:#666;'>{line[2:]}</div>" if line.startswith("  ") else ""
        for line in diff
    )
